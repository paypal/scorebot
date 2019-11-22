"""
external_tools defined exceptions
"""

# =====================================================
# Component Data exceptions
# =====================================================


class ComponentDataAPIError(IOError):
    """
    Exception class to handle unsuccessful API calls
    """
    pass


# =====================================================
# GIT exceptions
# =====================================================


class GitError(Exception):
    def __init__(self, cmd, return_code=1, stdout=None, stderr=None):
        self._cmd = cmd
        self._return_code = return_code
        self._stdout = stdout
        self._stderr = stderr

    def __str__(self):
        return "{cmd} failed with return code {code}\nDetails:\n{output}".format(cmd=self.cmd,
                                                                                 code=self.return_code,
                                                                                 output=self.output)
    @property
    def cmd(self):
        return " ".join(self._cmd)

    @property
    def return_code(self):
        return self._return_code

    @property
    def output(self):
        if not self._stdout and not self._stderr:
            return "<No Output>"

        _output = self._stdout if self._stdout else ''
        if self._stderr:
            _output = "{0}{1}".format(_output, self._stderr)
        return _output

    @property
    def stdout(self):
        """
        stdout - output message
        """
        return self._stdout

    @stdout.setter
    def stdout(self, output_message):
        """
        Setter for stdout
        """
        self._stdout = output_message

    @property
    def stderr(self):
        """
        stderr - error message
        """
        return self._stderr

    @stderr.setter
    def stderr(self, error_message):
        """
        Setter for stderr
        """
        self._stderr = error_message


class InvalidGitRepoError(GitError):
    def __init__(self,
                 path):
        super(InvalidGitRepoError, self).__init__(["No", "Command", "Was", "Run"])
        self._path = path

    def __str__(self):
        return "{path} is not a valid Git Repo".format(path=self._path)

    @property
    def output(self):
        return self.__str__()


class GitBranchNotFoundError(GitError):
    def __init__(self, branch, local_branches):
        super(GitBranchNotFoundError, self).__init__(["No", "Command", "Was", "Run"])
        self._branch = branch
        self._local_branches = local_branches

    def __str__(self):
        return "{branch} not found in {branches}".format(branch=self._branch, branches=str(self._local_branches))


class InvalidCommitError(GitError):
    def __init__(self, commit, issue):
        super(InvalidCommitError, self).__init__(["No", "Command", "Was", "Run"])
        self._commit = commit
        self._issue = issue

    def __str__(self):
        return "{commit} could not be merged: {issue}".format(commit=self._commit, issue=self._issue)


# =====================================================
# GitHub exceptions
# =====================================================


class GithubAPIError(IOError):
    """
    Exception class to handle unsuccessful API calls
    """
    pass


class GithubError(Exception):
    """
    Exception class to handle Github errors
    """
    pass
