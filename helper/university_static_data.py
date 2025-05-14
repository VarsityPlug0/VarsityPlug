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
        "minimum_aps": 35,
        "province": "Western Cape",
        "application_fee": "R100",
        "due_date": "2024-09-30",
        "description": "A leading research university in Africa, known for its beautiful campus and academic excellence."
    },
    {
        "id": 2,
        "name": "University of the Witwatersrand (Wits)",
        "minimum_aps": 34,
        "province": "Gauteng",
        "application_fee": "R200",
        "due_date": "2024-09-30",
        "description": "Located in Johannesburg, Wits is a renowned institution with a strong focus on research and innovation."
    },
    {
        "id": 3,
        "name": "Stellenbosch University (Maties)",
        "minimum_aps": 32,
        "province": "Western Cape",
        "application_fee": "R100",
        "due_date": "2024-08-31",
        "description": "Situated in the scenic winelands, Stellenbosch University offers a wide range of programs."
    },
    {
        "id": 4,
        "name": "University of Pretoria (UP)",
        "minimum_aps": 30,
        "province": "Gauteng",
        "application_fee": "R300",
        "due_date": "2024-06-30",
        "description": "One of South Africa's largest universities, offering diverse academic programs and vibrant student life."
    },
    {
        "id": 5,
        "name": "Rhodes University",
        "minimum_aps": 28,
        "province": "Eastern Cape",
        "application_fee": "R100",
        "due_date": "2024-10-31",
        "description": "A historic university located in Makhanda (Grahamstown), known for its strong humanities and journalism programs."
    },
    {
        "id": 6,
        "name": "University of KwaZulu-Natal (UKZN)",
        "minimum_aps": 26,
        "province": "KwaZulu-Natal",
        "application_fee": "Varies",
        "due_date": "2024-09-30",
        "description": "A multi-campus university formed from the merger of two major institutions in KwaZulu-Natal."
    },
    {
        # This university should be shown for an APS of 42
        "id": 7,
        "name": "Example High APS University",
        "minimum_aps": 40,
        "province": "Gauteng",
        "application_fee": "R50",
        "due_date": "2024-11-30",
        "description": "A sample university that requires a high APS score."
    },
    {
        "id": 8,
        "name": "Nelson Mandela University (NMU)",
        "minimum_aps": 24,
        "province": "Eastern Cape",
        "application_fee": "Free",
        "due_date": "2024-08-02", # According to their website for 2025
        "description": "A comprehensive university with a focus on social justice and sustainable development."
    }
]

def get_all_universities():
    """Returns a list of all university dictionaries."""
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