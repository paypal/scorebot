import time
import traceback

from django.db import connection
from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.utils import OperationalError
from django.utils import timezone
from external_tools.github.GithubConfig import GithubConfig
from external_tools.github.GithubPullRequest import GithubPullRequest

from common import constants
from core.models import ScorebotConfig, ScorebotMetrics, PostProcessMetrics, ScorebotControlCpp, \
    ScorebotControlJava, ScorebotControlKraken
from sb_service.common import daemon_utils


class PostProcessDaemon:

    def __init__(self, framework, logger):
        self.framework = framework
        self._logger = logger

        if self.framework == "CPP":
            self.ScorebotControl = ScorebotControlCpp
        elif self.framework == "Java":
            self.ScorebotControl = ScorebotControlJava
        elif self.framework == "Kraken":
            self.ScorebotControl = ScorebotControlKraken

    def _load_pp(self):
        post_process_list = self.ScorebotControl.objects.filter(post_process=True).values_list('security_category',
                                                                                               flat=True)
        pr_to_process = []
        for cat in post_process_list:
            pr_to_process += ScorebotMetrics.objects.filter(security_category=cat, framework=self.framework,
                                                            post_process=False)
        return pr_to_process

    def _process_pr(self, pr):
        github_pull_request = GithubPullRequest()
        config = GithubConfig()
        pr_url = pr.pull_request_url
        github_pull_request.load(config, pr_url)
        if github_pull_request.state == "closed":
            try:
                # Either merged or closed
                merged_bool = github_pull_request.merged
                if merged_bool:
                    pr_state = "merged"
                    merged_user = github_pull_request.merged_by
                else:
                    pr_state = "closed"
                    merged_user = github_pull_request.closed_by

                PostProcessMetrics.objects.create(pull_request_url=pr_url, state=pr_state, closed_user=merged_user,
                                                  security_category=pr.security_category, framework=self.framework)
                pr.post_process = True
                pr.save(update_fields=["post_process"])
            except Exception as err:
                self._logger.critical("{0}\n{1}\n".format(type(err), traceback.format_exc()) + pr.pull_request_url)

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

    def run(self):
        last_dbalarm_time = None
        while True:
            self._logger.info("start run")
            self._restore_db_connection()
            try:
                sleep_time = int(ScorebotConfig.objects.filter(config="post_process_sleeptime").values()[0]['value'])
            except OperationalError as err:
                # Close the ORM DB connection, so Django can re-open it next time a DB query needs processing.
                connection.close()
                if daemon_utils.is_time_up(constants.DB_EXCEPTION_CHECK_TIME, last_dbalarm_time, True):
                    # The overall effect of this check is to wait 15min between critical alert notifications.
                    # Unless the DB connection is bouncing, then we get notified on every bounce.
                    self._logger.info("{0}\n{1}\n".format(type(err), traceback.format_exc()))
                    last_dbalarm_time = timezone.now()
                else:
                    self._logger.error("***ORM DB Connection*** Still getting OperationalError from DB connector")
                continue
            except Exception as err:
                self._logger.critical("{0}\n{1}\n".format(type(err), traceback.format_exc()))
                return
            pr_to_process = self._load_pp()
            # Process PR
            self._logger.info("processing PRs")
            for pr in pr_to_process:
                try:
                    self._logger.info("processing pr: " + pr.pull_request_url)
                    # Prevent same PR from being processed
                    pr_processed = PostProcessMetrics.objects.filter(pull_request_url=pr.pull_request_url)
                    if pr.scorebot_mode == "silent":
                        pr.post_process = True
                        pr.save(update_fields=["post_process"])
                    elif pr_processed and pr.scorebot_mode is not "silent":
                        pr_processed = pr_processed[0]
                        if pr.security_category not in pr_processed.security_category:
                            pr_processed.security_category = pr_processed.security_category + ", " + pr.security_category
                            pr_processed.save(update_fields=["security_category"])
                        pr.post_process = True
                        pr.save(update_fields=["post_process"])
                    else:
                        self._process_pr(pr)
                    last_dbalarm_time = None

                except Exception as err:
                    self._logger.critical("{0}\n{1}\n".format(type(err), traceback.format_exc()) + pr.pull_request_url)

            self._logger.info("finished processing")
            # Sleep
            time.sleep(sleep_time)
