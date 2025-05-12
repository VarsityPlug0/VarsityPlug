from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('helper', '0013_alter_documentupload_document_types_and_university'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentprofile',
            name='subscription_date',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='studentprofile',
            name='last_chat_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='studentprofile',
            name='whatsapp_enabled',
            field=models.BooleanField(default=False),
        ),
    ] 