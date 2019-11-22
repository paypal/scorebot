import logging
import traceback

from rest_framework import response
from rest_framework import status
from rest_framework.views import APIView

from core.models import WebhookPR, ScorebotConfig


class WebhookScorebotHandler(APIView):
    """
    Handler Class to handle Webhook calls from GitHub
    """

    def __init__(self):
        super(WebhookScorebotHandler, self).__init__()
        self._logger = logging.getLogger(__name__)

    def _queue_pull_request_data(self, pull_request_url, framework):
        """
        Queue the pull request data for processing.
        :param pull_request_url: URL of the pull request
        :param : github webhook action
        :return: response_status: api status code
        """
        self._logger.info("_queue_pull_request_data: {0}".format(pull_request_url))

        framework_map = {"cpp": "CPP",
                         "java": "Java",
                         "kraken": "Kraken"}

        try:
            WebhookPR.objects.create(pull_request_url=pull_request_url, framework=framework_map[framework])
            self._logger.info("WebhookScoreBotHandler pull request data queued successfully")
            response_status = status.HTTP_204_NO_CONTENT
        except Exception as err:
            self._logger.error("\n{0}\n{1}\n".format(type(err), traceback.format_exc()))
            response_status = status.HTTP_500_INTERNAL_SERVER_ERROR

        return response_status

    def post(self, request, framework):
        """
        This method is called from GitHub webhooks to validate Score Bot rules.
        Queues the event data for processing by the ScoreBotDaemon.
        """
        self._logger.debug("WebhookScoreBot post entered.")

        pr_data = request.data.get("pull_request")
        if not pr_data:
            self._logger.error(f"Invalid pull request data received: {pr_data}")
            return response.Response(status=status.HTTP_400_BAD_REQUEST)

        pr_url = pr_data.get("html_url")
        if not pr_url:
            self._logger.error(f"Invalid pull request url received: {pr_data}")
            return response.Response(status=status.HTTP_400_BAD_REQUEST)

        user = pr_data.get("user")
        if user:
            login = user.get("login")
            self._logger.info(f"Username associated with PR: {login}")

        # Drop excluded repos
        excluded_repos = ScorebotConfig.objects.filter(config="excluded_repos")
        excluded_repos = excluded_repos.values()[0]["value"].split(",") if excluded_repos else []

        try:
            repo = pr_url.split("/pull")[0]
            repo = repo[repo.rfind("/")+1:]

        except Exception:
            self._logger.error(f"Invalid pull request url received: {pr_url}")
            return response.Response(status=status.HTTP_400_BAD_REQUEST)

        if repo in excluded_repos:
            self._logger.info(f"Repo {repo} found in excluded repos list")
            return response.Response(status=status.HTTP_200_OK)

        # Otherwise queue pull request data for processing
        self._logger.info(f"Queuing action: {pr_url} for pull request")
        response_status = self._queue_pull_request_data(pr_url, framework)

        return response.Response(status=response_status)
