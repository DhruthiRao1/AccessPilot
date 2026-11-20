-- AccessPilot schema for AlloyDB for PostgreSQL.
-- Needs AlloyDB AI: the instance flag google_ml_integration.enable_model_support=on
-- and the AlloyDB service agent granted roles/aiplatform.user (for Vertex AI embeddings).

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS google_ml_integration;

CREATE TABLE IF NOT EXISTS employees (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    team TEXT,
    manager_id TEXT
);

CREATE TABLE IF NOT EXISTS catalog (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    risk TEXT NOT NULL,
    cost NUMERIC NOT NULL,
    description TEXT NOT NULL,
    embedding vector(768)
);

CREATE TABLE IF NOT EXISTS inventory (
    item_id TEXT PRIMARY KEY REFERENCES catalog(id),
    in_stock INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS assets (
    employee_id TEXT REFERENCES employees(id),
    item_id TEXT REFERENCES catalog(id),
    PRIMARY KEY (employee_id, item_id)
);

CREATE TABLE IF NOT EXISTS requests (
    id SERIAL PRIMARY KEY,
    employee_id TEXT NOT NULL REFERENCES employees(id),
    item_id TEXT NOT NULL REFERENCES catalog(id),
    justification TEXT,
    status TEXT NOT NULL,
    reason TEXT,
    approver_id TEXT,
    comment TEXT,
    ticket TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);
