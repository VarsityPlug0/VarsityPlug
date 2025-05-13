from django.core.management.base import BaseCommand
from helper.models import University
from datetime import date

class Command(BaseCommand):
    help = 'Add universities to the database'

    def handle(self, *args, **kwargs):
        universities = [
            {
                'name': 'University of Cape Town (UCT)',
                'minimum_aps': 40,
                'province': 'Western Cape',
                'description': 'A leading research university in South Africa.',
                'application_fee': 'R100',
                'due_date': date(2025, 7, 31)
            },
            {
                'name': 'University of the Witwatersrand (Wits)',
                'minimum_aps': 38,
                'province': 'Gauteng',
                'description': 'A leading research university in Johannesburg.',
                'application_fee': 'R100',
                'due_date': date(2025, 9, 30)
            },
            {
                'name': 'Stellenbosch University (SU)',
                'minimum_aps': 35,
                'province': 'Western Cape',
                'description': 'A leading research university in Stellenbosch.',
                'application_fee': 'R100',
                'due_date': date(2025, 7, 31)
            },
            {
                'name': 'University of Pretoria (UP)',
                'minimum_aps': 32,
                'province': 'Gauteng',
                'description': 'A leading research university in Pretoria.',
                'application_fee': 'R300',
                'due_date': date(2025, 6, 30)
            },
            {
                'name': 'University of Johannesburg (UJ)',
                'minimum_aps': 30,
                'province': 'Gauteng',
                'description': 'A leading university in Johannesburg.',
                'application_fee': 'FREE (online), R200 (manual)',
                'due_date': date(2025, 10, 31)
            },
            {
                'name': 'University of KwaZulu-Natal (UKZN)',
                'minimum_aps': 30,
                'province': 'KwaZulu-Natal',
                'description': 'A leading university in KwaZulu-Natal.',
                'application_fee': 'R210 (on-time), R420 (late)',
                'due_date': date(2025, 6, 30)
            },
            {
                'name': 'University of the Free State (UFS)',
                'minimum_aps': 30,
                'province': 'Free State',
                'description': 'A leading university in Bloemfontein.',
                'application_fee': 'R100',
                'due_date': date(2025, 9, 30)
            },
            {
                'name': 'University of the Western Cape (UWC)',
                'minimum_aps': 30,
                'province': 'Western Cape',
                'description': 'A leading university in Bellville.',
                'application_fee': 'FREE',
                'due_date': date(2025, 9, 30)
            },
            {
                'name': 'Nelson Mandela University (NMU)',
                'minimum_aps': 30,
                'province': 'Eastern Cape',
                'description': 'A leading university in Port Elizabeth.',
                'application_fee': 'FREE',
                'due_date': date(2025, 9, 30)
            },
            {
                'name': 'University of Limpopo (UL)',
                'minimum_aps': 28,
                'province': 'Limpopo',
                'description': 'A leading university in Limpopo.',
                'application_fee': 'R200',
                'due_date': date(2025, 9, 30)
            },
            {
                'name': 'University of Fort Hare (UFH)',
                'minimum_aps': 28,
                'province': 'Eastern Cape',
                'description': 'A leading university in Alice.',
                'application_fee': 'FREE',
                'due_date': date(2025, 9, 30)
            },
            {
                'name': 'University of Venda (Univen)',
                'minimum_aps': 28,
                'province': 'Limpopo',
                'description': 'A leading university in Thohoyandou.',
                'application_fee': 'R100',
                'due_date': date(2025, 9, 27)
            },
            {
                'name': 'University of Zululand (UniZulu)',
                'minimum_aps': 28,
                'province': 'KwaZulu-Natal',
                'description': 'A leading university in KwaDlangezwa.',
                'application_fee': 'R220 (on-time), R440 (late)',
                'due_date': date(2025, 10, 31)
            },
            {
                'name': 'Walter Sisulu University (WSU)',
                'minimum_aps': 28,
                'province': 'Eastern Cape',
                'description': 'A leading university in Mthatha.',
                'application_fee': 'FREE',
                'due_date': date(2025, 10, 31)
            },
            {
                'name': 'University of Mpumalanga (UMP)',
                'minimum_aps': 28,
                'province': 'Mpumalanga',
                'description': 'A leading university in Mbombela.',
                'application_fee': 'R150',
                'due_date': date(2025, 1, 30)
            },
            {
                'name': 'Sol Plaatje University (SPU)',
                'minimum_aps': 28,
                'province': 'Northern Cape',
                'description': 'A leading university in Kimberley.',
                'application_fee': 'FREE',
                'due_date': date(2025, 10, 31)
            },
            {
                'name': 'Sefako Makgatho Health Sciences University (SMU)',
                'minimum_aps': 28,
                'province': 'Gauteng',
                'description': 'A leading health sciences university in Pretoria.',
                'application_fee': 'R200',
                'due_date': date(2025, 6, 28)
            },
            {
                'name': 'Rhodes University (RU)',
                'minimum_aps': 35,
                'province': 'Eastern Cape',
                'description': 'A leading university in Grahamstown.',
                'application_fee': 'R100',
                'due_date': date(2025, 9, 30)
            },
            {
                'name': 'North-West University (NWU)',
                'minimum_aps': 30,
                'province': 'North West',
                'description': 'A leading university in Potchefstroom.',
                'application_fee': 'FREE',
                'due_date': date(2025, 6, 30)
            },
            {
                'name': 'Cape Peninsula University of Technology (CPUT)',
                'minimum_aps': 28,
                'province': 'Western Cape',
                'description': 'A leading university of technology in Cape Town.',
                'application_fee': 'R100',
                'due_date': date(2025, 9, 30)
            },
            {
                'name': 'Central University of Technology (CUT)',
                'minimum_aps': 28,
                'province': 'Free State',
                'description': 'A leading university of technology in Bloemfontein.',
                'application_fee': 'FREE (online), R245 (manual via CAO)',
                'due_date': date(2025, 10, 31)
            },
            {
                'name': 'Durban University of Technology (DUT)',
                'minimum_aps': 28,
                'province': 'KwaZulu-Natal',
                'description': 'A leading university of technology in Durban.',
                'application_fee': 'R250 (on-time), R470 (late)',
                'due_date': date(2025, 9, 30)
            },
            {
                'name': 'Mangosuthu University of Technology (MUT)',
                'minimum_aps': 28,
                'province': 'KwaZulu-Natal',
                'description': 'A leading university of technology in Umlazi.',
                'application_fee': 'R250 (on-time), R470 (late)',
                'due_date': date(2025, 2, 28)
            },
            {
                'name': 'Tshwane University of Technology (TUT)',
                'minimum_aps': 28,
                'province': 'Gauteng',
                'description': 'A leading university of technology in Pretoria.',
                'application_fee': 'R240',
                'due_date': date(2025, 9, 30)
            },
            {
                'name': 'Vaal University of Technology (VUT)',
                'minimum_aps': 28,
                'province': 'Gauteng',
                'description': 'A leading university of technology in Vanderbijlpark.',
                'application_fee': 'R150',
                'due_date': date(2025, 9, 30)
            },
            {
                'name': 'University of South Africa (UNISA)',
                'minimum_aps': 28,
                'province': 'Gauteng',
                'description': 'A leading distance learning university in Pretoria.',
                'application_fee': 'R135',
                'due_date': date(2025, 10, 11)
            }
        ]

        for uni_data in universities:
            University.objects.get_or_create(
                name=uni_data['name'],
                defaults={
                    'minimum_aps': uni_data['minimum_aps'],
                    'province': uni_data['province'],
                    'description': uni_data['description'],
                    'application_fee': uni_data['application_fee'],
                    'due_date': uni_data['due_date']
                }
            )
            self.stdout.write(self.style.SUCCESS(f'Successfully added {uni_data["name"]}')) 