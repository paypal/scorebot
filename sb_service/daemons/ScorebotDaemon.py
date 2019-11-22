import logging
import time
import traceback
from logging import config

from django.db import connection
from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.utils import OperationalError
from django.utils import timezone
from external_tools.github.GithubConfig import GithubConfig
from external_tools.github.GithubPullRequest import GithubPullRequest

from common.orm_loaded_constants import constants
from core.models import WebhookPR
from sb_service.common import daemon_utils
from sb_service.common import logging_util
from sb_service.service.ScorebotProcessor import ScorebotProcessor


class ScorebotDaemon:
    """
    The ScorebotDaemon handles maintenance operations for SCORE Bot Rules.
    If there is any Github web-hook data (branch pull request) queued that has not been
    processed then load them and send for processing.
    """

    def __init__(self, framework, logger, daemon_name, log_name):
        self.framework = framework
        self._logger = logger
        self._daemon_name = daemon_name
        self._log_name = log_name

        self._score_bot_processor = ScorebotProcessor(self.framework)

    def _reset(self):
        """
        Reset the logging.
        This will reset the log so it gets logged in the daemon log.
        """
        logging.config.dictConfig(logging_util.get_logging_conf(self._daemon_name, self._log_name))
        self._logger.debug("_reset")

    def _restore_db_connection(self):
        """
        Restore db connection
        """
        try:
            cursor = connection.cursor()
            db = cursor.db
            assert issubclass(db.__class__, BaseDatabaseWrapper)
            if db.connection is None or not db.is_usable():
                db.close_if_unusable_or_obsolete()
                with db.wrap_database_errors:
                    db.connect()
                    self._logger.info('Restoring the MySQL connection')
        except Exception as err:
            self._logger.critical('DB connection error')
            self._logger.critical("{0}\n{1}\n".format(type(err), traceback.format_exc()))

    def _load_pull_request(self):
        """
        Load Github web-hook pull request data (WebhookPR) that has not been processed.

        :return: Github web-hook pull request data
        """
        self._logger.debug("_load_pull_request")
        pull_request_jobs = WebhookPR.objects.filter(processed=False, framework=self.framework)
        return pull_request_jobs

    def run(self):
        """
        Controls the flow of the Daemon.
        """
        self._logger.debug("***> {} Started <***".format(self._daemon_name))
        pull_request_job = 0
        last_dbalarm_time = None
        while True:
            time.sleep(constants.DAEMON_SLEEP_TIME_SCOREBOT)
            self._logger.info("==> Start {} Run <==".format(self._daemon_name))
            self._restore_db_connection()
            try:
                pull_request_jobs = self._load_pull_request()
                for pull_request_job in pull_request_jobs:
                    self._restore_db_connection()
                    if self.framework == "Kraken":
                        pull_request = GithubPullRequest()
                        pull_request.load(GithubConfig(), pull_request_job.pull_request_url, True)
                        self._score_bot_processor.process_pull_request(pull_request_job)
                    else:
                        self._score_bot_processor.process_pull_request(pull_request_job)
                self._reset()

                # Reset the alarm since we made it through all queries.  This handles a bouncing connection.
                last_dbalarm_time = None
            except OperationalError as err:
                self._logger.critical("{0}\n{1}\n".format(type(err), traceback.format_exc()))
                # Close the ORM DB connection, so Django can re-open it next time a DB query needs processing.
                connection.close()
                self._reset()
                self._score_bot_processor.finalize_web_hook_job(pull_request_job)
                if daemon_utils.is_time_up(constants.DB_EXCEPTION_CHECK_TIME, last_dbalarm_time, True):
                    # The overall effect of this check is to wait 15min between critical alert notifications.
                    # Unless the DB connection is bouncing, then we get notified on every bounce.
                    self._logger.critical("{0}\n{1}\n".format(type(err), traceback.format_exc()))
                    last_dbalarm_time = timezone.now()
                else:
                    self._logger.error("***ORM DB Connection*** Still getting OperationalError from DB connector")
            except ValueError:
                self._score_bot_processor.finalize_web_hook_job(pull_request_job)
                pull_request_url = pull_request_job.pull_request_url
                self._logger.critical("Invalid pull request:  " + pull_request_url)
                pass
            except Exception as err:
                self._reset()
                self._logger.critical("{0}\n{1}\n".format(type(err), traceback.format_exc()))
                self._score_bot_processor.finalize_web_hook_job(pull_request_job)
