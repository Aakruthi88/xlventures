"""
Send Email Tool
===============
LangChain tool to simulate sending emails to customer contacts.
"""

from typing import Dict, Any
from langchain.tools import tool


@tool
def send_email(to_address: str, subject: str, body: str) -> Dict[str, Any]:
    """
    Simulates sending an email notification to a customer or sponsor.

    Args:
        to_address: Recipient email address.
        subject: Email subject line.
        body: Email body text.

    Returns:
        Status dict indicating success.
    """
    print(f"\n>>> [SIMULATED EMAIL SENT] To: {to_address}\n>>> Subject: {subject}\n>>> Body: {body}\n")
    return {
        "status": "success",
        "action": f"Email sent to {to_address} with subject: {subject}"
    }
