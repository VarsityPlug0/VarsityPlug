from django.core.management.base import BaseCommand
from helper.models import University
import logging

logger = logging.getLogger('helper')

class Command(BaseCommand):
    help = 'Populates the University table with sample data for testing'

    def handle(self, *args, **kwargs):
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
        ]

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

        self.stdout.write(self.style.SUCCESS(f'Successfully created {created_count} universities.'))
        if created_count == 0:
            self.stdout.write(self.style.WARNING('No new universities were created (all may already exist).'))