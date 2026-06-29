"""
Action Executor Agent
=====================
Executes approved business recommendations by calling appropriate tools.
"""

from typing import Any, Dict
from agents.base_agent import BaseAgent
from tools.send_email_tool import send_email
from tools.create_crm_task_tool import create_crm_task
from tools.notify_owner_tool import notify_owner


class ActionExecutorAgent(BaseAgent):
    """
    Executes approved recommendations using mock business execution tools.
    """

    def __init__(self):
        super().__init__(
            name="action_executor_agent",
            description="Executes approved business actions (sending emails, assigning CRM tasks, raising alerts).",
            tools=[send_email, create_crm_task, notify_owner]
        )

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the approved action.

        Args:
            state: Should contain 'approval_decision' with 'recommendation_action' and 'customer_summary'.

        Returns:
            Dict with execution result status and details.
        """
        approval = state.get("approval_decision", {})
        customer_summary = state.get("customer_summary", {})
        customer_id = state.get("customer_id", "C001")
        owner = customer_summary.get("owner", "csm@xlventures.com")

        # Resolve the specific action text to execute
        action_text = approval.get("recommendation_action", "")
        if not action_text:
            action_text = state.get("recommendations", {}).get("recommendations", [{}])[0].get("action", "")

        action_lower = action_text.lower()
        result_desc = "No matching execution tool triggered."

        try:
            # Route to correct tool based on action description keywords
            if "email" in action_lower:
                # Trigger send_email tool
                res = send_email.invoke({
                    "to_address": owner,
                    "subject": f"Action Required: {action_text[:50]}",
                    "body": f"Please follow up on: {action_text} for customer {customer_id}"
                })
                result_desc = res.get("action", "Simulated email sent successfully.")
            elif "task" in action_lower or "schedule" in action_lower or "training" in action_lower:
                # Trigger create_crm_task tool
                res = create_crm_task.invoke({
                    "customer_id": customer_id,
                    "task_name": action_text,
                    "due_date": "Next Week",
                    "assignee": owner
                })
                result_desc = res.get("action", "Simulated CRM task created.")
            else:
                # Trigger notify_owner alert tool
                res = notify_owner.invoke({
                    "owner": owner,
                    "customer_id": customer_id,
                    "alert_message": action_text
                })
                result_desc = res.get("action", "Simulated account owner notification sent.")

            return {
                "action_execution": {
                    "status": "success",
                    "action": result_desc
                }
            }
        except Exception as e:
            print(f"[ActionExecutorAgent] Execution failed: {e}")
            return {
                "action_execution": {
                    "status": "failed",
                    "action": f"Failed to execute action: {e}"
                }
            }
