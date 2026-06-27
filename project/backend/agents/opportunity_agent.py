"""
Opportunity Agent
=================
Identifies upsell, cross-sell, and engagement opportunities
based on customer data and knowledge base context.

Phase 10: Implements real rule-based opportunity detection.
"""


def find(customer_summary: dict, knowledge_docs: dict) -> dict:
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

    # Rule 1: Active users / licensed users < 0.7 AND plan != Enterprise
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

    # Rule 2: health_score > 70 AND plan != Enterprise
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

    # Rule 3: open_support_tickets > 3
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

    # Rule 4: dashboard_usage_pct < 50
    dashboard_usage_pct = customer_summary.get("dashboard_usage_pct")
    if dashboard_usage_pct is not None:
        try:
            usage = int(dashboard_usage_pct)
            if usage < 50:
                opportunities.append({
                    "type": "Adoption",
                    "item": "Onboarding Refresher",
                    "rationale": "Dashboard adoption is below 50%. Recommend onboarding refresher training."
                })
        except (ValueError, TypeError):
            pass

    return {
        "opportunities": opportunities
    }

