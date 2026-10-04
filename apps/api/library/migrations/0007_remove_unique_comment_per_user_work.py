from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0006_phase6_public_list_slug'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='gamecomment',
            name='library_unique_comment_per_user_work',
        ),
    ]
