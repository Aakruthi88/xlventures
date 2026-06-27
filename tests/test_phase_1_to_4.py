"""Phase 1 to 4 End-to-End System Test"""
import os
import sys
import json
import time
import subprocess
import pandas as pd
import requests

# Setup paths relative to this script
workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_dir = os.path.join(workspace_root, "data")
kb_dir = os.path.join(data_dir, "knowledge_base")
backend_dir = os.path.join(workspace_root, "project", "backend")

# Insert backend dir to path for import tests
sys.path.insert(0, backend_dir)

print("=" * 60)
print("RUNNING END-TO-END VALIDATION (PHASES 1-4)")
print("=" * 60)

test_results = {
    "DATA": False,
    "AGENTS": False,
    "API": False,
    "FLOW": False
}

failures = []

def record_failure(stage, message):
    failures.append(f"[{stage}] {message}")

# =====================================================================
# TEST 1, 2, 3, 4: DATA VALIDATION
# =====================================================================
print("\n--- Running Data Validation ---")
data_ok = True

# Check files exist
required_files = [
    ("customers.csv", os.path.join(data_dir, "customers.csv")),
    ("usage.csv", os.path.join(data_dir, "usage.csv")),
    ("crm.json", os.path.join(data_dir, "crm.json")),
    ("support_tickets.csv", os.path.join(data_dir, "support_tickets.csv")),
    ("recommendation_history.json", os.path.join(data_dir, "recommendation_history.json"))
]

for name, path in required_files:
    if not os.path.exists(path):
        data_ok = False
        record_failure("DATA", f"File missing: {name} at {path}")

# Validate customers.csv
customers_path = os.path.join(data_dir, "customers.csv")
if os.path.exists(customers_path):
    try:
        df_cust = pd.read_csv(customers_path)
        required_cols = ["CustomerID", "Company", "Plan", "Industry", "RenewalDate", "HealthScore"]
        for col in required_cols:
            if col not in df_cust.columns:
                data_ok = False
                record_failure("DATA", f"customers.csv missing column: {col}")
        
        if len(df_cust) != 10:
            data_ok = False
            record_failure("DATA", f"customers.csv has {len(df_cust)} records, expected 10")
            
        abc = df_cust[df_cust["CustomerID"] == "C001"]
        if len(abc) == 0:
            data_ok = False
            record_failure("DATA", "C001 (ABC Manufacturing) not found in customers.csv")
        else:
            row = abc.iloc[0]
            if row["Company"] != "ABC Manufacturing":
                data_ok = False
                record_failure("DATA", f"C001 company name is '{row['Company']}', expected 'ABC Manufacturing'")
            if int(row["HealthScore"]) != 42:
                data_ok = False
                record_failure("DATA", f"C001 HealthScore is {row['HealthScore']}, expected 42")
    except Exception as e:
        data_ok = False
        record_failure("DATA", f"Error reading customers.csv: {e}")

# Validate usage.csv
usage_path = os.path.join(data_dir, "usage.csv")
if os.path.exists(usage_path):
    try:
        df_use = pd.read_csv(usage_path)
        use_cols = ["Company", "LicensedUsers", "ActiveUsers", "DashboardUsagePct", "APICalls"]
        for col in use_cols:
            if col not in df_use.columns:
                data_ok = False
                record_failure("DATA", f"usage.csv missing column: {col}")
                
        abc_use = df_use[df_use["Company"] == "ABC Manufacturing"]
        if len(abc_use) == 0:
            data_ok = False
            record_failure("DATA", "ABC Manufacturing not found in usage.csv")
        else:
            row = abc_use.iloc[0]
            if int(row["DashboardUsagePct"]) != 32:
                data_ok = False
                record_failure("DATA", f"ABC Manufacturing DashboardUsagePct is {row['DashboardUsagePct']}, expected 32")
    except Exception as e:
        data_ok = False
        record_failure("DATA", f"Error reading usage.csv: {e}")

# Validate crm.json
crm_path = os.path.join(data_dir, "crm.json")
if os.path.exists(crm_path):
    try:
        with open(crm_path, "r", encoding="utf-8") as f:
            crm_data = json.load(f)
        
        abc_crm = [item for item in crm_data if item.get("company") == "ABC Manufacturing"]
        if not abc_crm:
            data_ok = False
            record_failure("DATA", "ABC Manufacturing not found in crm.json")
        else:
            if abc_crm[0].get("support_tickets_open") != 7:
                data_ok = False
                record_failure("DATA", f"ABC open tickets in CRM is {abc_crm[0].get('support_tickets_open')}, expected 7")
    except Exception as e:
        data_ok = False
        record_failure("DATA", f"Error reading crm.json: {e}")

# Validate Knowledge Base
kb_files = [
    "onboarding_guide.md", "integration_guide.md",
    "renewal_playbook.md", "customer_success_sop.md", "faq_pricing.md"
]
for f_name in kb_files:
    f_path = os.path.join(kb_dir, f_name)
    if not os.path.exists(f_path):
        data_ok = False
        record_failure("DATA", f"KB file missing: {f_name}")
    else:
        with open(f_path, "r", encoding="utf-8") as f:
            content = f.read()
        if not content.strip():
            data_ok = False
            record_failure("DATA", f"KB file is empty: {f_name}")
            
        if f_name in ["renewal_playbook.md", "onboarding_guide.md"]:
            if "training" not in content.lower():
                data_ok = False
                record_failure("DATA", f"{f_name} does not contain the word 'training'")

test_results["DATA"] = data_ok
print(f"Data Validation: {'PASS' if data_ok else 'FAIL'}")

# =====================================================================
# TEST 5, 6: AGENT IMPORT & PLANNER TEST
# =====================================================================
print("\n--- Running Agent & Planner Validation ---")
agents_ok = True

try:
    # Test Imports
    from agents import customer_agent
    from agents import knowledge_agent
    from agents import sentiment_agent
    from agents import risk_agent
    from agents import opportunity_agent
    from agents import recommendation_agent
    from agents import explanation_agent
    from agents import memory_agent
    from agents import planner
    
    # Test Planner Run with mock stubs
    planner.sessions["test_session"] = {
        "customer_id": "C001",
        "transcript_text": "ABC Manufacturing has low analytics adoption, renewal in 20 days, SAP integration is slow and competitors are being considered"
    }
    
    res = planner.run("test_session")
    
    required_keys = [
        "customer_summary", "knowledge", "sentiment", 
        "risks", "opportunities", "recommendations", "explanations"
    ]
    for key in required_keys:
        if key not in res:
            agents_ok = False
            record_failure("AGENTS", f"Planner response missing key: {key}")
            
except Exception as e:
    agents_ok = False
    record_failure("AGENTS", f"Agent import or planner run failed: {e}")

test_results["AGENTS"] = agents_ok
print(f"Agent & Planner Validation: {'PASS' if agents_ok else 'FAIL'}")

# =====================================================================
# TEST 7, 8: API TESTING & SERVER START
# =====================================================================
print("\n--- Running FastAPI API Validation ---")
api_ok = True
flow_ok = True

process = None
try:
    # Start live server
    print("Starting uvicorn server in subprocess...")
    process = subprocess.Popen(
        ["uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=backend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Let server start
    time.sleep(3)
    
    base_url = "http://127.0.0.1:8000"
    
    # 1. POST /upload_transcript
    payload = {
        "customer_id": "C001",
        "transcript_text": "ABC Manufacturing has low analytics adoption, renewal in 20 days, SAP integration is slow and competitors are being considered"
    }
    r = requests.post(f"{base_url}/upload_transcript", json=payload)
    if r.status_code != 200:
        api_ok = False
        record_failure("API", f"POST /upload_transcript returned status {r.status_code}")
    else:
        res_data = r.json()
        if "session_id" not in res_data:
            api_ok = False
            record_failure("API", "POST /upload_transcript response missing session_id")
        else:
            session_id = res_data["session_id"]
            
            # 2. GET /recommendation/{session_id}
            r_rec = requests.get(f"{base_url}/recommendation/{session_id}")
            if r_rec.status_code != 200:
                api_ok = False
                record_failure("API", f"GET /recommendation/{session_id} returned status {r_rec.status_code}")
            else:
                rec_data = r_rec.json()
                for key in ["customer_summary", "risks", "recommendations", "explanations"]:
                    if key not in rec_data:
                        api_ok = False
                        record_failure("API", f"GET /recommendation response missing key: {key}")
                
                # =====================================================
                # TEST 9: BUSINESS FLOW VALIDATION (Checks mock answers)
                # =====================================================
                # Check Risk: Renewal Risk with evidence "Health score 42" and "Renewal in 20 days"
                risks = rec_data.get("risks", {}).get("risks", [])
                has_renewal_risk = False
                evidence_ok = False
                for rsk in risks:
                    if rsk.get("type") == "Renewal Risk":
                        has_renewal_risk = True
                        ev = rsk.get("evidence", "").lower()
                        if "20 days" in ev and "42" in ev:
                            evidence_ok = True
                
                if not has_renewal_risk:
                    flow_ok = False
                    record_failure("FLOW", "Expected risk type 'Renewal Risk' not found")
                if has_renewal_risk and not evidence_ok:
                    flow_ok = False
                    record_failure("FLOW", "Renewal Risk evidence does not mention health score 42 and renewal in 20 days")
                
                # Check Opportunity: Analytics training
                opps = rec_data.get("opportunities", {}).get("opportunities", [])
                has_training_opp = False
                for opp in opps:
                    if opp.get("type") == "Training" and "Analytics" in opp.get("item", ""):
                        has_training_opp = True
                
                if not has_training_opp:
                    flow_ok = False
                    record_failure("FLOW", "Expected Opportunity for Analytics training not found")
                
                # Check Recommendation: Schedule analytics training session
                recs = rec_data.get("recommendations", {}).get("recommendations", [])
                has_training_rec = False
                for rc in recs:
                    if "schedule analytics training" in rc.get("action", "").lower():
                        has_training_rec = True
                
                if not has_training_rec:
                    flow_ok = False
                    record_failure("FLOW", "Expected Recommendation 'Schedule analytics training session' not found")
            
            # 3. POST /approve
            approve_payload = {
                "session_id": session_id,
                "recommendation_id": "REC001"
            }
            r_app = requests.post(f"{base_url}/approve", json=approve_payload)
            if r_app.status_code != 200:
                api_ok = False
                record_failure("API", f"POST /approve returned status {r_app.status_code}")
            else:
                if r_app.json() != {"status": "approved"}:
                    api_ok = False
                    record_failure("API", f"POST /approve response is not status approved: {r_app.json()}")
            
            # 4. GET /history/C001
            r_hist = requests.get(f"{base_url}/history/C001")
            if r_hist.status_code != 200:
                api_ok = False
                record_failure("API", f"GET /history/C001 returned status {r_hist.status_code}")
            else:
                if not isinstance(r_hist.json(), list):
                    api_ok = False
                    record_failure("API", "GET /history/C001 did not return a list")

except Exception as e:
    api_ok = False
    flow_ok = False
    record_failure("API", f"API or flow test failed: {e}")

finally:
    if process:
        print("Stopping uvicorn server...")
        process.terminate()
        process.wait()
        print("Server stopped.")

test_results["API"] = api_ok
test_results["FLOW"] = flow_ok

print(f"API Validation: {'PASS' if api_ok else 'FAIL'}")
print(f"Business Flow Validation: {'PASS' if flow_ok else 'FAIL'}")

# =====================================================================
# FINAL REPORT
# =====================================================================
print("\n" + "=" * 30)
print(f"PHASE 2 DATA:\n{'PASS' if test_results['DATA'] else 'FAIL'}")
print(f"\nPHASE 3 AGENTS:\n{'PASS' if test_results['AGENTS'] else 'FAIL'}")
print(f"\nPHASE 4 API:\n{'PASS' if test_results['API'] else 'FAIL'}")
print(f"\nEND TO END FLOW:\n{'PASS' if test_results['FLOW'] else 'FAIL'}")
print("=" * 30)

if failures:
    print("\nDETAILED FAILURES:")
    for fail in failures:
        print(f"  - {fail}")
    sys.exit(1)
else:
    print("\nALL SYSTEM TESTS PASSED SUCCESSFULLY")
    sys.exit(0)
