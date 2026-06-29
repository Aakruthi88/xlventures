import os
import sys
import uuid
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from typing import List, Dict, Any, Optional

# Add current folder to path for import safety
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from agents import planner
from agents import memory_agent

app = FastAPI(
    title="Intelligent Next Best Action Platform API",
    description="Backend API for managing customer insights, recommendations, and memory",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Share session store with planner
sessions = planner.sessions


# Pydantic models for request bodies
class UploadTranscriptRequest(BaseModel):
    customer_id: str
    transcript_text: str


class ApproveRequest(BaseModel):
    session_id: str
    recommendation_id: str


class ApproveActionRequest(BaseModel):
    session_id: Optional[str] = None
    recommendation_id: str
    approved: bool


@app.get("/")
def read_root():
    return {"message": "Welcome to the Intelligent Next Best Action Platform API"}


@app.post("/upload_transcript")
def upload_transcript(req: UploadTranscriptRequest):
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "customer_id": req.customer_id,
        "transcript_text": req.transcript_text
    }
    return {"session_id": session_id}


@app.get("/recommendation/{session_id}")
def get_recommendation(session_id: str):
    if session_id not in sessions:
        return JSONResponse(status_code=404, content={"error": "Session not found"})
    
    result = planner.run(session_id)
    return result


@app.post("/approve")
def approve_recommendation(req: ApproveRequest):
    if req.session_id not in sessions:
        return JSONResponse(status_code=404, content={"error": "Session not found"})
    
    session = sessions[req.session_id]
    customer_id = session.get("customer_id")
    
    # Try to find the recommendation action data (best effort for stub)
    recommendation_data = {}
    try:
        planner_res = planner.run(req.session_id)
        recs = planner_res.get("recommendations", {}).get("recommendations", [])
        for r in recs:
            if r.get("id") == req.recommendation_id:
                recommendation_data = r
                break
    except Exception as e:
        print(f"[API] Error resolving recommendation details for store_approval: {e}")
        
    memory_agent.store_approval(req.session_id, customer_id, recommendation_data)
    return {"status": "approved"}


@app.post("/approve_action")
def approve_action(req: ApproveActionRequest):
    session_id = req.session_id
    if not session_id:
        # Fallback to the most recent session
        if sessions:
            session_id = list(sessions.keys())[-1]
        else:
            raise HTTPException(status_code=404, detail="No session found to approve.")

    if session_id not in sessions:
         raise HTTPException(status_code=404, detail=f"Session {session_id} not found.")

    session = sessions[session_id]
    customer_id = session.get("customer_id")

    # 1. Resolve recommendation action details
    recommendation_data = {}
    try:
        planner_res = planner.run(session_id)
        recs = planner_res.get("recommendations", {}).get("recommendations", [])
        for r in recs:
            if r.get("id") == req.recommendation_id:
                recommendation_data = r
                break
    except Exception as e:
        print(f"[API] Error resolving recommendation details: {e}")

    # 2. Store approval in database & ChromaDB
    if req.approved:
        memory_agent.store_approval(session_id, customer_id, recommendation_data)

    # 3. Resume LangGraph workflow
    execution_result = planner.resume_workflow(session_id, req.recommendation_id, req.approved)
    
    return {
        "status": "resumed",
        "approved": req.approved,
        "execution_result": execution_result
    }


@app.get("/history/{customer_id}")
def get_history(customer_id: str):
    history = memory_agent.get_history(customer_id)
    return history


@app.get("/agent_trace/{session_id}")
def get_agent_trace(session_id: str):
    """
    Return the execution trace for a session.
    Each entry contains: agent_name, status, input, output, timestamp.
    """
    trace = planner.get_session_trace(session_id)
    return {"session_id": session_id, "trace": trace}


@app.get("/graph_structure")
def get_graph_structure():
    """Return the agent pipeline graph nodes and edges for frontend visualization."""
    return planner.get_graph_structure()


@app.get("/customers")
def get_customers():
    from database import repository as repo
    from datetime import datetime
    customers = repo.get_all_customers()
    formatted = []
    for c in customers:
        days_to_renewal = 0
        if c.get("renewal_date"):
            try:
                renewal_date = datetime.strptime(c["renewal_date"], "%Y-%m-%d")
                today = datetime.now()
                today = today.replace(hour=0, minute=0, second=0, microsecond=0)
                days_to_renewal = (renewal_date - today).days
            except Exception:
                pass
        formatted.append({
            "id": c.get("customer_id"),
            "name": c.get("company"),
            "plan": c.get("plan"),
            "industry": c.get("industry"),
            "renewalDate": c.get("renewal_date"),
            "healthScore": c.get("health_score", 0),
            "daysToRenewal": days_to_renewal,
            "licensedUsers": c.get("licensed_users", 0),
            "activeUsers": c.get("active_users", 0),
            "openSupportTickets": c.get("support_tickets_open", 0),
            "recentMeetingDate": c.get("recent_meeting_date", ""),
            "owner": c.get("customer_owner", ""),
        })
    return formatted


@app.get("/customers/{customer_id}")
def get_customer_detail(customer_id: str):
    from database import repository as repo
    from datetime import datetime
    c = repo.get_customer_by_id(customer_id)
    if not c:
        raise HTTPException(status_code=404, detail="Customer not found")
        
    days_to_renewal = 0
    if c.get("renewal_date"):
        try:
            renewal_date = datetime.strptime(c["renewal_date"], "%Y-%m-%d")
            today = datetime.now()
            today = today.replace(hour=0, minute=0, second=0, microsecond=0)
            days_to_renewal = (renewal_date - today).days
        except Exception:
            pass
            
    return {
        "id": c.get("customer_id"),
        "name": c.get("company"),
        "plan": c.get("plan"),
        "industry": c.get("industry"),
        "renewalDate": c.get("renewal_date"),
        "healthScore": c.get("health_score", 0),
        "daysToRenewal": days_to_renewal,
        "licensedUsers": c.get("licensed_users", 0),
        "activeUsers": c.get("active_users", 0),
        "openSupportTickets": c.get("support_tickets_open", 0),
        "recentMeetingDate": c.get("recent_meeting_date", ""),
        "owner": c.get("customer_owner", ""),
    }


@app.get("/recommendations/{customer_id}")
def get_recommendations_by_customer(customer_id: str):
    from database import repository as repo
    recs = repo.get_recommendations_by_customer(customer_id)
    formatted_recs = []
    for r in recs:
        formatted_recs.append({
            "id": r.get("id"),
            "action": r.get("action_description"),
            "priority": r.get("priority", "Medium"),
            "confidence": r.get("confidence", 0.9)
        })
    return {"recommendations": formatted_recs, "explanations": []}


@app.get("/analytics")
def get_analytics():
    return memory_agent.get_analytics()


