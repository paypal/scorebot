from common import constants
import logging
from external_tools.common import constants as et_constants

logging.basicConfig()
logger = logging.getLogger(__name__)

github_token = constants.GITHUB_API_TOKEN

if github_token:
    et_constants.load_constants({"GITHUB_API_TOKEN": github_token})
