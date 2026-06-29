"""
Database Connection Manager
===========================
Configures connection parameters and instantiates database sessions.
Supports PostgreSQL with local SQLite fallback.
"""

import os
import sqlite3
from pathlib import Path
from typing import Any, Callable

import pandas as pd
from dotenv import load_dotenv

from database.models import (
    CREATE_CUSTOMERS_TABLE,
    CREATE_INTERACTIONS_TABLE,
    CREATE_INTERACTIONS_TABLE_SQLITE,
    CREATE_RECOMMENDATIONS_TABLE,
    CREATE_APPROVALS_TABLE,
    CREATE_APPROVALS_TABLE_SQLITE,
    CREATE_OUTCOMES_TABLE,
    CREATE_OUTCOMES_TABLE_SQLITE,
    CREATE_BUSINESS_METRICS_TABLE,
    CREATE_BUSINESS_METRICS_TABLE_SQLITE,
)

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
DB_TYPE = "postgres" if DATABASE_URL and DATABASE_URL.startswith("postgres") else "sqlite"

DB_DIR = Path(__file__).resolve().parent
SQLITE_DB_PATH = DB_DIR / "sqlite.db"

# Track connection status
_is_postgres_active = False


def get_db_connection() -> Any:
    """
    Establish and return a database connection.
    Attempts PostgreSQL if configured, otherwise falls back to local SQLite.
    """
    global _is_postgres_active

    if DB_TYPE == "postgres":
        try:
            import psycopg2
            # Connect to PostgreSQL
            conn = psycopg2.connect(DATABASE_URL)
            _is_postgres_active = True
            return conn
        except Exception as e:
            print(f"[DB Connection] Failed to connect to PostgreSQL ({e}). Falling back to SQLite.")

    # SQLite Fallback
    _is_postgres_active = False
    conn = sqlite3.connect(str(SQLITE_DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def execute_query(query_func: Callable[[Any], Any]) -> Any:
    """
    Helper to execute a function on a fresh database connection,
    ensuring it is safely closed.
    """
    conn = get_db_connection()
    try:
        result = query_func(conn)
        conn.commit()
        return result
    except Exception as e:
        conn.rollback()
        print(f"[DB Connection] Transaction failed: {e}")
        raise e
    finally:
        conn.close()


def _initialize_tables(conn: Any) -> None:
    """Create tables if they don't exist yet."""
    cursor = conn.cursor()

    if _is_postgres_active:
        cursor.execute(CREATE_CUSTOMERS_TABLE)
        cursor.execute(CREATE_INTERACTIONS_TABLE)
        cursor.execute(CREATE_RECOMMENDATIONS_TABLE)
        cursor.execute(CREATE_APPROVALS_TABLE)
        cursor.execute(CREATE_OUTCOMES_TABLE)
        cursor.execute(CREATE_BUSINESS_METRICS_TABLE)
    else:
        cursor.execute(CREATE_CUSTOMERS_TABLE)
        cursor.execute(CREATE_INTERACTIONS_TABLE_SQLITE)
        cursor.execute(CREATE_RECOMMENDATIONS_TABLE)
        cursor.execute(CREATE_APPROVALS_TABLE_SQLITE)
        cursor.execute(CREATE_OUTCOMES_TABLE_SQLITE)
        cursor.execute(CREATE_BUSINESS_METRICS_TABLE_SQLITE)


def _seed_customers_data(conn: Any) -> None:
    """Seed data from local customers.csv, usage.csv, and crm.json into SQL database."""
    cursor = conn.cursor()

    # Check if customers table is empty
    cursor.execute("SELECT COUNT(*) FROM customers")
    count = cursor.fetchone()[0]
    if count > 0:
        return  # Already seeded

    print("[DB Connection] Seeding customers table from CSV/JSON sources...")

    try:
        data_dir = Path(__file__).resolve().parents[3] / "data"

        # Load datasets using pandas
        customers_df = pd.read_csv(data_dir / "customers.csv")
        usage_df = pd.read_csv(data_dir / "usage.csv")
        crm_df = pd.read_json(data_dir / "crm.json")

        # Align column casing for joining (crm.json uses 'company', others use 'Company')
        crm_df = crm_df.rename(columns={"company": "Company"})

        # Perform a left join across the datasets
        merged_df = customers_df.merge(usage_df, on="Company", how="left").merge(crm_df, on="Company", how="left")

        # Insert records into customers table
        placeholder = "%s" if _is_postgres_active else "?"
        insert_query = f"""
        INSERT INTO customers (
            customer_id, company, plan, industry, renewal_date, health_score,
            licensed_users, active_users, dashboard_usage_pct, api_calls,
            support_tickets_open, customer_owner
        ) VALUES (
            {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder},
            {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}
        )
        """

        for _, row in merged_df.iterrows():
            params = (
                str(row["CustomerID"]),
                str(row["Company"]),
                str(row["Plan"]) if pd.notna(row["Plan"]) else "",
                str(row["Industry"]) if pd.notna(row["Industry"]) else "",
                str(row["RenewalDate"]) if pd.notna(row["RenewalDate"]) else "",
                int(row["HealthScore"]) if pd.notna(row["HealthScore"]) else 0,
                int(row["LicensedUsers"]) if pd.notna(row["LicensedUsers"]) else 0,
                int(row["ActiveUsers"]) if pd.notna(row["ActiveUsers"]) else 0,
                int(row["DashboardUsagePct"]) if pd.notna(row["DashboardUsagePct"]) else 0,
                int(row["APICalls"]) if pd.notna(row["APICalls"]) else 0,
                int(row["support_tickets_open"]) if pd.notna(row["support_tickets_open"]) else 0,
                str(row["customer_owner"]) if pd.notna(row["customer_owner"]) else ""
            )
            cursor.execute(insert_query, params)

        print(f"[DB Connection] Successfully seeded {len(merged_df)} customers.")

    except Exception as e:
        print(f"[DB Connection] Seeding customers failed: {e}")


def initialize_db() -> None:
    """Set up database tables and populate starting records."""
    try:
        conn = get_db_connection()
        _initialize_tables(conn)
        conn.commit()
        _seed_customers_data(conn)
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[DB Connection] DB Initialization failed: {e}")


# Run initialization on package load
initialize_db()
