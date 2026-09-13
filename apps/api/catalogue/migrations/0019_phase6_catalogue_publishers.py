"""Add the publisher facet without replacing the existing release hierarchy."""

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalogue", "0018_merge_new_releases_and_curated_labels"),
    ]

    operations = [
        migrations.CreateModel(
            name="Publisher",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("igdb_id", models.PositiveIntegerField(unique=True)),
                ("name", models.CharField(max_length=200)),
                ("slug", models.SlugField(max_length=200, unique=True)),
                ("source", models.CharField(default="igdb", max_length=50)),
                ("source_url", models.URLField(blank=True, max_length=500)),
                ("licence", models.CharField(blank=True, max_length=150)),
                ("snapshot_sha256", models.CharField(blank=True, max_length=64)),
                ("retrieved_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={"ordering": ("name",)},
        ),
        migrations.AddField(
            model_name="gamework",
            name="publishers",
            field=models.ManyToManyField(blank=True, related_name="works", to="catalogue.publisher"),
        ),
    ]
