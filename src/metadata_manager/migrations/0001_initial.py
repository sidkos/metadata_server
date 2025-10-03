from django.db import migrations, models

import src.metadata_manager.models.user


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                (
                    "id",
                    models.CharField(
                        help_text="Israeli ID (string, 5-9 digits, valid checksum)",
                        max_length=9,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                        validators=[src.metadata_manager.models.user.User.validate_israeli_id],
                    ),
                ),
                ("name", models.CharField(help_text="Full name (required).", max_length=100)),
                (
                    "phone",
                    models.CharField(
                        help_text="Phone number in E.164 format (e.g., +972...).",
                        max_length=20,
                        validators=[src.metadata_manager.models.user.User.validate_phone],
                    ),
                ),
                ("address", models.CharField(help_text="Street address (required).", max_length=255)),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
