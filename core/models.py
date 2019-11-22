from django.db import models
from django.utils import timezone

# If adding framework, update here
FRAMEWORK_CHOICES = (
    ("CPP","CPP"),
    ("Java", "Java"),
    ("Kraken","Kraken"),
)

# Add categories here
SECURITY_CHOICES = (
    # e.g. ("XSS", "XSS")
)

PRIORITY_CHOICES = (
    ("P1", "P1"),
    ("P2", "P2"),
    ("P3", "P3"),
    ("P4", "P4"),
)


class WebhookPR(models.Model):
    pull_request_url = models.CharField(max_length=1024)
    framework = models.CharField(max_length=32, choices=FRAMEWORK_CHOICES)
    processed = models.BooleanField(default=False)
    queued_time = models.DateTimeField(editable=False)
    completed_time = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        """
        On save, update timestamps
        """
        if not self.id:
            self.queued_time = timezone.now()
        return super(WebhookPR, self).save(*args, **kwargs)

    class Meta(object):
        verbose_name_plural = "Incoming PR List"


# Control tables for each framework

class ScorebotControlCpp(models.Model):
    id = models.AutoField(primary_key=True)
    security_category = models.CharField(choices=SECURITY_CHOICES, max_length=128, unique=True)
    silent = models.BooleanField(default=True)
    notify = models.BooleanField(default=False,)
    enforce = models.BooleanField(default=False)
    notify_pp = models.BooleanField(default=False)
    post_process = models.BooleanField(default=False)
    priority_level = models.CharField(choices=PRIORITY_CHOICES, max_length=32)
    excluded_paths = models.CharField(max_length=1024, blank=True)
    updated_time = models.DateTimeField(editable=True)

    def save(self, *args, **kwargs):
        """
        On save, update timestamps
        """
        if not self.id:
            self.updated_time = timezone.now()
        if self.silent:
            self.notify = False
            self.notify_pp = False
        if self.notify:
            self.silent = False
        if not self.silent and not self.notify and not self.notify_pp and not self.post_process and not self.enforce:
            self.silent = True
        return super(ScorebotControlCpp, self).save(*args, **kwargs)

    class Meta(object):
        verbose_name_plural = "Control: CPP"


class ScorebotControlJava(models.Model):
    id = models.AutoField(primary_key=True)
    security_category = models.CharField(choices=SECURITY_CHOICES, max_length=128, unique=True)
    silent = models.BooleanField(default=True)
    notify = models.BooleanField(default=False)
    enforce = models.BooleanField(default=False)
    notify_pp = models.BooleanField(default=False)
    post_process = models.BooleanField(default=False)
    priority_level = models.CharField(choices=PRIORITY_CHOICES, max_length=32)
    excluded_paths = models.CharField(max_length=1024, blank=True)
    updated_time = models.DateTimeField(editable=True)

    def save(self, *args, **kwargs):
        """
        On save, update timestamps
        """
        if not self.id:
            self.updated_time = timezone.now()
        if self.silent:
            self.notify = False
            self.notify_pp = False
        if self.notify:
            self.silent = False
        if not self.silent and not self.notify and not self.notify_pp and not self.post_process and not self.enforce:
            self.silent = True
        return super(ScorebotControlJava, self).save(*args, **kwargs)

    class Meta(object):
        verbose_name_plural = "Control: Java"


class ScorebotControlKraken(models.Model):
    id = models.AutoField(primary_key=True)
    security_category = models.CharField(choices=SECURITY_CHOICES, max_length=128, unique=True)
    silent = models.BooleanField(default=True)
    notify = models.BooleanField(default=False)
    enforce = models.BooleanField(default=False)
    notify_pp = models.BooleanField(default=False)
    post_process = models.BooleanField(default=False)
    priority_level = models.CharField(choices=PRIORITY_CHOICES, max_length=32)
    excluded_paths = models.CharField(max_length=1024, blank=True)
    updated_time = models.DateTimeField(editable=True)

    def save(self, *args, **kwargs):
        """
        On save, update timestamps
        """
        if not self.id:
            self.updated_time = timezone.now()
        if self.silent:
            self.notify = False
            self.notify_pp = False
        if self.notify:
            self.silent = False
        if not self.silent and not self.notify and not self.notify_pp and not self.post_process and not self.enforce:
            self.silent = True
        return super(ScorebotControlKraken, self).save(*args, **kwargs)

    class Meta(object):
        verbose_name_plural = "Control: Kraken"


class ScorebotMetrics(models.Model):
    id = models.AutoField(primary_key=True)
    function_name = models.CharField(max_length=256)
    security_category = models.CharField(choices=SECURITY_CHOICES, max_length=128)
    priority_level = models.CharField(choices=PRIORITY_CHOICES, max_length=32)
    framework = models.CharField(choices=FRAMEWORK_CHOICES, max_length=32)
    file_name = models.CharField(max_length=1024)
    user = models.CharField(max_length=128)
    repo = models.CharField(max_length=1024)
    branch = models.CharField(max_length=128)
    pull_request_url = models.CharField(max_length=1024)
    queued_time = models.DateTimeField(editable=False)
    scorebot_mode = models.CharField(max_length=64)
    notification_pp = models.CharField(max_length=16)
    post_process = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        """
        On save, update timestamps
        """
        if not self.id:
            self.queued_time = timezone.now()
        return super(ScorebotMetrics, self).save(*args, **kwargs)

    class Meta(object):
        verbose_name_plural = "SCORE Bot Metrics"


class ExemptionMetrics(models.Model):
    id = models.AutoField(primary_key=True)
    pull_request_url = models.CharField(max_length=1024)
    commit_id = models.CharField(max_length=256)
    framework = models.CharField(choices=FRAMEWORK_CHOICES, max_length=32)
    reason = models.CharField(max_length=128)
    description = models.CharField(max_length=1024)
    user = models.CharField(max_length=128)
    queued_time = models.DateTimeField(editable=False)

    def save(self, *args, **kwargs):
        """
        On save, update timestamps
        """
        if not self.id:
            self.queued_time = timezone.now()
        return super(ExemptionMetrics, self).save(*args, **kwargs)

    class Meta(object):
        verbose_name_plural = "Exemption Metrics"


class EnforcementMetrics(models.Model):
    id = models.AutoField(primary_key=True)
    function_name = models.CharField(max_length=256)
    security_category = models.CharField(choices=SECURITY_CHOICES, max_length=128)
    priority_level = models.CharField(choices=PRIORITY_CHOICES, max_length=32)
    framework = models.CharField(choices=FRAMEWORK_CHOICES, max_length=32)
    file_name = models.CharField(max_length=1024)
    pull_request_url = models.CharField(max_length=1024)
    repo = models.CharField(max_length=1024)
    branch = models.CharField(max_length=128)
    commit_id = models.CharField(max_length=256)
    user = models.CharField(max_length=128)
    notification_pp = models.CharField(max_length=16)
    status = models.CharField(max_length=64)
    queued_time = models.DateTimeField(editable=False)

    def save(self, *args, **kwargs):
        """
        On save, update timestamps
        """
        if not self.id:
            self.queued_time = timezone.now()
        return super(EnforcementMetrics, self).save(*args, **kwargs)

    class Meta(object):
        verbose_name_plural = "Enforcement Metrics"


class PostProcessMetrics(models.Model):
    id = models.AutoField(primary_key=True)
    pull_request_url = models.CharField(max_length=1024)
    state = models.CharField(max_length=32)
    closed_user = models.CharField(max_length=128)
    security_category = models.CharField(choices=SECURITY_CHOICES, max_length=128)
    framework = models.CharField(choices=FRAMEWORK_CHOICES, max_length=32)
    queued_time = models.DateTimeField(editable=False)

    def save(self, *args, **kwargs):
        """
        On save, update timestamps
        """
        if not self.id:
            self.queued_time = timezone.now()
        return super(PostProcessMetrics, self).save(*args, **kwargs)

    class Meta(object):
        verbose_name_plural = "Post-Process Metrics"


class BlacklistedPrsLog(models.Model):
    pull_request_url = models.CharField(max_length=1024)
    framework = models.CharField(choices=FRAMEWORK_CHOICES, max_length=32)
    repo = models.CharField(max_length=1024)
    user = models.CharField(max_length=128)
    queued_time = models.DateTimeField(editable=False)

    def save(self, *args, **kwargs):
        """
        On save, update timestamps
        """
        if not self.id:
            self.queued_time = timezone.now()
        return super(BlacklistedPrsLog, self).save(*args, **kwargs)

    class Meta(object):
        verbose_name_plural = "Blacklisted PRs Log"


class EntropyLog(models.Model):
    variable_name = models.CharField(max_length=256)
    entropy_value = models.CharField(max_length=32)
    variable_value = models.CharField(max_length=1024)
    entropy_line = models.CharField(max_length=1024)
    pull_request_url = models.CharField(max_length=1024)
    framework = models.CharField(choices=FRAMEWORK_CHOICES, max_length=32)
    queued_time = models.DateTimeField(editable=False)

    def save(self, *args, **kwargs):
        """
        On save, update timestamps
        """
        if not self.id:
            self.queued_time = timezone.now()
        return super(EntropyLog, self).save(*args, **kwargs)

    class Meta(object):
        verbose_name_plural = "Entropy Log"


class ValueLog(models.Model):
    variable_name = models.CharField(max_length=256)
    value = models.CharField(max_length=32)
    pull_request_url = models.CharField(max_length=1024)
    framework = models.CharField(choices=FRAMEWORK_CHOICES, max_length=32)
    logged_time = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        """
        On save, update timestamps
        """
        if not self.id:
            self.logged_time = timezone.now()
        return super(ValueLog, self).save(*args, **kwargs)

    class Meta(object):
        verbose_name_plural = "Value Log"


# ADD FRAMEWORK TO FOLLOWING MODELS=================================

class ScorebotConfig(models.Model):
    config = models.CharField(max_length=128)
    value = models.TextField(max_length=1024)
    cpp = models.BooleanField(default=True)
    java = models.BooleanField(default=False)
    kraken = models.BooleanField(default=False)

    class Meta(object):
        verbose_name_plural = "SCORE Bot Config"


class PatternList(models.Model):
    function_name = models.CharField(max_length=256)
    security_category = models.CharField(choices=SECURITY_CHOICES, max_length=128)
    cpp = models.BooleanField(default=True)
    java = models.BooleanField(default=False)
    kraken = models.BooleanField(default=False)

    class Meta(object):
        verbose_name_plural = "Patterns List"


class MessageList(models.Model):
    function_name = models.CharField(max_length=256)
    security_category = models.CharField(choices=SECURITY_CHOICES, max_length=128)
    header = models.CharField(max_length=128)
    intro = models.TextField(max_length=1024)
    security_issue = models.TextField(max_length=1024, blank=True)
    how_to_fix = models.TextField(max_length=4096, blank=True)
    references = models.TextField(max_length=1024, blank=True)
    reference_name = models.TextField(max_length=1024, blank=True)
    cpp = models.BooleanField(default=True)
    java = models.BooleanField(default=False)
    kraken = models.BooleanField(default=False)

    class Meta(object):
        verbose_name_plural = "Message List"
