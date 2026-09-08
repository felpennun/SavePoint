from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalogue", "0009_recommender_content_facets_and_popularity"),
    ]

    operations = [
        migrations.AddField(
            model_name="corpuspopularitysnapshot",
            name="normalised_value",
            field=models.FloatField(blank=True, null=True),
        ),
    ]
