import logging
import time
import traceback
import urllib

from common.constants import DOMAIN
from external_tools.common import constants
from external_tools.common import exceptions
from external_tools.github.GithubAPI import GithubAPI
from external_tools.github.GithubRepository import GithubRepository


class GithubPullRequest(object):
    """
    This class encapsulates the GitHub pull request data.
    It will load itself from JSON data from the Github API responses.
    """

    class File(object):
        """
        This class encapsulates the GitHub pull request File data.
        It will load itself from JSON data from the Github API response.
        """

        def __init__(self, load_patches=False):
            self._sha = None
            self._filename = None  # Name of the file that was modified
            self._status = None  # Like modified, etc
            self._additions = 0
            self._deletions = 0
            self._changes = 0
            self._patch_exists = False
            self._load_patches = load_patches
            self._patch = None

        @property
        def sha(self):
            return self._sha

        @property
        def filename(self):
            return self._filename

        @property
        def status(self):
            return self._status

        @property
        def additions(self):
            return self._additions

        @property
        def deletions(self):
            return self._deletions

        @property
        def changes(self):
            return self._changes

        @property
        def patch_exists(self):
            return self._patch_exists

        @property
        def patch(self):
            return self._patch

        def __unicode__(self):
            args = ['{}={}'.format(k, v) for (k, v) in vars(self).items()]
            return ', '.join(args)

        def __str__(self):
            return unicode(self).encode('utf-8')

        def __repr__(self):
            args = ['{}={}'.format(k, repr(v)) for (k, v) in vars(self).items()]
            return '{}({})'.format(self.__class__.__name__, ', '.join(args))

        def load(self,
                 response_data):
            """
            Load the members from the response_data.
            :param response_data: JSON data from the Github API response
            """
            self._sha = response_data['sha']
            self._filename = response_data['filename']
            self._status = response_data['status']
            self._additions = response_data.get('additions', 0)
            self._deletions = response_data.get('deletions', 0)
            self._changes = response_data.get('changes', 0)
            if 'patch' in response_data:
                self._patch_exists = True
                if self._load_patches:
                    self._patch = response_data['patch']

    class Commit(object):
        """
        This class encapsulates the GitHub pull request Commit data.
        It will load itself from JSON data from the Github API response.
        """

        def __init__(self):
            self._author_name = None
            self._author_email = None
            self._committer_name = None
            self._committer_email = None
            self._subject = None  # Commit message
            self._commit_date = None
            self._sha = None

        @property
        def author_name(self):
            return self._author_name

        @property
        def author_email(self):
            return self._author_email

        @property
        def committer_name(self):
            return self._committer_name

        @property
        def committer_email(self):
            return self._committer_email

        @property
        def subject(self):
            return self._subject

        @property
        def commit_date(self):
            return self._commit_date

        @property
        def sha(self):
            return self._sha

        def __unicode__(self):
            args = ['{}={}'.format(k, v) for (k, v) in vars(self).items()]
            return ', '.join(args)

        def __str__(self):
            return str(self).encode('utf-8')

        def __repr__(self):
            args = ['{}={}'.format(k, repr(v)) for (k, v) in vars(self).items()]
            return '{}({})'.format(self.__class__.__name__, ', '.join(args))

        def load(self,
                 response_data):
            """
            Load the members from the response_data.
            :param response_data: JSON data from the Github API response
            """
            self._author_name = response_data['commit']['author']['name']
            self._author_email = response_data['commit']['author']['email']
            self._committer_name = response_data['commit']['committer']['name']
            self._committer_email = response_data['commit']['committer']['email']
            self._subject = response_data['commit']['message']
            self._commit_date = response_data['commit']['committer']['date']
            self._sha = response_data['sha']

    class User(object):
        """
        This class encapsulates the GitHub pull request User data.
        It will load itself from JSON data from the Github API response.
        """

        def __init__(self):
            self._full_name = None  # LastName, FirstName
            self._email = None
            self._username = None

        @property
        def full_name(self):
            return self._full_name

        @property
        def email(self):
            return self._email

        @property
        def username(self):
            return self._username

        def __unicode__(self):
            args = ['{}={}'.format(k, v) for (k, v) in vars(self).items()]
            return ', '.join(args)

        def __str__(self):
            return str(self).encode('utf-8')

        def __repr__(self):
            args = ['{}={}'.format(k, repr(v)) for (k, v) in vars(self).items()]
            return '{}({})'.format(self.__class__.__name__, ', '.join(args))

        def load(self,
                 response_data):
            """
            Load the members from the response_data.
            :param response_data: JSON data from the Github API response
            """
            self._username = (response_data['login']).encode('utf-8').strip()
            full_name = response_data.get('name', None)
            if full_name:
                self._full_name = full_name.encode('utf-8').strip()
            else:
                self._full_name = self._username
            self._email = (response_data.get('email', None))
            if self._email is None:
                self._email = "{0}@{1}.com".format(self._username, DOMAIN)
            else:
                self._email = self._email.encode('utf-8').strip()

    ######################################################################
    # START PULL REQUEST METHODS
    ######################################################################
    def __init__(self):
        self._logger = logging.getLogger(__name__)

        self._config = None
        self._number = None  # Pull request number
        self._state = None  # Pull request state open, closed, etc
        self._title = None  # Pull request subject
        self._url = None  # Pull request URL
        self._api_url = None  # API URL for pull request
        self._closed_by = None # Username
        self._comments_url = None  # Git URL for adding comments to the pull request
        self._comments = []  # List of comment structures.
        self._commits_url = None
        self._issues_url = None
        self._user_url = None
        self._files_url = None
        self._mergeable = None  # true/false
        self._merged = None  # true/false
        self._merged_by = None  # Username
        self._num_changed_files = None
        self._num_commits = None
        self._num_additions = None
        self._num_deletions = None
        self._head_repo = None
        self._base_repo = None
        self._files = []  # Changed file data
        self._load_patches = False  # Load patches in file data
        self._commits = []  # Commits data
        self._user = None  # User data
        self._possible_binary_files = False  # PR might contain binary files

        self._loaded = False  # This will be set to true if the pull request loads correctly

    @property
    def number(self):
        return self._number

    @property
    def state(self):
        return self._state

    @property
    def title(self):
        return self._title

    @property
    def url(self):
        return self._url

    @property
    def org(self):
        org = ""
        if self._url is not None:
            match = constants.GITHUB_REGEX_ALL_GROUPS.match(self._url)
            if match:
                org = match.group(2)
        return org

    @property
    def api_url(self):
        return self._api_url

    @property
    def closed_by(self):
        if self._issues_url is not None and not self._closed_by:
            self._load_closed_by()
        return self._closed_by

    @property
    def comments_url(self):
        return self._comments_url

    @property
    def comments(self):
        if self._comments_url is not None and not self._comments:
            self._load_comments()
        return self._comments

    @property
    def commits_url(self):
        return self._commits_url

    @property
    def issues_url(self):
        return self._issues_url

    @property
    def user_url(self):
        return self._user_url

    @property
    def files_url(self):
        return self._files_url

    @property
    def mergeable(self):
        return self._mergeable

    @property
    def merged(self):
        return self._merged

    @property
    def merged_by(self):
        return self._merged_by

    @property
    def num_changed_files(self):
        return self._num_changed_files

    @property
    def num_commits(self):
        return self._num_commits

    @property
    def num_additions(self):
        return self._num_additions

    @property
    def num_deletions(self):
        return self._num_deletions

    @property
    def head_repo(self):
        return self._head_repo

    @property
    def base_repo(self):
        return self._base_repo

    @property
    def files(self):
        return self._files

    @property
    def commits(self):
        return self._commits

    @property
    def user(self):
        return self._user

    @property
    def possible_binary_files(self):
        return self._possible_binary_files

    @property
    def loaded(self):
        return self._loaded

    def __unicode__(self):
        args = ['{}={}'.format(k, v) for (k, v) in vars(self).items()]
        return ', '.join(args)

    def __str__(self):
        return str(self).encode('utf-8')

    def __repr__(self):
        args = ['{}={}'.format(k, repr(v)) for (k, v) in vars(self).items()]
        return '{}({})'.format(self.__class__.__name__, ', '.join(args))

    def _reset(self):
        """
        Reset the members to default values.
        """
        self._config = None
        self._number = None
        self._state = None
        self._title = None
        self._url = None
        self._api_url = None
        self._closed_by = None
        self._comments_url = None
        self._comments = []
        self._commits_url = None
        self._issues_url = None
        self._user_url = None
        self._files_url = None
        self._mergeable = None
        self._merged = None
        self._merged_by = None
        self._num_changed_files = None
        self._num_commits = None
        self._num_additions = None
        self._num_deletions = None
        self._head_repo = None
        self._base_repo = None
        self._files = []
        self._load_patches = False
        self._commits = []
        self._user = None
        self._possible_binary_files = False
        self._loaded = False

    def _load_pull_request(self, response_data):
        """
        Load the members from the response_data.
        :param response_data: JSON data from the Github API response
        :return: No return
        """
        self._number = response_data['number']
        self._state = response_data['state']
        self._title = response_data['title'].encode('utf-8').strip()
        self._url = response_data['html_url']
        self._api_url = response_data['url']
        self._files_url = "{0}{1}".format(self._api_url, '/files')
        self._comments_url = response_data['comments_url']
        self._commits_url = response_data['commits_url']
        self._issues_url = response_data['issue_url']
        self._user_url = response_data['user']['url']
        self._mergeable = response_data['mergeable']
        self._merged = response_data['merged']
        if self._merged:
            merged_by_data = response_data['merged_by']
            self._merged_by = merged_by_data['login']
        self._num_changed_files = response_data['changed_files']
        self._num_commits = response_data['commits']
        self._num_additions = response_data['additions']
        self._num_deletions = response_data['deletions']
        self._head_repo = GithubRepository()
        self._head_repo.load(response_data['head'])
        self._base_repo = GithubRepository()
        self._base_repo.load(response_data['base'])

    def _load_files(self, response_data):
        """
        Load the file data in File objects from the response_data.
        :param response_data: JSON data from the Github API response
        """
        for file_data in response_data:
            changed_file = self.File(self._load_patches)
            changed_file.load(file_data)
            self._files.append(changed_file)

            # Check the file information to see if it might be a binary file.  This check is based on the
            # inspection of PRs that contain binary files.

            if not self._possible_binary_files:
                if changed_file.status in ['added', 'modified'] \
                        and changed_file.additions == 0 \
                        and changed_file.deletions == 0 \
                        and changed_file.changes == 0 \
                        and not changed_file.patch_exists:
                    self._possible_binary_files = True

    def _load_commits(self, response_data):
        """
        Load the commit data in Commit objects from the response_data.
        :param response_data: JSON data from the Github API response
        """
        for commit_json in response_data:
            commit = self.Commit()
            commit.load(commit_json)
            self._commits.append(commit)

    def _load_user(self, response_data):
        """
        Load the user data in User object from the response_data.
        :param response_data: JSON data from the Github API response
        """
        user = self.User()
        user.load(response_data)
        self._user = user

    def _load_closed_by(self, response_data):
        if response_data['closed_by']:
            self._closed_by = response_data['closed_by']['login']

    def _load_comments(self):
        """
        Load the comments using the comments_url.
        """
        github_api = GithubAPI(self._config)
        self._comments = github_api.process_api_query(self._comments_url)

    def load(self, github_config, pull_request_url, load_patches=False):
        """
        Calls GitHub APIs and uses the API responses to fill in the PullRequest.
        :param github_config: GithubConfig
        :param pull_request_url: GitHub pull request URL
        :param load_patches: Boolean: If True then load file patches else do not load the patches.
        :return: Boolean: True if loaded else False
        :raises GithubAPIError, GithubError, Exception
        """
        self._logger.info("Loading pull request: {0}".format(pull_request_url))
        self._reset()
        self._load_patches = load_patches
        self._config = github_config

        try:
            github_api = GithubAPI(self._config)
            request_url = github_api.generate_api_url_from_pull_request_url(pull_request_url)

        except exceptions.GithubError as err:
            self._logger.error("\n{0}\n{1}\n".format(type(err), traceback.format_exc()))
            raise

        except Exception as err:
            self._logger.error("\n{0}\n{1}\n".format(type(err), traceback.format_exc()))
            raise

        # We need to test the mergeablity at this point due to an issue with GitHub.
        # We are going to load the pull request no matter what but we are going to loop on it
        # for a period of time or (until mergeable is not None or merged is true or the state is not open).
        total_time_in_seconds = 90  # total time we will loop
        sleep_time_in_seconds = 5  # loop increments
        sleep_counter = 0
        try:
            while sleep_counter < total_time_in_seconds:
                self._logger.info("Loading pull request from API URL: {0}".format(request_url))
                self._load_pull_request(github_api.process_api_query(request_url))
                # Break if mergeable is set or merged is true or the state is not open
                if self._mergeable is not None or self._merged or self._state.lower() != "open":
                    break
                self._logger.info("Waiting on mergeable field to be set.")
                time.sleep(sleep_time_in_seconds)
                sleep_counter += sleep_time_in_seconds

            self._logger.info("Mergeable: {0}".format(self._mergeable))

            self._logger.info("Loading issues from URL {0}".format(self._issues_url))
            self._load_closed_by(github_api.process_api_query(self._issues_url))

            self._logger.info("Loading user from URL {0}".format(self._user_url))
            self._load_user(github_api.process_api_query(self._user_url))

            self._logger.info("Loading files from URL {0}".format(self._files_url))
            file_query_response, header = github_api.process_api_query_with_header(self._files_url)

            while file_query_response:
                self._load_files(file_query_response)
                if not header.links or "next" not in header.links:
                    # No more links for files
                    break

                else:
                    file_query_response, header = github_api.process_api_query_with_header(header.links["next"]["url"])

            self._logger.info("Loading commits from URL {0}".format(self._commits_url))
            file_query_response, header = github_api.process_api_query_with_header(self._commits_url)

            while file_query_response:
                self._load_commits(file_query_response)
                if not header.links or "next" not in header.links:
                    # No more links for files
                    break

                else:
                    file_query_response, header = github_api.process_api_query_with_header(header.links["next"]["url"])

        except exceptions.GithubAPIError as err:
            self._logger.error("\n{0}\n{1}\n".format(type(err), traceback.format_exc()))
            raise

        except Exception as err:
            self._logger.error("\n{0}\n{1}\n".format(type(err), traceback.format_exc()))
            raise

        self._logger.info("GitHub pull request loaded")
        self._loaded = True
        return self._loaded

    def execute_pull_request(self, commit_comment="", pull_request_comment=""):
        """
        Execute the pull request adding a commit comment and a pull request comment. Return the response.
        :param commit_comment: Comment to add to the commit.
        :param pull_request_comment: Comment to add to the pull request.
        :return: Pull request execution response data
        :raise Doesnt catch exceptions - they need to be caught by caller.
        """
        self._logger.info("Executing pull request")

        result = None
        if self._loaded:
            # Execute the pull request
            api_query = GithubAPI(self._config)
            result = api_query.execute_pull_request(self._api_url, commit_comment)

            # Add comment to pull request now that it has been executed
            if pull_request_comment:
                self.comment_on_pull_request(pull_request_comment)

        return result

    def close_pull_request(self, pull_request_comment=""):
        """
        Close the pull request adding a commit comment and a pull request comment. Return the response.

        :param pull_request_comment: Comment to add to the pull request.
        :return: Pull request execution response data
        :raise Doesnt catch exceptions - they need to be caught by caller.
        """
        self._logger.info("Closing pull request")

        result = None
        if self._loaded:
            # Close the pull request
            api_query = GithubAPI(self._config)
            result = api_query.close_pull_request(self._api_url)

            # Add comment to pull request now that it has been executed
            if pull_request_comment:
                self.comment_on_pull_request(pull_request_comment)

        return result

    def comment_on_pull_request(self, pull_request_comment=""):
        """
        Add a comment to the pull request.
        :param pull_request_comment: Comment to add to the pull request.
        :raise Doesnt catch exceptions - they need to be caught by caller.
        """
        self._logger.info("Commenting on pull request")

        if self._loaded:
            api_query = GithubAPI(self._config)
            api_query.add_pull_request_comment(self._comments_url, pull_request_comment)

    def is_pull_request_mergeable(self):
        """
        Test if the pull request is able to be merged.
        :return True if pull request is able to be merged else False
        """
        self._logger.info("Entering is_pull_request_mergeable")

        mergable = False
        if self._loaded:
            if self._merged or self._state.lower() != "open" or not self._mergeable:
                self._logger.info("merged: {0}, state: {1}, mergeable: {2}".format(self._merged, self._state,
                                                                                   self._mergeable))
            else:
                mergable = True

        return mergable

    def compare_head_base(self):
        """
        Compare the head to the base and return dict containing the following fields.
                {
                    "status": "diverged",
                    "ahead_by": 5,
                    "behind_by": 211,
                    "total_commits": 5
                }
        :returns dictionary containing status, ahead_by, behind_by and total_commits
        :raise Doesnt catch exceptions - they need to be caught by caller.
        """
        self._logger.info("compare_head_base")
        result = {}

        if self._loaded:
            compare_url = self._head_repo.compare_url
            compare_url = compare_url.replace("{base}", self._base_repo.label)
            compare_url = compare_url.replace("{head}", urllib.quote(self._head_repo.label))
            api_query = GithubAPI(self._config)
            response = api_query.process_api_query(compare_url)
            if response:
                result["status"] = response.get("status")
                result["ahead_by"] = response.get("ahead_by")
                result["behind_by"] = response.get("behind_by")
                result["total_commits"] = response.get("total_commits")

        return result
