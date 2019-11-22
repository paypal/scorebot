import logging
from logging import config
import sys
from common.orm_loaded_constants import constants
from sb_service.common import logging_util
from external_tools.daemon.daemonize import Daemon
from sb_service.daemons.ScorebotDaemon import ScorebotDaemon


class ScorebotDaemonJava(Daemon):
    """
    The ScorebotDaemon handles maintenance operations for SCORE Bot Rules.
    If there is any Github web-hook data (branch pull request) queued that has not been
    processed then load them and send for processing.
    """
    def __init__(self, pidfile):
        super(ScorebotDaemonJava, self).__init__(pidfile=pidfile)

        self._daemon_name = "ScorebotDaemonJava"
        logging.config.dictConfig(logging_util.get_logging_conf(self._daemon_name, constants.SCOREBOT_DAEMON_JAVA_LOG))
        self._logger = logging.getLogger(__name__)
        self.ScorebotProcess = ScorebotDaemon("Java", self._logger, self._daemon_name,
                                              constants.SCOREBOT_DAEMON_JAVA_LOG)

    def run(self):
        self.ScorebotProcess.run()


daemon = ScorebotDaemonJava(constants.SCOREBOT_DAEMON_JAVA_PID)
# Check to see if we're running under the debugger, if we are then bypass the daemonize and just run directly.
if sys.gettrace() is not None:
    daemon.run()
else:
    daemon.perform_action()
