"""
*******************************************************************

    *** NOTE: KEEP THIS SECTION UP TO DATE ALPHABETICALLY:
        When you add a constant that is going to be loaded externally then you must update this area.

    *** NOTE: Variables that MUST BE environment variables ***
        DJANGO_KEY  # Required - django server secret key
        SMTP_SERVER  # Required - email server

*******************************************************************
"""
import os
import re
import socket

# =====================================================
# Daemons and logs
# =====================================================
DAEMON_LOG_DIR = "/var/log/scorebot2"  # path for logs
DAEMON_BASE_DIR = "/x/local/scorebot/scorebot-service/sb_service/daemons"  # path for the daemon pids

INIT_LOG_DIR = "/var/log/scorebot2"  # path for logs for the sb_service
SCOREBOT_INIT_LOG = os.path.join(INIT_LOG_DIR, "init_scorebot.log")

# sleep times
DAEMON_SLEEP_TIME_SCOREBOT = 5  # Seconds

# misc
DB_EXCEPTION_CHECK_TIME = 15  # Minutes between critical DB alerts

scorebot_log = "/var/log/scorebot2/scorebot.log"

# ========================CPP===========================
# log/pid
SCOREBOT_DAEMON_LOG = os.path.join(DAEMON_LOG_DIR, "daemon_scorebot.log")
SCOREBOT_DAEMON_PID = os.path.join(DAEMON_BASE_DIR, "maintenance_daemon.pid")

# post process log/pid
PP_LOG = os.path.join(DAEMON_LOG_DIR , "ppdaemon_scorebot.log")
PP_DAEMON_PID = os.path.join(DAEMON_BASE_DIR, "maintenance_ppdaemon.pid")

# ========================Java===========================
# log/pid
SCOREBOT_DAEMON_JAVA_LOG = os.path.join(DAEMON_LOG_DIR, "daemon_java_scorebot.log")
SCOREBOT_DAEMON_JAVA_PID = os.path.join(DAEMON_BASE_DIR, "maintenance_daemon_java.pid")

# post process log/pid
PP_JAVA_LOG = os.path.join(DAEMON_LOG_DIR, "ppdaemon_java_scorebot.log")
PP_JAVA_DAEMON_PID = os.path.join(DAEMON_BASE_DIR, "maintenance_ppdaemon_java.pid")

# =======================Kraken===========================
# log/pid
SCOREBOT_DAEMON_KRAKEN_LOG = os.path.join(DAEMON_LOG_DIR, "daemon_kraken_scorebot.log")
SCOREBOT_DAEMON_KRAKEN_PID = os.path.join(DAEMON_BASE_DIR, "maintenance_daemon_kraken.pid")

# post process log/pid
PP_KRAKEN_LOG = os.path.join(DAEMON_LOG_DIR, "ppdaemon_kraken_scorebot.log")
PP_KRAKEN_DAEMON_PID = os.path.join(DAEMON_BASE_DIR, "maintenance_ppdaemon_kraken.pid")

# =====================================================
# Service constants
# =====================================================

# Group 1 = domain, 2 = org, 3 = repo
GITHUB_PUSH_REGEX = re.compile(r"(?:https://)(\S+?)/(\S+?)/(\S+)")
STATUS_CONTEXT = os.getenv("STATUS_CONTEXT")

HOST_NAME = socket.gethostname()

SSO_FLAG = os.getenv("SSO_FLAG")
GCP_FLAG = os.getenv("GCP_FLAG")
SECURE_FLAG = os.getenv("SECURE_FLAG")
DEBUG = True

# Tokens
GITHUB_API_TOKEN = os.getenv("GITHUB_API_TOKEN")
DJANGO_KEY = os.getenv("DJANGO_KEY")

# DB configs
DB_NAME = os.getenv("DB_NAME")
SB_SQL_PASSWORD = os.getenv("SB_SQL_PASSWORD")
SB_SQL_USER = os.getenv("SB_SQL_USER")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

SSO_REDIRECT = os.getenv("SSO_REDIRECT")

# Email configs
SMTP_SERVER = os.getenv("SMTP_SERVER")
DEFAULT_SMTP_SERVER = SMTP_SERVER

SCOREBOT_DL_EMAIL_ADDRESS_CRITICAL = os.getenv("SCOREBOT_CRITICAL_DL")
SCOREBOT_DL_EMAIL_ADDRESS = os.getenv("SCOREBOT_DL")
if GCP_FLAG:
    SCOREBOT_FROM_DL_CRITICAL = os.getenv("SCOREBOT_CRITICAL_DL_GCP")
    SCOREBOT_FROM_DL_EMAIL = os.getenv("SCOREBOT_DL_GCP")
else:
    SCOREBOT_FROM_DL_CRITICAL = SCOREBOT_DL_EMAIL_ADDRESS_CRITICAL
    SCOREBOT_FROM_DL_EMAIL = SCOREBOT_DL_EMAIL_ADDRESS
SCOREBOT_CONTACT_MSG = "For questions please contact {0}".format(SCOREBOT_DL_EMAIL_ADDRESS)
DEFAULT_EMAIL_ADDRESS = os.getenv("DEFAULT_EMAIL")

# Domains
DOMAIN = os.getenv("DOMAIN")
GITHUB_DOMAIN = os.getenv("GITHUB_DOMAIN")

# =====================================================
# SCORE Bot constants
# =====================================================

INSECURE_VARIABLE_SECURITY_CATEGORY = "Insecure Variable"
