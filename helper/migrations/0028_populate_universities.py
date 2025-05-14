from django.db import migrations

def populate_universities(apps, schema_editor):
    University = apps.get_model('helper', 'University')
    
    universities = [
        {'name': 'University of Cape Town (UCT)', 'minimum_aps': 35, 'province': 'Western Cape', 'description': 'A leading research university in South Africa'},
        {'name': 'University of the Witwatersrand (Wits)', 'minimum_aps': 35, 'province': 'Gauteng', 'description': 'A leading research university in Johannesburg'},
        {'name': 'Stellenbosch University (SU)', 'minimum_aps': 33, 'province': 'Western Cape', 'description': 'A leading research university in Stellenbosch'},
        {'name': 'University of Johannesburg (UJ)', 'minimum_aps': 30, 'province': 'Gauteng', 'description': 'A comprehensive university in Johannesburg'},
        {'name': 'University of the Free State (UFS)', 'minimum_aps': 30, 'province': 'Free State', 'description': 'A leading university in Bloemfontein'},
        {'name': 'University of the Western Cape (UWC)', 'minimum_aps': 30, 'province': 'Western Cape', 'description': 'A leading university in Bellville'},
        {'name': 'Nelson Mandela University (NMU)', 'minimum_aps': 30, 'province': 'Eastern Cape', 'description': 'A comprehensive university in Port Elizabeth'},
        {'name': 'University of Fort Hare (UFH)', 'minimum_aps': 30, 'province': 'Eastern Cape', 'description': 'A historic university in Alice'},
        {'name': 'University of Venda (Univen)', 'minimum_aps': 30, 'province': 'Limpopo', 'description': 'A comprehensive university in Thohoyandou'},
        {'name': 'University of Zululand (UniZulu)', 'minimum_aps': 30, 'province': 'KwaZulu-Natal', 'description': 'A comprehensive university in KwaDlangezwa'},
        {'name': 'Walter Sisulu University (WSU)', 'minimum_aps': 30, 'province': 'Eastern Cape', 'description': 'A comprehensive university in Mthatha'},
        {'name': 'Sol Plaatje University (SPU)', 'minimum_aps': 30, 'province': 'Northern Cape', 'description': 'A new university in Kimberley'},
        {'name': 'Sefako Makgatho Health Sciences University (SMU)', 'minimum_aps': 30, 'province': 'Gauteng', 'description': 'A health sciences university in Pretoria'},
        {'name': 'Rhodes University (RU)', 'minimum_aps': 30, 'province': 'Eastern Cape', 'description': 'A historic university in Grahamstown'},
        {'name': 'North-West University (NWU)', 'minimum_aps': 30, 'province': 'North West', 'description': 'A comprehensive university with multiple campuses'},
        {'name': 'Cape Peninsula University of Technology (CPUT)', 'minimum_aps': 30, 'province': 'Western Cape', 'description': 'A university of technology in Cape Town'},
        {'name': 'Central University of Technology (CUT)', 'minimum_aps': 30, 'province': 'Free State', 'description': 'A university of technology in Bloemfontein'},
        {'name': 'Durban University of Technology (DUT)', 'minimum_aps': 30, 'province': 'KwaZulu-Natal', 'description': 'A university of technology in Durban'},
        {'name': 'Mangosuthu University of Technology (MUT)', 'minimum_aps': 30, 'province': 'KwaZulu-Natal', 'description': 'A university of technology in Umlazi'},
        {'name': 'Tshwane University of Technology (TUT)', 'minimum_aps': 30, 'province': 'Gauteng', 'description': 'A university of technology in Pretoria'},
        {'name': 'Vaal University of Technology (VUT)', 'minimum_aps': 30, 'province': 'Gauteng', 'description': 'A university of technology in Vanderbijlpark'},
    ]
    
    for uni_data in universities:
        University.objects.get_or_create(
            name=uni_data['name'],
            defaults={
                'minimum_aps': uni_data['minimum_aps'],
                'province': uni_data['province'],
                'description': uni_data['description']
            }
        )

def reverse_populate_universities(apps, schema_editor):
    University = apps.get_model('helper', 'University')
    University.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ('helper', '0027_remove_studentprofile_subscription_status'),
    ]

    operations = [
        migrations.RunPython(populate_universities, reverse_populate_universities),
    ] 