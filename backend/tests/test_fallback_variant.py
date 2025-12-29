
import os
import sys
from pathlib import Path
import random

# Ensure backend is in path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

# Set MOCK_LLM to avoid API key errors
os.environ['MOCK_LLM'] = 'true'

from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_fallback_variant_assignment():
    """Test that missing or invalid variants are reassigned to one of the 4 valid variants."""
    valid_variants = ["1.1", "1.2", "2.1", "2.2"]
    
    # Test 1: Missing header
    print("Test 1: Calling /api/validate/async without header...")
    response = client.post(
        "/api/validate/async",
        json={"citations": "Test citation", "style": "apa7"}
    )
    assert response.status_code == 200
    data = response.json()
    assigned_variant = data.get("experiment_variant")
    print(f"Assigned variant (missing header): {assigned_variant}")
    
    if assigned_variant not in valid_variants:
        print(f"FAILED: Variant {assigned_variant} is not in valid list {valid_variants}")
        sys.exit(1)
        
    # Test 2: Invalid header (old variant "1")
    print("Test 2: Calling /api/validate/async with invalid header '1'...")
    response = client.post(
        "/api/validate/async",
        headers={"X-Experiment-Variant": "1"},
        json={"citations": "Test citation", "style": "apa7"}
    )
    assert response.status_code == 200
    data = response.json()
    assigned_variant = data.get("experiment_variant")
    print(f"Assigned variant (header='1'): {assigned_variant}")
    
    if assigned_variant == "1":
        print("FAILED: Variant was not reassigned from '1'")
        sys.exit(1)
    if assigned_variant not in valid_variants:
        print(f"FAILED: Variant {assigned_variant} is not in valid list {valid_variants}")
        sys.exit(1)

    # Test 3: Invalid header (old variant "2")
    print("Test 3: Calling /api/validate/async with invalid header '2'...")
    response = client.post(
        "/api/validate/async",
        headers={"X-Experiment-Variant": "2"},
        json={"citations": "Test citation", "style": "apa7"}
    )
    assert response.status_code == 200
    data = response.json()
    assigned_variant = data.get("experiment_variant")
    print(f"Assigned variant (header='2'): {assigned_variant}")
    
    if assigned_variant == "2":
        print("FAILED: Variant was not reassigned from '2'")
        sys.exit(1)
    if assigned_variant not in valid_variants:
        print(f"FAILED: Variant {assigned_variant} is not in valid list {valid_variants}")
        sys.exit(1)

    # Test 4: Valid header "1.1" (should be kept)
    print("Test 4: Calling /api/validate/async with valid header '1.1'...")
    response = client.post(
        "/api/validate/async",
        headers={"X-Experiment-Variant": "1.1"},
        json={"citations": "Test citation", "style": "apa7"}
    )
    assert response.status_code == 200
    data = response.json()
    assigned_variant = data.get("experiment_variant")
    print(f"Assigned variant (header='1.1'): {assigned_variant}")
    
    if assigned_variant != "1.1":
        print(f"FAILED: Valid variant '1.1' was changed to {assigned_variant}")
        sys.exit(1)


    print("SUCCESS: All fallback tests passed!")

if __name__ == "__main__":
    test_fallback_variant_assignment()

