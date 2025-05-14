from django.core.management.base import BaseCommand
from helper.models import University
from django.core.exceptions import ObjectDoesNotExist

class Command(BaseCommand):
    help = 'Check universities in the database'

    def handle(self, *args, **options):
        self.stdout.write("=== Checking Universities in Database ===")
        
        # Check specific university (ID 8)
        uni_id_to_check = 8
        try:
            uni = University.objects.get(id=uni_id_to_check)
            self.stdout.write(self.style.SUCCESS(f'Found University ID {uni_id_to_check}: {uni.name}'))
        except ObjectDoesNotExist:
            self.stdout.write(self.style.ERROR(f'University with ID {uni_id_to_check} does NOT exist.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'An unexpected error occurred: {str(e)}'))
        
        # List all universities
        self.stdout.write("\n=== All Universities in Database ===")
        all_unis = University.objects.all().values('id', 'name')
        if all_unis:
            for uni_data in all_unis:
                self.stdout.write(f"ID: {uni_data['id']}, Name: {uni_data['name']}")
        else:
            self.stdout.write(self.style.WARNING("No universities found in the database.")) 