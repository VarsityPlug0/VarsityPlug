from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('helper', '0012_alter_studentprofile_stored_aps_score'),
    ]

    operations = [
        migrations.AlterField(
            model_name='DocumentUpload',
            name='document_type',
            field=models.CharField(
                choices=[
                    ('id_document', 'ID Document'),
                    ('grade_11_results', 'Grade 11 Results'),
                    ('grade_12_results', 'Grade 12 Results'),
                    ('proof_of_residence', 'Proof of Residence'),
                    ('payment_proof', 'Proof of Payment'),
                ],
                max_length=50,
                verbose_name='Document Type',
            ),
        ),
        migrations.AddField(
            model_name='DocumentUpload',
            name='university',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='document_uploads',
                to='helper.university',
                verbose_name='Associated University',
            ),
        ),
    ]