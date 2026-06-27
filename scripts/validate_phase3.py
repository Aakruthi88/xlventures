"""Phase 3 Validation Script"""
import sys
import os
import json

workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_dir = os.path.join(workspace_root, "project", "backend")
sys.path.insert(0, backend_dir)

print("=" * 60)
print("PHASE 3 VALIDATION")
print("=" * 60)

errors = []
passed = 0

# 1. Check all files exist
files = [
    "main.py", "requirements.txt",
    "agents/__init__.py", "agents/planner.py",
    "agents/customer_agent.py", "agents/knowledge_agent.py",
    "agents/sentiment_agent.py", "agents/risk_agent.py",
    "agents/opportunity_agent.py", "agents/recommendation_agent.py",
    "agents/explanation_agent.py", "agents/memory_agent.py",
    "rag/loader.py", "rag/retriever.py", "database/sqlite.db",
]
print("\n--- File Structure ---")
for f in files:
    path = os.path.join(backend_dir, f)
    if os.path.exists(path):
        passed += 1
        print(f"[PASS] {f}")
    else:
        errors.append(f"{f} not found")
        print(f"[FAIL] {f}")

# 2. Test agent imports and functions
print("\n--- Agent Imports & Function Calls ---")

from agents import customer_agent
r = customer_agent.get_summary("C001")
assert isinstance(r, dict) and "customer_id" in r
passed += 1
keys_preview = list(r.keys())[:4]
print(f"[PASS] customer_agent.get_summary() -> {keys_preview}...")

from agents import knowledge_agent
r = knowledge_agent.retrieve("test transcript")
assert isinstance(r, dict) and "retrieved_docs" in r
num_docs = len(r["retrieved_docs"])
passed += 1
print(f"[PASS] knowledge_agent.retrieve() -> {num_docs} docs")

from agents import sentiment_agent
r = sentiment_agent.analyze("test transcript")
assert isinstance(r, dict) and "sentiment" in r
passed += 1
print(f"[PASS] sentiment_agent.analyze() -> sentiment={r['sentiment']}")

from agents import risk_agent
r = risk_agent.assess({}, {}, {})
assert isinstance(r, dict) and "risks" in r
num_risks = len(r["risks"])
passed += 1
print(f"[PASS] risk_agent.assess() -> {num_risks} risks, overall={r['overall_risk']}")

from agents import opportunity_agent
r = opportunity_agent.find({}, {})
assert isinstance(r, dict) and "opportunities" in r
num_opps = len(r["opportunities"])
passed += 1
print(f"[PASS] opportunity_agent.find() -> {num_opps} opportunities")

from agents import recommendation_agent
r = recommendation_agent.generate({}, {}, {}, {}, {})
assert isinstance(r, dict) and "recommendations" in r
num_recs = len(r["recommendations"])
passed += 1
print(f"[PASS] recommendation_agent.generate() -> {num_recs} recommendations")

from agents import explanation_agent
r = explanation_agent.explain({})
assert isinstance(r, dict) and "explanations" in r
num_exp = len(r["explanations"])
passed += 1
print(f"[PASS] explanation_agent.explain() -> {num_exp} explanations")

from agents import memory_agent
memory_agent.store_approval("sess1", "C001", {})
r = memory_agent.get_history("C001")
assert isinstance(r, list)
passed += 1
print(f"[PASS] memory_agent.get_history() -> {len(r)} records")

r = memory_agent.get_similar_past_approvals("C001")
assert isinstance(r, list)
passed += 1
print(f"[PASS] memory_agent.get_similar_past_approvals() -> {len(r)} records")

# 3. Test planner orchestration
print("\n--- Planner Orchestration ---")
from agents import planner
planner.sessions["test-session"] = {"customer_id": "C001", "transcript_text": "test"}
result = planner.run("test-session")
expected_keys = ["customer_summary", "knowledge", "sentiment", "risks",
                 "opportunities", "recommendations", "explanations"]
for k in expected_keys:
    assert k in result, f"Missing key: {k}"
passed += 1
print(f"[PASS] planner.run() -> keys: {list(result.keys())}")

# 4. Test RAG stubs
print("\n--- RAG Stubs ---")
from rag import loader, retriever
loader.load_knowledge_base("test/")
passed += 1
print("[PASS] rag.loader.load_knowledge_base() - placeholder")

r = retriever.retrieve("test query")
assert isinstance(r, list)
passed += 1
print(f"[PASS] rag.retriever.retrieve() -> {len(r)} results")

# 5. JSON serialization test
print("\n--- JSON Serialization ---")
json_str = json.dumps(result, indent=2)
assert len(json_str) > 100
passed += 1
print(f"[PASS] Full planner output serializes to valid JSON ({len(json_str)} chars)")

# Summary
print("\n" + "-" * 60)
print(f"RESULTS: {passed} passed | {len(errors)} errors")
if errors:
    for e in errors:
        print(f"  ERROR: {e}")
else:
    print("\nALL VALIDATIONS PASSED")
    print("Phase 3 - Project Structure completed successfully")
print("-" * 60)
