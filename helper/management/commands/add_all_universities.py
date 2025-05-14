from django.core.management.base import BaseCommand
from helper.models import University
from datetime import date

class Command(BaseCommand):
    help = 'Add all South African universities to the database'

    def handle(self, *args, **kwargs):
        universities = [
            {
                'name': 'University of Cape Town (UCT)',
                'minimum_aps': 40,
                'province': 'Western Cape',
                'description': 'A leading research university in South Africa, known for its academic excellence and beautiful campus.',
                'application_fee': 'R100',
                'due_date': date(2025, 7, 31)
            },
            {
                'name': 'University of the Witwatersrand (Wits)',
                'minimum_aps': 38,
                'province': 'Gauteng',
                'description': 'A leading research university in Johannesburg, known for its strong focus on research and innovation.',
                'application_fee': 'R200',
                'due_date': date(2025, 9, 30)
            },
            {
                'name': 'Stellenbosch University (SU)',
                'minimum_aps': 35,
                'province': 'Western Cape',
                'description': 'A prestigious university in the scenic winelands, offering a wide range of programs.',
                'application_fee': 'R100',
                'due_date': date(2025, 8, 31)
            },
            {
                'name': 'University of Pretoria (UP)',
                'minimum_aps': 32,
                'province': 'Gauteng',
                'description': 'One of South Africa\'s largest universities, offering diverse academic programs and vibrant student life.',
                'application_fee': 'R300',
                'due_date': date(2025, 6, 30)
            },
            {
                'name': 'University of Johannesburg (UJ)',
                'minimum_aps': 30,
                'province': 'Gauteng',
                'description': 'A vibrant, multicultural university offering a wide range of undergraduate and postgraduate programs.',
                'application_fee': 'FREE (online), R200 (manual)',
                'due_date': date(2025, 10, 31)
            },
            {
                'name': 'University of KwaZulu-Natal (UKZN)',
                'minimum_aps': 30,
                'province': 'KwaZulu-Natal',
                'description': 'A leading university in KwaZulu-Natal, known for its research excellence and diverse student body.',
                'application_fee': 'R250',
                'due_date': date(2025, 9, 30)
            },
            {
                'name': 'University of the Western Cape (UWC)',
                'minimum_aps': 30,
                'province': 'Western Cape',
                'description': 'A public university committed to excellence in teaching, learning, and research.',
                'application_fee': 'R100',
                'due_date': date(2025, 9, 30)
            },
            {
                'name': 'Rhodes University (RU)',
                'minimum_aps': 35,
                'province': 'Eastern Cape',
                'description': 'A small, research-intensive university known for its strong academic reputation.',
                'application_fee': 'R100',
                'due_date': date(2025, 9, 30)
            },
            {
                'name': 'University of the Free State (UFS)',
                'minimum_aps': 30,
                'province': 'Free State',
                'description': 'A leading university in the Free State, offering a wide range of academic programs.',
                'application_fee': 'R300',
                'due_date': date(2025, 9, 30)
            },
            {
                'name': 'North-West University (NWU)',
                'minimum_aps': 30,
                'province': 'North West',
                'description': 'A multi-campus university offering diverse programs across various fields.',
                'application_fee': 'R250',
                'due_date': date(2025, 8, 31)
            },
            {
                'name': 'University of Limpopo (UL)',
                'minimum_aps': 28,
                'province': 'Limpopo',
                'description': 'A comprehensive university serving the Limpopo province and beyond.',
                'application_fee': 'R200',
                'due_date': date(2025, 9, 30)
            },
            {
                'name': 'University of Fort Hare (UFH)',
                'minimum_aps': 28,
                'province': 'Eastern Cape',
                'description': 'A historically significant university with a rich academic tradition.',
                'application_fee': 'R150',
                'due_date': date(2025, 9, 30)
            },
            {
                'name': 'University of Venda (Univen)',
                'minimum_aps': 28,
                'province': 'Limpopo',
                'description': 'A comprehensive university serving the Vhembe region.',
                'application_fee': 'R200',
                'due_date': date(2025, 9, 30)
            },
            {
                'name': 'University of Zululand (UniZulu)',
                'minimum_aps': 28,
                'province': 'KwaZulu-Natal',
                'description': 'A comprehensive university serving the Zululand region.',
                'application_fee': 'R200',
                'due_date': date(2025, 9, 30)
            },
            {
                'name': 'Walter Sisulu University (WSU)',
                'minimum_aps': 28,
                'province': 'Eastern Cape',
                'description': 'A comprehensive university serving the Eastern Cape region.',
                'application_fee': 'R200',
                'due_date': date(2025, 9, 30)
            },
            {
                'name': 'University of Mpumalanga (UMP)',
                'minimum_aps': 28,
                'province': 'Mpumalanga',
                'description': 'A young, dynamic university serving the Mpumalanga province.',
                'application_fee': 'R200',
                'due_date': date(2025, 9, 30)
            },
            {
                'name': 'Sol Plaatje University (SPU)',
                'minimum_aps': 28,
                'province': 'Northern Cape',
                'description': 'A young university serving the Northern Cape province.',
                'application_fee': 'R200',
                'due_date': date(2025, 9, 30)
            },
            {
                'name': 'Sefako Makgatho Health Sciences University (SMU)',
                'minimum_aps': 30,
                'province': 'Gauteng',
                'description': 'A specialized health sciences university.',
                'application_fee': 'R200',
                'due_date': date(2025, 9, 30)
            },
            {
                'name': 'Cape Peninsula University of Technology (CPUT)',
                'minimum_aps': 28,
                'province': 'Western Cape',
                'description': 'A university of technology offering career-focused education.',
                'application_fee': 'R150',
                'due_date': date(2025, 9, 30)
            },
            {
                'name': 'Central University of Technology (CUT)',
                'minimum_aps': 28,
                'province': 'Free State',
                'description': 'A university of technology serving the central region.',
                'application_fee': 'R150',
                'due_date': date(2025, 9, 30)
            },
            {
                'name': 'Durban University of Technology (DUT)',
                'minimum_aps': 28,
                'province': 'KwaZulu-Natal',
                'description': 'A university of technology serving the Durban region.',
                'application_fee': 'R150',
                'due_date': date(2025, 9, 30)
            },
            {
                'name': 'Mangosuthu University of Technology (MUT)',
                'minimum_aps': 28,
                'province': 'KwaZulu-Natal',
                'description': 'A university of technology serving the Umlazi region.',
                'application_fee': 'R150',
                'due_date': date(2025, 9, 30)
            },
            {
                'name': 'Tshwane University of Technology (TUT)',
                'minimum_aps': 28,
                'province': 'Gauteng',
                'description': 'A university of technology serving the Tshwane region.',
                'application_fee': 'R150',
                'due_date': date(2025, 9, 30)
            },
            {
                'name': 'Vaal University of Technology (VUT)',
                'minimum_aps': 28,
                'province': 'Gauteng',
                'description': 'A university of technology serving the Vaal region.',
                'application_fee': 'R150',
                'due_date': date(2025, 9, 30)
            },
            {
                'name': 'University of South Africa (UNISA)',
                'minimum_aps': 28,
                'province': 'Gauteng',
                'description': 'South Africa\'s largest distance learning institution.',
                'application_fee': 'R115',
                'due_date': date(2025, 9, 30)
            }
        ]

        # Clear existing universities
        University.objects.all().delete()
        self.stdout.write('Cleared existing universities.')

        # Add new universities
        for uni_data in universities:
            University.objects.create(**uni_data)
            self.stdout.write(self.style.SUCCESS(f'Successfully added {uni_data["name"]}'))

        self.stdout.write(self.style.SUCCESS('Successfully added all South African universities')) 