from helper.models import University
from django.core.exceptions import ObjectDoesNotExist

def check_universities():
    print("=== Checking Universities in Database ===")
    
    # Check specific university (ID 8)
    uni_id_to_check = 8
    try:
        uni = University.objects.get(id=uni_id_to_check)
        print(f'\nSUCCESS: Found University ID {uni_id_to_check}: {uni.name}')
    except ObjectDoesNotExist:
        print(f'\nERROR: University with ID {uni_id_to_check} does NOT exist.')
    except Exception as e:
        print(f'\nAn unexpected error occurred: {str(e)}')
    
    # List all universities
    print("\n=== All Universities in Database ===")
    all_unis = University.objects.all().values('id', 'name')
    if all_unis:
        for uni_data in all_unis:
            print(f"ID: {uni_data['id']}, Name: {uni_data['name']}")
    else:
        print("No universities found in the database.")

if __name__ == "__main__":
    check_universities() 