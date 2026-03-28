from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("confession", "0003_add_like_and_comment"),
    ]

    operations = [
        migrations.AddField(
            model_name="confessionmodal",
            name="is_draft",
            field=models.BooleanField(default=False),
        ),
    ]
