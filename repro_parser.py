
import sys
import os
import logging
from datetime import datetime

# Add current directory to path so we can import dashboard modules
sys.path.append('/opt/citations')

from dashboard.log_parser import parse_job_events, extract_timestamp, extract_user_ids
import re

# Mock log lines exactly as they appear in app.log
log_line = "2025-12-05 09:09:06 - citation_validator - INFO - app.py:791 - Async validation request - user_type=free, paid_user_id=N/A, free_user_id=b1382d93-5654-4e76-87b8-93b65a8dc185, style=apa7"

print(f"Testing line: {log_line}")

# Debug extract_user_ids internals
print("\nDebugging Regex:")
user_type_match = re.search(r'user_type=(\w+)', log_line)
print(f"user_type_match: {user_type_match.group(1) if user_type_match else 'None'}")

paid_match = re.search(r'paid_user_id=([^,]+)', log_line)
print(f"paid_match: {paid_match.group(1) if paid_match else 'None'}")

free_match = re.search(r'free_user_id=([^,]+)', log_line)
print(f"free_match: {free_match.group(1) if free_match else 'None'}")

print(f"\nOriginal function result: {extract_user_ids(log_line)}")
