"""
Planner Agent
=============
Analyzes customer interaction input, understands the business goal,
and dynamically decides which agents/tools are required.

Uses the local Ollama LLM for intelligent reasoning. Falls back to
a comprehensive default plan when the LLM is unavailable or returns
unparsable output.
"""

import json
from typing import Any, Dict, List

from agents.base_agent import BaseAgent
from agents.llm import query_llm_json, check_ollama_available


class PlannerAgent(BaseAgent):
    """
    Planner Agent that generates a dynamic execution plan.

    Responsibilities:
        - Analyze the customer transcript.
        - Understand the business goal.
        - Decide which agents/tools are required and why.
        - Output a structured execution plan as JSON.
    """

    def __init__(self):
        super().__init__(
            name="planner_agent",
            description="Analyzes customer interactions and generates a dynamic execution plan selecting required agents.",
            tools=[]
        )

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate an execution plan based on the transcript and semantic past cases.

        Args:
            state: Must contain 'transcript_text' and 'customer_id'.

        Returns:
            Dict with 'plan' key containing the structured plan JSON.
        """
        transcript_text = state.get("transcript_text", "")
        customer_id = state.get("customer_id", "")

        # Retrieve similar past cases from MemoryAgent
        from agents.memory_agent import get_similar_past_cases
        past_cases = get_similar_past_cases(transcript_text)
        state["past_cases"] = past_cases

        plan = self._plan_with_llm(transcript_text, customer_id, past_cases)
        if not plan:
            plan = self._fallback_plan(transcript_text, customer_id)

        print(f"[PlannerAgent] Goal: {plan.get('goal', 'N/A')}")
        print(f"[PlannerAgent] Required agents: {[a['name'] for a in plan.get('required_agents', [])]}")
        print(f"[PlannerAgent] Priority: {plan.get('priority', 'N/A')}")
        if plan.get("missing_information"):
            print(f"[PlannerAgent] Missing info: {plan['missing_information']}")

        return {"plan": plan}

    def _plan_with_llm(self, transcript_text: str, customer_id: str, past_cases: list) -> dict:
        """Use the local LLM to reason about which agents are needed, incorporating past experience."""
        if not check_ollama_available():
            return {}

        system_prompt = """You are a strategic planner agent for a Customer Success Next Best Action Platform.
Your job is to analyze a customer interaction transcript and decide which specialized agents must run.

Available agents (use these exact names):
- customer_agent: Always required for baseline context.
- knowledge_agent: Searches playbooks/integration guides. Run if integration, SAP, sync, API, compliance, or onboarding is mentioned.
- sentiment_agent: Analyzes emotional tone. Run if frustration, concerns, slow, happy, or angry feelings are shown.
- risk_agent: Identifies churn risks. Run if renewal, competitors, cancel, switch, or budget is mentioned.
- opportunity_agent: Finds training/upsell opportunities. Run if training, adoption, dashboard, growth, or expansion is mentioned.

You must output ONLY a valid JSON object matching this exact structure:
{
    "goal": "A concise description of the business objective for this customer interaction",
    "required_agents": [
        {
            "name": "agent_name",
            "reason": "Why this agent is needed for this specific interaction"
        }
    ],
    "priority": "High | Medium | Low",
    "missing_information": ["Any information gaps identified in the transcript"]
}

Respond ONLY with valid JSON. Do not include markdown code blocks, explanation, or extra text."""

        # Format semantic memory past cases as prompt context
        past_cases_str = ""
        if past_cases:
            case_snippets = []
            for c in past_cases:
                case_snippets.append(
                    f"- Similar Scenario: {c.get('similar_case', '')}\n"
                    f"  Action Taken: {c.get('previous_action', '')}\n"
                    f"  Result: {c.get('result', '')}"
                )
            past_cases_str = "\nRelevant Past Cases:\n" + "\n".join(case_snippets)

        # Robust few-shot prompting to guide small local models like qwen2.5:0.5b
        user_prompt = f"""Analyze this customer interaction and select all required agents based on the rules.
{past_cases_str}

Few-Shot Examples:
Transcript: "low analytics adoption, renewal in 20 days, SAP integration is slow, competitors are considered"
Output:
{{
    "goal": "Address renewal risk, improve analytics adoption, and resolve slow SAP integration sync speed",
    "required_agents": [
        {{"name": "customer_agent", "reason": "Retrieve customer profile and usage data for baseline context."}},
        {{"name": "knowledge_agent", "reason": "Search technical docs and guides for slow SAP integration fixes."}},
        {{"name": "sentiment_agent", "reason": "Analyze customer frustration regarding slow sync performance."}},
        {{"name": "risk_agent", "reason": "Assess high risk of churn due to competitor evaluation and close renewal date."}},
        {{"name": "opportunity_agent", "reason": "Address low analytics adoption through training opportunities."}}
    ],
    "priority": "High",
    "missing_information": ["competitors considered", "reasons for slow SAP sync"]
}}

Transcript: "wants training on the new analytics dashboard"
Output:
{{
    "goal": "Coordinate training for the new analytics dashboard to boost feature adoption",
    "required_agents": [
        {{"name": "customer_agent", "reason": "Retrieve customer profile and usage context."}},
        {{"name": "opportunity_agent", "reason": "Coordinate analytics dashboard training program."}}
    ],
    "priority": "Medium",
    "missing_information": ["number of team members to train"]
}}

Now, analyze the following customer interaction:
Customer ID: {customer_id}
Transcript: "{transcript_text}"

Return the JSON execution plan matching the schema exactly:"""

        try:
            result = query_llm_json(user_prompt, system_prompt)
            if result and "required_agents" in result and "goal" in result:
                # Validate agent names
                valid_names = {
                    "customer_agent", "knowledge_agent", "sentiment_agent",
                    "risk_agent", "opportunity_agent"
                }
                validated_agents = [
                    a for a in result["required_agents"]
                    if isinstance(a, dict) and a.get("name") in valid_names
                ]
                if validated_agents:
                    result["required_agents"] = validated_agents
                    # Ensure priority is valid
                    if result.get("priority") not in ("High", "Medium", "Low"):
                        result["priority"] = "Medium"
                    # Ensure missing_information is a list
                    if not isinstance(result.get("missing_information"), list):
                        result["missing_information"] = []
                    result["_method"] = "llm"
                    return result
        except Exception as e:
            print(f"[PlannerAgent] LLM planning failed: {e}")

        return {}

    def _fallback_plan(self, transcript_text: str, customer_id: str) -> dict:
        """
        Generate a comprehensive fallback plan when the LLM is unavailable.
        Runs all analysis agents to ensure nothing is missed.
        """
        return {
            "goal": f"Comprehensive analysis of customer interaction for {customer_id}",
            "required_agents": [
                {"name": "customer_agent", "reason": "Retrieve customer profile and usage data for baseline context."},
                {"name": "knowledge_agent", "reason": "Search enterprise knowledge base for relevant playbooks and guides."},
                {"name": "sentiment_agent", "reason": "Analyze sentiment of the customer interaction."},
                {"name": "risk_agent", "reason": "Identify potential churn and renewal risks."},
                {"name": "opportunity_agent", "reason": "Find upsell, training, and expansion opportunities."},
            ],
            "priority": "Medium",
            "missing_information": [],
            "_method": "fallback"
        }
