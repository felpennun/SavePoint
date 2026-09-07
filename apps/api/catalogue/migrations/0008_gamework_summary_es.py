from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("catalogue", "0007_igdb_rating_fields")]

    operations = [
        migrations.AddField(
            model_name="gamework",
            name="summary_es",
            field=models.TextField(blank=True),
        ),
    ]
