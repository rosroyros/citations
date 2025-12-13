import requests
import time
import subprocess
import os
import signal
import sys
import json

# Configuration
BACKEND_PORT = 8002
BASE_URL = f"http://localhost:{BACKEND_PORT}"
BACKEND_CMD = ["venv/bin/python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", str(BACKEND_PORT)]
LOG_FILE = "backend_test.log"

def start_backend():
    print(f"Starting backend on port {BACKEND_PORT}...")
    env = os.environ.copy()
    env["MOCK_LLM"] = "true" # Enable Mock Mode for testing
    # Ensure necessary env vars are set if not present
    if "POLAR_ACCESS_TOKEN" not in env:
        # Use a dummy token if not set, hoping it doesn't crash on startup
        # app.py warns but doesn't crash on optional vars, but POLAR_ACCESS_TOKEN is used in Polar init.
        # However, checking app.py: polar = Polar(access_token=os.getenv('POLAR_ACCESS_TOKEN'))
        # If it's None, it might work until we use it.
        pass
        
    # Redirect stdout/stderr to file to check logs later
    with open(LOG_FILE, "w") as log:
        process = subprocess.Popen(
            BACKEND_CMD,
            cwd="backend",
            stdout=log,
            stderr=log,
            env=env
        )
    time.sleep(5)  # Wait for startup
    return process

def test_create_checkout():
    print("\n--- Testing /api/create-checkout ---")
    url = f"{BASE_URL}/api/create-checkout"
    payload = {
        "token": "test_user_token",
        "productId": "817c70f8-6cd1-4bdc-aa80-dd0a43e69a5e", # 100 Credits
        "variantId": "1"
    }
    
    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("SUCCESS: Checkout created.")
        else:
            print("FAILURE: Checkout creation failed.")
            
    except Exception as e:
        print(f"EXCEPTION: {e}")

def test_validate_variant_logging():
    print("\n--- Testing /api/validate/async Variant Logging ---")
    url = f"{BASE_URL}/api/validate/async"
    
    # Test 1: With Header
    headers = {
        "X-User-Token": "test_user_token",
        "X-Experiment-Variant": "1"
    }
    payload = {
        "citations": "Smith, J. (2020). Test citation.",
        "style": "apa7"
    }
    
    print("Sending request WITH X-Experiment-Variant: 1")
    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"EXCEPTION: {e}")

    # Test 2: Without Header
    print("\nSending request WITHOUT X-Experiment-Variant")
    try:
        response = requests.post(url, json=payload, headers={"X-User-Token": "test_user_token"})
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"EXCEPTION: {e}")

def main():
    backend_proc = start_backend()
    
    try:
        # Check if backend is up
        try:
            requests.get(f"{BASE_URL}/health", timeout=2)
            print("Backend is up.")
        except:
            print("Backend failed to start or is not reachable.")
            # Print logs
            with open(LOG_FILE, "r") as f:
                print(f.read())
            return

        test_create_checkout()
        test_validate_variant_logging()
        
    finally:
        print("\nStopping backend...")
        backend_proc.terminate()
        backend_proc.wait()
        
        print("\n--- Backend Logs ---")
        if os.path.exists(LOG_FILE):
             # Read the last 50 lines of log to see what happened
            with open(LOG_FILE, "r") as f:
                lines = f.readlines()
                for line in lines[-50:]:
                    print(line.strip())

if __name__ == "__main__":
    main()
