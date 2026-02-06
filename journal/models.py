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
    
    @property
    def word_count(self):
        """Calculate the word count of the entry"""
        if not self.entry:
            return 0
        # Count words by splitting on whitespace
        words = self.entry.strip().split()
        return len(words)
    
    @property
    def read_time(self):
        """Calculate estimated reading time in minutes (average 200 words per minute)"""
        words = self.word_count
        if words == 0:
            return 1  # Minimum 1 minute
        # Average reading speed: 200 words per minute
        minutes = max(1, round(words / 200))
        return minutes