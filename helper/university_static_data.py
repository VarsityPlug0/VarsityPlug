# helper/university_static_data.py

# IMPORTANT:
# IDs must be unique integers.
# Due dates should ideally be in 'YYYY-MM-DD' format for consistency if parsing is needed later,
# but can be strings like "Contact University" or "Varies".
# Application fees can also be strings like "R100", "Free", or "Check Website".

UNIVERSITIES = [
    {
        "id": 1,
        "name": "University of Cape Town (UCT)",
        "minimum_aps": 40,
        "province": "Western Cape",
        "application_fee": "R100",
        "due_date": "2025-07-31",
        "description": "A leading research university in South Africa, known for its academic excellence and beautiful campus."
    },
    {
        "id": 2,
        "name": "University of the Witwatersrand (Wits)",
        "minimum_aps": 38,
        "province": "Gauteng",
        "application_fee": "R200",
        "due_date": "2025-09-30",
        "description": "A leading research university in Johannesburg, known for its strong focus on research and innovation."
    },
    {
        "id": 3,
        "name": "Stellenbosch University (SU)",
        "minimum_aps": 35,
        "province": "Western Cape",
        "application_fee": "R100",
        "due_date": "2025-08-31",
        "description": "A prestigious university in the scenic winelands, offering a wide range of programs."
    },
    {
        "id": 4,
        "name": "University of Pretoria (UP)",
        "minimum_aps": 32,
        "province": "Gauteng",
        "application_fee": "R300",
        "due_date": "2025-06-30",
        "description": "One of South Africa's largest universities, offering diverse academic programs and vibrant student life."
    },
    {
        "id": 5,
        "name": "University of Johannesburg (UJ)",
        "minimum_aps": 30,
        "province": "Gauteng",
        "application_fee": "FREE (online), R200 (manual)",
        "due_date": "2025-10-31",
        "description": "A vibrant, multicultural university offering a wide range of undergraduate and postgraduate programs."
    },
    {
        "id": 6,
        "name": "University of KwaZulu-Natal (UKZN)",
        "minimum_aps": 30,
        "province": "KwaZulu-Natal",
        "application_fee": "R250",
        "due_date": "2025-09-30",
        "description": "A leading university in KwaZulu-Natal, known for its research excellence and diverse student body."
    },
    {
        "id": 7,
        "name": "University of the Western Cape (UWC)",
        "minimum_aps": 30,
        "province": "Western Cape",
        "application_fee": "R100",
        "due_date": "2025-09-30",
        "description": "A public university committed to excellence in teaching, learning, and research."
    },
    {
        "id": 8,
        "name": "Rhodes University (RU)",
        "minimum_aps": 35,
        "province": "Eastern Cape",
        "application_fee": "R100",
        "due_date": "2025-09-30",
        "description": "A small, research-intensive university known for its strong academic reputation."
    },
    {
        "id": 9,
        "name": "University of the Free State (UFS)",
        "minimum_aps": 30,
        "province": "Free State",
        "application_fee": "R300",
        "due_date": "2025-09-30",
        "description": "A leading university in the Free State, offering a wide range of academic programs."
    },
    {
        "id": 10,
        "name": "North-West University (NWU)",
        "minimum_aps": 30,
        "province": "North West",
        "application_fee": "R250",
        "due_date": "2025-08-31",
        "description": "A multi-campus university offering diverse programs across various fields."
    },
    {
        "id": 11,
        "name": "University of Limpopo (UL)",
        "minimum_aps": 28,
        "province": "Limpopo",
        "application_fee": "R200",
        "due_date": "2025-09-30",
        "description": "A comprehensive university serving the Limpopo province and beyond."
    },
    {
        "id": 12,
        "name": "University of Fort Hare (UFH)",
        "minimum_aps": 28,
        "province": "Eastern Cape",
        "application_fee": "R150",
        "due_date": "2025-09-30",
        "description": "A historically significant university with a rich academic tradition."
    },
    {
        "id": 13,
        "name": "University of Venda (Univen)",
        "minimum_aps": 28,
        "province": "Limpopo",
        "application_fee": "R200",
        "due_date": "2025-09-30",
        "description": "A comprehensive university serving the Vhembe region."
    },
    {
        "id": 14,
        "name": "University of Zululand (UniZulu)",
        "minimum_aps": 28,
        "province": "KwaZulu-Natal",
        "application_fee": "R200",
        "due_date": "2025-09-30",
        "description": "A comprehensive university serving the Zululand region."
    },
    {
        "id": 15,
        "name": "Walter Sisulu University (WSU)",
        "minimum_aps": 28,
        "province": "Eastern Cape",
        "application_fee": "R200",
        "due_date": "2025-09-30",
        "description": "A comprehensive university serving the Eastern Cape region."
    },
    {
        "id": 16,
        "name": "University of Mpumalanga (UMP)",
        "minimum_aps": 28,
        "province": "Mpumalanga",
        "application_fee": "R200",
        "due_date": "2025-09-30",
        "description": "A young, dynamic university serving the Mpumalanga province."
    },
    {
        "id": 17,
        "name": "Sol Plaatje University (SPU)",
        "minimum_aps": 28,
        "province": "Northern Cape",
        "application_fee": "R200",
        "due_date": "2025-09-30",
        "description": "A young university serving the Northern Cape province."
    },
    {
        "id": 18,
        "name": "Sefako Makgatho Health Sciences University (SMU)",
        "minimum_aps": 30,
        "province": "Gauteng",
        "application_fee": "R200",
        "due_date": "2025-09-30",
        "description": "A specialized health sciences university."
    },
    {
        "id": 19,
        "name": "Cape Peninsula University of Technology (CPUT)",
        "minimum_aps": 28,
        "province": "Western Cape",
        "application_fee": "R150",
        "due_date": "2025-09-30",
        "description": "A university of technology offering career-focused education."
    },
    {
        "id": 20,
        "name": "Central University of Technology (CUT)",
        "minimum_aps": 28,
        "province": "Free State",
        "application_fee": "R150",
        "due_date": "2025-09-30",
        "description": "A university of technology serving the central region."
    },
    {
        "id": 21,
        "name": "Durban University of Technology (DUT)",
        "minimum_aps": 28,
        "province": "KwaZulu-Natal",
        "application_fee": "R150",
        "due_date": "2025-09-30",
        "description": "A university of technology serving the Durban region."
    },
    {
        "id": 22,
        "name": "Mangosuthu University of Technology (MUT)",
        "minimum_aps": 28,
        "province": "KwaZulu-Natal",
        "application_fee": "R150",
        "due_date": "2025-09-30",
        "description": "A university of technology serving the Umlazi region."
    },
    {
        "id": 23,
        "name": "Tshwane University of Technology (TUT)",
        "minimum_aps": 28,
        "province": "Gauteng",
        "application_fee": "R150",
        "due_date": "2025-09-30",
        "description": "A university of technology serving the Tshwane region."
    },
    {
        "id": 24,
        "name": "Vaal University of Technology (VUT)",
        "minimum_aps": 28,
        "province": "Gauteng",
        "application_fee": "R150",
        "due_date": "2025-09-30",
        "description": "A university of technology serving the Vaal region."
    },
    {
        "id": 25,
        "name": "University of South Africa (UNISA)",
        "minimum_aps": 28,
        "province": "Gauteng",
        "application_fee": "R115",
        "due_date": "2025-09-30",
        "description": "South Africa's largest distance learning institution."
    }
]

def get_all_universities():
    """Returns the list of all universities."""
    return UNIVERSITIES

def get_university_by_id(university_id):
    """Returns a single university dictionary by its ID, or None if not found."""
    try:
        university_id = int(university_id)
    except ValueError:
        return None
    for uni in UNIVERSITIES:
        if uni['id'] == university_id:
            return uni
    return None 