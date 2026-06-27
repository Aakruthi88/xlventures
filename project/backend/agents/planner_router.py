"""
Planner Router
==============
Dynamically selects which specialized agents should execute
based on the customer transcript content.

Strategy:
1. Try Ollama (Llama 3.1) for intelligent routing
2. Fallback to keyword-based heuristic routing if Ollama unavailable

Phase 5: Hybrid routing (LLM + rules).
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.llm import query_llm_json, check_ollama_available

# Valid agent names for routing
VALID_AGENTS = [
    "customer_agent",
    "knowledge_agent",
    "sentiment_agent",
    "risk_agent",
    "opportunity_agent",
]

# Agents that ALWAYS run regardless of routing decision
MANDATORY_AGENTS = [
    "recommendation_agent",
    "explanation_agent",
]


def route_with_llm(transcript_text: str) -> dict:
    """
    Use Ollama Llama 3.1 to analyze the transcript and select agents.

    Returns:
        dict with "agents" list and "reasoning" string, or empty dict on failure
    """
    system_prompt = """You are a routing agent for a Customer Success platform.
Analyze the customer transcript and return a JSON list of required agents.

Available agents:
- customer_agent: Retrieves customer profile and usage data.
- knowledge_agent: Searches product playbooks/integration guides. Run if integration, SAP, sync, API, or compliance is mentioned.
- sentiment_agent: Analyzes tone. Run if frustration, concerns, slow, happy, or angry feelings are shown.
- risk_agent: Identifies churn risks. Run if renewal, competitors, cancel, or budget is mentioned.
- opportunity_agent: Finds training/upsell opportunities. Run if training, adoption, dashboard, or expansion is mentioned.

Few-Shot Example:
Transcript: "SAP sync is slow. Our renewal is in 10 days and VP is looking at competitors. Analytics adoption is low."
Output:
{
    "agents": ["customer_agent", "knowledge_agent", "sentiment_agent", "risk_agent", "opportunity_agent"],
    "reasoning": "Detected slow SAP integration (knowledge, sentiment), upcoming renewal and competitors (risk), and low adoption (opportunity)."
}

Respond with valid JSON only. No markdown fences. No other text."""

    user_prompt = f"""Analyze this transcript and select the required agents:
"{transcript_text}"

Return JSON matching the format:
{{
    "agents": ["agent_name_1", "agent_name_2"],
    "reasoning": "why"
}}"""

    result = query_llm_json(user_prompt, system_prompt)

    if result and "agents" in result:
        # Validate agent names
        valid_selected = [a for a in result["agents"] if a in VALID_AGENTS]
        if valid_selected:
            return {
                "agents": valid_selected,
                "reasoning": result.get("reasoning", "LLM-selected agents")
            }

    return {}


def route_with_rules(transcript_text: str) -> dict:
    """
    Keyword-based heuristic routing fallback.
    Scans transcript for known trigger words and selects agents accordingly.

    Returns:
        dict with "agents" list and "reasoning" string
    """
    text = transcript_text.lower()
    agents = set()
    reasons = []

    # Always include customer_agent for context
    agents.add("customer_agent")
    reasons.append("customer_agent: always included for customer context")

    # Risk agent triggers
    risk_keywords = ["renewal", "renew", "contract", "competitor", "bamboohr",
                     "workday", "peopleforce", "churn", "cancel", "budget",
                     "cost", "expensive", "risk", "leave", "switch"]
    if any(kw in text for kw in risk_keywords):
        agents.add("risk_agent")
        matched = [kw for kw in risk_keywords if kw in text]
        reasons.append(f"risk_agent: detected [{', '.join(matched[:3])}]")

    # Knowledge agent triggers
    knowledge_keywords = ["integration", "sap", "api", "sync", "technical",
                          "configuration", "setup", "compliance", "audit",
                          "training", "onboarding", "documentation"]
    if any(kw in text for kw in knowledge_keywords):
        agents.add("knowledge_agent")
        matched = [kw for kw in knowledge_keywords if kw in text]
        reasons.append(f"knowledge_agent: detected [{', '.join(matched[:3])}]")

    # Sentiment agent triggers
    sentiment_keywords = ["frustrated", "slow", "unhappy", "angry", "concerned",
                          "disappointed", "worried", "painful", "rough",
                          "struggling", "love", "amazing", "great", "happy",
                          "impressed", "excellent"]
    if any(kw in text for kw in sentiment_keywords):
        agents.add("sentiment_agent")
        matched = [kw for kw in sentiment_keywords if kw in text]
        reasons.append(f"sentiment_agent: detected [{', '.join(matched[:3])}]")

    # Opportunity agent triggers
    opportunity_keywords = ["usage", "adoption", "dashboard", "expand",
                            "new center", "new office", "growth", "upgrade",
                            "enterprise", "feature", "analytics", "upsell",
                            "training"]
    if any(kw in text for kw in opportunity_keywords):
        agents.add("opportunity_agent")
        matched = [kw for kw in opportunity_keywords if kw in text]
        reasons.append(f"opportunity_agent: detected [{', '.join(matched[:3])}]")

    # If nothing matched, run all analysis agents as safe default
    if len(agents) <= 1:
        agents = set(VALID_AGENTS)
        reasons = ["No specific triggers detected - running all agents as safety default"]

    return {
        "agents": list(agents),
        "reasoning": "; ".join(reasons)
    }


def route_agents(transcript_text: str) -> dict:
    """
    Main routing function. Tries LLM first, falls back to rules.

    Args:
        transcript_text: The customer meeting transcript

    Returns:
        dict with:
            "agents": List of selected agent names
            "reasoning": Explanation of routing decision
            "method": "llm" or "rules"
    """
    # Try LLM routing first (if Ollama is available)
    if check_ollama_available():
        print("[Router] Attempting LLM-based routing via Ollama...")
        llm_result = route_with_llm(transcript_text)
        if llm_result:
            print(f"[Router] LLM selected agents: {llm_result['agents']}")
            print(f"[Router] LLM reasoning: {llm_result['reasoning']}")
            return {
                "agents": llm_result["agents"],
                "reasoning": llm_result["reasoning"],
                "method": "llm"
            }
        print("[Router] LLM routing failed, falling back to rules...")

    # Fallback: rule-based routing
    rules_result = route_with_rules(transcript_text)
    print(f"[Router] Rule-based selected agents: {rules_result['agents']}")
    print(f"[Router] Rule-based reasoning: {rules_result['reasoning']}")
    return {
        "agents": rules_result["agents"],
        "reasoning": rules_result["reasoning"],
        "method": "rules"
    }
