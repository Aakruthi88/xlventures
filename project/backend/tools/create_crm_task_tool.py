"""
Create CRM Task Tool
====================
LangChain tool to simulate adding a task in the CRM system.
"""

from typing import Dict, Any
from langchain.tools import tool


@tool
def create_crm_task(customer_id: str, task_name: str, due_date: str, assignee: str) -> Dict[str, Any]:
    """
    Simulates creating a CRM task entry for account managers or CSMs.

    Args:
        customer_id: Customer ID.
        task_name: Description of the task.
        due_date: Due date for the task.
        assignee: Staff member assigned to the task.

    Returns:
        Status dict indicating success.
    """
    print(f"\n>>> [SIMULATED CRM TASK CREATED] Customer: {customer_id}\n>>> Task: {task_name}\n>>> Assignee: {assignee}\n")
    return {
        "status": "success",
        "action": f"CRM Task '{task_name}' created for {assignee} (Due: {due_date})"
    }
