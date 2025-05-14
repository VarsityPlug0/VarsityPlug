from django.db import migrations, models

def convert_selected_universities_to_json(apps, schema_editor):
    StudentProfile = apps.get_model('helper', 'StudentProfile')
    for profile in StudentProfile.objects.all():
        if hasattr(profile, 'selected_universities'):
            # Convert the ManyToMany relationship to a list of IDs
            university_ids = list(profile.selected_universities.values_list('id', flat=True))
            profile.selected_universities = university_ids
            profile.save()

class Migration(migrations.Migration):

    dependencies = [
        ('helper', '0030_alter_applicationstatus_unique_together_and_more'),
    ]

    operations = [
        # First, remove the old field
        migrations.RemoveField(
            model_name='studentprofile',
            name='selected_universities',
        ),
        # Then add the new JSONField
        migrations.AddField(
            model_name='studentprofile',
            name='selected_universities',
            field=models.JSONField(default=list, blank=True),
        ),
        # Run the data migration
        migrations.RunPython(
            convert_selected_universities_to_json,
            reverse_code=migrations.RunPython.noop
        ),
    ] 