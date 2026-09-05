"""CAT-02 (Plan 01.1-03): denormalised filter/sort scalars + supporting
indexes.

``GameWork.first_release_date`` / ``GameWork.total_rating`` let the catalogue
year-range and rating filters/sorts run as a single indexed btree scan rather
than a GROUP BY over every ``GameRelease`` row (threat T-01.1-06). The data
migration backfills ``first_release_date`` from the releases already present so
the year filter works against the existing corpus immediately; ``total_rating``
has no prior source and stays null until the next IGDB import pass.
"""

from __future__ import annotations

from django.db import migrations, models
from django.db.models import Min, OuterRef, Subquery


def backfill_first_release_date(apps, schema_editor):
    GameWork = apps.get_model("catalogue", "GameWork")
    GameRelease = apps.get_model("catalogue", "GameRelease")
    earliest = (
        GameRelease.objects.filter(work=OuterRef("pk"), release_date__isnull=False)
        .values("work")
        .annotate(m=Min("release_date"))
        .values("m")[:1]
    )
    GameWork.objects.update(first_release_date=Subquery(earliest))


def noop_reverse(apps, schema_editor):
    # The column is dropped by the reverse of AddField; nothing to undo here.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("catalogue", "0003_genre_igdb_import"),
    ]

    operations = [
        migrations.AddField(
            model_name="gamework",
            name="first_release_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="gamework",
            name="total_rating",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddIndex(
            model_name="gamework",
            index=models.Index(fields=["original_title"], name="catalogue_work_title_idx"),
        ),
        migrations.AddIndex(
            model_name="gamework",
            index=models.Index(fields=["first_release_date"], name="catalogue_work_release_idx"),
        ),
        migrations.AddIndex(
            model_name="gamework",
            index=models.Index(fields=["total_rating"], name="catalogue_work_rating_idx"),
        ),
        migrations.AddIndex(
            model_name="gamerelease",
            index=models.Index(fields=["release_date"], name="catalogue_release_date_idx"),
        ),
        migrations.RunPython(backfill_first_release_date, noop_reverse),
    ]
