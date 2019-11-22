import re
import traceback
from external_tools.github.GithubAPI import GithubAPI
from external_tools.github.GithubConfig import GithubConfig

from common import constants
from core.models import BlacklistedPrsLog, EnforcementMetrics


class EnforcementFunctions:
    def __init__(self, pull_request, file_extensions, logger):
        self.pull_request = pull_request
        self.file_extensions_to_include = file_extensions
        self._logger = logger
        self.github_config = GithubConfig()
        self.p_levels = {}

    def check_write_permission(self, api_url, framework):
        github_api = GithubAPI(self.github_config)
        enforce_bool = True

        collab_url = api_url + "/collaborators/"
        user = "SCORE-Bot"

        try:
            github_api.check_user_permission(collab_url, user)["permission"]
        except Exception as err:
            BlacklistedPrsLog.objects.create(pull_request_url=self.pull_request.url,
                                             user=self.pull_request.user.username.decode("utf-8"),
                                             repo=self.pull_request.base_repo.name,
                                             framework=framework)
            self._logger.info("{0}\n{1}\n".format(type(err), traceback.format_exc()) + self.pull_request.url)
            self._logger.info("No permission to update commit status on: " + self.pull_request.url)
            enforce_bool = False

        return enforce_bool

    def get_exemption(self, framework, pull_request_url, commit_id):
        github_api = GithubAPI(self.github_config)
        # Update metrics
        repo = re.findall(r"(?<=https://github.{0}.com/)(.*?)(?=/pull)".format(constants.GITHUB_DOMAIN), pull_request_url)[0].split("/")[1]
        EnforcementMetrics.objects.filter(repo=repo, commit_id=commit_id, framework=framework, status="failure").\
            update(status="exemption")
        api_url = github_api.generate_api_url_from_pull_request_url(pull_request_url)
        api_url = api_url[:api_url.find("/pulls/")]
        status_url = api_url + "/statuses/" + commit_id
        data = {"state": "success",
                "context": constants.STATUS_CONTEXT,
                "description": "SCORE Bot exemption"}
        github_api.post_status_check(status_url, data)

    def get_enforced_commits(self, category_enforce_list, enforced_commits, sha):
        # Get all the security categories that have been enforced previously
        enforced_sec_cat = list(set([sec_cat for (commit_id, status, pr, func, sec_cat, framework, pp) in
                                     enforced_commits if commit_id == sha]))
        status_framework = [(curr_status, framework) for (commit_id, curr_status, pr, func, sec_cat, framework, pp) in
                            enforced_commits if commit_id == sha][0]
        commit_status = status_framework[0]
        exempt = False
        if commit_status == "exemption":
            metrics_status = "exemption"
            status = "success"
            exempt = True
        elif commit_status == "silent":
            metrics_status = "silent"
            status = "silent"
        else:
            metrics_status = "failure"
            status = "failure"

        updated_enforce_list = []
        enforce_vulnerability_d = {}
        for (security_category, mode) in category_enforce_list:
            file_list_d = {}
            if security_category in enforced_sec_cat:
                # Check if scanned use case previously & get list of variables to record in metrics
                func_list = list(set([(func, pp) for (commit_id, status, pr, func, sec_cat, framework, pp) in
                                 enforced_commits if (commit_id == sha and sec_cat == security_category)]))
                committed_prs = list(set([pr for (commit_id, status, pr, func, sec_cat, framework, pp) in
                                         enforced_commits if (commit_id == sha and sec_cat == security_category)]))

                for function_name in func_list:
                    if self.pull_request.url not in committed_prs:
                        filename_list = list(set(EnforcementMetrics.objects.filter(function_name=function_name,
                                                                                   pull_request_url=committed_prs[0],
                                                                                   commit_id=sha,
                                                                                   security_category=security_category).
                                                 values_list('file_name', flat=True)))
                        for filename in filename_list:
                            EnforcementMetrics.objects.create(function_name=function_name,
                                                              priority_level=self.p_levels[security_category],
                                                              framework=status_framework[1],
                                                              security_category=security_category,
                                                              file_name=filename,
                                                              pull_request_url=self.pull_request.url,
                                                              repo=self.pull_request.base_repo.name,
                                                              branch=self.pull_request.base_repo.ref,
                                                              commit_id=sha,
                                                              user=self.pull_request.user.username.decode("utf-8"),
                                                              status=metrics_status)

                            if metrics_status is not "silent" and metrics_status is not "exemption":
                                if function_name not in file_list_d:
                                    file_list_d[function_name] = set([])

                                file_list_d[function_name].add((filename, sha))
            else:
                updated_enforce_list.append((security_category, mode))
            if file_list_d:
                if security_category not in enforce_vulnerability_d:
                    enforce_vulnerability_d[security_category] = file_list_d
                else:
                    for p in file_list_d:
                        if p not in enforce_vulnerability_d[security_category]:
                            enforce_vulnerability_d[security_category][p] = file_list_d[p]
                        else:
                            enforce_vulnerability_d[security_category][p].update(file_list_d[p])

        return status, updated_enforce_list, exempt, enforce_vulnerability_d
