"""
CRM Tool
========
LangChain tool to fetch customer profile and account manager details.
"""

from typing import Any, Dict
from langchain.tools import tool
from database.repository import get_customer_by_id


@tool
def get_crm_details(customer_id: str) -> Dict[str, Any]:
    """
    Fetch customer profile details from the CRM database including company name,
    plan type, industry, account health score, open support tickets, and assigned owner.

    Args:
        customer_id: Unique customer ID (e.g., 'C001').

    Returns:
        A dictionary containing CRM record fields, or an empty dictionary if not found.
    """
    try:
        details = get_customer_by_id(customer_id)
        if details:
            return {
                "customer_id": details.get("customer_id"),
                "company": details.get("company"),
                "plan": details.get("plan"),
                "industry": details.get("industry"),
                "health_score": details.get("health_score"),
                "open_support_tickets": details.get("support_tickets_open"),
                "owner": details.get("customer_owner"),
                "renewal_date": details.get("renewal_date")
            }
    except Exception as e:
        print(f"[CRM Tool] Error: {e}")

    return {}
