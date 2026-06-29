"""
Recommendation Agent (Decision Agent)
=====================================
Generates next-best-action recommendations by synthesizing
insights from all other agents using LLM reasoning.

Refactored: Uses crm_tool and customer_history_tool.
No direct database access.
"""

from dotenv import load_dotenv
import os
import json
from typing import Any, Dict, List

from agents.base_agent import BaseAgent
from tools.crm_tool import get_crm_details
from tools.customer_history_tool import get_customer_history

# Load environment variables (Task 1)
# Try loading from the current working directory first
load_dotenv()

# Also try loading explicitly from the backend directory where this file resides to prevent path issues
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
explicit_dotenv_path = os.path.join(backend_dir, ".env")
if os.path.exists(explicit_dotenv_path):
    load_dotenv(dotenv_path=explicit_dotenv_path)

# Initialize Groq API configurations
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


# ============================================================
# FALLBACK STRUCTURE (Task 6)
# ============================================================
def get_fallback_recommendations() -> dict:
    """
    Fallback helper function returning mock recommendations and explanations if the LLM fails.

    Returns:
        dict: A dictionary containing the mock recommendations and explanations matching the contract.
    """
    return {
        "recommendations": [
            {
                "id": "REC001",
                "action": "Schedule analytics training session for ABC Manufacturing team",
                "priority": "High",
                "confidence": 0.91
            },
            {
                "id": "REC002",
                "action": "Escalate SAP integration issues to engineering team with priority fix",
                "priority": "High",
                "confidence": 0.88
            },
            {
                "id": "REC003",
                "action": "Initiate executive sponsor outreach before renewal deadline",
                "priority": "High",
                "confidence": 0.85
            },
            {
                "id": "REC004",
                "action": "Prepare competitive comparison document addressing BambooHR and Workday",
                "priority": "Medium",
                "confidence": 0.79
            }
        ],
        "explanations": [
            {
                "recommendation_id": "REC001",
                "reason": "Improve product adoption before renewal to demonstrate ROI",
                "evidence": [
                    "Health score is 42 (below 50 threshold)",
                    "Dashboard usage at 32% (below 40% training trigger per renewal playbook)",
                    "Renewal in 20 days - urgent timeline",
                    "Transcript: team exports to Excel instead of using dashboards"
                ],
                "confidence": 0.91
            },
            {
                "recommendation_id": "REC002",
                "reason": "Resolve critical integration blocker affecting daily operations",
                "evidence": [
                    "SAP sync takes 20 minutes daily per transcript",
                    "Open ticket: SAP integration sync failing intermittently",
                    "Integration guide: schedule sync outside peak hours, break into 200-record batches",
                    "API rate limit errors reported during payroll processing"
                ],
                "confidence": 0.88
            },
            {
                "recommendation_id": "REC003",
                "reason": "High-risk account requires executive engagement per escalation matrix",
                "evidence": [
                    "Health score 42 + renewal in 20 days triggers Tier 3 escalation per SOP",
                    "Customer champion (Priya Sharma) departed in April",
                    "Customer VP evaluating competitors (BambooHR, Workday)",
                    "QBR postponed twice - disengagement signal"
                ],
                "confidence": 0.85
            },
            {
                "recommendation_id": "REC004",
                "reason": "Counter competitive threat with targeted comparison",
                "evidence": [
                    "Transcript: management considering BambooHR and Workday",
                    "Customer success SOP: prepare tailored competitive comparison",
                    "Focus on platform strengths in manufacturing compliance reporting"
                ],
                "confidence": 0.79
            }
        ]
    }


def _generate(customer_summary: dict, risks: dict, opportunities: dict,
              sentiment: dict, knowledge_docs: dict,
              past_approvals: list = None) -> dict:
    """
    Generate next-best-action recommendations for a customer using Groq LLM.

    Args:
        customer_summary: CustomerSummary dict from customer_agent
        risks: RiskAgent dict from risk_agent
        opportunities: OpportunityAgent dict from opportunity_agent
        sentiment: SentimentAgent dict from sentiment_agent
        knowledge_docs: KnowledgeAgent dict from knowledge_agent
        past_approvals: List of previously approved recommendations (optional)

    Returns:
        dict matching RecommendationAgent schema (containing recommendations and explanations)
    """
    # Verify that the Groq API key is present
    if not GROQ_API_KEY:
        print("[RecommendationAgent] Warning: GROQ_API_KEY environment variable is not set. Using fallback.")
        return get_fallback_recommendations()

    try:
        from groq import Groq

        # Initialize Groq client
        client = Groq(api_key=GROQ_API_KEY)

        # Format prompt inputs as serialized JSON
        customer_json = json.dumps(customer_summary, indent=2)
        risks_json = json.dumps(risks, indent=2)
        opportunities_json = json.dumps(opportunities, indent=2)
        sentiment_json = json.dumps(sentiment, indent=2)
        knowledge_json = json.dumps(knowledge_docs, indent=2)
        past_approvals_json = json.dumps(past_approvals if past_approvals is not None else [], indent=2)

        # Construct the user prompt using the requested template
        prompt = (
            "You are a Customer Success Decision Agent.\n\n"
            f"Customer: {customer_json}\n\n"
            f"Risks: {risks_json}\n\n"
            f"Opportunities: {opportunities_json}\n\n"
            f"Sentiment: {sentiment_json}\n\n"
            f"Knowledge base excerpts: {knowledge_json}\n\n"
            f"Past approved actions: {past_approvals_json}\n\n"
            "Recommend 3–5 next best actions grounded ONLY in the information provided.\n"
            "Do NOT invent facts.\n\n"
            "For every recommendation provide:\n"
            "* id\n"
            "* action\n"
            "* priority\n"
            "* confidence\n\n"
            "Also provide:\n"
            "* recommendation_id\n"
            "* reason\n"
            "* evidence (2–4 concrete facts from the supplied inputs)\n"
            "* confidence\n\n"
            "Return ONLY valid JSON."
        )

        # Construct system instructions to enforce JSON output format and structure
        system_instruction = (
            "You are a Customer Success Decision Agent. You must output ONLY a valid JSON object matching the following structure:\n"
            "{\n"
            "  \"recommendations\": [\n"
            "    {\n"
            "      \"id\": \"REC001\",\n"
            "      \"action\": \"Action description\",\n"
            "      \"priority\": \"High\",\n"
            "      \"confidence\": 0.95\n"
            "    }\n"
            "  ],\n"
            "  \"explanations\": [\n"
            "    {\n"
            "      \"recommendation_id\": \"REC001\",\n"
            "      \"reason\": \"Reason description\",\n"
            "      \"evidence\": [\n"
            "        \"Concrete evidence 1\",\n"
            "        \"Concrete evidence 2\"\n"
            "      ],\n"
            "      \"confidence\": 0.95\n"
            "    }\n"
            "  ]\n"
            "}"
        )

        print(f"[RecommendationAgent] Calling Groq API with model: {MODEL_NAME}")

        # Execute exactly one LLM call
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            model=MODEL_NAME,
            temperature=0.0,  # Zero temperature for factual correctness and grounding
            response_format={"type": "json_object"}
        )

        # Retrieve response text
        response_text = response.choices[0].message.content
        if not response_text:
            raise ValueError("Groq API returned an empty completion content.")

        # Clean the response text (strip markdown fences if present)
        cleaned = response_text.strip()
        if "```json" in cleaned:
            start = cleaned.index("```json") + 7
            end = cleaned.index("```", start)
            cleaned = cleaned[start:end].strip()
        elif "```" in cleaned:
            start = cleaned.index("```") + 3
            end = cleaned.index("```", start)
            cleaned = cleaned[start:end].strip()

        # Isolate the outermost curly braces of the JSON object
        brace_start = cleaned.find("{")
        brace_end = cleaned.rfind("}") + 1
        if brace_start >= 0 and brace_end > brace_start:
            cleaned = cleaned[brace_start:brace_end]

        # Safely parse JSON
        data = json.loads(cleaned)

        # Validate that the keys required by the JSON contract are present
        if not isinstance(data, dict) or "recommendations" not in data or "explanations" not in data:
            raise ValueError("Parsed JSON is missing 'recommendations' or 'explanations' keys")

        if not isinstance(data["recommendations"], list) or not isinstance(data["explanations"], list):
            raise ValueError("'recommendations' or 'explanations' structure is not a list")

        return data

    except Exception as e:
        # Gracefully log/print error and return fallback recommendations matching the expected schema
        print(f"[RecommendationAgent] Exception occurred during generation or parsing: {e}")
        print("[RecommendationAgent] Returning fallback recommendations and explanations...")
        return get_fallback_recommendations()


class RecommendationAgent(BaseAgent):
    """
    Generates next-best-action recommendations by synthesizing
    insights from all other agents using LLM reasoning.
    """

    def __init__(self):
        super().__init__(
            name="recommendation_agent",
            description="Generates next-best-action recommendations by synthesizing all agent insights.",
            tools=[get_crm_details, get_customer_history]
        )

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute recommendation generation.

        Args:
            state: Should contain outputs from analysis agents and 'customer_id'.

        Returns:
            Dict with 'recommendations' key.
        """
        # Import memory_agent here to avoid circular imports at module load
        from agents import memory_agent

        customer_id = state.get("customer_id", "C001")
        past_approvals = memory_agent.get_similar_past_approvals(customer_id)

        result = _generate(
            customer_summary=state.get("customer_summary", {}),
            risks=state.get("risks", {}),
            opportunities=state.get("opportunities", {}),
            sentiment=state.get("sentiment", {}),
            knowledge_docs=state.get("knowledge", {}),
            past_approvals=past_approvals
        )
        return {"recommendations": result}


# ── Module-level backward-compatible function ─────────────────────────────────

def generate(customer_summary: dict, risks: dict, opportunities: dict,
             sentiment: dict, knowledge_docs: dict,
             past_approvals: list = None) -> dict:
    """Backward-compatible wrapper."""
    return _generate(customer_summary, risks, opportunities,
                     sentiment, knowledge_docs, past_approvals)
