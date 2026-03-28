from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("journal", "0002_rename_user_id_journalentry_user"),
    ]

    operations = [
        migrations.AddField(
            model_name="journalentry",
            name="mood",
            field=models.CharField(
                blank=True,
                choices=[
                    ("great", "Great"),
                    ("good", "Good"),
                    ("okay", "Okay"),
                    ("low", "Low"),
                    ("tough", "Tough"),
                ],
                default="",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="journalentry",
            name="sentiment_analysis",
            field=models.JSONField(blank=True, null=True),
        ),
    ]
