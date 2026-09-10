# Add the unified, typed editorial label layer without changing raw IGDB facets.

import uuid

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("catalogue", "0015_curated_subgenres"),
    ]

    operations = [
        migrations.CreateModel(
            name="CuratedLabel",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=120, unique=True)),
                ("slug", models.SlugField(max_length=120, unique=True)),
                (
                    "kind",
                    models.CharField(
                        choices=[
                            ("genre", "Genre"),
                            ("subgenre", "Subgenre"),
                            ("theme", "Theme"),
                            ("mode", "Mode"),
                            ("feature", "Feature"),
                        ],
                        max_length=16,
                    ),
                ),
                ("curation_version", models.CharField(max_length=64)),
            ],
            options={"ordering": ("name",)},
        ),
        migrations.CreateModel(
            name="GameWorkCuratedLabel",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "source_kind",
                    models.CharField(
                        choices=[
                            ("genre", "Genre"),
                            ("theme", "Theme"),
                            ("game_mode", "Game mode"),
                            ("keyword", "Keyword"),
                            ("subgenre", "Subgenre"),
                        ],
                        max_length=16,
                    ),
                ),
                ("source_value", models.CharField(max_length=200)),
                (
                    "label",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="catalogue.curatedlabel",
                    ),
                ),
                (
                    "work",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="catalogue.gamework",
                    ),
                ),
            ],
            options={
                "constraints": [
                    models.UniqueConstraint(
                        fields=("work", "label", "source_kind", "source_value"),
                        name="catalogue_unique_curated_label_evidence",
                    )
                ],
                "indexes": [
                    models.Index(
                        fields=("label", "work"),
                        name="cat_cur_label_work_idx",
                    )
                ],
            },
        ),
        migrations.AddField(
            model_name="gamework",
            name="curated_labels",
            field=models.ManyToManyField(
                blank=True,
                related_name="works",
                through="catalogue.GameWorkCuratedLabel",
                to="catalogue.curatedlabel",
            ),
        ),
    ]
