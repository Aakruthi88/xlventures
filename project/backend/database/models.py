"""
Database Models
===============
Defines SQL table schemas for PostgreSQL / SQLite.
"""

CREATE_CUSTOMERS_TABLE = """
CREATE TABLE IF NOT EXISTS customers (
    customer_id VARCHAR(50) PRIMARY KEY,
    company VARCHAR(255) NOT NULL,
    plan VARCHAR(100),
    industry VARCHAR(100),
    renewal_date VARCHAR(50),
    health_score INTEGER,
    licensed_users INTEGER,
    active_users INTEGER,
    dashboard_usage_pct INTEGER,
    api_calls INTEGER,
    support_tickets_open INTEGER,
    customer_owner VARCHAR(255)
);
"""

CREATE_INTERACTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS interactions (
    id SERIAL PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    transcript_text TEXT,
    sentiment VARCHAR(50),
    confidence REAL,
    key_phrases TEXT, -- stored as comma-separated values or JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_RECOMMENDATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS recommendations (
    id VARCHAR(50) PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL,
    customer_id VARCHAR(50) NOT NULL,
    action_description TEXT NOT NULL,
    priority VARCHAR(50),
    confidence REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_APPROVALS_TABLE = """
CREATE TABLE IF NOT EXISTS approvals (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL,
    customer_id VARCHAR(50) NOT NULL,
    recommendation_id VARCHAR(50) NOT NULL,
    approved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_OUTCOMES_TABLE = """
CREATE TABLE IF NOT EXISTS outcomes (
    id SERIAL PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    action TEXT NOT NULL,
    before_score INTEGER,
    after_score INTEGER,
    success BOOLEAN,
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_BUSINESS_METRICS_TABLE = """
CREATE TABLE IF NOT EXISTS business_metrics (
    id SERIAL PRIMARY KEY,
    interaction_id VARCHAR(100) UNIQUE,
    customer_id VARCHAR(50) NOT NULL,
    recommendation TEXT,
    confidence_score REAL,
    approval_status VARCHAR(50) DEFAULT 'pending',
    execution_status VARCHAR(50) DEFAULT 'pending',
    outcome TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# SQLite compatibility changes (mapping SERIAL to INTEGER PRIMARY KEY AUTOINCREMENT)
CREATE_INTERACTIONS_TABLE_SQLITE = CREATE_INTERACTIONS_TABLE.replace("id SERIAL PRIMARY KEY", "id INTEGER PRIMARY KEY AUTOINCREMENT")
CREATE_APPROVALS_TABLE_SQLITE = CREATE_APPROVALS_TABLE.replace("id SERIAL PRIMARY KEY", "id INTEGER PRIMARY KEY AUTOINCREMENT")
CREATE_OUTCOMES_TABLE_SQLITE = CREATE_OUTCOMES_TABLE.replace("id SERIAL PRIMARY KEY", "id INTEGER PRIMARY KEY AUTOINCREMENT")
CREATE_BUSINESS_METRICS_TABLE_SQLITE = CREATE_BUSINESS_METRICS_TABLE.replace("id SERIAL PRIMARY KEY", "id INTEGER PRIMARY KEY AUTOINCREMENT")

