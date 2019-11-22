from django import forms

from core.models import ExemptionMetrics


class ExemptionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ExemptionForm, self).__init__(*args, **kwargs)

    FRAMEWORKS = (("CPP", "CPP"),
                  ("Java", "Java"),
                  ("Kraken", "Kraken"))

    REASONS = (("This is not an issue", "This is not an issue"),
               ("Cannot fix the issue", "Cannot fix the issue"),
               ("Do not know how to fix the issue", "Do not know how to fix the issue"),
               ("Fixed issue in a different commit", "Fixed issue in a different commit "
                                                     "(Provide commit ID in the box below)"),
               ("Will fix at a later time", "Will fix at a later time"),
               ("Other", "Other"))

    framework = forms.ChoiceField(label="Stack", choices=FRAMEWORKS, required=True,
                                  widget=forms.Select(attrs={"class": "vx_form-control"}))
    pull_request_url = forms.CharField(label="Pull Request URL", max_length=1024, required=True,
                                       widget=forms.TextInput(attrs={"class": "form-control vx_form-control"}))
    commit_id = forms.CharField(label="Failed Commit ID", max_length=64, required=True,
                                widget=forms.TextInput(attrs={"class": "form-control vx_form-control"}))
    reason = forms.ChoiceField(choices=REASONS, required=True,
                               widget=forms.Select(attrs={"class": "vx_form-control"}))
    description = forms.CharField(label="", required=True,
                                  widget=forms.Textarea(attrs={"rows": "5", "cols": "102",
                                                               "class": "form-control vx_form-control",
                                                               "placeholder": "If the reason is 'Fixed issue in a "
                                                                              "different commit provide the commit id "
                                                                              "here. No other information is needed. "
                                                                              "For all other reasons, provide a brief "
                                                                              "summary."}))

    class Meta:
        model = ExemptionMetrics
        fields = ["pull_request_url", "commit_id", "framework", "reason", "description"]
        exclude = ["user"]
