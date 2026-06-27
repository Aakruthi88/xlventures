"""
Memory Agent
============
Manages persistent storage of approved recommendations and
retrieval of historical actions for learning/context.

Phase 3: Returns hardcoded mock data.
Phase 13: Uses SQLite for real persistence.
"""

import os
import sqlite3
from datetime import datetime, timezone


DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database")
DB_PATH = os.path.join(DB_DIR, "sqlite.db")


def _initialize_db() -> None:
    """Create the database directory and approvals table if needed."""
    try:
        os.makedirs(DB_DIR, exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS approvals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                customer_id TEXT,
                recommendation_action TEXT,
                priority TEXT,
                confidence REAL,
                approved_at TEXT
            )
            """
        )
        conn.commit()
        conn.close()
    except Exception as exc:
        print(f"[Memory Agent] Database initialization failed: {exc}")


# Initialize the SQLite database when this module is imported.
_initialize_db()


def store_approval(session_id: str, customer_id: str, recommendation: dict) -> None:
    """
    Store an approved recommendation in the database.

    Args:
        session_id: The current session identifier
        customer_id: The customer identifier
        recommendation: The approved recommendation dict
    """
    try:
        if not isinstance(recommendation, dict):
            recommendation = {}

        recommendation_action = recommendation.get("action") or recommendation.get("recommendation_action") or ""
        priority = recommendation.get("priority") or ""
        confidence = recommendation.get("confidence")
        if confidence is None:
            confidence = 0.0
        else:
            confidence = float(confidence)

        approved_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            """
            INSERT INTO approvals (session_id, customer_id, recommendation_action, priority, confidence, approved_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (session_id, customer_id, recommendation_action, priority, confidence, approved_at),
        )
        conn.commit()
        conn.close()
    except Exception as exc:
        print(f"[Memory Agent] Failed to store approval: {exc}")


def get_history(customer_id: str) -> list:
    """
    Get all approved recommendations for a customer, ordered by most recent.

    Args:
        customer_id: The customer identifier

    Returns:
        List of approved recommendation dicts
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT recommendation_action, priority, confidence, approved_at
            FROM approvals
            WHERE customer_id = ?
            ORDER BY approved_at DESC, id DESC
            """,
            (customer_id,),
        ).fetchall()
        conn.close()
        return [
            {
                "action": row["recommendation_action"],
                "priority": row["priority"],
                "confidence": row["confidence"],
                "approved_at": row["approved_at"],
            }
            for row in rows
        ]
    except Exception as exc:
        print(f"[Memory Agent] Failed to fetch history: {exc}")
        return []


def get_similar_past_approvals(customer_id: str) -> list:
    """
    Get past approvals for a customer to provide context to the
    recommendation agent (enables learning from past interactions).

    Args:
        customer_id: The customer identifier

    Returns:
        List of past approval dicts relevant to current context
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT recommendation_action, priority, confidence, approved_at
            FROM approvals
            WHERE customer_id = ?
            ORDER BY approved_at DESC, id DESC
            """,
            (customer_id,),
        ).fetchall()
        conn.close()
        return [
            {
                "action": row["recommendation_action"],
                "priority": row["priority"],
                "confidence": row["confidence"],
                "approved_at": row["approved_at"],
            }
            for row in rows
        ]
    except Exception as exc:
        print(f"[Memory Agent] Failed to fetch past approvals: {exc}")
        return []
