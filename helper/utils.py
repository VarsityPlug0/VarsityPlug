from typing import List, Dict, Any, Tuple

def calculate_application_fees(universities_data: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    """
    Calculate application fees for a list of universities.
    
    Args:
        universities_data: List of dictionaries containing university data with 'university' and 'application_fee' keys
        
    Returns:
        Tuple containing:
        - List of dictionaries with payment breakdown
        - Total university fee amount
    """
    payment_breakdown = []
    total_university_fee = 0
    
    for uni_data in universities_data:
        fee = uni_data.get('application_fee', "0")
        university_name = uni_data['university'].name if hasattr(uni_data['university'], 'name') else uni_data['university']
        
        if fee == "FREE" or ("free" in fee.lower()):
            payment_breakdown.append({
                'university': university_name,
                'university_fee': 0,
                'late_fee': None,
                'has_late_fee': False,
                'is_free': True,
                'fee_label': fee
            })
            continue
        if fee == "Not specified" or "manual" in fee.lower():
            continue
        try:
            # Handle fees with multiple values (e.g., "R220 (on-time), R440 (late)")
            if "on-time" in fee.lower():
                # Extract both on-time and late fees
                fee_parts = fee.split(",")
                on_time_fee = fee_parts[0].strip()
                late_fee = fee_parts[1].strip() if len(fee_parts) > 1 else None
                
                # Extract numeric values
                on_time_amount = int(''.join(filter(str.isdigit, on_time_fee)))
                late_amount = int(''.join(filter(str.isdigit, late_fee))) if late_fee else None
                
                payment_breakdown.append({
                    'university': university_name,
                    'university_fee': on_time_amount,
                    'late_fee': late_amount,
                    'has_late_fee': late_amount is not None,
                    'is_free': False,
                    'fee_label': fee
                })
                total_university_fee += on_time_amount
            else:
                # Handle simple fees (e.g., "R100")
                fee_amount = int(''.join(filter(str.isdigit, fee)))
                payment_breakdown.append({
                    'university': university_name,
                    'university_fee': fee_amount,
                    'late_fee': None,
                    'has_late_fee': False,
                    'is_free': False,
                    'fee_label': fee
                })
                total_university_fee += fee_amount
        except ValueError:
            continue
    
    return payment_breakdown, total_university_fee 