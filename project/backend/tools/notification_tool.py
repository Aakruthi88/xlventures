"""
Notification Tool
=================
LangChain tool to dispatch alerts, emails, or notifications.
"""

from typing import Dict, Any
from langchain.tools import tool


@tool
def send_alert(recipient: str, message: str) -> Dict[str, Any]:
    """
    Send an email or system notification to a specific recipient (e.g., account owner, manager)
    regarding customer success issues or actions that require immediate review.

    Args:
        recipient: Email address or user identifier of the recipient.
        message: The message body to send.

    Returns:
        A dictionary indicating transmission status: {'status': 'sent', 'recipient': recipient}.
    """
    print(f"\n>>> [NOTIFICATION SENT] To: {recipient}\n>>> Message: {message}\n")
    return {
        "status": "sent",
        "recipient": recipient,
        "message_preview": message[:100] + "..." if len(message) > 100 else message
    }
