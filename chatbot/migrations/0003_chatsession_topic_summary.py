from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("chatbot", "0002_remove_chatmessage_session_id_chatsession_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="chatsession",
            name="topic_summary",
            field=models.TextField(
                blank=True,
                help_text="Short recap of themes (e.g. from Rasa actions or heuristics).",
            ),
        ),
    ]
