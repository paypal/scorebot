"""
    This will setup Django ORM and models so they can be used outside of the Django server.
    NOTE: Only import this from code that is not a part of the Django server.
"""
from common import constants
import logging
from common.orm_loaded_constants.enable_django_orm import enable_django_orm
from external_tools.common import constants as et_constants

logger = logging.getLogger(__name__)
github_token = constants.GITHUB_API_TOKEN
enable_django_orm()

if github_token:
    et_constants.load_constants({"GITHUB_API_TOKEN": github_token})
