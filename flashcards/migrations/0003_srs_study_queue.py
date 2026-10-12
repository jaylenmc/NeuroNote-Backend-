# Generated manually for Phase 1 SRS Study Queue

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("flashcards", "0002_remove_card_difficulty_remove_card_learning_status_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name="card",
            name="last_review_date",
        ),
        migrations.AddField(
            model_name="card",
            name="last_reviewed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="card",
            name="bucket",
            field=models.CharField(
                choices=[
                    ("bkt_0", "New Card"),
                    ("bkt_1", "Bucket 1"),
                    ("bkt_2", "Bucket 2"),
                    ("bkt_3", "Bucket 3"),
                    ("bkt_4", "Bucket 4"),
                ],
                default="bkt_0",
                max_length=10,
            ),
        ),
        migrations.CreateModel(
            name="ReviewGroup",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "scope",
                    models.CharField(
                        choices=[("single_deck", "Single deck"), ("all_cards", "All cards")],
                        max_length=20,
                    ),
                ),
                (
                    "group_type",
                    models.CharField(
                        choices=[
                            ("study_queue", "Study Queue"),
                            ("time_crunch", "Time Crunch"),
                            ("exam", "Exam"),
                        ],
                        default="study_queue",
                        max_length=20,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("active", "Active"),
                            ("completed", "Completed"),
                            ("cancelled", "Cancelled"),
                        ],
                        default="active",
                        max_length=20,
                    ),
                ),
                ("scheduled_study_date", models.DateField(blank=True, null=True)),
                ("sequence_index", models.IntegerField(blank=True, null=True)),
                ("group_size", models.IntegerField(default=20)),
                ("is_timed", models.BooleanField(default=False)),
                ("timer_seconds", models.IntegerField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "deck",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="flashcards.deck",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="review_groups",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="CardStudyRestriction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("blacklisted_until", models.DateTimeField(blank=True, null=True)),
                (
                    "card",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="flashcards.card"),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ReviewGroupCard",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("time_in_group", models.DateTimeField()),
                (
                    "source",
                    models.CharField(
                        choices=[("auto", "Auto"), ("manual", "Manual")],
                        default="auto",
                        max_length=10,
                    ),
                ),
                (
                    "card",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="group_memberships",
                        to="flashcards.card",
                    ),
                ),
                (
                    "group",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="memberships",
                        to="flashcards.reviewgroup",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="reviewlog",
            name="review_group",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="review_logs",
                to="flashcards.reviewgroup",
            ),
        ),
        migrations.AddConstraint(
            model_name="reviewgroup",
            constraint=models.UniqueConstraint(
                condition=models.Q(("group_type", "study_queue"), ("status", "active")),
                fields=("user",),
                name="unique_active_study_queue_per_user",
            ),
        ),
        migrations.AddConstraint(
            model_name="reviewgroupcard",
            constraint=models.UniqueConstraint(
                fields=("group", "card"),
                name="unique_card_per_review_group",
            ),
        ),
        migrations.AddConstraint(
            model_name="cardstudyrestriction",
            constraint=models.UniqueConstraint(
                fields=("user", "card"),
                name="unique_card_restriction_per_user",
            ),
        ),
    ]
