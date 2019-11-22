"""
    KEEP THIS SECTION UP TO DATE ALPHABETICALLY:
        When you add a constant that is going to be loaded externally then:
            * Update this area.
            * Update the method (load_constants) at the bottom of this file.
            * Update the the appropriate config.sql script in the rma_notes repo.

    Environment variables:
        DEFAULT_EMAIL_ADDRESS  # Required
        GITHUB_API_TOKEN  # Required
        GITHUB_API_USER  # Required
        SMTP_SERVER  # Optional

    Variables that can be loaded:
        DEFAULT_EMAIL_ADDRESS
        GITHUB_API_TOKEN
        GITHUB_API_USER
        GITHUB_ORG
"""

import os
import re

# =====================================================
# Constants - keep sections in alphabetical order
# =====================================================

# =====================================================
# Common constants
# =====================================================

try:
    CURRENT_USER = os.environ.get('LOGNAME') or os.environ['USER']
    if not CURRENT_USER:
        CURRENT_USER = "Unknown"
except KeyError:
    CURRENT_USER = "Unknown"

# =====================================================
# GitHub constants
# =====================================================

GITHUB_API_PATH = "/api/v3/"
GITHUB_API_TOKEN = os.getenv("GITHUB_API_TOKEN")
GITHUB_API_USER = os.getenv("GITHUB_API_USER")
GITHUB_DOMAIN = os.getenv("GITHUB_DOMAIN")
GITHUB_ORG = ""  # If using loaded configs below then this is a list of org names
GITHUB_SCHEMA = "https"

# GitHub regex
GITHUB_REGEX = re.compile(r'(https://{0}/\S+?/\S+?/pull/\d+)'.format(GITHUB_DOMAIN))
GITHUB_REGEX_GROUP = re.compile(r'(?:https://{0})/(\S+?)/(\S+?)/pull/(\d+)'.format(GITHUB_DOMAIN))
# Group 1 = domain, 2 = org, 3 = repo, 4 = PR number
GITHUB_REGEX_ALL_GROUPS = re.compile(r"(?:https://)(\S+?)/(\S+?)/(\S+?)/pull/(\d+)")

# =====================================================
# Notification constants
# =====================================================

DEFAULT_EMAIL_ADDRESS = os.getenv("DEFAULT_EMAIL_ADDRESS")
SMTP_SERVER = os.getenv("SMTP_SERVER")

# =====================================================
# =====================================================
# Utility method to set env var constants from dictionary instead of env vars.
#
# NOTE: please add any constant, that needs to be loaded, to this method.
# =====================================================
# =====================================================

# using this to ensure we only load the configs once
CONFIGS_LOADED = False


def load_constants(loaded_configs):
    """
    Utility method to set env var constants from dictionary instead of env vars.

    The idea is that you will store these values in your own db table instead of environment variables.

    On start up, create a dictionary out of the key/values in your table,
    then pass the dictionary into this method to load the constants.

    :param loaded_configs: dictionary of configs with values to be used to set constants.
    """
    global CONFIGS_LOADED

    # required
    global DEFAULT_EMAIL_ADDRESS
    global GITHUB_API_TOKEN
    global GITHUB_API_USER
    global GITHUB_ORG

    if not CONFIGS_LOADED:
        DEFAULT_EMAIL_ADDRESS = loaded_configs.get("DEFAULT_EMAIL_ADDRESS", DEFAULT_EMAIL_ADDRESS)
        GITHUB_API_TOKEN = loaded_configs.get("GITHUB_API_TOKEN", GITHUB_API_TOKEN)
        GITHUB_API_USER = loaded_configs.get("GITHUB_API_USER", GITHUB_API_USER)
        temp_github_org = loaded_configs.get("GITHUB_ORG", GITHUB_ORG)
        GITHUB_ORG = temp_github_org.split(",")

        CONFIGS_LOADED = True
