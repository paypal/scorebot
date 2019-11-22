class GithubRepository(object):
    """
    This class encapsulates the GitHub Repository data.
    """

    def __init__(self):
        self._label = None  # branch name
        self._ref = None  # base: target branch master/release, head: source branch
        self._sha = None
        self._url = None  # "Human Readable" URL for the Github repo
        self._api_url = None  # Github API URL for running queries against
        self._ssh_url = None  # SSH URL for doing git operations against
        self._git_url = None  # Git URL for doing git operations against (read only - cant push)
        self._pulls_url = None  # Git URL for pulling the pull request
        self._compare_url = None  # Git URL for comparing base and head
        self._full_name = None  # org/repo names
        self._name = None  # repo name code or pexml
        self._owner = None
        self._is_private = None
        self._is_fork = None
        self._default_branch = None  # head: RM branch the source branch is based off of

        self._repo_loaded = False  # This will be set to true if the pull request loaded correctly

    @property
    def label(self):
        return self._label

    @property
    def ref(self):
        return self._ref

    @property
    def sha(self):
        return self._sha

    @property
    def url(self):
        return self._url

    @property
    def api_url(self):
        return self._api_url

    @property
    def ssh_url(self):
        return self._ssh_url

    @property
    def git_url(self):
        return self._git_url

    @property
    def pull_url(self):
        return self._pulls_url

    @property
    def compare_url(self):
        return self._compare_url

    @property
    def full_name(self):
        return self._full_name

    @property
    def name(self):
        return self._name

    @property
    def owner(self):
        return self._owner

    @property
    def is_private(self):
        return self._is_private

    @property
    def is_fork(self):
        return self._is_fork

    @property
    def default_branch(self):
        return self._default_branch

    @property
    def repo_loaded(self):
        return self._repo_loaded

    def __unicode__(self):
        args = ['{}={}'.format(k, v) for (k, v) in vars(self).items()]
        return ', '.join(args)

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __repr__(self):
        args = ['{}={}'.format(k, repr(v)) for (k, v) in vars(self).items()]
        return '{}({})'.format(self.__class__.__name__, ', '.join(args))

    def _reset(self):
        """
        Reset the members to default values.
        """
        self._label = None
        self._ref = None
        self._sha = None
        self._url = None
        self._api_url = None
        self._ssh_url = None
        self._git_url = None
        self._pulls_url = None
        self._compare_url = None
        self._full_name = None
        self._name = None
        self._owner = None
        self._is_private = None
        self._is_fork = None
        self._default_branch = None
        self._repo_loaded = False

    def load(self, response_data):
        """
        Load the members from the response_data.

        :param response_data: JSON data from the Github API response
        :return: Boolean loaded == True if loaded else False
        """
        self._reset()
        if response_data['repo'] is not None:
            self._label = response_data['label']
            self._ref = response_data['ref']
            self._sha = response_data['sha']
            self._url = response_data['repo']['html_url']
            self._api_url = response_data['repo']['url']
            self._ssh_url = response_data['repo']['ssh_url']
            self._git_url = response_data['repo']['git_url']
            self._pulls_url = response_data['repo']['pulls_url']
            self._compare_url = response_data['repo']['compare_url']
            self._full_name = response_data['repo']['full_name']
            self._name = response_data['repo']['name']
            self._owner = response_data['repo']['owner']['login']
            self._is_private = response_data['repo']['private']
            self._is_fork = response_data['repo']['fork']
            self._default_branch = response_data['repo']['default_branch']
            self._repo_loaded = True

        return self._repo_loaded
