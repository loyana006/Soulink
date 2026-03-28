from django import forms
from confession.models import ConfessionModal


class ConfessionEntryForm(forms.ModelForm):
    class Meta:
        model = ConfessionModal
        fields = ["title", "content", "topic", "is_anonymous", "is_draft"]

        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control-custom mb-3",
                    "placeholder": "A short title for your post",
                }
            ),
            "content": forms.Textarea(
                attrs={
                    "class": "form-control-custom mb-3",
                    "placeholder": "What's on your mind?",
                }
            ),
            "topic": forms.Select(
                attrs={
                    "class": "form-control-custom mb-3",
                }
            ),
            "is_anonymous": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_draft": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
