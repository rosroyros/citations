import time
import requests
import threading
import sqlite3
import subprocess
import sys
import os
import signal
from concurrent.futures import ThreadPoolExecutor
import random
import string

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from database import init_db, add_pass, get_daily_usage_for_current_window

# Configuration
NUM_USERS = 100
REQUESTS_PER_USER = 10
BASE_URL = "http://localhost:8001"  # Use different port to avoid conflict
DB_FILE = os.path.join(os.path.dirname(__file__), '..', 'credits.db')

def generate_token():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=16))

def setup_users():
    print("Setting up users...")
    init_db()
    users = []
    for i in range(NUM_USERS):
        token = generate_token()
        # Add pass: 1 day pass
        add_pass(token, 1, '1day', f'load_test_order_{token}')
        users.append(token)
    print(f"Created {len(users)} users with active passes.")
    return users

def run_user_load(token):
    success_count = 0
    errors = []
    
    headers = {
        "X-User-Token": token,
        "Content-Type": "application/json"
    }
    
    payload = {
        "citations": "Smith, J. (2020). Test citation.",
        "style": "apa7"
    }
    
    for _ in range(REQUESTS_PER_USER):
        try:
            # Add random sleep to scatter requests slightly
            # time.sleep(random.uniform(0.01, 0.1))
            
            response = requests.post(f"{BASE_URL}/api/validate", json=payload, headers=headers)
            if response.status_code == 200:
                success_count += 1
            else:
                errors.append(f"Status {response.status_code}: {response.text}")
        except Exception as e:
            errors.append(str(e))
            
    return success_count, errors

def main():
    # Set test database paths
    test_db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'load_test_credits.db'))
    test_validations_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'load_test_validations.db'))
    os.environ['TEST_DB_PATH'] = test_db_path
    os.environ['TEST_VALIDATIONS_DB_PATH'] = test_validations_path
    
    # Remove existing test DBs if they exist
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    if os.path.exists(test_validations_path):
        os.remove(test_validations_path)

    # 1. Setup Data
    users = setup_users()
    
    # 2. Start Server
    print("Starting server...")
    # Pass environment variables to subprocess
    env = os.environ.copy()
    
    # Open log file for server output
    server_log = open('server_load_test.log', 'w')
    
    # Using a different port 8001 for test
    server_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app:app", "--port", "8001", "--host", "127.0.0.1"],
        cwd=os.path.join(os.path.dirname(__file__), '..'),
        env=env,
        stdout=server_log,
        stderr=server_log
    )
    
    # Wait for server to be ready
    print("Waiting for server to be ready...")
    ready = False
    for _ in range(30):
        try:
            requests.get(f"{BASE_URL}/health")
            ready = True
            break
        except:
            time.sleep(1)
            
    if not ready:
        print("Server failed to start.")
        server_process.kill()
        sys.exit(1)
        
    print("Server is ready. Starting load test...")
    
    # 3. Run Load Test
    start_time = time.time()
    
    results = []
    with ThreadPoolExecutor(max_workers=100) as executor:
        futures = {executor.submit(run_user_load, token): token for token in users}
        for future in futures:
            results.append(future.result())
            
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\nLoad test completed in {duration:.2f} seconds.")
    
    # 4. Verify Results
    total_requests = NUM_USERS * REQUESTS_PER_USER
    total_success = sum(r[0] for r in results)
    
    print(f"Total Requests: {total_requests}")
    print(f"Total Success: {total_success}")
    
    if total_success != total_requests:
        print("❌ Some requests failed!")
        for i, (success, errors) in enumerate(results):
            if success != REQUESTS_PER_USER:
                print(f"User {i} failed: {success}/{REQUESTS_PER_USER} success. Errors: {errors}")
    else:
        print("✅ All API requests succeeded.")
        
    # 5. Verify Database
    print("\nVerifying database usage counts...")
    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()
    
    # Check daily_usage
    # We assume each request counts as 1 citation (based on "Smith, J. (2020). Test citation.")
    # Actually app.py counts citations. "Smith, J. (2020). Test citation." might be 1.
    # Let's verify what the app counts it as.
    # Usually split by newlines. One line = 1 citation.
    
    mismatch_count = 0
    for token in users:
        # We can't use get_daily_usage_for_current_window directly because it imports from backend which might be using a different DB path if not careful?
        # But we set DB_PATH in setup.
        # Let's query DB directly.
        # Get next midnight from DB (reset_timestamp)
        # Or just check if ANY row matches expectations
        
        cursor.execute("SELECT citations_count FROM daily_usage WHERE token = ?", (token,))
        row = cursor.fetchone()
        
        expected = REQUESTS_PER_USER # 1 citation per request
        actual = row[0] if row else 0
        
        if actual != expected:
            print(f"❌ User {token} usage mismatch: Expected {expected}, Got {actual}")
            mismatch_count += 1
            
    if mismatch_count == 0:
        print("✅ All database usage counts match expected values.")
    else:
        print(f"❌ {mismatch_count} users had incorrect usage counts.")
        
    conn.close()
    
    # 6. Cleanup
    server_process.terminate()
    try:
        server_process.wait(timeout=5)
    except:
        server_process.kill()

    if mismatch_count == 0 and total_success == total_requests:
        print("\n✅ Load Test PASSED")
        sys.exit(0)
    else:
        print("\n❌ Load Test FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()
