"""
Planner Agent (LangGraph Orchestrator)
======================================
Dynamically orchestrates specialized agents using LangGraph StateGraph.

Architecture:
    load_context -> planner_router -> [agent nodes based on selection] ->
    recommendation_node -> explanation_node -> END

Phase 5: LangGraph with dynamic routing via Ollama + rule-based fallback.
"""

import sys
import os
from typing import Any, Dict, List, Annotated
import operator

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import customer_agent
from agents import knowledge_agent
from agents import sentiment_agent
from agents import risk_agent
from agents import opportunity_agent
from agents import recommendation_agent
from agents import explanation_agent
from agents import memory_agent
from agents.planner_router import route_agents

# LangGraph imports
try:
    from langgraph.graph import StateGraph, END
    from typing_extensions import TypedDict
    LANGGRAPH_AVAILABLE = True
    print("[Planner] LangGraph loaded successfully")
except ImportError:
    LANGGRAPH_AVAILABLE = False
    print("[Planner] LangGraph not installed - using sequential fallback")

# In-memory session store (shared with main.py)
sessions = {}


# ============================================================
# LANGGRAPH STATE DEFINITION
# ============================================================

if LANGGRAPH_AVAILABLE:
    class PlannerState(TypedDict):
        """State schema for the LangGraph planner workflow."""
        session_id: str
        customer_id: str
        transcript_text: str
        selected_agents: list
        routing_reasoning: str
        customer_summary: dict
        knowledge: dict
        sentiment: dict
        risks: dict
        opportunities: dict
        recommendations: dict
        explanations: dict


# ============================================================
# LANGGRAPH NODE FUNCTIONS
# ============================================================

def load_context_node(state: dict) -> dict:
    """Load session data into the workflow state."""
    session = sessions.get(state.get("session_id", ""), {})
    customer_id = session.get("customer_id", "C001")
    transcript_text = session.get("transcript_text", "")
    print(f"\n[Planner] Loading context for session: {state.get('session_id', 'unknown')}")
    print(f"[Planner] Customer: {customer_id}")
    print(f"[Planner] Transcript length: {len(transcript_text)} chars")
    return {
        **state,
        "customer_id": customer_id,
        "transcript_text": transcript_text
    }


def router_node(state: dict) -> dict:
    """Dynamically decide which agents to execute."""
    transcript_text = state.get("transcript_text", "")
    routing = route_agents(transcript_text)

    selected = routing.get("agents", [])
    reasoning = routing.get("reasoning", "")
    method = routing.get("method", "rules")

    print(f"\n[Planner] Routing method: {method}")
    print(f"[Planner] Selected agents: {selected}")
    print(f"[Planner] Reasoning: {reasoning}")

    return {
        **state,
        "selected_agents": selected,
        "routing_reasoning": reasoning
    }


def customer_agent_node(state: dict) -> dict:
    """Run customer_agent if selected."""
    if "customer_agent" not in state.get("selected_agents", []):
        print("[Planner] Skipping customer_agent (not selected)")
        return state
    try:
        print("[Planner] Running customer_agent...")
        result = customer_agent.get_summary(state.get("customer_id", "C001"))
        return {**state, "customer_summary": result}
    except Exception as e:
        print(f"[Planner] customer_agent failed: {e}")
        return {**state, "customer_summary": customer_agent.get_summary("C001")}


def knowledge_agent_node(state: dict) -> dict:
    """Run knowledge_agent if selected."""
    if "knowledge_agent" not in state.get("selected_agents", []):
        print("[Planner] Skipping knowledge_agent (not selected)")
        return state
    try:
        print("[Planner] Running knowledge_agent...")
        result = knowledge_agent.retrieve(state.get("transcript_text", ""))
        return {**state, "knowledge": result}
    except Exception as e:
        print(f"[Planner] knowledge_agent failed: {e}")
        return {**state, "knowledge": {"retrieved_docs": []}}


def sentiment_agent_node(state: dict) -> dict:
    """Run sentiment_agent if selected."""
    if "sentiment_agent" not in state.get("selected_agents", []):
        print("[Planner] Skipping sentiment_agent (not selected)")
        return state
    try:
        print("[Planner] Running sentiment_agent...")
        result = sentiment_agent.analyze(state.get("transcript_text", ""))
        return {**state, "sentiment": result}
    except Exception as e:
        print(f"[Planner] sentiment_agent failed: {e}")
        return {**state, "sentiment": {"sentiment": "Neutral", "confidence": 0.5, "key_phrases": []}}


def risk_agent_node(state: dict) -> dict:
    """Run risk_agent if selected."""
    if "risk_agent" not in state.get("selected_agents", []):
        print("[Planner] Skipping risk_agent (not selected)")
        return state
    try:
        print("[Planner] Running risk_agent...")
        result = risk_agent.assess(
            state.get("customer_summary", {}),
            state.get("sentiment", {}),
            state.get("knowledge", {})
        )
        return {**state, "risks": result}
    except Exception as e:
        print(f"[Planner] risk_agent failed: {e}")
        return {**state, "risks": {"risks": [], "overall_risk": "Unknown"}}


def opportunity_agent_node(state: dict) -> dict:
    """Run opportunity_agent if selected."""
    if "opportunity_agent" not in state.get("selected_agents", []):
        print("[Planner] Skipping opportunity_agent (not selected)")
        return state
    try:
        print("[Planner] Running opportunity_agent...")
        result = opportunity_agent.find(
            state.get("customer_summary", {}),
            state.get("knowledge", {})
        )
        return {**state, "opportunities": result}
    except Exception as e:
        print(f"[Planner] opportunity_agent failed: {e}")
        return {**state, "opportunities": {"opportunities": []}}


def recommendation_node(state: dict) -> dict:
    """Always runs - generates next best actions from all agent outputs."""
    try:
        print("[Planner] Running recommendation_agent...")
        past_approvals = memory_agent.get_similar_past_approvals(
            state.get("customer_id", "C001")
        )
        result = recommendation_agent.generate(
            state.get("customer_summary", {}),
            state.get("risks", {}),
            state.get("opportunities", {}),
            state.get("sentiment", {}),
            state.get("knowledge", {}),
            past_approvals=past_approvals
        )
        return {**state, "recommendations": result}
    except Exception as e:
        print(f"[Planner] recommendation_agent failed: {e}")
        return {**state, "recommendations": {"recommendations": []}}


def explanation_node(state: dict) -> dict:
    """Always runs - explains recommendations with evidence."""
    try:
        print("[Planner] Running explanation_agent...")
        result = explanation_agent.explain(state.get("recommendations", {}))
        return {**state, "explanations": result}
    except Exception as e:
        print(f"[Planner] explanation_agent failed: {e}")
        return {**state, "explanations": {"explanations": []}}


# ============================================================
# BUILD LANGGRAPH WORKFLOW
# ============================================================

def build_graph():
    """
    Construct the LangGraph StateGraph with all agent nodes.

    Graph topology:
        START -> load_context -> planner_router ->
        customer_agent -> knowledge_agent -> sentiment_agent ->
        risk_agent -> opportunity_agent ->
        recommendation -> explanation -> END

    Each analysis agent node checks if it was selected by the router.
    If not selected, it returns the state unchanged (skip).
    recommendation and explanation nodes always execute.
    """
    workflow = StateGraph(PlannerState)

    # Add all nodes
    workflow.add_node("load_context", load_context_node)
    workflow.add_node("planner_router", router_node)
    workflow.add_node("customer_agent", customer_agent_node)
    workflow.add_node("knowledge_agent", knowledge_agent_node)
    workflow.add_node("sentiment_agent", sentiment_agent_node)
    workflow.add_node("risk_agent", risk_agent_node)
    workflow.add_node("opportunity_agent", opportunity_agent_node)
    workflow.add_node("recommendation", recommendation_node)
    workflow.add_node("explanation", explanation_node)

    # Set entry point
    workflow.set_entry_point("load_context")

    # Define edges (sequential flow with skip logic inside nodes)
    workflow.add_edge("load_context", "planner_router")
    workflow.add_edge("planner_router", "customer_agent")
    workflow.add_edge("customer_agent", "knowledge_agent")
    workflow.add_edge("knowledge_agent", "sentiment_agent")
    workflow.add_edge("sentiment_agent", "risk_agent")
    workflow.add_edge("risk_agent", "opportunity_agent")
    workflow.add_edge("opportunity_agent", "recommendation")
    workflow.add_edge("recommendation", "explanation")
    workflow.add_edge("explanation", END)

    return workflow.compile()


# Build the graph at module load time
_graph = None
if LANGGRAPH_AVAILABLE:
    try:
        _graph = build_graph()
        print("[Planner] LangGraph workflow compiled successfully")
    except Exception as e:
        print(f"[Planner] LangGraph compilation failed: {e}")
        _graph = None


# ============================================================
# SEQUENTIAL FALLBACK (if LangGraph unavailable)
# ============================================================

def run_sequential(session_id: str) -> dict:
    """
    Fallback sequential orchestration without LangGraph.
    Used when LangGraph is not installed.
    """
    print("[Planner] Using sequential fallback (no LangGraph)")
    session = sessions.get(session_id, {})
    customer_id = session.get("customer_id", "C001")
    transcript_text = session.get("transcript_text", "")

    # Route agents
    routing = route_agents(transcript_text)
    selected = routing.get("agents", [])
    print(f"[Planner] Selected agents: {selected}")

    result = {
        "customer_summary": {},
        "knowledge": {},
        "sentiment": {},
        "risks": {},
        "opportunities": {},
        "recommendations": {},
        "explanations": {},
    }

    if "customer_agent" in selected:
        try:
            result["customer_summary"] = customer_agent.get_summary(customer_id)
        except Exception as e:
            print(f"[Planner] customer_agent failed: {e}")

    if "knowledge_agent" in selected:
        try:
            result["knowledge"] = knowledge_agent.retrieve(transcript_text)
        except Exception as e:
            print(f"[Planner] knowledge_agent failed: {e}")

    if "sentiment_agent" in selected:
        try:
            result["sentiment"] = sentiment_agent.analyze(transcript_text)
        except Exception as e:
            print(f"[Planner] sentiment_agent failed: {e}")

    if "risk_agent" in selected:
        try:
            result["risks"] = risk_agent.assess(
                result["customer_summary"], result["sentiment"], result["knowledge"]
            )
        except Exception as e:
            print(f"[Planner] risk_agent failed: {e}")

    if "opportunity_agent" in selected:
        try:
            result["opportunities"] = opportunity_agent.find(
                result["customer_summary"], result["knowledge"]
            )
        except Exception as e:
            print(f"[Planner] opportunity_agent failed: {e}")

    try:
        past_approvals = memory_agent.get_similar_past_approvals(customer_id)
        result["recommendations"] = recommendation_agent.generate(
            result["customer_summary"], result["risks"],
            result["opportunities"], result["sentiment"],
            result["knowledge"], past_approvals=past_approvals
        )
    except Exception as e:
        print(f"[Planner] recommendation_agent failed: {e}")

    try:
        result["explanations"] = explanation_agent.explain(result["recommendations"])
    except Exception as e:
        print(f"[Planner] explanation_agent failed: {e}")

    return result


# ============================================================
# PUBLIC API - run(session_id)
# ============================================================

def run(session_id: str) -> dict:
    """
    Execute the planner workflow for a given session.

    Uses LangGraph if available, falls back to sequential execution.
    Always returns a dict matching the API contract with all 7 keys.

    Args:
        session_id: Session identifier from /upload_transcript

    Returns:
        Dict with: customer_summary, knowledge, sentiment, risks,
                   opportunities, recommendations, explanations
    """
    print(f"\n{'=' * 50}")
    print(f"[Planner] Starting workflow for session: {session_id}")
    print(f"{'=' * 50}")

    if _graph is not None:
        # Use LangGraph workflow
        try:
            initial_state = {
                "session_id": session_id,
                "customer_id": "",
                "transcript_text": "",
                "selected_agents": [],
                "routing_reasoning": "",
                "customer_summary": {},
                "knowledge": {},
                "sentiment": {},
                "risks": {},
                "opportunities": {},
                "recommendations": {},
                "explanations": {},
            }

            final_state = _graph.invoke(initial_state)

            # Extract API response from final state
            response = {
                "customer_summary": final_state.get("customer_summary", {}),
                "knowledge": final_state.get("knowledge", {}),
                "sentiment": final_state.get("sentiment", {}),
                "risks": final_state.get("risks", {}),
                "opportunities": final_state.get("opportunities", {}),
                "recommendations": final_state.get("recommendations", {}),
                "explanations": final_state.get("explanations", {}),
            }

            print(f"\n[Planner] Workflow completed via LangGraph")
            print(f"[Planner] Agents executed: {final_state.get('selected_agents', [])}")
            print(f"[Planner] Routing: {final_state.get('routing_reasoning', 'N/A')}")

            return response

        except Exception as e:
            print(f"[Planner] LangGraph execution failed: {e}")
            print("[Planner] Falling back to sequential execution...")
            return run_sequential(session_id)
    else:
        # LangGraph not available
        return run_sequential(session_id)
