from external_tools.common import constants
from external_tools.common.ServiceConfig import ServiceConfig


class GithubConfig(ServiceConfig):
    def __init__(self,
                 schema=constants.GITHUB_SCHEMA,
                 domain=constants.GITHUB_DOMAIN,
                 api_path=constants.GITHUB_API_PATH,
                 username=constants.GITHUB_API_USER,
                 token=constants.GITHUB_API_TOKEN,
                 dry_run=False):
        super(GithubConfig, self).__init__(schema=schema,
                                           domain=domain,
                                           api_path=api_path,
                                           username=username,
                                           token=token,
                                           dry_run=dry_run)

    def __unicode__(self):
        args = ['{}={}'.format(k, v) for (k, v) in vars(self).items()]
        return ', '.join(args)

    def __str__(self):
        return str(self).encode('utf-8')

    def __repr__(self):
        args = ['{}={}'.format(k, repr(v)) for (k, v) in vars(self).items()]
        return '{}({})'.format(self.__class__.__name__, ', '.join(args))


def _internal_test():
    config = GithubConfig()
    print("api_url={0}".format(config.api_url))
    print("url={0}".format(config.url))


if __name__ == "__main__":
    _internal_test()
