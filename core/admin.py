from django.contrib import admin

from core.models import WebhookPR, ScorebotControlCpp, ScorebotControlJava, ScorebotControlKraken, ScorebotMetrics,\
    ExemptionMetrics, EnforcementMetrics, PostProcessMetrics, BlacklistedPrsLog, EntropyLog, ValueLog, ScorebotConfig,\
    PatternList, MessageList


# ============= CORE =====================

@admin.register(WebhookPR)
class WebhookPRAdmin(admin.ModelAdmin):
    fields = ["pull_request_url", "framework", "processed"]
    list_display = ("id", "pull_request_url", "framework", "processed", "queued_time", "completed_time")


@admin.register(ScorebotControlCpp)
class ScorebotControlCppAdmin(admin.ModelAdmin):
    fields = ["security_category", "silent", "notify", "enforce", "notify_pp", "post_process", "priority_level",
              "excluded_paths"]
    list_display = ("security_category", "silent", "notify", "enforce", "notify_pp", "post_process", "priority_level",
                    "excluded_paths", "updated_time")


@admin.register(ScorebotControlJava)
class ScorebotControlJavaAdmin(admin.ModelAdmin):
    fields = ["security_category", "silent", "notify", "enforce", "notify_pp", "post_process", "priority_level",
              "excluded_paths"]
    list_display = ("security_category", "silent", "notify", "enforce", "notify_pp", "post_process", "priority_level",
                    "excluded_paths", "updated_time")


@admin.register(ScorebotControlKraken)
class ScorebotControlKrakenAdmin(admin.ModelAdmin):
    fields = ["security_category", "silent", "notify", "enforce", "notify_pp", "post_process", "priority_level",
              "excluded_paths"]
    list_display = ("security_category", "silent", "notify", "enforce", "notify_pp", "post_process", "priority_level",
                    "excluded_paths", "updated_time")


@admin.register(ScorebotMetrics)
class ScorebotMetricsAdmin(admin.ModelAdmin):
    fields = ["function_name", "priority_level", "security_category", "framework", "file_name", "user", "repo",
              "branch", "pull_request_url", "scorebot_mode", "notification_pp", "post_process"]
    list_display = ("id", "function_name", "priority_level", "security_category", "framework", "file_name", "user",
                    "repo", "branch", "pull_request_url", "scorebot_mode", "notification_pp", "post_process",
                    "queued_time")


@admin.register(ExemptionMetrics)
class ExemptionMetricsAdmin(admin.ModelAdmin):
    fields = ["pull_request_url", "commit_id", "framework", "reason", "description", "user"]
    list_display = ("id", "pull_request_url", "commit_id", "framework", "reason", "description", "user", "queued_time")


@admin.register(EnforcementMetrics)
class EnforcementMetricsAdmin(admin.ModelAdmin):
    fields = ["function_name", "security_category", "priority_level", "framework", "file_name", "pull_request_url",
              "repo", "branch", "commit_id", "user", "notification_pp", "status"]
    list_display = ("id", "function_name", "security_category", "priority_level", "framework", "file_name",
                    "pull_request_url", "repo", "branch", "commit_id", "user", "notification_pp", "status",
                    "queued_time")


@admin.register(PostProcessMetrics)
class PostProcessMetricsAdmin(admin.ModelAdmin):
    fields = ["pull_request_url", "state", "closed_user", "security_category", "framework"]
    list_display = ("id", "pull_request_url", "state", "closed_user", "security_category", "framework", "queued_time")


@admin.register(BlacklistedPrsLog)
class BlacklistedPrLogAdmin(admin.ModelAdmin):
    fields = ["pull_request_url", "framework", "repo", "user"]
    list_display = ("pull_request_url", "framework", "repo", "user", "queued_time")


@admin.register(EntropyLog)
class EntropyLogAdmin(admin.ModelAdmin):
    fields = ["variable_name", "entropy_value", "variable_value", "entropy_line", "framework", "pull_request_url"]
    list_display = ("variable_name", "entropy_value", "variable_value", "entropy_line", "framework",
                    "pull_request_url", "queued_time")


@admin.register(ValueLog)
class ValueLogAdmin(admin.ModelAdmin):
    fields = ["variable_name", "value", "pull_request_url"]
    list_display = ("variable_name", "value", "pull_request_url", "logged_time")


@admin.register(ScorebotConfig)
class ScorebotConfigAdmin(admin.ModelAdmin):
    fields = ["config", "value", "cpp", "java", "kraken"]
    list_display = ("config", "value", "cpp", "java", "kraken")


@admin.register(PatternList)
class PatternListAdmin(admin.ModelAdmin):
    fields = ["function_name", "security_category", "cpp", "java", "kraken"]
    list_display = ("function_name", "security_category", "cpp", "java", "kraken")


@admin.register(MessageList)
class MessageListAdmin(admin.ModelAdmin):
    fields = ["function_name", "security_category", "header", "intro", "security_issue", "how_to_fix", "references",
              "reference_name", "cpp", "java", "kraken"]
    list_display = ("function_name", "security_category", "header", "intro", "security_issue", "how_to_fix",
                    "references", "reference_name", "cpp", "java", "kraken")
