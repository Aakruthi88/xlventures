"""
Customer Agent
==============
Retrieves and aggregates customer data from multiple sources
(customers.csv, usage.csv, crm.json, support_tickets.csv).

Phase 6: Loads real data from CSV/JSON files.
"""

import os
from pathlib import Path
from datetime import datetime
import pandas as pd

# Global variables for caching
_merged_df = None
_base_date = None


def _load_data():
    """
    Load data from customers.csv, usage.csv, and crm.json,
    cache them, and perform a join across the datasets.
    """
    global _merged_df, _base_date
    if _merged_df is None:
        # Determine the absolute data directory path relative to this agent file
        # (project/backend/agents/customer_agent.py -> 4 levels up to workspace root)
        data_dir = Path(__file__).resolve().parents[3] / "data"

        # Load datasets using pandas
        customers_df = pd.read_csv(data_dir / "customers.csv")
        usage_df = pd.read_csv(data_dir / "usage.csv")
        crm_df = pd.read_json(data_dir / "crm.json")

        # Determine reference date for calculating days_to_renewal dynamically
        # from the maximum last_login_date in crm.json (generation timestamp proxy)
        try:
            login_dates = pd.to_datetime(crm_df["last_login_date"])
            _base_date = login_dates.max().date()
        except Exception:
            _base_date = datetime.now().date()

        # Align column casing for joining (crm.json uses 'company', others use 'Company')
        crm_df = crm_df.rename(columns={"company": "Company"})

        # Perform a left join across the datasets using pandas
        _merged_df = customers_df.merge(usage_df, on="Company", how="left").merge(crm_df, on="Company", how="left")


def get_summary(customer_id: str) -> dict:
    """
    Get a unified customer summary by aggregating data from
    customers.csv, usage.csv, and crm.json.

    Args:
        customer_id: The customer identifier (e.g., "C001")

    Returns:
        dict matching CustomerSummary schema
    """
    _load_data()

    # Query the joined dataframe for the requested CustomerID
    row = _merged_df[_merged_df["CustomerID"] == customer_id]
    if row.empty:
        raise ValueError(f"Customer ID {customer_id} not found in database.")

    record = row.iloc[0]

    # Calculate days to renewal based on the anchor base date
    renewal_date_str = str(record["RenewalDate"])
    try:
        renewal_date = pd.to_datetime(renewal_date_str).date()
        days_to_renewal = (renewal_date - _base_date).days
    except Exception:
        days_to_renewal = 0

    return {
        "customer_id": str(record["CustomerID"]),
        "company": str(record["Company"]),
        "plan": str(record["Plan"]),
        "industry": str(record["Industry"]),
        "renewal_date": renewal_date_str,
        "days_to_renewal": int(days_to_renewal),
        "health_score": int(record["HealthScore"]),
        "licensed_users": int(record["LicensedUsers"]) if pd.notna(record["LicensedUsers"]) else 0,
        "active_users": int(record["ActiveUsers"]) if pd.notna(record["ActiveUsers"]) else 0,
        "dashboard_usage_pct": int(record["DashboardUsagePct"]) if pd.notna(record["DashboardUsagePct"]) else 0,
        "api_calls": int(record["APICalls"]) if pd.notna(record["APICalls"]) else 0,
        "open_support_tickets": int(record["support_tickets_open"]) if pd.notna(record["support_tickets_open"]) else 0,
        "owner": str(record["customer_owner"]) if pd.notna(record["customer_owner"]) else ""
    }

