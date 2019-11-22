import sys
import logging
from logging import config
from sb_service.common import logging_util
from external_tools.daemon.daemonize import Daemon
from common import constants
from sb_service.daemons.PostProcessDaemon import PostProcessDaemon


class PostProcessDaemonKraken(Daemon):

    def __init__(self, pidfile):
        super(PostProcessDaemonKraken, self).__init__(pidfile=pidfile)

        self._daemon_name = "ScorebotDaemonKrakenPP"
        logging.config.dictConfig(logging_util.get_logging_conf(self._daemon_name, constants.PP_KRAKEN_LOG))
        self._logger = logging.getLogger(__name__)
        self.PostProcess = PostProcessDaemon("Kraken", self._logger)

    def run(self):
        self.PostProcess.run()


daemon = PostProcessDaemonKraken(constants.PP_KRAKEN_DAEMON_PID)

if sys.gettrace() is not None:
    daemon.run()
else:
    daemon.perform_action()
