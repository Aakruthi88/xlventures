"""
Database Repository Layer
=========================
Handles CRUD operations for SQL database tables.
Provides cross-compatibility between PostgreSQL and SQLite.
"""

from typing import Any, Dict, List, Optional
from database.connection import get_db_connection


def _execute_query(query: str, params: tuple = (), fetch: bool = False, fetch_one: bool = False) -> Any:
    """Helper function to execute SQL query with automatic placeholder replacement for SQLite fallback."""
    conn = get_db_connection()
    is_postgres = hasattr(conn, "closed")  # postgres connection has 'closed' attribute

    # Convert placeholder from postgres '%s' to sqlite '?'
    if not is_postgres:
        query = query.replace("%s", "?")

    try:
        cursor = conn.cursor()
        cursor.execute(query, params)

        if fetch or fetch_one:
            columns = [desc[0] for desc in cursor.description]
            if fetch_one:
                row = cursor.fetchone()
                if row:
                    return dict(zip(columns, row))
                return None
            else:
                rows = cursor.fetchall()
                return [dict(zip(columns, row)) for row in rows]

        conn.commit()
        # For inserts with RETURNING or lastrowid
        if "INSERT" in query.upper() and not is_postgres:
            return cursor.lastrowid
        return None
    except Exception as e:
        conn.rollback()
        print(f"[Repository] Database query error: {e}")
        print(f"[Repository] Query was: {query}")
        print(f"[Repository] Params: {params}")
        raise e
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# CUSTOMERS REPOSITORY
# ─────────────────────────────────────────────────────────────────────────────

def get_customer_by_id(customer_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve customer by their Customer ID."""
    query = "SELECT * FROM customers WHERE customer_id = %s"
    return _execute_query(query, (customer_id,), fetch_one=True)


def get_customer_by_company(company: str) -> Optional[Dict[str, Any]]:
    """Retrieve customer by their Company name."""
    query = "SELECT * FROM customers WHERE company = %s"
    return _execute_query(query, (company,), fetch_one=True)


def get_all_customers() -> List[Dict[str, Any]]:
    """Retrieve all customers in the database."""
    query = "SELECT * FROM customers"
    return _execute_query(query, (), fetch=True)


def update_customer_health(customer_id: str, new_score: int) -> None:
    """Update customer health score."""
    query = "UPDATE customers SET health_score = %s WHERE customer_id = %s"
    _execute_query(query, (new_score, customer_id))


# ─────────────────────────────────────────────────────────────────────────────
# INTERACTIONS REPOSITORY
# ─────────────────────────────────────────────────────────────────────────────

def add_interaction(customer_id: str, transcript_text: str, sentiment: str,
                    confidence: float, key_phrases: List[str]) -> int:
    """Insert a customer interaction record."""
    query = """
    INSERT INTO interactions (customer_id, transcript_text, sentiment, confidence, key_phrases)
    VALUES (%s, %s, %s, %s, %s)
    """
    phrases_str = ",".join(key_phrases)
    return _execute_query(query, (customer_id, transcript_text, sentiment, confidence, phrases_str))


# ─────────────────────────────────────────────────────────────────────────────
# RECOMMENDATIONS REPOSITORY
# ─────────────────────────────────────────────────────────────────────────────

def add_recommendation(rec_id: str, session_id: str, customer_id: str,
                      action_description: str, priority: str, confidence: float) -> None:
    """Insert a generated next-best-action recommendation."""
    # Check if recommendation already exists to avoid PK conflict (idempotency)
    existing = _execute_query("SELECT id FROM recommendations WHERE id = %s", (rec_id,), fetch_one=True)
    if existing:
        return

    query = """
    INSERT INTO recommendations (id, session_id, customer_id, action_description, priority, confidence)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    _execute_query(query, (rec_id, session_id, customer_id, action_description, priority, confidence))


def get_recommendations_by_customer(customer_id: str) -> List[Dict[str, Any]]:
    """Retrieve all recommendations for a customer."""
    query = "SELECT * FROM recommendations WHERE customer_id = %s"
    return _execute_query(query, (customer_id,), fetch=True)


# ─────────────────────────────────────────────────────────────────────────────
# APPROVALS REPOSITORY
# ─────────────────────────────────────────────────────────────────────────────

def add_approval(session_id: str, customer_id: str, recommendation_id: str) -> int:
    """Insert a human approval record for a recommendation."""
    query = """
    INSERT INTO approvals (session_id, customer_id, recommendation_id)
    VALUES (%s, %s, %s)
    """
    return _execute_query(query, (session_id, customer_id, recommendation_id))


def get_approvals_by_customer(customer_id: str) -> List[Dict[str, Any]]:
    """Retrieve all approved recommendations for a customer, newest first."""
    query = """
    SELECT a.approved_at, r.action_description AS action, r.priority, r.confidence
    FROM approvals a
    JOIN recommendations r ON a.recommendation_id = r.id
    WHERE a.customer_id = %s
    ORDER BY a.approved_at DESC
    """
    return _execute_query(query, (customer_id,), fetch=True)


# ─────────────────────────────────────────────────────────────────────────────
# OUTCOMES REPOSITORY
# ─────────────────────────────────────────────────────────────────────────────

def add_outcome(customer_id: str, action: str, before_score: int,
                after_score: int, success: bool) -> int:
    """Log an outcome metric associated with an executed recommendation."""
    query = """
    INSERT INTO outcomes (customer_id, action, before_score, after_score, success)
    VALUES (%s, %s, %s, %s, %s)
    """
    return _execute_query(query, (customer_id, action, before_score, after_score, success))


def update_customer_health(customer_id: str, new_health_score: int) -> None:
    """Update the health_score for a customer after outcome analysis."""
    query = "UPDATE customers SET health_score = %s WHERE customer_id = %s"
    _execute_query(query, (new_health_score, customer_id))


# ─────────────────────────────────────────────────────────────────────────────
# BUSINESS METRICS REPOSITORY
# ─────────────────────────────────────────────────────────────────────────────

def add_business_metric(interaction_id: str, customer_id: str, recommendation: str,
                        confidence_score: float, approval_status: str = 'pending',
                        execution_status: str = 'pending', outcome: str = '') -> None:
    """Insert a new business metric record, or update if it exists (upsert)."""
    existing = _execute_query("SELECT id FROM business_metrics WHERE interaction_id = %s", (interaction_id,), fetch_one=True)
    if existing:
        query = """
        UPDATE business_metrics
        SET customer_id = %s, recommendation = %s, confidence_score = %s, approval_status = %s, execution_status = %s, outcome = %s
        WHERE interaction_id = %s
        """
        _execute_query(query, (customer_id, recommendation, confidence_score, approval_status, execution_status, outcome, interaction_id))
    else:
        query = """
        INSERT INTO business_metrics (interaction_id, customer_id, recommendation, confidence_score, approval_status, execution_status, outcome)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        _execute_query(query, (interaction_id, customer_id, recommendation, confidence_score, approval_status, execution_status, outcome))


def update_business_metric_status(interaction_id: str, approval_status: str, execution_status: str = None) -> None:
    """Update approval status (and optional execution status) for a metric record."""
    if execution_status:
        query = "UPDATE business_metrics SET approval_status = %s, execution_status = %s WHERE interaction_id = %s"
        _execute_query(query, (approval_status, execution_status, interaction_id))
    else:
        query = "UPDATE business_metrics SET approval_status = %s WHERE interaction_id = %s"
        _execute_query(query, (approval_status, interaction_id))


def update_business_metric_outcome(interaction_id: str, outcome: str, execution_status: str) -> None:
    """Update outcome text and execution status for a metric record."""
    query = "UPDATE business_metrics SET outcome = %s, execution_status = %s WHERE interaction_id = %s"
    _execute_query(query, (outcome, execution_status, interaction_id))


def get_all_business_metrics() -> List[Dict[str, Any]]:
    """Retrieve all business metrics records."""
    query = "SELECT * FROM business_metrics ORDER BY timestamp DESC"
    return _execute_query(query, (), fetch=True)


