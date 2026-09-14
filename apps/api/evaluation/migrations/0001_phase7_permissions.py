from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ResearchPublication",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
            ],
            options={
                "default_permissions": (),
                "managed": False,
                "permissions": [
                    ("view_research_panel", "Can view the research panel"),
                    ("export_research_panel", "Can export research evidence"),
                    ("access_platform_admin", "Can access the platform admin"),
                ],
            },
        ),
    ]

