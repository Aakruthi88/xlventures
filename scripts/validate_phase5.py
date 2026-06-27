"""Phase 5 Validation - LangGraph Planner Agent Test"""
import sys
import os
import json

workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_dir = os.path.join(workspace_root, "project", "backend")
sys.path.insert(0, backend_dir)

print("=" * 60)
print("PHASE 5 VALIDATION - LANGGRAPH PLANNER AGENT")
print("=" * 60)

passed = 0
errors = []

# TEST 1: Import LangGraph
print("\n--- Test 1: LangGraph Import ---")
try:
    from langgraph.graph import StateGraph, END
    passed += 1
    print("[PASS] LangGraph imported successfully")
except ImportError as e:
    errors.append(f"LangGraph import failed: {e}")
    print(f"[FAIL] LangGraph import: {e}")

# TEST 2: Import new planner files
print("\n--- Test 2: New File Imports ---")
try:
    from agents.llm import check_ollama_available, query_llm, query_llm_json
    passed += 1
    print("[PASS] agents/llm.py imported")
except Exception as e:
    errors.append(f"llm.py import failed: {e}")
    print(f"[FAIL] llm.py: {e}")

try:
    from agents.planner_state import AgentState
    passed += 1
    print("[PASS] agents/planner_state.py imported")
except Exception as e:
    errors.append(f"planner_state.py import failed: {e}")
    print(f"[FAIL] planner_state.py: {e}")

try:
    from agents.planner_router import route_agents, route_with_rules
    passed += 1
    print("[PASS] agents/planner_router.py imported")
except Exception as e:
    errors.append(f"planner_router.py import failed: {e}")
    print(f"[FAIL] planner_router.py: {e}")

# TEST 3: Rule-based routing
print("\n--- Test 3: Rule-Based Routing ---")
try:
    test_transcript = (
        "ABC Manufacturing has low analytics adoption. "
        "Renewal is in 20 days. "
        "SAP integration is slow. "
        "Management is considering competitors."
    )
    result = route_with_rules(test_transcript)
    agents = result["agents"]
    reasoning = result["reasoning"]

    print(f"  Transcript: '{test_transcript[:60]}...'")
    print(f"  Selected agents: {agents}")
    print(f"  Reasoning: {reasoning}")

    # Verify expected agents are selected
    assert "customer_agent" in agents, "customer_agent should always be selected"
    assert "risk_agent" in agents, "risk_agent should be selected (renewal, competitors)"
    assert "knowledge_agent" in agents, "knowledge_agent should be selected (SAP, integration)"
    assert "opportunity_agent" in agents, "opportunity_agent should be selected (adoption, analytics)"
    passed += 1
    print("[PASS] Rule-based routing selected correct agents")
except Exception as e:
    errors.append(f"Rule-based routing failed: {e}")
    print(f"[FAIL] Rule-based routing: {e}")

# TEST 4: Ollama availability check (informational, not a failure)
print("\n--- Test 4: Ollama Availability ---")
try:
    ollama_ok = check_ollama_available()
    if ollama_ok:
        print("[INFO] Ollama IS available - LLM routing will be used")
    else:
        print("[INFO] Ollama NOT available - rule-based fallback will be used")
    passed += 1
    print("[PASS] Ollama check completed without crash")
except Exception as e:
    errors.append(f"Ollama check crashed: {e}")
    print(f"[FAIL] Ollama check: {e}")

# TEST 5: LangGraph planner compilation and execution
print("\n--- Test 5: LangGraph Planner Execution ---")
try:
    from agents import planner

    # Check that LangGraph is being used
    if planner.LANGGRAPH_AVAILABLE:
        print("[INFO] Planner is using LangGraph workflow")
    else:
        print("[INFO] Planner is using sequential fallback")

    # Set up test session
    planner.sessions["phase5-test"] = {
        "customer_id": "C001",
        "transcript_text": test_transcript
    }

    result = planner.run("phase5-test")

    # Verify all 7 keys present
    expected_keys = [
        "customer_summary", "knowledge", "sentiment",
        "risks", "opportunities", "recommendations", "explanations"
    ]
    for key in expected_keys:
        assert key in result, f"Missing key: {key}"

    passed += 1
    print(f"[PASS] Planner returned all 7 keys: {list(result.keys())}")
except Exception as e:
    errors.append(f"LangGraph planner execution failed: {e}")
    print(f"[FAIL] Planner execution: {e}")

# TEST 6: Business flow validation
print("\n--- Test 6: Business Flow Validation ---")
try:
    # Check Risk
    risks = result.get("risks", {}).get("risks", [])
    has_renewal_risk = any(r.get("type") == "Renewal Risk" for r in risks)
    assert has_renewal_risk, "Expected 'Renewal Risk' in risks"
    print("[PASS] Renewal Risk detected")

    # Check Opportunity
    opps = result.get("opportunities", {}).get("opportunities", [])
    has_training = any("Analytics" in o.get("item", "") for o in opps)
    assert has_training, "Expected Analytics training opportunity"
    print("[PASS] Analytics training opportunity found")

    # Check Recommendation
    recs = result.get("recommendations", {}).get("recommendations", [])
    has_training_rec = any("training" in r.get("action", "").lower() for r in recs)
    assert has_training_rec, "Expected training recommendation"
    print("[PASS] Training recommendation generated")

    # Check Explanation
    exps = result.get("explanations", {}).get("explanations", [])
    has_evidence = any(
        any("42" in str(ev) for ev in e.get("evidence", []))
        for e in exps
    )
    assert has_evidence, "Expected evidence mentioning health score 42"
    print("[PASS] Explanation evidence includes health score 42")

    passed += 1
    print("[PASS] Full business flow validated")
except Exception as e:
    errors.append(f"Business flow validation failed: {e}")
    print(f"[FAIL] Business flow: {e}")

# TEST 7: Live API test
print("\n--- Test 7: Live API Server Test ---")
import subprocess
import time
import requests

process = None
try:
    process = subprocess.Popen(
        ["uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=backend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    time.sleep(4)

    # Upload transcript
    payload = {
        "customer_id": "C001",
        "transcript_text": test_transcript
    }
    r = requests.post("http://127.0.0.1:8000/upload_transcript", json=payload)
    assert r.status_code == 200
    session_id = r.json()["session_id"]
    print(f"[PASS] POST /upload_transcript -> session_id: {session_id[:16]}...")

    # Get recommendation
    r = requests.get(f"http://127.0.0.1:8000/recommendation/{session_id}")
    assert r.status_code == 200
    data = r.json()
    assert "customer_summary" in data
    assert "recommendations" in data
    print(f"[PASS] GET /recommendation -> {list(data.keys())}")

    passed += 1
    print("[PASS] Live API endpoints work with LangGraph planner")

except Exception as e:
    errors.append(f"Live API test failed: {e}")
    print(f"[FAIL] Live API: {e}")
finally:
    if process:
        process.terminate()
        process.wait()

# FINAL REPORT
print("\n" + "=" * 60)
print(f"RESULTS: {passed} passed | {len(errors)} errors")
if errors:
    for e in errors:
        print(f"  ERROR: {e}")
    print("\nPHASE 5 COMPLETED WITH ERRORS")
else:
    print("\nALL PHASE 5 VALIDATIONS PASSED")
    print("LangGraph Planner Agent is operational")
print("=" * 60)
