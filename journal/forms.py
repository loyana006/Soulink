from django import forms

from journal.models import JournalEntry


class JournalEntryForm(forms.ModelForm):
    title = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder": "Title of your entry",
            }
        )
    )
    entry = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "placeholder": "Start writing here... What happened today? How did it make you feel? What did you learn?"
            }
        )
    )
    mood = forms.ChoiceField(
        choices=[("", "How are you feeling? (optional)")] + list(JournalEntry.MOOD_CHOICES),
        required=False,
        widget=forms.Select(attrs={"class": "form-select form-control-custom mb-3"}),
    )

    class Meta:
        model = JournalEntry
        fields = ["title", "entry", "mood"]
