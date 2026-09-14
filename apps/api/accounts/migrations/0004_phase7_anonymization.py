import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("accounts", "0003_phase5_profile")]

    operations = [
        migrations.AddField(
            model_name="accountprofile",
            name="admin_uuid",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.AddField(
            model_name="accountprofile",
            name="is_anonymized",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="accountprofile",
            name="anonymized_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]

