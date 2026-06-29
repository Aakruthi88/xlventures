"""
Planner (Orchestrator)
======================
Orchestrates the agentic workflow using PlannerAgent for dynamic
reasoning and AgentExecutor for plan-driven execution.

Architecture:
    1. PlannerAgent analyzes the transcript and generates an execution plan.
    2. AgentExecutor dynamically executes only the agents selected by the plan.
    3. Mandatory agents (recommendation, explanation) always run after analysis.
    4. State is checkpointed after recommendations for HITL approval.
    5. resume_workflow() resumes execution with ActionExecutorAgent + OutcomeAgent.

Human-In-The-Loop (HITL) Flow:
    run(session_id)          → Runs to recommendation stage, saves paused state
    resume_workflow(...)     → Resumes after approval, runs action + outcome agents
"""

import sys
import os
from typing import Any, Dict

# Add parent directory to path for imports
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from agents.planner_agent import PlannerAgent
from agents.customer_agent import CustomerAgent
from agents.knowledge_agent import KnowledgeAgent
from agents.sentiment_agent import SentimentAgent
from agents.risk_agent import RiskAgent
from agents.opportunity_agent import OpportunityAgent
from agents.recommendation_agent import RecommendationAgent
from agents.explanation_agent import ExplanationAgent
from agents.memory_agent import MemoryAgent

from graph.agent_executor import (
    register_agent,
    execute_plan,
    run_mandatory_agents,
    get_trace,
    graph,  # LangGraph compiled graph (used for trace/visualization)
)

# ============================================================
# SESSION & HITL STATE STORES
# ============================================================

# In-memory session store (shared with main.py)
sessions = {}

# HITL checkpoint: stores the full analysis state after recommendations
# so resume_workflow() can pick up exactly where we paused.
_paused_states: Dict[str, dict] = {}


# ============================================================
# AGENT REGISTRATION
# ============================================================

_planner_agent = PlannerAgent()
_customer_agent = CustomerAgent()
_knowledge_agent = KnowledgeAgent()
_sentiment_agent = SentimentAgent()
_risk_agent = RiskAgent()
_opportunity_agent = OpportunityAgent()
_recommendation_agent = RecommendationAgent()
_explanation_agent = ExplanationAgent()
_memory_agent = MemoryAgent()

# Analysis agents — dynamically selected by the planner
register_agent(_customer_agent)
register_agent(_knowledge_agent)
register_agent(_sentiment_agent)
register_agent(_risk_agent)
register_agent(_opportunity_agent)
register_agent(_memory_agent)

# Mandatory agents — always run after analysis
register_agent(_recommendation_agent)
register_agent(_explanation_agent)

print("[Planner] All agents registered. Dynamic orchestration ready.")


# ============================================================
# PUBLIC API — run(session_id)   [Phase 1 of HITL]
# ============================================================

def run(session_id: str) -> dict:
    """
    Execute the planner workflow up to the HITL interrupt point.

    1. PlannerAgent selects required agents.
    2. AgentExecutor runs selected agents.
    3. Mandatory agents (recommendation, explanation) run.
    4. State is saved to _paused_states for HITL resumption.

    On subsequent calls for the same session the cached state is returned
    immediately — avoiding a redundant re-run while the user decides.

    Returns:
        Dict with: customer_summary, knowledge, sentiment, risks,
                   opportunities, recommendations, explanations, past_cases
    """
    # ── Return cached state if already computed ──────────────────────────────
    if session_id in _paused_states:
        state = _paused_states[session_id]
        print(f"[Planner] Returning cached HITL state for session: {session_id}")
        return _build_response(state)

    print(f"\n{'=' * 50}")
    print(f"[Planner] Starting dynamic workflow for session: {session_id}")
    print(f"{'=' * 50}")

    session = sessions.get(session_id, {})
    customer_id = session.get("customer_id", "C001")
    transcript_text = session.get("transcript_text", "")

    try:
        from metrics.business_metrics import BusinessMetricsService
        BusinessMetricsService.start_session_tracking(session_id, customer_id)
    except Exception as e:
        print(f"[Planner] Metrics error starting session: {e}")

    # Initialise shared state
    state = {
        "session_id": session_id,
        "customer_id": customer_id,
        "transcript_text": transcript_text,
        "customer_summary": {},
        "knowledge": {},
        "sentiment": {},
        "risks": {},
        "opportunities": {},
        "recommendations": {},
        "explanations": {},
        "past_cases": [],
        "approval_decision": {},
        "action_execution": {},
        "outcome_learning": {},
    }

    # Step 1: PlannerAgent generates execution plan
    print(f"\n[Planner] Step 1: Generating execution plan...")
    plan_result = _planner_agent.execute(state)
    plan = plan_result.get("plan", {})
    state["plan"] = plan

    method = plan.get("_method", "unknown")
    agent_names = [a["name"] for a in plan.get("required_agents", [])]
    print(f"[Planner] Plan method: {method} | Selected agents: {agent_names}")

    # Step 2: Execute selected analysis agents
    print(f"\n[Planner] Step 2: Executing analysis agents...")
    state = execute_plan(session_id, plan, state)

    # Step 3: Run mandatory agents (recommendation + explanation)
    print(f"\n[Planner] Step 3: Running mandatory agents...")
    state = run_mandatory_agents(
        session_id, state,
        mandatory_names=["recommendation_agent", "explanation_agent"]
    )

    # -- HITL INTERRUPT: checkpoint the full state before action execution ----
    _paused_states[session_id] = dict(state)
    print(f"[Planner] HITL interrupt: state saved. Awaiting human approval.")

    try:
        from metrics.business_metrics import BusinessMetricsService
        recs_list = state.get("recommendations", {}).get("recommendations", [])
        rec_text = "; ".join(r.get("action", "") for r in recs_list if isinstance(r, dict))
        avg_conf = sum(float(r.get("confidence", 0.95)) for r in recs_list if isinstance(r, dict)) / max(1, len(recs_list))
        BusinessMetricsService.end_session_tracking(session_id, rec_text, avg_conf)
    except Exception as e:
        print(f"[Planner] Metrics error ending session: {e}")

    print(f"[Planner] Workflow paused. Agents executed: {agent_names}")
    return _build_response(state)


# ============================================================
# PUBLIC API — resume_workflow()  [Phase 2 of HITL]
# ============================================================

def resume_workflow(session_id: str, rec_id: str, approved: bool) -> dict:
    """
    Resume execution after human-in-the-loop approval decision.

    Retrieves the paused state, injects the approval decision, then runs:
        ActionExecutorAgent → executes the approved business action
        OutcomeAgent        → logs before/after health score & success flag

    Args:
        session_id: Session identifier.
        rec_id:     The recommendation ID the user approved/rejected.
        approved:   True = proceed with execution; False = reject.

    Returns:
        action_execution dict: { status, action }
    """
    if session_id not in _paused_states:
        raise ValueError(
            f"No paused state found for session '{session_id}'. "
            "Call run() first to generate recommendations."
        )

    state = dict(_paused_states[session_id])

    # Resolve the action text for the approved recommendation
    recs_list = state.get("recommendations", {}).get("recommendations", [])
    action_text = ""
    for r in recs_list:
        if isinstance(r, dict) and r.get("id") == rec_id:
            action_text = r.get("action", "")
            break

    state["approval_decision"] = {
        "recommendation_id": rec_id,
        "recommendation_action": action_text,
        "approved": approved,
    }

    print(f"\n[Planner] >> Resuming workflow for session {session_id}")
    print(f"[Planner]   rec_id={rec_id} | approved={approved} | action='{action_text}'")

    if not approved:
        print("[Planner] Action rejected by user — skipping execution.")
        try:
            from metrics.business_metrics import BusinessMetricsService
            BusinessMetricsService.record_approval(session_id, False)
        except Exception as e:
            print(f"[Planner] Metrics error recording rejection: {e}")
        return {"status": "rejected", "action": "Action was not approved."}

    # Step 4: ActionExecutorAgent — execute the approved action
    from agents.action_executor_agent import ActionExecutorAgent
    executor = ActionExecutorAgent()
    print("[Planner] Step 4: Running ActionExecutorAgent...")
    exec_result = executor.execute(state)
    state.update(exec_result)

    # Step 5: OutcomeAgent — log metrics to database
    from agents.outcome_agent import OutcomeAgent
    outcome = OutcomeAgent()
    print("[Planner] Step 5: Running OutcomeAgent...")
    out_result = outcome.execute(state)
    state.update(out_result)

    # Update checkpoint with execution results
    _paused_states[session_id] = state

    try:
        from metrics.business_metrics import BusinessMetricsService
        BusinessMetricsService.record_approval(session_id, True)
        out_data = state.get("outcome_learning", {})
        success = out_data.get("success", True)
        outcome_str = f"Executed action. Health Delta: {out_data.get('before_score', 0)} -> {out_data.get('after_score', 0)}"
        BusinessMetricsService.record_outcome(session_id, outcome_str, success)
    except Exception as e:
        print(f"[Planner] Metrics error recording outcome: {e}")

    print(f"[Planner] Workflow resumed and completed for session: {session_id}")
    return state.get("action_execution", {"status": "success", "action": "Action executed."})


# ============================================================
# HELPERS
# ============================================================

def _build_response(state: dict) -> dict:
    """Build the standard API response dict from a state dict."""
    return {
        "customer_summary": state.get("customer_summary", {}),
        "knowledge": state.get("knowledge", {}),
        "sentiment": state.get("sentiment", {}),
        "risks": state.get("risks", {}),
        "opportunities": state.get("opportunities", {}),
        "recommendations": state.get("recommendations", {}),
        "explanations": state.get("explanations", {}),
        "past_cases": state.get("past_cases", []),
    }


def get_session_trace(session_id: str) -> list:
    """Return the execution trace for a session."""
    return get_trace(session_id)


def get_graph_structure() -> dict:
    """Return the LangGraph node/edge structure for frontend visualization."""
    return {
        "nodes": [
            {"id": "planner_node",          "label": "Planner Agent",         "type": "planner"},
            {"id": "analysis_node",          "label": "Analysis Agents",       "type": "analysis"},
            {"id": "decision_node",          "label": "Recommendation Agent",  "type": "decision"},
            {"id": "action_execution_node",  "label": "Action Executor",       "type": "action"},
        ],
        "edges": [
            {"source": "planner_node",         "target": "analysis_node"},
            {"source": "analysis_node",         "target": "decision_node"},
            {"source": "decision_node",         "target": "action_execution_node", "label": "HITL Interrupt"},
        ]
    }
