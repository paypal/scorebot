"""
These two fields must be set - use get_logging_conf() method below.
"filename": "<NEEDS FILE PATH/NAME>"
"subject": "<NEEDS SUBJECT>",

Example usage:
import logging
from logging import config
    daemon_name = "MergeDaemon"
    logging.config.dictConfig(logging_util.get_logging_conf(daemon_name, "merge_daemon.log"))
    logger = logging.getLogger(__name__)  # main daemon log
    logger.debug("This is a debug message in the daemon log.")
    job_log_name = logging_util.get_job_log_name(pull_request_url, jira_ticket_id)
    logging.config.dictConfig(logging_util.get_logging_conf(daemon_name, job_log_name))
    logger.debug("This is a debug message in the job log.") # switched to job log
    logging_util.force_log_rollover(logger) # start with a clean log
    logger.error("This is an error message in a new job log.")
    logging.config.dictConfig(logging_util.get_logging_conf(daemon_name, "merge_daemon.log"))
    logger.debug("This is a debug message in the daemon log.") # back to the main daemon log
"""
from copy import deepcopy
import os
import socket

from common import constants
from common.orm_loaded_constants import et_constants


LOGGING_CONF = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(asctime)s %(levelname)s %(module)s::%(funcName)s::%(lineno)d %(message)s",
        },
        "simple": {
            "format": "%(levelname)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "simple",
        },
        "logfile": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "verbose",
            "filename": "<NEEDS PATH/FILENAME>",
            "mode": "a",
            "maxBytes": 1024*1024*100,  # 100 MB
            "backupCount": 4,
            "encoding": "utf8",
        },
        "error_email": {
            "class": "logging.handlers.SMTPHandler",
            "level": "CRITICAL",
            "formatter": "verbose",
            "mailhost": constants.SMTP_SERVER,
            "fromaddr": constants.SCOREBOT_FROM_DL_CRITICAL,
            "toaddrs": [constants.SCOREBOT_DL_EMAIL_ADDRESS_CRITICAL, ],
            "subject": "<NEEDS SUBJECT>",
        },
    },
    "loggers": {
        '': {
            "handlers": ["console", "logfile", "error_email"],
            "level": "DEBUG" if constants.DEBUG else "INFO",
            "propagate": True,
        },
    }
}


def get_logging_conf(daemon_name, log_name):
    """
    Pass in your daemon name and the path/log_name and get back a logging conf.

    :param daemon_name: name of the daemon to be used in the subject for critical error emails
    :param log_name: full path and log name to be used for the log
    :return:
    """
    logging_conf = deepcopy(LOGGING_CONF)
    subject = "{0} CRITICAL Error on {1}".format(daemon_name, socket.gethostname())
    logging_conf["handlers"]["logfile"]["filename"] = log_name
    logging_conf["handlers"]["error_email"]["subject"] = subject
    return logging_conf


def get_job_log_name(pull_request_url=None, repo_url=None, custom_field=None):
    """
    Create the fully qualified log name using the passed in params.
        If only PR then uses PR number and repo name
        If jira ticket id then uses ticket id with repo name
        If custom field not None then uses custom field instead of repo name

    :param pull_request_url: pull_request_url
    :param repo_url: repo_url
    :param custom_field: field to use instead of repo name. e.g. deploy or cert
    :return: fully qualified log name
    :raise ValueError if parameters are invalid
    """
    job_path = constants.DAEMON_LOG_DIR

    if pull_request_url:
        match = et_constants.GITHUB_REGEX_ALL_GROUPS.match(pull_request_url)
        if match:
            job_name = "github_{0}".format(match.group(4))

            if custom_field is None:
                job_name = "{}_{}.log".format(job_name, match.group(3))
            else:
                job_name = "{}_{}.log".format(job_name, custom_field)
        else:
            raise ValueError("Invalid pull_request_url")
    elif repo_url:
        match = constants.GITHUB_PUSH_REGEX.match(repo_url)
        if match:
            job_name = "github_{}_{}".format(match.group(2), match.group(3))

            if custom_field:
                job_name = "{}_{}.log".format(job_name, custom_field)
        else:
            raise ValueError("Invalid pull_request_url")
    else:
        raise ValueError("Invalid params")

    return os.path.join(job_path, job_name)


def force_log_rollover(logger):
    """
    This will access the handler that is configured as a RotatingFileHandler and force a rollover.

    :param logger: logger that you are using to write logs
    :return boolean: True if successful else false
    """
    rolled_over = False

    for handle in logger.root.handlers:
        if handle.name == "logfile":
            handle.doRollover()
            rolled_over = True
            break

    return rolled_over
