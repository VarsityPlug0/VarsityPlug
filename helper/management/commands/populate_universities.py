from django.core.management.base import BaseCommand
from django.db import DatabaseError
from helper.models import University
import logging

logger = logging.getLogger('helper')

class Command(BaseCommand):
    help = 'Populates the University table with sample data for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing universities before populating',
        )

    def handle(self, *args, **kwargs):
        clear = kwargs.get('clear', False)

        universities = [
            {
                'name': 'University of Cape Town (UCT)',
                'minimum_aps': 40,
                'province': 'Western Cape',
                'description': 'A leading research university in South Africa.'
            },
            {
                'name': 'Cape Peninsula University of Technology (CPUT)',
                'minimum_aps': 30,
                'province': 'Western Cape',
                'description': 'Known for its technical and vocational programs.'
            },
            {
                'name': 'University of Johannesburg (UJ)',
                'minimum_aps': 35,
                'province': 'Gauteng',
                'description': 'A vibrant, multicultural university.'
            },
            {
                'name': 'Stellenbosch University',
                'minimum_aps': 38,
                'province': 'Western Cape',
                'description': 'Renowned for its academic excellence and scenic campus.'
            },
            {
                'name': 'Tshwane University of Technology (TUT)',
                'minimum_aps': 28,
                'province': 'Gauteng',
                'description': 'Focuses on technology and innovation.'
            },
            {
                'name': 'University of Pretoria (UP)',
                'minimum_aps': 36,
                'province': 'Gauteng',
                'description': 'A top-tier university with a strong research focus.'
            },
            {
                'name': 'Durban University of Technology (DUT)',
                'minimum_aps': 25,
                'province': 'KwaZulu-Natal',
                'description': 'Specializes in technology and applied sciences.'
            },
            {
                'name': 'University of KwaZulu-Natal (UKZN)',
                'minimum_aps': 32,
                'province': 'KwaZulu-Natal',
                'description': 'A comprehensive university with a global reputation.'
            },
        ]

        try:
            # Optionally clear existing universities
            if clear:
                deleted_count = University.objects.all().delete()[1].get('helper.University', 0)
                logger.info(f"Cleared {deleted_count} existing universities.")
                self.stdout.write(self.style.WARNING(f'Cleared {deleted_count} existing universities.'))

            created_count = 0
            for uni in universities:
                try:
                    # Check if university already exists to avoid duplicates
                    if not University.objects.filter(name=uni['name']).exists():
                        University.objects.create(
                            name=uni['name'],
                            minimum_aps=uni['minimum_aps'],
                            province=uni['province'],
                            description=uni['description']
                        )
                        created_count += 1
                        logger.info(f"Created university: {uni['name']} (APS: {uni['minimum_aps']})")
                    else:
                        logger.debug(f"University already exists: {uni['name']}")
                except Exception as e:
                    logger.error(f"Failed to create university {uni['name']}: {str(e)}")
                    self.stdout.write(self.style.ERROR(f"Failed to create {uni['name']}: {str(e)}"))

            if created_count > 0:
                self.stdout.write(self.style.SUCCESS(f'Successfully created {created_count} universities.'))
            else:
                self.stdout.write(self.style.WARNING('No new universities were created (all may already exist).'))

            # Log the current state of the University table for debugging
            total_count = University.objects.count()
            logger.info(f"Total universities in database: {total_count}")
            self.stdout.write(f"Total universities in database: {total_count}")

        except DatabaseError as e:
            logger.error(f"Database error while populating universities: {str(e)}")
            self.stdout.write(self.style.ERROR(f"Database error: {str(e)}"))
            raise