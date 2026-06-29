"""
Opportunity Agent
=================
Identifies upsell, cross-sell, and training opportunities
based on customer data using tools.

Refactored: Uses usage_analysis_tool and customer_history_tool.
No direct database or file access.
"""

from typing import Any, Dict, List

from agents.base_agent import BaseAgent
from tools.usage_analysis_tool import analyze_usage_metrics
from tools.customer_history_tool import get_customer_history


class OpportunityAgent(BaseAgent):
    """
    Finds upsell, cross-sell, training, and expansion opportunities
    by invoking usage_analysis and customer_history tools.
    """

    def __init__(self):
        super().__init__(
            name="opportunity_agent",
            description="Finds upsell, cross-sell, training, and expansion opportunities using tools.",
            tools=[analyze_usage_metrics, get_customer_history]
        )

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute opportunity detection.

        Args:
            state: Should contain 'customer_summary' and 'knowledge'.
                   Falls back to tool calls if customer_summary is incomplete.

        Returns:
            Dict with 'opportunities' key.
        """
        customer_id = state.get("customer_id", "C001")
        customer_summary = state.get("customer_summary", {})
        knowledge_docs = state.get("knowledge", {})

        # Enrich customer_summary via tool call if it is incomplete
        if not customer_summary or not customer_summary.get("dashboard_usage_pct"):
            try:
                usage = analyze_usage_metrics.invoke({"customer_id": customer_id})
                if usage:
                    customer_summary = {**customer_summary, **usage}
            except Exception as e:
                print(f"[OpportunityAgent] Tool call failed: {e}")

        result = _find(customer_summary, knowledge_docs)
        return {"opportunities": result}


def _find(customer_summary: dict, knowledge_docs: dict) -> dict:
    """
    Find business opportunities for a customer.

    Args:
        customer_summary: CustomerSummary dict from customer_agent
        knowledge_docs: KnowledgeAgent dict from knowledge_agent

    Returns:
        dict matching OpportunityAgent schema
    """
    opportunities = []

    plan = customer_summary.get("plan")
    plan_str = str(plan).strip().title() if plan is not None else ""

    # Rule 1: dashboard_usage_pct < 50 -> Analytics Training opportunity
    dashboard_usage_pct = customer_summary.get("dashboard_usage_pct")
    if dashboard_usage_pct is not None:
        try:
            usage = int(dashboard_usage_pct)
            if usage < 50:
                opportunities.append({
                    "type": "Training",
                    "item": "Analytics Training",
                    "rationale": f"Dashboard adoption is at {usage}% (below 50%). Analytics training can improve product adoption and ROI."
                })
        except (ValueError, TypeError):
            pass

    # Rule 2: Active users / licensed users < 0.7 AND plan != Enterprise
    active_users = customer_summary.get("active_users")
    licensed_users = customer_summary.get("licensed_users")
    if active_users is not None and licensed_users is not None:
        try:
            active = int(active_users)
            licensed = int(licensed_users)
            if licensed > 0 and (active / licensed) < 0.7 and plan_str != "Enterprise":
                opportunities.append({
                    "type": "Cross Sell",
                    "item": "Training Program",
                    "rationale": "Active users are below 70% of licensed users. Training can improve product adoption."
                })
        except (ValueError, TypeError):
            pass

    # Rule 3: health_score > 70 AND plan != Enterprise
    health_score = customer_summary.get("health_score")
    if health_score is not None:
        try:
            health = int(health_score)
            if health > 70 and plan_str != "Enterprise":
                opportunities.append({
                    "type": "Upsell",
                    "item": "Enterprise Plan",
                    "rationale": "Healthy customer with high adoption is a strong Enterprise upgrade candidate."
                })
        except (ValueError, TypeError):
            pass

    # Rule 4: open_support_tickets > 3
    open_support_tickets = customer_summary.get("open_support_tickets")
    if open_support_tickets is not None:
        try:
            tickets = int(open_support_tickets)
            if tickets > 3:
                opportunities.append({
                    "type": "Support",
                    "item": "Premium Support Package",
                    "rationale": "Customer has multiple open support tickets and may benefit from premium support."
                })
        except (ValueError, TypeError):
            pass

    return {
        "opportunities": opportunities
    }


# ── Module-level backward-compatible function ─────────────────────────────────

def find(customer_summary: dict, knowledge_docs: dict) -> dict:
    """Backward-compatible wrapper."""
    return _find(customer_summary, knowledge_docs)
