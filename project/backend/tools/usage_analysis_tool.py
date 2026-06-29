"""
Usage Analysis Tool
===================
LangChain tool to retrieve and analyze customer platform usage metrics.
"""

from typing import Any, Dict
from datetime import datetime
import pandas as pd
from langchain.tools import tool
from database.repository import get_customer_by_id

# Fixed reference date calculation to match the existing customer_agent logic
_base_date = None


def _get_base_date() -> datetime.date:
    """Calculate baseline reference date dynamically from data files or default to current date."""
    global _base_date
    if _base_date is None:
        try:
            from pathlib import Path
            data_dir = Path(__file__).resolve().parents[3] / "data"
            crm_df = pd.read_json(data_dir / "crm.json")
            login_dates = pd.to_datetime(crm_df["last_login_date"])
            _base_date = login_dates.max().date()
        except Exception:
            _base_date = datetime.now().date()
    return _base_date


@tool
def analyze_usage_metrics(customer_id: str) -> Dict[str, Any]:
    """
    Fetch and analyze platform adoption metrics for a customer, including licensed users,
    active users, dashboard usage percentage, API calls, and days remaining until contract renewal.

    Args:
        customer_id: Unique customer ID (e.g., 'C001').

    Returns:
        A dictionary containing usage metrics and calculated adoption ratios,
        or an empty dictionary if the customer is not found.
    """
    try:
        details = get_customer_by_id(customer_id)
        if details:
            renewal_date_str = details.get("renewal_date")
            days_to_renewal = 0
            if renewal_date_str:
                try:
                    renewal_date = pd.to_datetime(renewal_date_str).date()
                    base_date = _get_base_date()
                    days_to_renewal = (renewal_date - base_date).days
                except Exception:
                    pass

            return {
                "customer_id": details.get("customer_id"),
                "company": details.get("company"),
                "licensed_users": details.get("licensed_users"),
                "active_users": details.get("active_users"),
                "dashboard_usage_pct": details.get("dashboard_usage_pct"),
                "api_calls": details.get("api_calls"),
                "renewal_date": renewal_date_str,
                "days_to_renewal": int(days_to_renewal)
            }
    except Exception as e:
        print(f"[Usage Analysis Tool] Error: {e}")

    return {}
