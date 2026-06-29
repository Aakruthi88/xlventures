"""
Risk Agent
==========
Identifies and assesses risks based on customer data, sentiment,
and knowledge base context using rule-based logic.

Refactored: Uses usage_analysis_tool and customer_history_tool.
No direct database or file access.
"""

from typing import Any, Dict, List

from agents.base_agent import BaseAgent
from tools.usage_analysis_tool import analyze_usage_metrics
from tools.customer_history_tool import get_customer_history


class RiskAgent(BaseAgent):
    """
    Identifies churn risks, renewal risks, and competitive threats
    by invoking usage_analysis and customer_history tools.
    """

    def __init__(self):
        super().__init__(
            name="risk_agent",
            description="Identifies churn risks, renewal risks, and competitive threats using tools.",
            tools=[analyze_usage_metrics, get_customer_history]
        )

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute risk assessment.

        Args:
            state: Should contain 'customer_summary', 'sentiment', 'knowledge'.
                   Falls back to tool calls if customer_summary is incomplete.

        Returns:
            Dict with 'risks' key.
        """
        customer_id = state.get("customer_id", "C001")
        customer_summary = state.get("customer_summary", {})
        sentiment = state.get("sentiment", {})
        knowledge_docs = state.get("knowledge", {})

        # Enrich customer_summary via tool call if it is incomplete
        if not customer_summary or not customer_summary.get("health_score"):
            try:
                usage = analyze_usage_metrics.invoke({"customer_id": customer_id})
                if usage:
                    customer_summary = {**customer_summary, **usage}
            except Exception as e:
                print(f"[RiskAgent] Tool call failed: {e}")

        result = _assess(customer_summary, sentiment, knowledge_docs)
        return {"risks": result}


def _assess(customer_summary: dict, sentiment: dict, knowledge_docs: dict) -> dict:
    """
    Assess risks for a customer based on their summary, sentiment, and KB context.

    Args:
        customer_summary: CustomerSummary dict from customer_agent
        sentiment: SentimentAgent dict from sentiment_agent
        knowledge_docs: KnowledgeAgent dict from knowledge_agent

    Returns:
        dict matching RiskAgent schema
    """
    risks = []

    health_score = customer_summary.get("health_score")

    # 1. Renewal Risk: If days_to_renewal <= 30
    days_to_renewal = customer_summary.get("days_to_renewal")
    if days_to_renewal is not None:
        try:
            days = int(days_to_renewal)
            if days <= 30:
                severity = "High" if days <= 15 else "Medium"
                health_part = ""
                if health_score is not None:
                    health_part = f" Health score is {health_score}."
                risks.append({
                    "type": "Renewal Risk",
                    "severity": severity,
                    "evidence": f"Customer contract renewal is approaching in {days} days.{health_part}"
                })
        except (ValueError, TypeError):
            pass

    # 2. Low Adoption Risk: If dashboard_usage_pct < 50
    dashboard_usage_pct = customer_summary.get("dashboard_usage_pct")
    if dashboard_usage_pct is not None:
        try:
            usage = int(dashboard_usage_pct)
            if usage < 50:
                risks.append({
                    "type": "Low Adoption",
                    "severity": "Medium",
                    "evidence": f"Low platform adoption: dashboard usage is currently at {usage}% (below 50% threshold)."
                })
        except (ValueError, TypeError):
            pass

    # 3. Support Risk: If open_support_tickets > 5
    open_support_tickets = customer_summary.get("open_support_tickets")
    if open_support_tickets is not None:
        try:
            tickets = int(open_support_tickets)
            if tickets > 5:
                risks.append({
                    "type": "Support Risk",
                    "severity": "High",
                    "evidence": f"High support volume: client has {tickets} open support tickets."
                })
        except (ValueError, TypeError):
            pass

    # 4. High Churn Risk: If sentiment is "Negative" or "Urgent"
    sentiment_val = sentiment.get("sentiment")
    if sentiment_val:
        sentiment_str = str(sentiment_val).strip().title()
        if sentiment_str in ["Negative", "Urgent"]:
            risks.append({
                "type": "High Churn",
                "severity": "High",
                "evidence": f"Elevated churn indicator: customer meeting transcript exhibits {sentiment_str} sentiment."
            })

    # Determine overall_risk
    severities = {r["severity"] for r in risks}
    if "High" in severities:
        overall_risk = "High"
    elif "Medium" in severities:
        overall_risk = "Medium"
    else:
        overall_risk = "Low"

    return {
        "risks": risks,
        "overall_risk": overall_risk
    }


# ── Module-level backward-compatible function ─────────────────────────────────

def assess(customer_summary: dict, sentiment: dict, knowledge_docs: dict) -> dict:
    """Backward-compatible wrapper."""
    return _assess(customer_summary, sentiment, knowledge_docs)
