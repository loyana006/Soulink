from django import forms
from confession.models import ConfessionModal


class ConfessionEntryForm(forms.ModelForm):
    class Meta:
        model = ConfessionModal
        fields = ["title", "content", "topic", "is_anonymous"]

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
                    "placeholder": "Share your feelings, story, or question anonymously...",
                }
            ),
            "topic": forms.Select(
                attrs={
                    "class": "form-control-custom mb-3",
                }
            ),
            "is_anonymous": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
