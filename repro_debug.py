
import re

log_line = "2025-12-05 09:09:06 - citation_validator - INFO - app.py:791 - Async validation request - user_type=free, paid_user_id=N/A, free_user_id=b1382d93-5654-4e76-87b8-93b65a8dc185, style=apa7"

print(f"Log line: {log_line}")

def debug_extract(line):
    print(f"\nChecking 'Validation request' in line: {'Validation request' in line}")
    
    user_type_match = re.search(r'user_type=(\w+)', line)
    print(f"user_type_match: {user_type_match.group(1) if user_type_match else 'No match'}")
    
    if not user_type_match:
        return "Early exit on user_type"

    paid_match = re.search(r'paid_user_id=([^,]+)', line)
    print(f"paid_match raw: {paid_match.group(1) if paid_match else 'No match'}")
    
    paid_user_id = None
    if paid_match:
        paid_value = paid_match.group(1).strip()
        print(f"paid_value stripped: '{paid_value}'")
        if paid_value != 'N/A':
            paid_user_id = paid_value
        else:
            print("paid_value is N/A")
    
    free_match = re.search(r'free_user_id=([^,]+)', line)
    print(f"free_match raw: {free_match.group(1) if free_match else 'No match'}")
    
    free_user_id = None
    if free_match:
        free_value = free_match.group(1).strip()
        print(f"free_value stripped: '{free_value}'")
        if free_value != 'N/A':
            free_user_id = free_value
        else:
            print("free_value is N/A")
            
    return paid_user_id, free_user_id

print(f"\nResult: {debug_extract(log_line)}")
