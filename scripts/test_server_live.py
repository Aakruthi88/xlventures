"""Live Server API Integration Test Script"""
import subprocess
import time
import requests
import sys

print("=" * 60)
print("LIVE BACKEND API SERVER TEST")
print("=" * 60)

# Start uvicorn server in a subprocess
process = None
try:
    print("Starting uvicorn server on http://localhost:8000...")
    process = subprocess.Popen(
        ["uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=r"c:\Users\HP\Desktop\Aakruthi\xlventures\project\backend",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for server to start
    time.sleep(3)
    
    # Run tests using requests
    base_url = "http://127.0.0.1:8000"
    
    # Test 1: Root
    print("Testing GET / ...")
    r = requests.get(f"{base_url}/")
    print(f"Status: {r.status_code}, Body: {r.json()}")
    assert r.status_code == 200
    
    # Test 2: Upload transcript
    print("\nTesting POST /upload_transcript ...")
    payload = {
        "customer_id": "C001",
        "transcript_text": "Live server integration test discussion."
    }
    r = requests.post(f"{base_url}/upload_transcript", json=payload)
    print(f"Status: {r.status_code}, Body: {r.json()}")
    assert r.status_code == 200
    session_id = r.json()["session_id"]
    
    # Test 3: Get recommendation
    print(f"\nTesting GET /recommendation/{session_id} ...")
    r = requests.get(f"{base_url}/recommendation/{session_id}")
    print(f"Status: {r.status_code}")
    assert r.status_code == 200
    keys = list(r.json().keys())
    print(f"Keys returned: {keys}")
    
    # Test 4: Get recommendation (invalid)
    print("\nTesting GET /recommendation/invalid-id ...")
    r = requests.get(f"{base_url}/recommendation/invalid-id")
    print(f"Status: {r.status_code}, Body: {r.json()}")
    assert r.status_code == 404
    
    # Test 5: Approve
    print("\nTesting POST /approve ...")
    payload = {
        "session_id": session_id,
        "recommendation_id": "REC001"
    }
    r = requests.post(f"{base_url}/approve", json=payload)
    print(f"Status: {r.status_code}, Body: {r.json()}")
    assert r.status_code == 200
    
    # Test 6: Approve (invalid)
    print("\nTesting POST /approve (invalid) ...")
    payload = {
        "session_id": "invalid-id",
        "recommendation_id": "REC001"
    }
    r = requests.post(f"{base_url}/approve", json=payload)
    print(f"Status: {r.status_code}, Body: {r.json()}")
    assert r.status_code == 404
    
    # Test 7: History
    print("\nTesting GET /history/C001 ...")
    r = requests.get(f"{base_url}/history/C001")
    print(f"Status: {r.status_code}, Records count: {len(r.json())}")
    assert r.status_code == 200
    
    print("\n" + "=" * 60)
    print("ALL ROUTE INTEGRATION TESTS PASSED")
    print("=" * 60)
    sys.exit(0)

except Exception as e:
    print(f"\n❌ TEST FAILED: {e}")
    sys.exit(1)

finally:
    if process:
        print("\nShutting down uvicorn server...")
        process.terminate()
        process.wait()
        print("Server shutdown completed.")
