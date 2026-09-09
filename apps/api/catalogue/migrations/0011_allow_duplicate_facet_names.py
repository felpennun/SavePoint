# IGDB stable IDs, not provider display names, identify facets.

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalogue", "0010_corpuspopularitysnapshot_normalised_value"),
    ]

    operations = [
        migrations.AlterField(
            model_name="developer",
            name="name",
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name="franchise",
            name="name",
            field=models.CharField(max_length=200),
        ),
    ]
