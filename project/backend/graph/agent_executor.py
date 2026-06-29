"""
Agent Executor
==============
Dynamically executes agents based on the PlannerAgent's execution plan.

Architecture:
    1. Reads the structured plan from PlannerAgent output.
    2. Looks up required agents in a registry (no hardcoded graph nodes).
    3. Executes each agent, merging results into shared state.
    4. Records execution traces for every agent invocation.
    5. Supports adding new agents by simply registering them.
"""

import sys
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

# Ensure backend dir is on path for imports
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from agents.base_agent import BaseAgent

# ─────────────────────────────────────────────────────────────────────────────
# Trace Store
# ─────────────────────────────────────────────────────────────────────────────

# In-memory trace store keyed by session_id
_trace_store: Dict[str, List[Dict[str, Any]]] = {}


def get_trace(session_id: str) -> List[Dict[str, Any]]:
    """Return the execution trace for a given session."""
    return _trace_store.get(session_id, [])


def _record_trace(session_id: str, agent_name: str, status: str,
                  input_data: Any, output_data: Any) -> None:
    """Append an execution trace entry for a session."""
    if session_id not in _trace_store:
        _trace_store[session_id] = []

    _trace_store[session_id].append({
        "agent_name": agent_name,
        "status": status,
        "input": _summarize(input_data),
        "output": _summarize(output_data),
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    })


def _summarize(data: Any, max_len: int = 500) -> str:
    """Create a concise string summary of data for the trace."""
    if data is None:
        return ""
    if isinstance(data, str):
        return data[:max_len]
    if isinstance(data, dict):
        # Show keys and truncated values
        parts = []
        for k, v in data.items():
            v_str = str(v)
            if len(v_str) > 80:
                v_str = v_str[:80] + "..."
            parts.append(f"{k}: {v_str}")
        result = "; ".join(parts)
        return result[:max_len]
    return str(data)[:max_len]


# ─────────────────────────────────────────────────────────────────────────────
# Agent Registry
# ─────────────────────────────────────────────────────────────────────────────

# Registry maps agent name -> BaseAgent instance
_agent_registry: Dict[str, BaseAgent] = {}


def register_agent(agent: BaseAgent) -> None:
    """Register a BaseAgent instance in the global registry."""
    _agent_registry[agent.name] = agent
    print(f"[AgentExecutor] Registered agent: {agent.name}")


def get_registry() -> Dict[str, BaseAgent]:
    """Return a copy of the current agent registry."""
    return dict(_agent_registry)


# ─────────────────────────────────────────────────────────────────────────────
# Executor
# ─────────────────────────────────────────────────────────────────────────────

def execute_plan(session_id: str, plan: dict, state: dict) -> dict:
    """
    Execute agents dynamically based on the planner's plan.

    Args:
        session_id: The session identifier for tracing.
        plan: The structured plan from PlannerAgent with 'required_agents'.
        state: The shared workflow state dict.

    Returns:
        The updated state dict after all agents have executed.
    """
    required_agents = plan.get("required_agents", [])

    # Record the planner trace
    _record_trace(
        session_id,
        agent_name="planner_agent",
        status="completed",
        input_data={"transcript_length": len(state.get("transcript_text", "")),
                     "customer_id": state.get("customer_id", "")},
        output_data=plan
    )

    # Execute each required agent in order
    for agent_spec in required_agents:
        agent_name = agent_spec.get("name", "")
        agent_reason = agent_spec.get("reason", "")

        if agent_name not in _agent_registry:
            print(f"[AgentExecutor] WARNING: Agent '{agent_name}' not found in registry. Skipping.")
            _record_trace(session_id, agent_name, "skipped",
                          {"reason": "Agent not found in registry"}, {})
            continue

        agent = _agent_registry[agent_name]
        print(f"[AgentExecutor] Running {agent_name} — {agent_reason}")

        try:
            result = agent.execute(state)
            # Merge result into state
            if isinstance(result, dict):
                state.update(result)
            _record_trace(session_id, agent_name, "completed",
                          {"reason": agent_reason}, result)
        except Exception as e:
            print(f"[AgentExecutor] Agent '{agent_name}' failed: {e}")
            _record_trace(session_id, agent_name, "failed",
                          {"reason": agent_reason}, {"error": str(e)})

    return state


def run_mandatory_agents(session_id: str, state: dict,
                         mandatory_names: List[str]) -> dict:
    """
    Execute mandatory agents (recommendation, explanation) that always run
    regardless of the planner's selection.

    Args:
        session_id: The session identifier for tracing.
        state: The shared workflow state dict.
        mandatory_names: List of agent names to run unconditionally.

    Returns:
        The updated state dict.
    """
    for agent_name in mandatory_names:
        if agent_name not in _agent_registry:
            print(f"[AgentExecutor] WARNING: Mandatory agent '{agent_name}' not found. Skipping.")
            _record_trace(session_id, agent_name, "skipped",
                          {"reason": "Mandatory agent not in registry"}, {})
            continue

        agent = _agent_registry[agent_name]
        print(f"[AgentExecutor] Running mandatory agent: {agent_name}")

        try:
            result = agent.execute(state)
            if isinstance(result, dict):
                state.update(result)
            _record_trace(session_id, agent_name, "completed",
                          {"reason": "Mandatory execution"}, result)
        except Exception as e:
            print(f"[AgentExecutor] Mandatory agent '{agent_name}' failed: {e}")
            _record_trace(session_id, agent_name, "failed",
                          {"reason": "Mandatory execution"}, {"error": str(e)})

    return state


# ─────────────────────────────────────────────────────────────────────────────
# LangGraph Workflow and Human-In-The-Loop Integration
# ─────────────────────────────────────────────────────────────────────────────

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

# Nodes definitions mapping to agents / executor helpers

def planner_node(state: dict) -> dict:
    """Execute the PlannerAgent to retrieve plans."""
    from agents.planner_agent import PlannerAgent
    planner = PlannerAgent()
    res = planner.execute(state)
    # Merge plan into state
    return {"plan": res.get("plan", {})}


def analysis_node(state: dict) -> dict:
    """Execute the planner-selected analysis agents dynamically."""
    session_id = state.get("session_id", "default_session")
    plan = state.get("plan", {})
    # Execute and return modifications to the state
    updated_state = execute_plan(session_id, plan, dict(state))
    return {
        "customer_summary": updated_state.get("customer_summary", {}),
        "knowledge": updated_state.get("knowledge", {}),
        "sentiment": updated_state.get("sentiment", {}),
        "risks": updated_state.get("risks", {}),
        "opportunities": updated_state.get("opportunities", {}),
        "past_cases": updated_state.get("past_cases", []),
    }


def decision_node(state: dict) -> dict:
    """Execute the mandatory recommendation and explanation agents."""
    session_id = state.get("session_id", "default_session")
    updated_state = run_mandatory_agents(
        session_id, dict(state),
        mandatory_names=["recommendation_agent", "explanation_agent"]
    )
    return {
        "recommendations": updated_state.get("recommendations", {}),
        "explanations": updated_state.get("explanations", {}),
    }


def action_execution_node(state: dict) -> dict:
    """Execute approved action using the ActionExecutorAgent and log metrics via OutcomeAgent."""
    session_id = state.get("session_id", "default_session")
    
    # 1. Action Executor Agent
    from agents.action_executor_agent import ActionExecutorAgent
    executor = ActionExecutorAgent()
    print("[AgentExecutor] Running action_executor_agent...")
    exec_res = executor.execute(state)
    
    # 2. Outcome Agent
    from agents.outcome_agent import OutcomeAgent
    outcome = OutcomeAgent()
    print("[AgentExecutor] Running outcome_agent...")
    # Merge execution result into state before running outcome analysis
    temp_state = {**state, **exec_res}
    out_res = outcome.execute(temp_state)
    
    # Record trace entries
    _record_trace(session_id, "action_executor_agent", "completed", 
                  {"action": state.get("approval_decision", {}).get("recommendation_action", "")}, exec_res)
    _record_trace(session_id, "outcome_agent", "completed", 
                  exec_res, out_res)
                  
    return {
        "action_execution": exec_res.get("action_execution", {}),
        "outcome_learning": out_res.get("outcome_learning", {})
    }


# Compile StateGraph with memory checkpointer
workflow = StateGraph(dict)

# Add nodes
workflow.add_node("planner_node", planner_node)
workflow.add_node("analysis_node", analysis_node)
workflow.add_node("decision_node", decision_node)
workflow.add_node("action_execution_node", action_execution_node)

# Set edges
workflow.add_edge(START, "planner_node")
workflow.add_edge("planner_node", "analysis_node")
workflow.add_edge("analysis_node", "decision_node")
workflow.add_edge("decision_node", "action_execution_node")
workflow.add_edge("action_execution_node", END)

# Interrupt before execution to support human verification/approval (HITL)
checkpointer = MemorySaver()
graph = workflow.compile(
    checkpointer=checkpointer,
    interrupt_before=["action_execution_node"]
)
print("[AgentExecutor] LangGraph orchestration compiled with interrupt before action_execution_node.")

