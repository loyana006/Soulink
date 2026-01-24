from django.db import models
from django.db.models.fields import TextField
from accounts.models import CustomUser


class JournalEntry(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    title = TextField()
    entry = TextField(max_length=50000)
    entry_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
