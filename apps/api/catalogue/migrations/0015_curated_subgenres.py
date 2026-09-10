# Create the curated subgenre layer without changing the raw IGDB keyword
# tables. Rebuilding this derived layer is safe and reproducible.

import uuid

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("catalogue", "0014_igdb_content_facets"),
    ]

    operations = [
        migrations.CreateModel(
            name="Subgenre",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=200)),
                ("slug", models.SlugField(max_length=200, unique=True)),
                ("curation_version", models.CharField(max_length=64)),
            ],
            options={"ordering": ("name",)},
        ),
        migrations.CreateModel(
            name="SubgenreKeyword",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "keyword",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="catalogue.keyword",
                    ),
                ),
                (
                    "subgenre",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="catalogue.subgenre",
                    ),
                ),
            ],
            options={
                "constraints": [
                    models.UniqueConstraint(
                        fields=("subgenre", "keyword"),
                        name="catalogue_unique_subgenre_keyword",
                    )
                ],
            },
        ),
        migrations.AddField(
            model_name="subgenre",
            name="source_keywords",
            field=models.ManyToManyField(
                related_name="subgenres",
                through="catalogue.SubgenreKeyword",
                to="catalogue.keyword",
            ),
        ),
        migrations.AddField(
            model_name="gamework",
            name="subgenres",
            field=models.ManyToManyField(
                blank=True,
                related_name="works",
                to="catalogue.subgenre",
            ),
        ),
    ]
