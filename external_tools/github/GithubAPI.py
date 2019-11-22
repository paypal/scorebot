"""
Class to query GitHub's REST APIs
"""
import json
import logging
import re
import requests
import traceback

from external_tools.common import exceptions


class GithubAPI(object):
    """
    A class to query GitHub's REST APIs
    Unit tests: test_GithubAPI.py
    """
    PULL_PARSE_REGEX = re.compile(r"(?:https://)(?:\S+?)/(\S+?)/(\S+?)/pull/(\d+)")
    PULL_REQUEST_API_URL_TMPLT = "{host}repos/{org}/{repo}/pulls/{pull_number}"
    CREATE_PULL_REQUEST_API_URL_TMPLT = "{host}repos/{org}/{repo}/pulls"
    COMPARE_BRANCH_API_URL_TMPLT = "{host}repos/{org}/{repo}/compare/{base}...{head}"
    LANGUAGE_API_URL_TMPLT = "{host}repos/{org}/{repo}/languages"

    def __init__(self, config):
        self._logger = logging.getLogger(__name__)
        self._config = config
        self._header = {"content-type": "application/json",
                        "Authorization": "token {0}".format(self._config.token)}
        self._json_indent = 2

    def _get_message(self, response_data):
        """
        Get the message from the response_data and return it.
        If there is no message then return "".
            example response_data:
                {
                    "documentation_url":
                        "https://developer.github.com/enterprise/2.2/v3/pulls/#merge-a-pull-request-merge-button",
                    "message": "Base branch was modified. Review and try the merge again."
                }
        :param response_data: response that contains the message we want
        :return: message if it is exists else ""
        """
        message = "No message data available"

        try:
            if response_data.get("message"):
                message = response_data.get("message")

                if response_data.get("errors"):
                    error_message = []
                    errors = response_data.get("errors")

                    for error in errors:
                        if error.get("message"):
                            error_message.append(error.get("message"))

                    if error_message:
                        message = "{0}: {1}".format(message, ",".join(error_message))

        except Exception as err:
            self._logger.error("Could not parse message from response_data.")
            self._logger.error("\n{0}\n{1}\n".format(type(err), traceback.format_exc()))

        return message

    def _parse_response_data(self, response):
        """
        Use in the case of a bad response.status_code to safely parse out the reason for the failure.
        Handles parsing the response to json if possible
        else check to see if there is a reason in the payload and use that with the status code.

            ex. if 200 <= response.status_code < 300:
                    response_data = response.json()
                    return response_data
                else:
                    response_data = self._parse_response_data(response)
                    ...

        :param response: API response payload
        :return: dict with response as json if it exists else code with reason
        """
        try:
            response_data = response.json()

        except Exception as err:
            # json failed so try to read the reason and status code from the response
            self._logger.error("{0} {1}".format(type(err), "Could not parse response as json."))

            if getattr(response, "reason"):
                message = "{0} {1}".format(response.status_code, response.reason)

            else:
                message = "No message data available"
            response_data = {"message": message}

        return response_data

    def parse_pull_request_url(self, pull_url):
        """
        Parse a GitHub pull request URL and return the org, repo, and pull request number.
        :param pull_url: GitHub pull request URL
        :return: Tuple consisting of org, repo, pull_number
        :raise GithubError
        """
        match = self.PULL_PARSE_REGEX.match(pull_url)
        if not match:
            raise exceptions.GithubError("Invalid URL")

        org = match.group(1)
        repo = match.group(2)
        pull_number = match.group(3)
        return org, repo, pull_number

    def generate_api_url_from_pull_request_url(self, pull_request_url):
        """
        Create and return a GitHub API URL from a GitHub pull request URL.
        :param pull_request_url: GitHub pull request URL
        :return: GitHub API URL to retrieve a pull request
        :raise GithubError
        """
        try:
            org, repo, pull_number = self.parse_pull_request_url(pull_request_url)
            return self.PULL_REQUEST_API_URL_TMPLT.format(host=self._config.api_url,
                                                          org=org,
                                                          repo=repo,
                                                          pull_number=pull_number)

        except exceptions.GithubError as err:
            self._logger.error("Could not parse {0}.".format(pull_request_url))
            self._logger.error("\n{0}\n{1}\n".format(type(err), traceback.format_exc()))
            raise

    def process_api_query(self, query_url):
        """
        Make the GitHub API call for a URL and return the response.
        :param query_url: GitHub API URL
        :return: json response data from the API call and the header data
        :raise GithubAPIError
        """
        self._logger.info("Calling GitHub API for URL: {0}".format(query_url))

        response = requests.get(query_url, headers=self._header)
        if 200 <= response.status_code < 300:
            return response.json()

        else:
            response_data = self._parse_response_data(response)
            message = self._get_message(response_data)
            error_message = "Error getting pull request from GitHub: {0} : {1}".format(query_url, message)
            self._logger.error(error_message)
            self._logger.error(json.dumps(response_data, sort_keys=True, indent=self._json_indent))
            raise exceptions.GithubAPIError(response.status_code, error_message)

    def process_api_query_with_header(self, query_url):
        """
        Make the GitHub API call for a URL and return the response and header data.
        Note: Header data is needed to parse any data that is paginated. e.g. files and commits
        :param query_url: GitHub API URL
        :return: json response data from the API call and the header data
        :raise GithubAPIError
        """
        self._logger.info("Calling GitHub API for URL: {0}".format(query_url))

        response = requests.get(query_url, headers=self._header)
        if 200 <= response.status_code < 300:
            return response.json(), response

        else:
            response_data = self._parse_response_data(response)
            message = self._get_message(response_data)
            error_message = "Error getting pull request from GitHub: {0} : {1}".format(query_url, message)
            self._logger.error(error_message)
            self._logger.error(json.dumps(response_data, sort_keys=True, indent=self._json_indent))
            raise exceptions.GithubAPIError(response.status_code, error_message)

    def get_a_file(self, query_url):
        """
        Make the GitHub API call using "application/vnd.github.v3.raw" in the header to get a raw file.
        :param query_url: GitHub API URL to retrieve the contents of a file
        :return: raw file data
        :raise GithubAPIError
        """
        self._logger.info("Calling GitHub API for file URL: {0}".format(query_url))

        temp = "scorebot"
        headers = {"Accept": "application/vnd.github.v3.raw",
                   "Authorization": "token {0}".format(self._config.token),
                   "Ref": "{0}".format(temp)}

        response = requests.get(query_url, headers=headers)
        if 200 <= response.status_code < 300:
            # Need content here instead of json since it is raw file
            response_data = response.content
            return response_data

        else:
            response_data = self._parse_response_data(response)
            message = self._get_message(response_data)
            error_message = "Error getting file from GitHub: {0} : {1}".format(query_url, message)
            self._logger.error(error_message)
            self._logger.error(json.dumps(response_data, sort_keys=True, indent=self._json_indent))
            raise exceptions.GithubAPIError(response.status_code, error_message)

    def get_diff_patch(self, pull_url, patch=False):
        """
        Make the GitHub API call to get the diff or patch of the pull request.
        If patch == False then diff, else if patch == True then patch.
        :param pull_url: GitHub API URL
        :param patch: Boolean: True if you want patch, False if you want diff.
        :return: raw diff patch of the PR
        """
        self._logger.info("Calling GitHub API for diff patch: {0}".format(pull_url))
        headers = {"content-type": "application/json",
                   "Authorization": "token {0}".format(self._config.token)}
        if patch:
            headers["Accept"] = "application/vnd.github.patch"
        else:
            headers["Accept"] = "application/vnd.github.diff"

        response = requests.get(pull_url, headers=headers)
        if 200 <= response.status_code < 300:
            # Need content here since it is a raw file
            response_data = response.content
            return response_data
        else:
            response_data = self._parse_response_data(response)
            message = self._get_message(response_data)
            error_message = "Error getting diff patch data from Github: {0} : {1}".format(pull_url, message)
            self._logger.error(error_message)
            self._logger.error(json.dumps(response_data, sort_keys=True, indent=self._json_indent))
            raise exceptions.GithubAPIError(response.status_code, error_message)

    def add_pull_request_comment(self, comments_url, pull_request_comment=""):
        """
        Make the GitHub API call to add a comment to the pull request.
        :param comments_url: GitHub API URL used to add the comment to the pull request
        :param pull_request_comment: Comment to add to the pull request
        :return: json response from the API call
        :raise GithubAPIError
        """
        self._logger.info("{0} Adding Comment: {1}".format(comments_url, pull_request_comment))

        data = {"body": pull_request_comment}
        response = requests.post(comments_url, headers=self._header, data=json.dumps(data))
        if 200 <= response.status_code < 300:
            return response.json()
        else:
            response_data = self._parse_response_data(response)
            message = self._get_message(response_data)
            error_message = "Error adding comment to GitHub Pull Request: {0} : {1}".format(comments_url, message)
            self._logger.error(error_message)
            self._logger.error(json.dumps(response_data, sort_keys=True, indent=self._json_indent))
            raise exceptions.GithubAPIError(response.status_code, error_message)

    def execute_pull_request(self, pull_url, commit_comment=""):
        """
        Make the GitHub API call for a URL to execute (merge) the pull request and return the response.
        :param pull_url: GitHub API URL
        :param commit_comment: Comment to add to the commit
        :return: json response from the API call
        :raise GithubAPIQueryError
        """
        github_url = "{0}{1}".format(pull_url, "/merge")
        self._logger.info("Executing Pull Request: {0}".format(github_url))

        data = {"commit_message": commit_comment}
        response = requests.put(github_url, headers=self._header, data=json.dumps(data))
        if 200 <= response.status_code < 300:
            return response.json()

        else:
            response_data = self._parse_response_data(response)
            message = self._get_message(response_data)
            error_message = "Error executing GitHub Pull Request: {0} : {1}".format(github_url, message)
            self._logger.error(error_message)
            self._logger.error(json.dumps(response_data, sort_keys=True, indent=self._json_indent))
            raise exceptions.GithubAPIError(response.status_code, error_message)

    def close_pull_request(self, pull_url):
        """
        Make the GitHub API call for a URL to close the pull request and return the response.
        :param pull_url: GitHub API URL
        :return: json response from the API call
        :raise GithubAPIQueryError
        """
        self._logger.info("Closing Pull Request: {0}".format(pull_url))

        data = {"state": "closed"}
        response = requests.patch(pull_url, headers=self._header, data=json.dumps(data))
        if 200 <= response.status_code < 300:
            return response.json()

        else:
            response_data = self._parse_response_data(response)
            message = self._get_message(response_data)
            error_message = "Error closing GitHub Pull Request: {0} : {1}".format(pull_url, message)
            self._logger.error(error_message)
            self._logger.error(json.dumps(response_data, sort_keys=True, indent=self._json_indent))
            raise exceptions.GithubAPIError(response.status_code, error_message)

    def update_pull_request(self, pull_url, data):
        """
        Make the GitHub API call for a URL to update the pull request and return the response.
        :param pull_url: GitHub pull request url to update 
        :param data: data which is dictionary contains title,body,state to update
        :return: json response from the API call
        :raise GithubAPIQueryError
        """
        self._logger.info("Updating Pull Request: {0}".format(pull_url))

        github_update_url = self.generate_api_url_from_pull_request_url(pull_url)
        response = requests.patch(github_update_url, headers=self._header, data=json.dumps(data))
        if 200 <= response.status_code < 300:
            return response.json()

        else:
            response_data = self._parse_response_data(response)
            message = self._get_message(response_data)
            error_message = "Error updating GitHub Pull Request: {0} : {1}".format(pull_url, message)
            self._logger.error(error_message)
            self._logger.error(json.dumps(response_data, sort_keys=True, indent=self._json_indent))
            raise exceptions.GithubAPIError(response.status_code, error_message)

    def get_pull_requests(self, owner, repo, data):
        """
        Get all the pull requests for the given owner(or org)/repo and data(mainly head and base).
        :param owner: owner or org whichever is applicable.
        :param repo: name of the repo e.g. code or pexml
        :param data: which is dictionary
                   state	Either open, closed, or all to filter by state. Default: open
                   head		Filter pulls by head user and branch name in the format of user:ref-name.
                            Example: github:new-script-format.
                   base		Filter pulls by base branch name. Example: gh-pages.
                   sort		What to sort results by. Can be either created, updated, popularity (comment count)
                            or long-running (age, filtering by pulls updated in the last month). Default: created
                   direction	The direction of the sort. Can be either asc or desc.
                                Default: desc when sort is created or sort is not specified, otherwise asc.
        :return: list of pull requests data
        :raise GithubAPIQueryError
        """
        github_get_pull_requests_url = self.CREATE_PULL_REQUEST_API_URL_TMPLT.format(host=self._config.api_url,
                                                                                     org=owner, repo=repo)
        response = requests.get(github_get_pull_requests_url, headers=self._header, params=data)
        if 200 == response.status_code:
            return response.json()
        else:
            response_data = self._parse_response_data(response)
            message = self._get_message(response_data)
            error_message = "Error listing GitHub Pull Request: {0} : {1} : {2}".format(owner, repo, message)
            self._logger.error(error_message)
            self._logger.error(json.dumps(response_data, sort_keys=True, indent=self._json_indent))
            raise exceptions.GithubAPIError(response.status_code, error_message)

    def clone_pull_request(self, orig_pull_request_url, new_title, new_target, orig_head, use_orig_head):
        """
        Make the GitHub API call for a URL to clone the pull request and return the response
        :param orig_pull_request_url: GitHub pull request API
        :param new_title: title for the new pull request
        :param new_target: target branch(or base parameter for the GitHub create pull request API)
        :param orig_head: if client provides head information, use that to create pull request
        :param use_orig_head: indicator to use the original head
        :return: newly created pull request
        :raise GithubAPIQueryError
        """
        self._logger.info("clone_pull_request: {0}".format(orig_pull_request_url))

        try:
            org, repo, pull_number = self.parse_pull_request_url(orig_pull_request_url)
            github_create_pull_request_url = self.CREATE_PULL_REQUEST_API_URL_TMPLT.format(host=self._config.api_url,
                                                                                           org=org, repo=repo)
            _new_body = "propagation of {0} to {1}".format(orig_pull_request_url, new_target)

            if use_orig_head:
                # Keep the source branch same indicated by the client
                _head = orig_head

            else:
                _head = "refs/pull/{0}/head".format(pull_number)

            _payload = dict(maintainer_can_modify=False, title=new_title, body=_new_body, head=_head, base=new_target)
            self._logger.info("github_create_pull_request_url : {0}".format(github_create_pull_request_url))
            self._logger.info("payload : {0}".format(_payload))
            response = requests.post(github_create_pull_request_url,
                                     headers=self._header,
                                     data=json.dumps(_payload))

            if 200 <= response.status_code < 300:
                return response.json()

            else:
                response_data = self._parse_response_data(response)
                message = self._get_message(response_data)
                error_message = "Error Creating GitHub Pull Request: {0} : {1}".format(github_create_pull_request_url,
                                                                                       message)
                self._logger.error(error_message)
                self._logger.error(json.dumps(response_data, sort_keys=True, indent=self._json_indent))
                raise exceptions.GithubAPIError(response.status_code, error_message)

        except exceptions.GithubError as err:
            self._logger.error("\n{0}\n{1}\n".format(type(err), traceback.format_exc()))
            raise

    def create_pull_request(self, org, repo, data):
        """
        Create the pull requests for the given org, repo and data(mainly head and base).
        :param org: owner or org whichever is applicable
        :param repo: name of the repo e.g. code or pexml.
        :param data: which is dictionary
            head	 head for the pull request i.e. master or release.
            base	 base(or target branch) for the pull request.
            title	 title of the pull request
            body 	 body of the pull request
        :return: response of the create pull request API
        :raise GithubAPIQueryError
        """
        self._logger.info("create_pull_request: {0}".format(data))

        try:
            _head = data["head"]
            _base = data["base"]
            _title = data["title"]
            _body = data["body"]
            github_create_pull_request_url = self.CREATE_PULL_REQUEST_API_URL_TMPLT.format(host=self._config.api_url,
                                                                                           org=org, repo=repo)
            _payload = dict(maintainer_can_modify=False, title=_title, body=_body, head=_head, base=_base)
            self._logger.info("github_create_pull_request_url : {0}".format(github_create_pull_request_url))
            self._logger.info("payload : {0}".format(_payload))

            response = requests.post(github_create_pull_request_url, headers=self._header, data=json.dumps(_payload))
            if 200 <= response.status_code < 300:
                return response.json()

            else:
                response_data = self._parse_response_data(response)
                message = self._get_message(response_data)
                error_message = "Error Creating GitHub Pull Request: {0} : {1}".format(github_create_pull_request_url,
                                                                                       message)
                self._logger.error(error_message)
                self._logger.error(json.dumps(response_data, sort_keys=True, indent=self._json_indent))
                raise exceptions.GithubAPIError(response.status_code, error_message)

        except exceptions.GithubError as err:
            self._logger.error("\n{0}\n{1}\n".format(type(err), traceback.format_exc()))
            raise

    def compare_branches(self, org, repo, base, head):
        """
        Make the GitHub API call to compare the two branches from the same repo.
        ***Both base and head must be branch names(or commit ids) in the repo
        :param org: org or owner of the repo
        :param repo: repo name
        :param base: target branch name or commit id
        :param head: source branch name or commit id
        :return: json response from the API call
        :raise GithubAPIQueryError
        """
        self._logger.info("compare branches org:{0}, repo:{1}, base:{2}, head:{3}".format(org, repo, base, head))

        github_compare_branch_url = self.COMPARE_BRANCH_API_URL_TMPLT.format(host=self._config.api_url,
                                                                             org=org,
                                                                             repo=repo,
                                                                             base=base,
                                                                             head=head)

        response = requests.get(github_compare_branch_url, headers=self._header)
        if 200 <= response.status_code < 300:
            return response.json()

        else:
            response_data = self._parse_response_data(response)
            message = self._get_message(response_data)
            error_message = "error in compare api org:{0}, repo:{1}, base:{2}, head:{3}, message:{4}".format(org, repo, 
                                                                                                             base, 
                                                                                                             head,
                                                                                                             message)
            self._logger.error(error_message)
            self._logger.error(json.dumps(response_data, sort_keys=True, indent=self._json_indent))
            raise exceptions.GithubAPIError(response.status_code, error_message)

    def check_repo_language(self, org, repo):
        """
        GitHub API to get the programming language information associated with a org/repo.  For more information refer
        to this, https://github.com/github/linguist.
        :param org: org or owner of the repo
        :param repo: repo name
        :return: json response from the API call
        :raise GithubAPIQueryError
        """
        self._logger.info("check repo language:{0}, repo:{1}".format(org, repo))

        check_language_url = self.LANGUAGE_API_URL_TMPLT.format(host=self._config.api_url, org=org, repo=repo)
        response = requests.get(check_language_url, headers=self._header)
        if 200 <= response.status_code < 300:
            return response.json()

        else:
            response_data = self._parse_response_data(response)
            message = self._get_message(response_data)
            error_message = ("error in check language api  org:{0}, repo:{1}, message:{2}".format(org, repo, message))
            self._logger.error(error_message)
            self._logger.error(json.dumps(response_data, sort_keys=True, indent=self._json_indent))
            raise exceptions.GithubAPIError(response.status_code, error_message)
   
    def post_status_check(self, status_url, data):
        """
        Make the GitHub API call to post a status to commits.
        :param status_url: status url of specified commit
        :param data: dictionary of data to post
            e.g. data = {"state": status,
                         "context": "scorebot"}
        :return: JSON response from the API call
        :raise GithubAPIError
        """
        self._logger.info("Posting status on commit : {0}".format(status_url))

        response = requests.post(status_url, headers=self._header, data=json.dumps(data))
        if 200 <= response.status_code < 300:
            return response.json()

        else:
            response_data = self._parse_response_data(response)
            message = self._get_message(response_data)
            error_message = "Error setting status check on commit: {0} : {1}".format(status_url, message)
            self._logger.error(error_message)
            self._logger.error(json.dumps(response_data, sort_keys=True, indent=self._json_indent))
            raise exceptions.GithubAPIError(response.status_code, error_message)

    def check_commit_status(self, commit_url):
        """
        Make the GitHub API call to post a status to commits.

        :param commit_url: commit url of specified commit
        :return: JSON response from the API call
        :raise GithubAPIError
        """
        self._logger.info("Checking status on commit: {0}".format(commit_url))
        response = requests.get(commit_url, headers=self._header)
        if 200 <= response.status_code < 300:
            return response.json()

        else:
            response_data = self._parse_response_data(response)
            message = self._get_message(response_data)
            error_message = "Error setting status check on commit: {0} : {1}".format(commit_url, message)
            self._logger.error(error_message)
            self._logger.error(json.dumps(response_data, sort_keys=True, indent=self._json_indent))
            raise exceptions.GithubAPIError(response.status_code, error_message)

    def check_user_permission(self, collab_url, user):
        """
        Make the GitHub API call to check if user permission
        :param collab_url: collab url
        :param user: username
        :return: JSON response from the API call
        :raise GithubAPIError
        """
        collab_url = collab_url + user + "/permission"
        self._logger.info("Checking user permission for repo: {0}".format(collab_url))
        response = requests.get(collab_url, headers=self._header)
        if 200 <= response.status_code < 300:
            return response.json()

        else:
            response_data = self._parse_response_data(response)
            message = self._get_message(response_data)
            error_message = "Error setting status check on commit: {0} : {1}".format(collab_url, message)
            self._logger.error(error_message)
            self._logger.error(json.dumps(response_data, sort_keys=True, indent=self._json_indent))
            raise exceptions.GithubAPIError(response.status_code, error_message)

    def get_commit_patch(self, commit_url):
        """
        Make the GitHub API call to get the patch of the commit.
        :param commit_url: GitHub commit URL
        :return: JSON response of the API call
        :raise GithubAPIError
        """
        self._logger.info("Calling GitHub API for commit patch: {0}".format(commit_url))
        response = requests.get(commit_url, headers=self._header)
        if 200 <= response.status_code < 300:
            return response.json()

        else:
            response_data = self._parse_response_data(response)
            message = self._get_message(response_data)
            error_message = "Error getting commit url from Github: {0} : {1}".format(commit_url, message)
            self._logger.error(error_message)
            self._logger.error(json.dumps(response_data, sort_keys=True, indent=self._json_indent))
            raise exceptions.GithubAPIError(response.status_code, error_message)
