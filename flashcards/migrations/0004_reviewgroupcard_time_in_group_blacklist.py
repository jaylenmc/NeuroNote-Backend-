from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("flashcards", "0003_srs_study_queue"),
    ]

    operations = [
        migrations.AlterField(
            model_name="reviewgroupcard",
            name="time_in_group",
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.DeleteModel(
            name="CardStudyRestriction",
        ),
    ]
