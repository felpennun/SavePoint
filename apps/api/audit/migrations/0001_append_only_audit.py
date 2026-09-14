from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


FORWARD_SQL = """
CREATE OR REPLACE FUNCTION audit_event_append_only() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'audit_event rows are append-only';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_event_append_only_trigger
BEFORE UPDATE OR DELETE ON audit_auditevent
FOR EACH ROW EXECUTE FUNCTION audit_event_append_only();
"""

REVERSE_SQL = """
DROP TRIGGER IF EXISTS audit_event_append_only_trigger ON audit_auditevent;
DROP FUNCTION IF EXISTS audit_event_append_only();
"""


class Migration(migrations.Migration):
    initial = True

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="AuditEvent",
            fields=[
                ("id", models.UUIDField(editable=False, primary_key=True, serialize=False)),
                (
                    "action",
                    models.CharField(
                        choices=[
                            ("account.anonymized", "Account anonymized"),
                            ("account.deleted", "Account deleted"),
                            ("account.deactivated", "Account deactivated"),
                        ],
                        max_length=32,
                    ),
                ),
                (
                    "resource_type",
                    models.CharField(
                        choices=[
                            ("account", "Account"),
                            ("profile", "Profile"),
                            ("catalogue", "Catalogue"),
                            ("import", "Import"),
                            ("job", "Job"),
                            ("experiment", "Experiment"),
                        ],
                        max_length=16,
                    ),
                ),
                ("resource_id", models.CharField(max_length=64)),
                ("occurred_at", models.DateTimeField(auto_now_add=True)),
                (
                    "result",
                    models.CharField(
                        choices=[("succeeded", "Succeeded"), ("already_applied", "Already applied")],
                        max_length=16,
                    ),
                ),
                ("operation_ref", models.UUIDField(unique=True)),
                (
                    "actor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="audit_events",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ("occurred_at", "id"),
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(action__in=["account.anonymized", "account.deleted", "account.deactivated"]),
                        name="audit_action_allowlisted",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(resource_type__in=["account", "profile", "catalogue", "import", "job", "experiment"]),
                        name="audit_resource_type_allowlisted",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(result__in=["succeeded", "already_applied"]),
                        name="audit_result_allowlisted",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(resource_id__regex="^[A-Za-z0-9._:-]{1,64}$"),
                        name="audit_resource_id_sanitized",
                    ),
                ],
            },
        ),
        migrations.RunSQL(FORWARD_SQL, REVERSE_SQL),
    ]

