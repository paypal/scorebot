from rest_framework import serializers


class ScorebotMetricsSerializer(serializers.Serializer):
    function_name = serializers.CharField(max_length=128)
    priority_level = serializers.CharField(max_length=32)
    security_category = serializers.CharField(max_length=64)
    framework = serializers.CharField(max_length=32)
    file_name = serializers.CharField(max_length=256)
    user = serializers.CharField(max_length=128)
    repo = serializers.CharField(max_length=128)
    branch = serializers.CharField(max_length=64)
    pull_request_url = serializers.CharField(max_length=1024)
    queued_time = serializers.DateTimeField()
    scorebot_mode = serializers.CharField(max_length=64)
    notification_pp = serializers.CharField(max_length=16)
    id = serializers.ReadOnlyField()


class WebhookPRSerializer(serializers.Serializer):
    pull_request_url = serializers.CharField(max_length=1024)
    framework = serializers.CharField(max_length=32)
    completed_time = serializers.DateTimeField()
    id = serializers.ReadOnlyField()


class EnforcementMetricsSerializer(serializers.Serializer):
    function_name = serializers.CharField(max_length=1024)
    security_category = serializers.CharField(max_length=128)
    priority_level = serializers.CharField(max_length=32)
    framework = serializers.CharField(max_length=32)
    file_name = serializers.CharField(max_length=1024)
    pull_request_url = serializers.CharField(max_length=1024)
    repo = serializers.CharField(max_length=128)
    branch = serializers.CharField(max_length=128)
    commit_id = serializers.CharField(max_length=64)
    user = serializers.CharField(max_length=1024)
    status = serializers.CharField(max_length=64)
    queued_time = serializers.DateTimeField()
    id = serializers.ReadOnlyField()
