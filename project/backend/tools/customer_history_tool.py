"""
Customer History Tool
=====================
LangChain tool to fetch historical actions and approvals for a customer.
"""

from typing import List, Dict, Any
from langchain.tools import tool
from database.repository import get_approvals_by_customer


@tool
def get_customer_history(customer_id: str) -> List[Dict[str, Any]]:
    """
    Fetch the list of historical recommendations that were approved by customer success managers
    for this customer. Returns them ordered by approval timestamp, newest first.

    Args:
        customer_id: Unique customer ID (e.g., 'C001').

    Returns:
        List of approved recommendation dictionaries containing: action description,
        priority, confidence score, and approved timestamp.
    """
    try:
        return get_approvals_by_customer(customer_id)
    except Exception as e:
        print(f"[Customer History Tool] Error: {e}")
        return []
