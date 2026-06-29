"""
Customer Agent
==============
Retrieves and aggregates customer profile and usage data from the SQL database
using reusable LangChain tools.

Refactored: Uses crm_tool and usage_analysis_tool. No direct file or DB access.
"""

from typing import Any, Dict, List

from agents.base_agent import BaseAgent
from tools.crm_tool import get_crm_details
from tools.usage_analysis_tool import analyze_usage_metrics


class CustomerAgent(BaseAgent):
    """
    Retrieves and aggregates customer profile and usage data
    using registered LangChain tools.
    """

    def __init__(self):
        super().__init__(
            name="customer_agent",
            description="Retrieves customer profile, usage metrics, and CRM data using tools.",
            tools=[get_crm_details, analyze_usage_metrics]
        )

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute customer data retrieval using tools.

        Args:
            state: Must contain 'customer_id'.

        Returns:
            Dict with 'customer_summary' key containing the aggregated details.
        """
        customer_id = state.get("customer_id", "C001")
        try:
            # 1. Fetch CRM details using the crm_tool
            crm_res = get_crm_details.invoke({"customer_id": customer_id})

            # 2. Fetch usage metrics using the usage_analysis_tool
            usage_res = analyze_usage_metrics.invoke({"customer_id": customer_id})

            # 3. Aggregate details
            summary = {
                "customer_id": customer_id,
                "company": crm_res.get("company", ""),
                "plan": crm_res.get("plan", ""),
                "industry": crm_res.get("industry", ""),
                "renewal_date": crm_res.get("renewal_date", ""),
                "days_to_renewal": usage_res.get("days_to_renewal", 0),
                "health_score": crm_res.get("health_score", 0),
                "licensed_users": usage_res.get("licensed_users", 0),
                "active_users": usage_res.get("active_users", 0),
                "dashboard_usage_pct": usage_res.get("dashboard_usage_pct", 0),
                "api_calls": usage_res.get("api_calls", 0),
                "open_support_tickets": crm_res.get("open_support_tickets", 0),
                "owner": crm_res.get("owner", "")
            }
            return {"customer_summary": summary}
        except Exception as e:
            print(f"[CustomerAgent] Failed: {e}")
            return {"customer_summary": {}}


# ── Module-level backward-compatible function ─────────────────────────────────

def get_summary(customer_id: str) -> dict:
    """Backward-compatible wrapper. Calls tools directly."""
    crm_res = get_crm_details.invoke({"customer_id": customer_id})
    usage_res = analyze_usage_metrics.invoke({"customer_id": customer_id})
    return {
        "customer_id": customer_id,
        "company": crm_res.get("company", ""),
        "plan": crm_res.get("plan", ""),
        "industry": crm_res.get("industry", ""),
        "renewal_date": crm_res.get("renewal_date", ""),
        "days_to_renewal": usage_res.get("days_to_renewal", 0),
        "health_score": crm_res.get("health_score", 0),
        "licensed_users": usage_res.get("licensed_users", 0),
        "active_users": usage_res.get("active_users", 0),
        "dashboard_usage_pct": usage_res.get("dashboard_usage_pct", 0),
        "api_calls": usage_res.get("api_calls", 0),
        "open_support_tickets": crm_res.get("open_support_tickets", 0),
        "owner": crm_res.get("owner", "")
    }
