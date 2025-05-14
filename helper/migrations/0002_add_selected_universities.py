from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('helper', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentprofile',
            name='selected_universities',
            field=models.JSONField(blank=True, default=list),
        ),
    ] 