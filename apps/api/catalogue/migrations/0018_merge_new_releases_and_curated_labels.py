"""Merge the independent catalogue migration branches."""

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("catalogue", "0015_newreleasessnapshot"),
        ("catalogue", "0017_curated_label_perspective_and_split_screen"),
    ]

    operations = []
