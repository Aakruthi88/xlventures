"""
Notify Owner Tool
=================
LangChain tool to simulate notifying a customer account owner.
"""

from typing import Dict, Any
from langchain.tools import tool


@tool
def notify_owner(owner: str, customer_id: str, alert_message: str) -> Dict[str, Any]:
    """
    Simulates notifying the owner of a customer account about critical updates or risks.

    Args:
        owner: Assignee account owner email or username.
        customer_id: Customer ID.
        alert_message: Message description of the alert.

    Returns:
        Status dict indicating success.
    """
    print(f"\n>>> [SIMULATED OWNER NOTIFIED] Owner: {owner}\n>>> Customer: {customer_id}\n>>> Alert: {alert_message}\n")
    return {
        "status": "success",
        "action": f"Owner {owner} notified of alert for {customer_id}"
    }
