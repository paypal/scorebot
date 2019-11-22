import logging
from logging import config
import sys
from common.orm_loaded_constants import constants
from sb_service.common import logging_util
from external_tools.daemon.daemonize import Daemon
from sb_service.daemons.ScorebotDaemon import ScorebotDaemon


class ScorebotDaemonCpp(Daemon):
    def __init__(self, pidfile):
        super(ScorebotDaemonCpp, self).__init__(pidfile=pidfile)

        self._daemon_name = "ScorebotDaemon"
        logging.config.dictConfig(logging_util.get_logging_conf(self._daemon_name, constants.SCOREBOT_DAEMON_LOG))
        self._logger = logging.getLogger(__name__)
        self.ScorebotProcess = ScorebotDaemon("CPP", self._logger, self._daemon_name, constants.SCOREBOT_DAEMON_LOG)

    def run(self):
        self.ScorebotProcess.run()


daemon = ScorebotDaemonCpp(constants.SCOREBOT_DAEMON_PID)
# Check to see if we're running under the debugger,
# if we are then bypass the daemonize and just run directly.
if sys.gettrace() is not None:
    daemon.run()
else:
    daemon.perform_action()
