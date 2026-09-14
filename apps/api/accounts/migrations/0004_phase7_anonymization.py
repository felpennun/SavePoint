import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("accounts", "0003_phase5_profile")]

    def _backfill_admin_uuids(apps, schema_editor):
        AccountProfile = apps.get_model("accounts", "AccountProfile")
        for profile in AccountProfile.objects.only("pk").iterator():
            AccountProfile.objects.filter(pk=profile.pk).update(admin_uuid=uuid.uuid4())

    operations = [
        migrations.AddField(
            model_name="accountprofile",
            name="admin_uuid",
            field=models.UUIDField(default=uuid.uuid4, editable=False),
        ),
        migrations.RunPython(_backfill_admin_uuids, migrations.RunPython.noop),
        migrations.AlterField(
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
