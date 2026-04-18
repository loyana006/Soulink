from django import forms

from .models import BlogPost


class BlogPostForm(forms.ModelForm):
    class Meta:
        model = BlogPost
        fields = ["title", "excerpt", "body", "category", "is_published"]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control form-control-custom",
                    "placeholder": "Post title",
                }
            ),
            "excerpt": forms.Textarea(
                attrs={
                    "class": "form-control form-control-custom",
                    "rows": 3,
                    "placeholder": "Short summary (optional)",
                }
            ),
            "body": forms.Textarea(
                attrs={
                    "class": "form-control form-control-custom",
                    "rows": 12,
                    "placeholder": "Write your blog post...",
                }
            ),
            "category": forms.Select(attrs={"class": "form-select form-control-custom"}),
            "is_published": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
