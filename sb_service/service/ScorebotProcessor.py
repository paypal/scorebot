import logging
import os
import random
import re
import traceback
from logging import config
from django.utils import timezone
from django.utils.http import urlencode
from common import constants
from core.models import EnforcementMetrics, MessageList, PatternList, ScorebotConfig, ScorebotControlCpp, \
    ScorebotControlJava, ScorebotControlKraken, ScorebotMetrics
from sb_service.common import logging_util
from sb_service.service.EnforcementFunctions import EnforcementFunctions
from sb_service.service.ScorebotUsecases import ScorebotUsecases
from external_tools.common import exceptions
from external_tools.github.GithubConfig import GithubConfig
from external_tools.github.GithubAPI import GithubAPI
from external_tools.github.GithubPullRequest import GithubPullRequest
from packages.notifications.Email import Email


class ScorebotProcessor(object):
    def __init__(self, framework, processor="CI"):
        super(ScorebotProcessor, self).__init__()
        self.framework = framework
        self.processor = processor

        if self.framework == "CPP":
            self.ScorebotControl = ScorebotControlCpp
        elif self.framework == "Java":
            self.ScorebotControl = ScorebotControlJava
        elif self.framework == "Kraken":
            self.ScorebotControl = ScorebotControlKraken
        self.file_extensions_to_include = [x.strip(" ") for x in ScorebotConfig.objects.filter(
            config="file_extensions_" + str(self.framework)).values("value")[0]["value"].split(",")]
        self.pull_request_job = ""
        self.diff_patch = {}
        self.notify_pp = {}
        self.notify = {}
        self.p_levels = {}
        self.excluded_paths = {}

        self.github_config = GithubConfig()
        self.github_api = GithubAPI(self.github_config)
        self.pull_request = GithubPullRequest()

        self._processor_name = "Scorebot Processor " + str(self.framework)
        self.pull_request_url = self.pull_request.url

        self._logger = logging.getLogger(__name__)

        self.ScorebotUsecases = ScorebotUsecases(self.framework, self.pull_request, self._logger, processor)
        self.EnforcementFunctions = EnforcementFunctions(self.pull_request, self.file_extensions_to_include,
                                                         self._logger)
        self.EnforcementFunctions.p_levels = self.p_levels

    def _init_job_log(self, pull_request_url=None, repo_url=None, custom_field=None):
        """
        Set up the log for the job being processed.
        :param pull_request_url: pull request url for the active job
        :param repo_url: repo_url
        :param custom_field: field to use instead of repo name. e.g. push
        """
        self._logger.debug("_init_job_log")

        job_log_name = logging_util.get_job_log_name(pull_request_url=pull_request_url,
                                                     repo_url=repo_url,
                                                     custom_field=custom_field)
        logging.config.dictConfig(logging_util.get_logging_conf(self._processor_name, job_log_name))

    @staticmethod
    def notify_pp_helper():
        """
        If the mode is notify_pp, then we are sending a/b email
        :return mode and pp_var
        """

        mode = "notify"
        a_b = random.randint(1, 2)
        if a_b == 1:
            pp_var = "a"
        else:
            pp_var = "b"

        return mode, pp_var

    def finalize_web_hook_job(self, web_hook_job):
        """
        Finalize the Github web-hook job.
        :param web_hook_job: WebhookPR or WebhookPush object that has been processed.
        """
        self._logger.debug("_finalize_web_hook_job")

        web_hook_job.processed = True
        web_hook_job.completed_time = timezone.now()
        web_hook_job.save(update_fields=["processed", "completed_time"])

    def get_file_diff(self):
        """
        Get patch diff for the PR and parse file to create a dictionary,
        where key is the filename, and value is the diff patch
        """
        self._logger.debug("get_diff_patch")

        patch_content = self.github_api.get_diff_patch(self.pull_request.api_url)

        content_split = patch_content.decode("utf-8").split("diff --git a/")

        for diff in content_split:
            filename = diff[:diff.find(" b/")].strip()
            content = diff[diff.find("@@"):]
            self.diff_patch[filename] = content

    def clean_patch(self, patch, file_name):
        """
        Remove comments and removed lines from the changed code from the commit.
        :param patch: Changed code as part of the commit
        :param file_name: Changed file name as part of the commit
        :return: patch free of comments and removed lines
        """
        self._logger.debug("_clean_patch")
        pull_request_url = self.pull_request_url
        stripped_patch = []
        if patch is None:
            if not self.diff_patch:
                self.get_file_diff()
            if file_name in self.diff_patch:
                patch = self.diff_patch[file_name].decode("utf-8", "ignore")

        try:
            if not patch:
                return stripped_patch
            elif patch:
                # Remove removed lines from the patch
                patch1 = re.sub(re.compile("(?m)^-.*?$"), "", patch)
                # Remove comments of style /* comments */ from the patch
                patch2 = re.sub(re.compile("/\*.*?\*/", re.DOTALL), "", patch1)
                # Remove comments of style // comments from the patch
                stripped_patch = re.sub(re.compile("//.*?\n"), "", patch2)

        except Exception as err:
            self._logger.critical("Exception during clean patch: {0}\n{1}\n".format(type(err), traceback.format_exc())
                                  + pull_request_url)
            self.finalize_web_hook_job(pull_request_url)

        return stripped_patch

    def create_message(self, template, file_list, enforce_bool, generic_bool, security_category):
        curr_message = ""
        a_b_message = "\nThe appropriate actions must be taken before merging.\n" \
                      "Not fixing this might block the release of the code to production."

        header, intro, security_issue, how_to_fix, references, reference_name = template
        curr_message += "<b>" + header + "</b>\n\n" + intro + " #<a href=" + self.pull_request.url + ">" + \
                        str(self.pull_request.number) + "</a>"

        if self.notify_pp[security_category] == "b":
            curr_message += a_b_message

        # For enforce bool - file_list = set(filename, sha)
        # For non enforce - file_list = set(file names)

        if enforce_bool:
            exemption_url = ScorebotConfig.objects.filter(config="exception_url").values()[0]["value"]
            if generic_bool:
                files = "<table style='border: 1px solid black'><tr>" \
                        "<th style='border: 1px solid black'>Commit</th>" \
                        "<th style='border: 1px solid black'>Variable</th>" \
                        "<th style='border: 1px solid black'>Files(s)</th>" \
                        "<th style='border: 1px solid black'>Exemption Form</th></tr>"
                temp_d = {}
                for (variable, commit_list) in file_list:
                    for (filename, sha) in commit_list:
                        if sha not in temp_d:
                            temp_d[sha] = {variable: {filename}}
                        else:
                            if variable not in temp_d[sha]:
                                temp_d[sha].update({variable: {filename}})
                            else:
                                temp_d[sha][variable].add(filename)
                for sha in temp_d:
                    for (variable, file_list) in temp_d[sha].items():
                        exemption_url += "?" + urlencode(
                            {"pr": self.pull_request.url, "framework": self.framework, "commit_id": sha})
                        exemption_link = "<a href=" + exemption_url + ">Create exemption request</a>\n"
                        files += "<tr><td style='border: 1px solid black'>" + sha + \
                                 "</td><td style='border: 1px solid black'>" + variable + \
                                 "</td><td style='border: 1px solid black'>" + ",\n".join(list(file_list)) + \
                                 "</td><td style='border: 1px solid black'>" + exemption_link + \
                                 "</td></tr>"
                files += "</table>"
            else:
                files = "<table style='border: 1px solid black'><tr>" \
                        "<th style='border: 1px solid black'>Commit</th>" \
                        "<th style='border: 1px solid black'>File(s)</th>" \
                        "<th style='border: 1px solid black'>Exemption Form</th></tr>"
                temp_d = {}
                for (filename, sha) in file_list:
                    if sha not in temp_d:
                        temp_d[sha] = set([])
                    temp_d[sha].add(filename)
                for sha in temp_d:
                    exemption_url += "?" + urlencode({"pr": self.pull_request.url, "framework": self.framework,
                                                      "commit_id": sha})
                    exemption_link = "<a href=" + exemption_url + ">Create exemption request</a>\n"
                    files += "<tr><td style='border: 1px solid black'>" + sha + \
                             "</td><td style='border: 1px solid black'>" + ",\n".join(list(temp_d[sha])) + \
                             "</td><td style='border: 1px solid black'>" + exemption_link + \
                             "</td></tr>"
                files += "</table>"

        else:
            if generic_bool:
                files = "<table style='border: 1px solid black'><tr>" \
                        "<th style='border: 1px solid black'>Variable" \
                        "</th><th style='border: 1px solid black'>File(s)</th></tr>"
                for (variable, file_name) in file_list:
                    files += "<tr><td style='border: 1px solid black'>" + variable + \
                             "</td><td style='border: 1px solid black'>" + ",\n".join(list(file_name)) + \
                             "</td></tr>"
                files += "</table>"
            else:
                files = "<table style='border: 1px solid black'><tr>" \
                        "<th style='border: 1px solid black'>File(s)</th></tr>"
                for filename in list(file_list):
                    files += "<tr><td style='border: 1px solid black'>" + filename + "</td></tr>"
                files += "</table>"
        curr_message += files + "\n\n"

        if security_issue:
            curr_message += "\n\n<b>What is the security issue?</b>\n\n" + security_issue
        if how_to_fix:
            curr_message += "\n\n<b>How to fix it?</b>\n\n" + how_to_fix

        if references:
            curr_message += "\n\n<b>References:</b>\n"
            references = references.split("\r\n")
            reference_name = reference_name.split("\r\n")
            for ref in range(len(references)):
                curr_message += "<a href=" + references[ref] + ">" + reference_name[ref] + "</a>\n"
        curr_message += "\n\n\n\n"

        return curr_message

    def create_message_list(self, vulnerability_d, enforce_bool):
        """
        Create dictionary of messages to email, where key is security category
         and value is list of messages for the security category
        :param vulnerability_d: dictionary where key is security category and
        if enforced: value is dictionary of dictionaries, ordered by sha id,
                     then filename, and then set of patterns found
        if not-enforced: value is list of tuples with (variable, filename)
        :param enforce_bool: bool to determine whether to add commit info
        :return: dictionary with the messages
        """
        message_list = {}

        for security_category in vulnerability_d:
            message_list[security_category] = []
            messages = []
            # For enforce bool - d[pattern] = set(filename, sha)
            # For non enforce - d[pattern] = set(file names)
            variable_file_list = vulnerability_d[security_category]

            if self.framework == "CPP":
                messages = MessageList.objects.filter(security_category=security_category, cpp=True).values_list(
                    "function_name", "header", "intro", "security_issue", "how_to_fix", "references", "reference_name")
            elif self.framework == "Java":
                messages = MessageList.objects.filter(security_category=security_category, java=True).values_list(
                    "function_name", "header", "intro", "security_issue", "how_to_fix", "references", "reference_name")
            elif self.framework == "Kraken":
                messages = MessageList.objects.filter(security_category=security_category, kraken=True).values_list(
                    "function_name", "header", "intro", "security_issue", "how_to_fix", "references", "reference_name")

            temp_msg_d = {}
            generic_list = []
            for template in messages:
                # function name, header, intro, security issue, how to fix, references, reference name
                temp_msg_d[template[0]] = [(template[1], template[2], template[3], template[4], template[5],
                                            template[6])]

            for (variable, file_list) in variable_file_list.items():
                # File list for enforce bool - d[sha] = set(file names)
                # File list for non enforce bool - set(file names)
                if variable in temp_msg_d:
                    # Specific message for variable
                    generic_bool = False
                    template = temp_msg_d[variable]
                    curr_message = self.create_message(template[0], file_list, enforce_bool,
                                                       generic_bool, security_category)
                    message_list[security_category].append(curr_message)
                else:
                    # Generic message for category
                    generic_list.append((variable, file_list))
            if generic_list:
                generic_bool = True
                template = temp_msg_d[security_category]
                curr_message = self.create_message(template[0], generic_list, enforce_bool,
                                                   generic_bool, security_category)
                message_list[security_category].append(curr_message)

        return message_list

    def _add_comment_to_pull_request(self, pull_request, pr_comment):
        """
        Add the message to the pull request.
        :param pull_request: loaded pull request object
        :param pr_comment: List - List with banned function message and solution.
        :return:
        """
        self._logger.debug("_add_comment_to_pull_request")

        comment = "<pre>{0}</pre>".format("<br>".join(pr_comment))
        pull_request.comment_on_pull_request(comment)

    def _send_email_to_stakeholders(self, pull_request_url, owner, message_list):
        """
        Send email to the domain lock owners and the change owner.
        :param pull_request_url: URL of the pull request
        :param owner: username of the person who made the changes
        :param message_list: List of the vulnerabilities found and how to fix
        """
        self._logger.debug("_send_email_to_stakeholders")

        template_prefix = "score_bot_email"
        subject = "SCORE Bot: Detected possible insecure code in files changed by {0}"
        email_info = {"pull_request": pull_request_url, "owner": owner}
        owner_email = "{0}@{1}.com".format(owner, constants.DOMAIN)

        score_bot_email = Email()
        email_info["message"] = message_list
        recipients = "{0}".format(owner_email) + ", " + constants.SCOREBOT_DL_EMAIL_ADDRESS
        email_subject = subject.format(owner)
        score_bot_email.send_email(template_prefix, email_subject, recipients, email_info)

    def scan_files(self, category_list, files_to_scan, enforce_bool, status, sha, exempt):
        """
        Scan for all categories for each file
        :param category_list: list of tuples with (use cases, mode) to be scanned for
        :param files_to_scan: list of objects with metadata like filename, status, etc
        :param enforce_bool: bool for whether enforced or not
        :param status: status of the commit for enforcement
        :param sha: commit id to record in metrics
        :param exempt: exemption status
        :return: dictionary of all found vulnerabilities
        """
        excluded_folder_found = []
        excluded_path_found = []
        exclude_folders = []
        search_patch_categories = []
        vulnerability_d = {}

        self.file_extensions_to_include = [x.strip(" ") for x in ScorebotConfig.objects.
            filter(config="file_extensions_" + str(self.framework)).values("value")[0]["value"].split(",")]

        if self.framework == "CPP":
            search_patch_categories = list(set(PatternList.objects.filter(cpp=True).values_list("security_category",
                                                                                                flat=True)))
            exclude_folders = ScorebotConfig.objects.filter(config="excluded_folders", cpp=True).values("value")

        elif self.framework == "Java":
            search_patch_categories = list(set(PatternList.objects.filter(java=True).values_list("security_category",
                                                                                                 flat=True)))
            exclude_folders = ScorebotConfig.objects.filter(config="excluded_folders", java=True).values("value")

        elif self.framework == "Kraken":
            search_patch_categories = list(set(PatternList.objects.filter(kraken=True).values_list("security_category",
                                                                                                   flat=True)))
            exclude_folders = ScorebotConfig.objects.filter(config="excluded_folders", kraken=True).values("value")

        if exclude_folders:
            exclude_folders = [x.strip(" ") for x in exclude_folders[0]["value"].split(",")]

        for item in files_to_scan:
            filename = item["filename"]
            if exclude_folders:
                excluded_folder_found = [folder_name for folder_name in exclude_folders if
                                         re.findall("(^" + folder_name + "/)|(/" + folder_name + "/)",
                                                    filename.lower())]
            if excluded_folder_found:
                continue
            if item["status"] == "removed":
                continue

            # Go through each security category and determine if file scans and patch scans
            for (security_category, mode) in category_list:
                excluded_paths = self.excluded_paths[security_category].split(",")
                if excluded_paths:
                    excluded_path_found = [folder_name for folder_name in excluded_paths if
                                           re.findall("(^" + folder_name.strip() + "/)|"
                                                      "(/" + folder_name.strip() + "/)", filename.lower())]
                if excluded_path_found:
                    continue
                vulnerability_found = False
                patterns_found = []
                file_list_d = {}
                ext = os.path.splitext(filename)[1]
                if ext.lower() in self.file_extensions_to_include:
                    if "patch" in item:
                        # Scan patch
                        stripped_patch = self.clean_patch(item["patch"], filename)
                        if security_category in search_patch_categories:
                            patterns_found, vulnerability_found = self.ScorebotUsecases.\
                                scan_patch_pattern(stripped_patch, security_category)

                if vulnerability_found:
                    vulnerability_d, file_list_d, status = self.record_metrics(patterns_found, enforce_bool,
                                                                               filename, sha, security_category,
                                                                               exempt, mode, file_list_d,
                                                                               vulnerability_d, status)

        return vulnerability_d, status

    def record_metrics(self, patterns_found, enforce_bool, filename, sha, security_category, exempt, mode,
                       file_list_d, vulnerability_d, status):
        for pattern in patterns_found:
            if enforce_bool:
                # Record in enforce metrics
                if exempt:
                    metrics_status = "exemption"
                else:
                    metrics_status = "failure"
                    status = "failure"

                EnforcementMetrics.objects.create(function_name=pattern,
                                                  priority_level=self.p_levels[security_category],
                                                  security_category=security_category,
                                                  framework=self.framework,
                                                  file_name=filename,
                                                  pull_request_url=self.pull_request.url,
                                                  repo=self.pull_request.base_repo.name,
                                                  branch=self.pull_request.base_repo.ref,
                                                  commit_id=sha,
                                                  user=self.pull_request.user.username.decode("utf-8"),
                                                  notification_pp=self.notify_pp[security_category],
                                                  status=metrics_status)

                if mode is not "silent":
                    if sha not in file_list_d:
                        file_list_d[pattern] = set([])
                    file_list_d[pattern].add((filename, sha))
                else:
                    status = "silent"

            else:
                recorded_metrics = ScorebotMetrics.objects.filter(function_name=pattern,
                                                                  file_name=filename,
                                                                  pull_request_url=self.pull_request.url). \
                    values_list("function_name")
                if not recorded_metrics:
                    ScorebotMetrics.objects.create(
                        function_name=pattern,
                        priority_level=self.p_levels[security_category],
                        security_category=security_category,
                        framework=self.framework,
                        file_name=filename,
                        user=self.pull_request.user.username.decode("utf-8"),
                        repo=self.pull_request.base_repo.name,
                        branch=self.pull_request.base_repo.ref,
                        pull_request_url=self.pull_request.url,
                        scorebot_mode=mode,
                        notification_pp=self.notify_pp[security_category],
                        post_process=False)

                    if mode is not "silent":
                        if pattern not in file_list_d:
                            file_list_d[pattern] = set([])
                        file_list_d[pattern].add(filename)

        if file_list_d:
            if security_category not in vulnerability_d:
                vulnerability_d[security_category] = file_list_d
            else:
                for p in file_list_d:
                    if p not in vulnerability_d[security_category]:
                        vulnerability_d[security_category][p] = file_list_d[p]
                    else:
                        vulnerability_d[security_category][p].update(file_list_d[p])
        return vulnerability_d, file_list_d, status

    def _scan_pull_request(self, category_list):
        """
        Scans each pull request file with all the applicable security categories
        :param category_list: List of tuples with (SCORE Bot categories, mode) to process
        return: two dictionaries, with enforced and non-enforced use cases
        """

        enforce_use_cases = []
        enforce_bool = False
        exempt = False
        excluded_commit = []
        enforce_d = {}
        sha = ""
        status = ""

        whitelist_apps = [x.strip(" ") for x in ScorebotConfig.objects.filter(config="enforcement_whitelist").
                          values("value")[0]["value"].split(",")]
        enforced_branch = [x.strip(" ") for x in ScorebotConfig.objects.filter(config="enforcement_branches").
                           values("value")[0]["value"].split(",")]
        blacklist_apps = [x.strip(" ") for x in ScorebotConfig.objects.filter(config="enforcement_blacklist").
                          values("value")[0]["value"].split(",")]
        exclude_commits = [x.strip(" ") for x in ScorebotConfig.objects.filter(config="excluded_commits").
                           values("value")[0]["value"].split(",")]

        if self.pull_request.base_repo.name.lower() not in blacklist_apps:
            if str(whitelist_apps[0]).strip(" ") == "none" or \
                            self.pull_request.base_repo.name.lower() in [i.strip(" ") for i in whitelist_apps]:
                if enforced_branch and \
                   self.pull_request.base_repo.ref.lower() in [i.strip(" ") for i in enforced_branch]:
                    enforce_use_cases = self.ScorebotControl.objects.filter(enforce=True).\
                        values_list("security_category", flat=True)

        if enforce_use_cases:
            all_enforced_category = \
                [(sec_cat, mode) for (sec_cat, mode) in category_list if sec_cat in enforce_use_cases]
            api_url = self.pull_request.base_repo.api_url

            # If cannot enforce, scan normally
            enforce_bool = self.EnforcementFunctions.check_write_permission(api_url, self.framework)
            if enforce_bool:
                enforced_commits = list(set(EnforcementMetrics.objects.filter(repo=self.pull_request.base_repo.name,
                                                                              framework=self.framework).
                                            values_list("commit_id", "status", "pull_request_url", "function_name",
                                                        "security_category", "framework", "notification_pp")))
                enforced_commit_id = [commit_id for (commit_id, status, pr, func, sec_cat, framework, pp) in
                                      enforced_commits]

                for commit in self.pull_request.commits:
                    category_enforce_list = all_enforced_category
                    silent_modes = [mode for (category, mode) in category_enforce_list if mode == "silent"]
                    status = "silent" if len(silent_modes) == len(category_enforce_list) else "success"
                    sha = commit.sha
                    commit_url = api_url + "/commits/" + sha
                    status_url = api_url + "/statuses/" + sha
                    override_status = ""

                    if exclude_commits:
                        excluded_commit = [desc for desc in exclude_commits if re.findall(desc.strip(), commit.subject)]

                    if excluded_commit:
                        if status != "silent":
                            data = {"state": status,
                                    "context": constants.STATUS_CONTEXT,
                                    "description": "SCORE Bot"}
                            self.github_api.post_status_check(status_url, data)
                        continue

                    # If commit id enforced previously
                    if sha in enforced_commit_id:
                        override_status, category_enforce_list, exempt, enforced_failures_d = \
                            self.EnforcementFunctions.get_enforced_commits(category_enforce_list, enforced_commits, sha)

                        for category in enforced_failures_d:
                            if category not in enforce_d:
                                enforce_d[category] = enforced_failures_d[category]

                            else:
                                for pattern in enforced_failures_d[category]:
                                    if pattern not in enforce_d[category]:
                                        enforce_d[category][pattern] = enforced_failures_d[category][pattern]

                                    else:
                                        enforce_d[category][pattern].update(enforced_failures_d[category][pattern])

                    # Get all the files to be scanned
                    commit_files = self.github_api.get_commit_patch(commit_url.strip())["files"]
                    enforce_d_temp, status = self.scan_files(category_enforce_list, commit_files, enforce_bool, status,
                                                             sha, exempt)

                    if override_status:
                        status = override_status

                    for category in enforce_d_temp:
                        if category not in enforce_d:
                            enforce_d[category] = enforce_d_temp[category]
                        else:
                            for pattern in enforce_d_temp[category]:
                                if pattern not in enforce_d[category]:
                                    enforce_d[category][pattern] = enforce_d_temp[category][pattern]
                                else:
                                    enforce_d[category][pattern].update(enforce_d_temp[category][pattern])

                    if status is not "silent":
                        data = {"state": status,
                                "context": constants.STATUS_CONTEXT,
                                "description": "SCORE Bot"}
                        self.github_api.post_status_check(status_url, data)

                # Prevent duplicate scanning for enforce/non-enforce
                category_list = list(set(category_list) - set(all_enforced_category))
                enforce_bool = False
                exempt = False

        # Non-enforce use cases
        pr_files, header = self.github_api.process_api_query_with_header(self.pull_request.files_url)
        non_enforce_d, status = self.scan_files(category_list, pr_files, enforce_bool, status, sha, exempt)

        return enforce_d, non_enforce_d

    def process_pull_request(self, pull_request_job):
        """
        Process the Github web-hook branch pull request data that is queued up:
            - Check if the pull request has any security vulnerabilities.
              If yes add comment to the pull request and send email (if notify)
        :param pull_request_job: WebhookPR object that has not been processed.
        """
        self.pull_request_job = pull_request_job
        pull_request_url = pull_request_job.pull_request_url
        self._init_job_log(pull_request_url=pull_request_url)
        self._logger.info("process_pull_request: {}".format(pull_request_url))

        try:
            # Load the pull request
            try:
                self.pull_request.load(self.github_config, pull_request_url, True)
            except Exception as err:
                self.finalize_web_hook_job(pull_request_job)
                self._logger.critical("{0}\n{1}\n".format(type(err), traceback.format_exc()) + self.pull_request.url)

            # Load p_levels for each use case
            use_case_config_list = self.ScorebotControl.objects.values_list("security_category", "priority_level",
                                                                            "excluded_paths")
            for (sec_cat, p_level, exclude_path) in use_case_config_list:
                self.p_levels[sec_cat] = p_level
                self.excluded_paths[sec_cat] = exclude_path

            if self.pull_request.loaded and self.pull_request.files:
                category_list = []
                # Check notify_pp mode (a/b email)
                notify_pp_list = self.ScorebotControl.objects.filter(silent=False, notify=True, notify_pp=True).\
                    values_list("security_category", flat=True)
                self._logger.info("Categories with notify_pp mode on: {}".format(notify_pp_list))

                # Determine a/b message
                for category in notify_pp_list:
                    mode, ab_var = self.notify_pp_helper()
                    category_list.append((category, mode))
                    self.notify_pp[category] = ab_var

                # Check notify mode
                notify_list = self.ScorebotControl.objects.filter(silent=False, notify=True, notify_pp=False).\
                    values_list("security_category", flat=True)
                self._logger.info("Categories with notify only mode on: {}".format(notify_list))

                # Check for silent mode use cases
                silent_list = self.ScorebotControl.objects.filter(silent=True).values_list("security_category",
                                                                                           flat=True)
                self._logger.info("Categories with silent only mode on: {}".format(silent_list))

                for (category, mode) in [(category, "notify") for category in notify_list] + \
                                        [(category, "silent") for category in silent_list]:
                    ab_var = "no"
                    category_list.append((category, mode))
                    self.notify_pp[category] = ab_var

                enforced_d, non_enforce_d = self._scan_pull_request(category_list)
                message_list = []
                duplicate_msg_list = []

                if enforced_d:
                    enforced = True
                    message_list = ["<h3>SCORE Bot Message</h3>Fix the following security issues before merging:"]
                    msg_enforced = self.create_message_list(enforced_d, enforced)
                    for sec_cat in msg_enforced:
                        message_list.append("\n\n\n\n".join(msg_enforced[sec_cat]))
                if non_enforce_d:
                    enforced = False
                    message_list += ["<h3>SCORE Bot Warnings</h3>"]
                    msg_non_enforced = self.create_message_list(non_enforce_d, enforced)
                    for sec_cat in msg_non_enforced:
                        message_list.append("\n\n\n\n".join(msg_non_enforced[sec_cat]))

                if message_list:
                    user = self.pull_request.user.username.decode("utf-8")
                    self._add_comment_to_pull_request(self.pull_request, message_list)
                    self._send_email_to_stakeholders(self.pull_request.url,
                                                     user,
                                                     message_list)

                # Send additional email to separate DL
                if duplicate_msg_list:
                    for (sec_cat, extra_message) in duplicate_msg_list:
                        self._send_email_to_stakeholders(self.pull_request.url,
                                                         self.pull_request.user.username.decode("utf-8"),
                                                         extra_message)

            else:
                self._logger.error("Pull request not loaded or missing files: {0}".format(self.pull_request.url))

            self.finalize_web_hook_job(pull_request_job)
        except exceptions.GithubAPIError:
            pull_request_url = pull_request_job.pull_request_url
            self.finalize_web_hook_job(pull_request_job)
            self._logger.critical("Invalid pull request:  " + pull_request_url)
            pass
        except ConnectionError:
            self.finalize_web_hook_job(pull_request_job)
            self._logger.critical("Github Connection Error:  " + self.pull_request.url)
            pass

        except Exception as err:
            self.finalize_web_hook_job(pull_request_job)
            self._logger.critical("{0}\n{1}\n".format(type(err), traceback.format_exc()) + self.pull_request.url)

