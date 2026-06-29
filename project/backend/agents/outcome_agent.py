"""
Outcome Agent
============
Analyzes whether recommendation actions were successful and logs outcome metrics.
"""

from typing import Any, Dict
from agents.base_agent import BaseAgent
import database.repository as repo


class OutcomeAgent(BaseAgent):
    """
    Analyzes action outcomes, assesses success metrics, and writes records to database.
    """

    def __init__(self):
        super().__init__(
            name="outcome_agent",
            description="Analyzes recommendation effectiveness and logs results in the outcomes database.",
            tools=[]
        )

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze and log recommendation outcomes.

        Args:
            state: Contains 'customer_summary', 'action_execution', 'customer_id', and 'approval_decision'.

        Returns:
            Dict with 'outcome_learning' details.
        """
        customer_id = state.get("customer_id", "C001")
        customer_summary = state.get("customer_summary", {})
        action_execution = state.get("action_execution", {})

        # Resolve action text
        approval = state.get("approval_decision", {})
        action = approval.get("recommendation_action", "")
        if not action:
            action = state.get("recommendations", {}).get("recommendations", [{}])[0].get("action", "General follow up")

        # Capture customer baseline health score
        before_score = customer_summary.get("health_score", 50)

        # Simulate improved score following successful mock execution
        after_score = before_score
        if action_execution.get("status") == "success":
            # Simulate a 10-15 point health improvement for demo
            after_score = min(before_score + 12, 100)

        success = after_score > before_score

        try:
            # Save metrics to repository database
            repo.add_outcome(
                customer_id=customer_id,
                action=action,
                before_score=before_score,
                after_score=after_score,
                success=success
            )

            # Update live customer health in the session context / DB for feedback loop
            repo.update_customer_health(customer_id, after_score)
            print(f"[OutcomeAgent] Logged outcome success={success} (Health score: {before_score} -> {after_score})")

            return {
                "outcome_learning": {
                    "customer_id": customer_id,
                    "action": action,
                    "before_score": before_score,
                    "after_score": after_score,
                    "success": success
                }
            }
        except Exception as e:
            print(f"[OutcomeAgent] Logging outcome failed: {e}")
            return {
                "outcome_learning": {
                    "status": "failed",
                    "error": str(e)
                }
            }
