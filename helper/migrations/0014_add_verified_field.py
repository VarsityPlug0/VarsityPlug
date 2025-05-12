from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('helper', '0013_alter_documentupload_document_types_and_university'),
    ]

    operations = [
        migrations.AddField(
            model_name='DocumentUpload',
            name='verified',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='DocumentUpload',
            name='notes',
            field=models.TextField(blank=True, null=True),
        ),
    ] 