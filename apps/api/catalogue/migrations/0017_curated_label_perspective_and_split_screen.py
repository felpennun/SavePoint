# Add player-perspective evidence and the Split Screen editorial label.

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalogue", "0016_curated_labels"),
    ]

    operations = [
        migrations.AlterField(
            model_name="gameworkcuratedlabel",
            name="source_kind",
            field=models.CharField(
                choices=[
                    ("genre", "Genre"),
                    ("theme", "Theme"),
                    ("game_mode", "Game mode"),
                    ("player_perspective", "Player perspective"),
                    ("keyword", "Keyword"),
                    ("subgenre", "Subgenre"),
                ],
                max_length=24,
            ),
        ),
    ]
