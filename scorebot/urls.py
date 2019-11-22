"""SCORE Bot URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, re_path, include
from core import views
from core.webhook_handlers.WebhookScorebotHandler import WebhookScorebotHandler
score_bot_handler = WebhookScorebotHandler.as_view()

prefix_path = ""
ADMIN_PREFIX_PATH = ""

urlpatterns = [
    path(prefix_path, include([
        path("", views.exemptions_page, {"template_name": "exemptions.html"}, name="exemptions"),
        re_path(r"^admin/", admin.site.urls),

        # APIs
        re_path(r"score_bot_metrics_(?P<framework>[\w\-]+)$", views.scorebot_metrics_all),
        re_path(r"score_bot_metrics_(?P<framework>[\w\-]+)/(?P<start>\d{4}-\d{2}-\d{2})/(?P<end>\d{4}-\d{2}-\d{2})$",
                views.scorebot_metrics_start_end),
        re_path("enforcement_metrics_(?P<framework>[\w\-]+)$", views.enforcement_metrics_all),
        re_path(r"enforcement_metrics_(?P<framework>[\w\-]+)/(?P<start>\d{4}-\d{2}-\d{2})/(?P<end>\d{4}-\d{2}-\d{2})$",
                views.enforcement_metrics_start_end),
        re_path("score_bot_pr_(?P<framework>[\w\-]+)$", views.pr_count_all),
        re_path(r"score_bot_pr_(?P<framework>[\w\-]+)/(?P<start>\d{4}-\d{2}-\d{2})/(?P<end>\d{4}-\d{2}-\d{2})$",
                views.pr_count_start_end),
        re_path(r"score_bot_daemon_(?P<framework>[\w\-]+)$", views.daemon_health),

        # SSO
        path("saml/acs", views.acs, name="acs"),
        path("attrs", views.attrs, name="attrs"),
        path("metadata", views.metadata, name="metadata"),

        # Webhooks
        re_path(r"api/v1/webhook/scorebot_(?P<framework>[\w\-]+)$", score_bot_handler),
    ])),
]
