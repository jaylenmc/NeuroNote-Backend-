from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("flashcards", "0004_reviewgroupcard_time_in_group_blacklist"),
    ]

    operations = [
        migrations.AddField(
            model_name="card",
            name="is_blacklisted",
            field=models.BooleanField(
                default=False,
                help_text="True while the card is in the user's active Study Queue review group.",
            ),
        ),
    ]
