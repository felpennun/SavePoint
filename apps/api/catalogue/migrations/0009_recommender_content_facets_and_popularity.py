# Generated manually for the governed recommender signal extension.

import django.db.models.deletion
import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalogue", "0008_gamework_summary_es"),
    ]

    operations = [
        migrations.CreateModel(
            name="Developer",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("igdb_id", models.PositiveIntegerField(unique=True)),
                ("name", models.CharField(max_length=200, unique=True)),
                ("slug", models.SlugField(max_length=200, unique=True)),
            ],
            options={"ordering": ("name",)},
        ),
        migrations.CreateModel(
            name="Franchise",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("igdb_id", models.PositiveIntegerField(unique=True)),
                ("name", models.CharField(max_length=200, unique=True)),
                ("slug", models.SlugField(max_length=200, unique=True)),
            ],
            options={"ordering": ("name",)},
        ),
        migrations.AddField(
            model_name="gamework",
            name="developers",
            field=models.ManyToManyField(blank=True, related_name="works", to="catalogue.developer"),
        ),
        migrations.AddField(
            model_name="gamework",
            name="franchises",
            field=models.ManyToManyField(blank=True, related_name="works", to="catalogue.franchise"),
        ),
        migrations.CreateModel(
            name="CorpusPopularitySnapshot",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("corpus_version", models.CharField(max_length=32)),
                ("popularity_type_id", models.PositiveIntegerField()),
                ("popularity_type_name", models.CharField(max_length=120)),
                ("external_source", models.CharField(blank=True, max_length=120)),
                ("value", models.FloatField()),
                ("calculated_at", models.DateTimeField(blank=True, null=True)),
                ("source_updated_at", models.DateTimeField(blank=True, null=True)),
                ("retrieved_at", models.DateTimeField()),
                ("payload_sha256", models.CharField(max_length=64)),
                ("work", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="popularity_snapshots", to="catalogue.gamework")),
            ],
        ),
        migrations.AddConstraint(
            model_name="corpuspopularitysnapshot",
            constraint=models.UniqueConstraint(fields=("work", "corpus_version", "popularity_type_id"), name="catalogue_unique_popularity_snapshot"),
        ),
        migrations.AddIndex(
            model_name="corpuspopularitysnapshot",
            index=models.Index(fields=["corpus_version", "popularity_type_id"], name="catalogue_pop_ver_type_idx"),
        ),
    ]
