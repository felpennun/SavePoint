"""Explicitly provision Phase 7 capabilities for operator-selected users."""

from __future__ import annotations

import uuid

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand, CommandError

GROUP_PERMISSIONS = {
    "Research Viewer": ("view_research_panel", "export_research_panel"),
    "Platform Admin": ("access_platform_admin",),
}


class Command(BaseCommand):
    help = "Assign Phase 7 groups only to explicitly named user UUIDs."

    @staticmethod
    def _as_list(value):  # noqa: ANN001
        """Normalize argparse lists and direct ``call_command`` scalar kwargs."""
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        return list(value)

    def add_arguments(self, parser) -> None:  # noqa: ANN001
        parser.add_argument(
            "--user-id",
            action="append",
            default=[],
            help="Explicit account UUID(s), used with one or more --group values.",
        )
        parser.add_argument(
            "--group",
            action="append",
            choices=tuple(GROUP_PERMISSIONS),
            default=[],
            help="Group(s) to assign to every --user-id.",
        )
        parser.add_argument(
            "--research-viewer-user-id",
            action="append",
            default=[],
            help="UUID of an explicitly selected user to add to Research Viewer.",
        )
        parser.add_argument(
            "--platform-admin-user-id",
            action="append",
            default=[],
            help="UUID of an explicitly selected user to add to Platform Admin.",
        )

    def handle(self, *args, **options) -> None:  # noqa: ANN002, ANN003
        assignments = {
            "Research Viewer": self._as_list(options["research_viewer_user_id"]),
            "Platform Admin": self._as_list(options["platform_admin_user_id"]),
        }
        user_ids = self._as_list(options["user_id"])
        groups = self._as_list(options["group"])
        if user_ids:
            if not groups:
                raise CommandError("--user-id requires at least one --group.")
            for group_name in groups:
                assignments[group_name].extend(user_ids)
        if not any(assignments.values()):
            raise CommandError("At least one explicit user UUID is required.")

        user_model = get_user_model()
        for group_name, raw_ids in assignments.items():
            if not raw_ids:
                continue
            users = []
            for raw_id in raw_ids:
                try:
                    user_uuid = uuid.UUID(raw_id)
                    user = user_model.objects.get(profile__admin_uuid=user_uuid)
                except (ValueError, AttributeError) as exc:
                    raise CommandError(f"Invalid user UUID: {raw_id}") from exc
                except user_model.DoesNotExist as exc:
                    raise CommandError(f"No account matches the explicit UUID: {raw_id}") from exc
                users.append((user, user_uuid))

            permission_codenames = GROUP_PERMISSIONS[group_name]
            group, _ = Group.objects.get_or_create(name=group_name)
            permissions = Permission.objects.filter(
                content_type__app_label="evaluation",
                codename__in=permission_codenames,
            )
            if permissions.count() != len(permission_codenames):
                raise CommandError(f"Phase 7 permissions are not migrated for {group_name}.")
            group.permissions.set(permissions)
            for user, user_uuid in users:
                user.groups.add(group)
                self.stdout.write(f"Provisioned {group_name} for account UUID {user_uuid}.")
