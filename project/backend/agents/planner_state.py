"""
Planner State
=============
Shared LangGraph state definition used by all planner nodes.
TypedDict ensures type safety across the workflow graph.
"""

from typing import TypedDict, List, Dict, Any


class AgentState(TypedDict):
    """
    Shared state that flows through the LangGraph planner workflow.

    Each node reads from and writes to this state dict.
    LangGraph merges each node's returned dict into this state.
    """
    # Session context (set by load_context node)
    session_id: str
    customer_id: str
    transcript_text: str

    # Dynamic routing decision (set by planner_router node)
    selected_agents: List[str]
    routing_reasoning: str

    # Agent outputs (set by individual agent nodes)
    customer_summary: Dict[str, Any]
    knowledge: Dict[str, Any]
    sentiment: Dict[str, Any]
    risks: Dict[str, Any]
    opportunities: Dict[str, Any]
    recommendations: Dict[str, Any]
    explanations: Dict[str, Any]
