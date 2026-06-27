"""Phase 4 FastAPI Validation Script"""
import sys
import os
import json
from fastapi.testclient import TestClient

# Setup path
workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_dir = os.path.join(workspace_root, "project", "backend")
sys.path.insert(0, backend_dir)

from main import app

print("=" * 60)
print("PHASE 4 BACKEND ROUTE VALIDATION")
print("=" * 60)

client = TestClient(app)
passed = 0
errors = []

# 1. Test Root
try:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Intelligent Next Best Action Platform API"}
    passed += 1
    print("[PASS] GET / - Root endpoint works")
except Exception as e:
    errors.append(f"GET / failed: {e}")
    print(f"[FAIL] GET /: {e}")

# 2. Test POST /upload_transcript
session_id = None
try:
    payload = {
        "customer_id": "C001",
        "transcript_text": "Customer mentions SAP integration sync issue and low adoption."
    }
    response = client.post("/upload_transcript", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    session_id = data["session_id"]
    passed += 1
    print(f"[PASS] POST /upload_transcript -> session_id: {session_id}")
except Exception as e:
    errors.append(f"POST /upload_transcript failed: {e}")
    print(f"[FAIL] POST /upload_transcript: {e}")

# 3. Test GET /recommendation/{session_id} (Valid Session)
if session_id:
    try:
        response = client.get(f"/recommendation/{session_id}")
        assert response.status_code == 200
        data = response.json()
        
        # Verify merged mock agent schema keys
        expected_keys = [
            "customer_summary", "knowledge", "sentiment", 
            "risks", "opportunities", "recommendations", "explanations"
        ]
        for key in expected_keys:
            assert key in data, f"Missing key '{key}' in response"
            
        passed += 1
        print("[PASS] GET /recommendation/{session_id} -> Successful response with all expected keys")
    except Exception as e:
        errors.append(f"GET /recommendation/{session_id} failed: {e}")
        print(f"[FAIL] GET /recommendation/{session_id}: {e}")

# 4. Test GET /recommendation/{session_id} (Invalid Session - 404)
try:
    invalid_session = "invalid-uuid-string"
    response = client.get(f"/recommendation/{invalid_session}")
    assert response.status_code == 404
    data = response.json()
    assert data == {"error": "Session not found"}
    passed += 1
    print("[PASS] GET /recommendation/{invalid_session} -> Returns HTTP 404 Session not found")
except Exception as e:
    errors.append(f"GET /recommendation/invalid failed: {e}")
    print(f"[FAIL] GET /recommendation/invalid: {e}")

# 5. Test POST /approve
if session_id:
    try:
        payload = {
            "session_id": session_id,
            "recommendation_id": "REC001"
        }
        response = client.post("/approve", json=payload)
        assert response.status_code == 200
        assert response.json() == {"status": "approved"}
        passed += 1
        print("[PASS] POST /approve -> Successful approval response")
    except Exception as e:
        errors.append(f"POST /approve failed: {e}")
        print(f"[FAIL] POST /approve: {e}")

# 6. Test POST /approve (Invalid Session - 404)
try:
    payload = {
        "session_id": "invalid-session-id",
        "recommendation_id": "REC001"
    }
    response = client.post("/approve", json=payload)
    assert response.status_code == 404
    assert response.json() == {"error": "Session not found"}
    passed += 1
    print("[PASS] POST /approve (invalid) -> Returns HTTP 404 Session not found")
except Exception as e:
    errors.append(f"POST /approve (invalid) failed: {e}")
    print(f"[FAIL] POST /approve (invalid): {e}")

# 7. Test GET /history/{customer_id}
try:
    response = client.get("/history/C001")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "action" in data[0]
    assert "priority" in data[0]
    passed += 1
    print(f"[PASS] GET /history/C001 -> Mock history retrieved ({len(data)} records)")
except Exception as e:
    errors.append(f"GET /history/C001 failed: {e}")
    print(f"[FAIL] GET /history/C001: {e}")

# Summary
print("\n" + "-" * 60)
print(f"RESULTS: {passed} passed | {len(errors)} errors")
if errors:
    for e in errors:
        print(f"  ERROR: {e}")
else:
    print("\nALL BACKEND API ROUTES VALIDATED SUCCESSFULLY")
    print("Phase 4 Completed Successfully")
print("-" * 60)
