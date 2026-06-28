"""
Memory Agent
============
Manages persistent storage of recommendation actions (approve / reject / edit)
and retrieval of historical actions for learning/context.

Phase 13+: Uses SQLite with a generalised recommendation_actions table.
           Keeps a legacy `approvals` view so existing queries still work.
"""

import os
import sqlite3
from datetime import datetime, timezone


DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database")
DB_PATH = os.path.join(DB_DIR, "sqlite.db")


def _initialize_db() -> None:
    """
    Create (or migrate) the database schema.

    New schema:  recommendation_actions
    Legacy compat: approvals table is kept so old rows are not lost;
                   new writes go to recommendation_actions only.
    """
    try:
        os.makedirs(DB_DIR, exist_ok=True)
        conn = sqlite3.connect(DB_PATH)

        # New generalised table
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS recommendation_actions (
                id                   INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id           TEXT,
                customer_id          TEXT,
                recommendation_action TEXT,
                action               TEXT DEFAULT 'approve',
                edited_text          TEXT,
                priority             TEXT,
                confidence           REAL,
                timestamp            TEXT
            )
            """
        )

        # Keep legacy approvals table so existing rows are not lost
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


# Initialize on import
_initialize_db()


# ─────────────────────────────────────────────────────────────────────────────
# Write
# ─────────────────────────────────────────────────────────────────────────────

def store_action(
    session_id: str,
    customer_id: str,
    recommendation: dict,
    action: str = "approve",
    edited_text: str = None,
) -> None:
    """
    Store a recommendation action (approve | reject | edit) in recommendation_actions.

    Args:
        session_id:     Session identifier
        customer_id:    Customer identifier
        recommendation: Recommendation dict (id, action, priority, confidence …)
        action:         "approve" | "reject" | "edit"
        edited_text:    Replacement text when action == "edit"
    """
    try:
        if not isinstance(recommendation, dict):
            recommendation = {}

        recommendation_action = (
            recommendation.get("action")
            or recommendation.get("recommendation_action")
            or ""
        )
        priority = recommendation.get("priority") or ""
        confidence = recommendation.get("confidence")
        confidence = float(confidence) if confidence is not None else 0.0
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            """
            INSERT INTO recommendation_actions
                (session_id, customer_id, recommendation_action,
                 action, edited_text, priority, confidence, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                customer_id,
                recommendation_action,
                action,
                edited_text,
                priority,
                confidence,
                timestamp,
            ),
        )
        conn.commit()
        conn.close()
    except Exception as exc:
        print(f"[Memory Agent] Failed to store action: {exc}")


def store_approval(session_id: str, customer_id: str, recommendation: dict) -> None:
    """
    Backwards-compatible wrapper — stores an 'approve' action.
    Delegates to store_action so all new writes land in recommendation_actions.
    """
    store_action(session_id, customer_id, recommendation, action="approve")


# ─────────────────────────────────────────────────────────────────────────────
# Read – history
# ─────────────────────────────────────────────────────────────────────────────

def get_history(customer_id: str) -> list:
    """
    Return all stored actions for a customer, newest first.

    Merges rows from both recommendation_actions (new) and approvals (legacy).
    Each row contains:
        action, status, edited_text, priority, confidence, approved_at, customer_id
    """
    rows = []

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row

        # New table
        new_rows = conn.execute(
            """
            SELECT recommendation_action, action AS status,
                   edited_text, priority, confidence, timestamp AS approved_at
            FROM recommendation_actions
            WHERE customer_id = ?
            ORDER BY timestamp DESC, id DESC
            """,
            (customer_id,),
        ).fetchall()

        for r in new_rows:
            rows.append({
                "action":      r["recommendation_action"],
                "status":      r["status"],
                "edited_text": r["edited_text"],
                "priority":    r["priority"],
                "confidence":  r["confidence"],
                "approved_at": r["approved_at"],
            })

        # Legacy approvals table (status always "approve")
        legacy_rows = conn.execute(
            """
            SELECT recommendation_action, priority, confidence, approved_at
            FROM approvals
            WHERE customer_id = ?
            ORDER BY approved_at DESC, id DESC
            """,
            (customer_id,),
        ).fetchall()

        for r in legacy_rows:
            rows.append({
                "action":      r["recommendation_action"],
                "status":      "approve",
                "edited_text": None,
                "priority":    r["priority"],
                "confidence":  r["confidence"],
                "approved_at": r["approved_at"],
            })

        conn.close()
    except Exception as exc:
        print(f"[Memory Agent] Failed to fetch history: {exc}")

    # Sort combined list newest-first
    rows.sort(
        key=lambda r: r["approved_at"] or "",
        reverse=True,
    )
    return rows


# ─────────────────────────────────────────────────────────────────────────────
# Read – analytics aggregates
# ─────────────────────────────────────────────────────────────────────────────

def get_analytics() -> dict:
    """
    Compute aggregate metrics from recommendation_actions for the Analytics page.

    Returns:
        {
            generated:     int,   # total rows
            approved:      int,
            rejected:      int,
            edited:        int,
            approval_rate: float, # approved / (approved + rejected) * 100, or None
            avg_confidence: float | None,
            by_month: [{ month: str, approved: int }]
        }
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row

        rows = conn.execute(
            """
            SELECT action, confidence, timestamp
            FROM recommendation_actions
            ORDER BY timestamp ASC
            """
        ).fetchall()

        # Also include legacy approvals (counted as action="approve")
        legacy = conn.execute(
            "SELECT confidence, approved_at FROM approvals"
        ).fetchall()

        conn.close()

        all_rows = [
            {"action": r["action"], "confidence": r["confidence"], "timestamp": r["timestamp"]}
            for r in rows
        ] + [
            {"action": "approve", "confidence": r["confidence"], "timestamp": r["approved_at"]}
            for r in legacy
        ]

        if not all_rows:
            return {
                "generated": 0, "approved": 0, "rejected": 0, "edited": 0,
                "approval_rate": None, "avg_confidence": None, "by_month": [],
            }

        generated = len(all_rows)
        approved  = sum(1 for r in all_rows if r["action"] == "approve")
        rejected  = sum(1 for r in all_rows if r["action"] == "reject")
        edited    = sum(1 for r in all_rows if r["action"] == "edit")

        decisive  = approved + rejected
        approval_rate = round(approved / decisive * 100, 1) if decisive > 0 else None

        confs = [r["confidence"] for r in all_rows if r["confidence"] is not None]
        avg_confidence = round(sum(confs) / len(confs) * 100, 1) if confs else None

        # Monthly breakdown (approved only for trend chart)
        by_month: dict[str, int] = {}
        for r in all_rows:
            if r["action"] != "approve" or not r["timestamp"]:
                continue
            try:
                month_key = datetime.fromisoformat(
                    r["timestamp"].replace("Z", "+00:00")
                ).strftime("%b")
                by_month[month_key] = by_month.get(month_key, 0) + 1
            except Exception:
                pass

        return {
            "generated":      generated,
            "approved":       approved,
            "rejected":       rejected,
            "edited":         edited,
            "approval_rate":  approval_rate,
            "avg_confidence": avg_confidence,
            "by_month":       [{"month": m, "approved": c} for m, c in by_month.items()],
        }

    except Exception as exc:
        print(f"[Memory Agent] Failed to compute analytics: {exc}")
        return {
            "generated": 0, "approved": 0, "rejected": 0, "edited": 0,
            "approval_rate": None, "avg_confidence": None, "by_month": [],
        }


# ─────────────────────────────────────────────────────────────────────────────
# Read – planner context
# ─────────────────────────────────────────────────────────────────────────────

def get_similar_past_approvals(customer_id: str) -> list:
    """
    Return past approved actions for a customer to provide context to the
    recommendation agent.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row

        new_rows = conn.execute(
            """
            SELECT recommendation_action, priority, confidence, timestamp AS approved_at
            FROM recommendation_actions
            WHERE customer_id = ? AND action = 'approve'
            ORDER BY timestamp DESC, id DESC
            """,
            (customer_id,),
        ).fetchall()

        legacy_rows = conn.execute(
            """
            SELECT recommendation_action, priority, confidence, approved_at
            FROM approvals
            WHERE customer_id = ?
            ORDER BY approved_at DESC, id DESC
            """,
            (customer_id,),
        ).fetchall()

        conn.close()

        result = [
            {
                "action":      r["recommendation_action"],
                "priority":    r["priority"],
                "confidence":  r["confidence"],
                "approved_at": r["approved_at"],
            }
            for r in list(new_rows) + list(legacy_rows)
        ]
        return result

    except Exception as exc:
        print(f"[Memory Agent] Failed to fetch past approvals: {exc}")
        return []
