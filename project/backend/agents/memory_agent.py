"""
Memory Agent
============
Manages persistent storage of approved recommendations and
retrieval of historical actions for learning/context.

Phase 3: Returns hardcoded mock data.
Phase 13: Will use SQLite for real persistence.
"""


def store_approval(session_id: str, customer_id: str, recommendation: dict) -> None:
    """
    Store an approved recommendation in the database.

    Args:
        session_id: The current session identifier
        customer_id: The customer identifier
        recommendation: The approved recommendation dict
    """
    # Phase 3: No-op stub
    pass


def get_history(customer_id: str) -> list:
    """
    Get all approved recommendations for a customer, ordered by most recent.

    Args:
        customer_id: The customer identifier

    Returns:
        List of approved recommendation dicts
    """
    # Phase 3: Mock response
    return [
        {
            "action": "Schedule analytics training session",
            "priority": "High",
            "confidence": 0.91,
            "approved_at": "2026-06-25T10:30:00"
        }
    ]


def get_similar_past_approvals(customer_id: str) -> list:
    """
    Get past approvals for a customer to provide context to the
    recommendation agent (enables learning from past interactions).

    Args:
        customer_id: The customer identifier

    Returns:
        List of past approval dicts relevant to current context
    """
    # Phase 3: Mock response
    return []
