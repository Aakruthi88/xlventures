import os
import sys
import uuid
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

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
    allow_origins=["http://localhost:5173"],
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


@app.get("/history/{customer_id}")
def get_history(customer_id: str):
    history = memory_agent.get_history(customer_id)
    return history

