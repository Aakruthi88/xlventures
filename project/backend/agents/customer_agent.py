"""
Customer Agent
==============
Retrieves and aggregates customer data from multiple sources
(customers.csv, usage.csv, crm.json, support_tickets.csv).

Phase 3: Returns hardcoded mock data.
Phase 6: Will load real data from CSV/JSON files.
"""


def get_summary(customer_id: str) -> dict:
    """
    Get a unified customer summary by aggregating data from
    customers.csv, usage.csv, crm.json, and support_tickets.csv.

    Args:
        customer_id: The customer identifier (e.g., "C001")

    Returns:
        dict matching CustomerSummary schema
    """
    # Phase 3: Mock response
    return {
        "customer_id": "C001",
        "company": "ABC Manufacturing",
        "plan": "Growth",
        "industry": "Manufacturing",
        "renewal_date": "2026-07-17",
        "days_to_renewal": 20,
        "health_score": 42,
        "licensed_users": 500,
        "active_users": 160,
        "dashboard_usage_pct": 32,
        "api_calls": 15000,
        "open_support_tickets": 7,
        "owner": "Sarah Mitchell"
    }
