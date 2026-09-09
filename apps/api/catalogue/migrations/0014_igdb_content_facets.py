# Additive IGDB classification facets: themes, player perspectives, game
# modes, and free-form keywords. New lookup tables plus their many-to-many
# join tables only -- catalogue_gamework itself is not altered, so this is
# safe to apply while the recommendation workers are reading the catalogue.
# These facets are import-only: not folded into the content checksum, the
# governed corpus, or any recommender feature cache.

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalogue", "0013_corpusratingsnapshot_total_rating_count"),
    ]

    operations = [
        migrations.CreateModel(
            name="Theme",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("igdb_id", models.PositiveIntegerField(unique=True)),
                ("name", models.CharField(max_length=120)),
                ("slug", models.SlugField(max_length=120, unique=True)),
            ],
            options={"ordering": ("name",)},
        ),
        migrations.CreateModel(
            name="PlayerPerspective",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("igdb_id", models.PositiveIntegerField(unique=True)),
                ("name", models.CharField(max_length=120)),
                ("slug", models.SlugField(max_length=120, unique=True)),
            ],
            options={"ordering": ("name",)},
        ),
        migrations.CreateModel(
            name="GameMode",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("igdb_id", models.PositiveIntegerField(unique=True)),
                ("name", models.CharField(max_length=120)),
                ("slug", models.SlugField(max_length=120, unique=True)),
            ],
            options={"ordering": ("name",)},
        ),
        migrations.CreateModel(
            name="Keyword",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("igdb_id", models.PositiveIntegerField(unique=True)),
                ("name", models.CharField(max_length=200)),
                ("slug", models.SlugField(max_length=200, unique=True)),
            ],
            options={"ordering": ("name",)},
        ),
        migrations.AddField(
            model_name="gamework",
            name="themes",
            field=models.ManyToManyField(blank=True, related_name="works", to="catalogue.theme"),
        ),
        migrations.AddField(
            model_name="gamework",
            name="player_perspectives",
            field=models.ManyToManyField(blank=True, related_name="works", to="catalogue.playerperspective"),
        ),
        migrations.AddField(
            model_name="gamework",
            name="game_modes",
            field=models.ManyToManyField(blank=True, related_name="works", to="catalogue.gamemode"),
        ),
        migrations.AddField(
            model_name="gamework",
            name="keywords",
            field=models.ManyToManyField(blank=True, related_name="works", to="catalogue.keyword"),
        ),
    ]
