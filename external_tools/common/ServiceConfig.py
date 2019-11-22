class ServiceConfig(object):
    def __init__(self,
                 schema=None,
                 domain=None,
                 api_path=None,
                 port=None,
                 username=None,
                 password=None,
                 token=None,
                 dry_run=False):
        self._schema = schema
        self._domain = domain
        self._api_path = api_path
        self._port = port
        self._username = username
        self._password = password
        self._token = token
        self._url = None
        self._api_url = None
        self._dry_run = dry_run

    @property
    def schema(self):
        return self._schema

    @property
    def domain(self):
        return self._domain

    @property
    def api_path(self):
        return self._api_path

    @property
    def port(self):
        return self._port

    @property
    def username(self):
        return self._username

    @property
    def password(self):
        return self._password

    @property
    def token(self):
        return self._token

    @token.setter
    def token(self, token):
        """
        Allows the user to set the token.

        :param token: token to set in config
        """
        self._token = token

    @property
    def dry_run(self):
        return self._dry_run

    @property
    def url(self):
        if self._url is None:
            if self._schema:
                self._url = "{schema}://{domain}".format(schema=self._schema, domain=self._domain)
            else:
                self._url = self._domain

            if self.port:
                self._url = "{url}:{port}".format(url=self._url, port=self._port)

        return self._url

    @property
    def api_url(self):
        if self._api_url is None:
            self._api_url = self.url

            if self._api_path:
                self._api_url = "{url}{api_path}".format(url=self._api_url, api_path=self._api_path)

        return self._api_url

    def __unicode__(self):
        args = ['{}={}'.format(k, v) for (k, v) in vars(self).items()]
        return ', '.join(args)

    def __str__(self):
        return str(self).encode('utf-8')

    def __repr__(self):
        args = ['{}={}'.format(k, repr(v)) for (k, v) in vars(self).items()]
        return '{}({})'.format(self.__class__.__name__, ', '.join(args))
