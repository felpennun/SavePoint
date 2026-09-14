"""Database-backed permission anchor for the research and platform roles."""

from django.db import models


class ResearchPublication(models.Model):
    """Permission anchor; published evidence remains an immutable file."""

    class Meta:
        default_permissions = ()
        managed = False
        permissions = [
            ("view_research_panel", "Can view the research panel"),
            ("export_research_panel", "Can export research evidence"),
            ("access_platform_admin", "Can access the platform admin"),
        ]

