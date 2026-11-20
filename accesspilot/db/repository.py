"""Data access. One SQL implementation shared by SQLite and AlloyDB (PostgreSQL).

Only catalog search differs: SQLite uses keyword scoring, AlloyDB uses
AlloyDB AI vector search (pgvector + in-database Vertex AI embeddings).
"""
import re
import sqlite3
from pathlib import Path

from . import seed

SCHEMA_SQLITE = """
CREATE TABLE IF NOT EXISTS employees (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, team TEXT, manager_id TEXT);
CREATE TABLE IF NOT EXISTS catalog (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, category TEXT NOT NULL,
    risk TEXT NOT NULL, cost REAL NOT NULL, description TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS inventory (item_id TEXT PRIMARY KEY, in_stock INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS assets (employee_id TEXT, item_id TEXT, PRIMARY KEY (employee_id, item_id));
CREATE TABLE IF NOT EXISTS requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id TEXT NOT NULL, item_id TEXT NOT NULL, justification TEXT,
    status TEXT NOT NULL, reason TEXT, approver_id TEXT, comment TEXT, ticket TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP);
"""

_COLS = "id, employee_id, item_id, justification, status, reason, approver_id, comment, ticket"


class SqlRepository:
    """Works with any DB-API connection whose rows behave like dicts."""

    def __init__(self, conn, placeholder: str):
        self.conn = conn
        self.p = placeholder

    def _q(self, sql: str) -> str:
        return sql.replace("?", self.p)

    def _one(self, sql, args=()):
        cur = self.conn.cursor()
        cur.execute(self._q(sql), args)
        row = cur.fetchone()
        return dict(row) if row else None

    def _all(self, sql, args=()):
        cur = self.conn.cursor()
        cur.execute(self._q(sql), args)
        return [dict(r) for r in cur.fetchall()]

    def _exec(self, sql, args=()):
        cur = self.conn.cursor()
        cur.execute(self._q(sql), args)
        self.conn.commit()
        return cur

    # --- reads -----------------------------------------------------------
    def get_employee(self, employee_id):
        return self._one("SELECT id, name, team, manager_id FROM employees WHERE id = ?", (employee_id,))

    def get_item(self, item_id):
        return self._one(
            "SELECT id, name, category, risk, cost, description FROM catalog WHERE id = ?", (item_id,))

    def stock(self, item_id):
        row = self._one("SELECT in_stock FROM inventory WHERE item_id = ?", (item_id,))
        return None if row is None else row["in_stock"]  # None = not stock-tracked

    def employee_assets(self, employee_id):
        return self._all(
            "SELECT c.id, c.name, c.category FROM assets a JOIN catalog c ON c.id = a.item_id "
            "WHERE a.employee_id = ? ORDER BY c.id", (employee_id,))

    def has_asset(self, employee_id, item_id):
        return self._one("SELECT 1 AS x FROM assets WHERE employee_id = ? AND item_id = ?",
                         (employee_id, item_id)) is not None

    def get_request(self, request_id):
        return self._one(f"SELECT {_COLS} FROM requests WHERE id = ?", (request_id,))

    def pending_for_manager(self, manager_id):
        return self._all(
            f"SELECT r.{_COLS.replace(', ', ', r.')} FROM requests r "
            "JOIN employees e ON e.id = r.employee_id "
            "WHERE e.manager_id = ? AND r.status = 'PENDING_MANAGER' ORDER BY r.id", (manager_id,))

    def search_catalog(self, query, limit=3):
        """Keyword search (offline backend)."""
        words = set(re.findall(r"[a-z0-9]+", query.lower()))
        scored = []
        for item in self._all("SELECT id, name, category, risk, cost, description FROM catalog"):
            text = set(re.findall(r"[a-z0-9]+", f"{item['name']} {item['description']} {item['category']}".lower()))
            score = len(words & text)
            if score:
                scored.append((score, item))
        scored.sort(key=lambda s: (-s[0], s[1]["id"]))
        return [i for _, i in scored[:limit]]

    # --- writes ----------------------------------------------------------
    def create_request(self, employee_id, item_id, justification, status, reason, ticket=None):
        cur = self._exec(
            "INSERT INTO requests (employee_id, item_id, justification, status, reason, ticket) "
            "VALUES (?, ?, ?, ?, ?, ?) RETURNING id",
            (employee_id, item_id, justification, status, reason, ticket))
        return cur.fetchone()["id"]

    def update_request(self, request_id, status, approver_id=None, comment=None, ticket=None):
        self._exec(
            "UPDATE requests SET status = ?, approver_id = COALESCE(?, approver_id), "
            "comment = COALESCE(?, comment), ticket = COALESCE(?, ticket) WHERE id = ?",
            (status, approver_id, comment, ticket, request_id))

    def fulfil(self, employee_id, item_id):
        """Assign the item and take one unit out of stock if it is stock-tracked."""
        self._exec("INSERT INTO assets (employee_id, item_id) VALUES (?, ?)", (employee_id, item_id))
        self._exec("UPDATE inventory SET in_stock = in_stock - 1 WHERE item_id = ? AND in_stock > 0",
                   (item_id,))


class SqliteRepository(SqlRepository):
    def __init__(self, path=":memory:"):
        conn = sqlite3.connect(path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        super().__init__(conn, "?")
        conn.executescript(SCHEMA_SQLITE)
        if not self._one("SELECT 1 AS x FROM employees LIMIT 1"):
            load_seed(self)

    def create_request(self, employee_id, item_id, justification, status, reason, ticket=None):
        cur = self._exec(
            "INSERT INTO requests (employee_id, item_id, justification, status, reason, ticket) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (employee_id, item_id, justification, status, reason, ticket))
        return cur.lastrowid


class AlloyDBRepository(SqlRepository):
    """AlloyDB for PostgreSQL. Run scripts/init_alloydb.py once to create tables and embeddings."""

    def __init__(self, dsn, embedding_model="text-embedding-005"):
        import psycopg  # optional dependency: pip install -e ".[alloydb]"
        from psycopg.rows import dict_row

        conn = psycopg.connect(dsn, row_factory=dict_row)
        super().__init__(conn, "%s")
        self.embedding_model = embedding_model

    def search_catalog(self, query, limit=3):
        """Semantic search: AlloyDB embeds the query with Vertex AI and ranks by cosine distance."""
        return self._all(
            "SELECT id, name, category, risk, cost, description FROM catalog "
            "ORDER BY embedding <=> embedding(?, ?)::vector LIMIT ?",
            (self.embedding_model, query, limit))


def load_seed(repo: SqlRepository):
    for e in seed.EMPLOYEES:
        repo._exec("INSERT INTO employees (id, name, team, manager_id) VALUES (?, ?, ?, ?)", e)
    for c in seed.CATALOG:
        repo._exec("INSERT INTO catalog (id, name, category, risk, cost, description) "
                   "VALUES (?, ?, ?, ?, ?, ?)", c)
    for item_id, n in seed.INVENTORY.items():
        repo._exec("INSERT INTO inventory (item_id, in_stock) VALUES (?, ?)", (item_id, n))
    for emp, items in seed.ASSETS.items():
        for item_id in items:
            repo._exec("INSERT INTO assets (employee_id, item_id) VALUES (?, ?)", (emp, item_id))


ALLOYDB_SCHEMA_FILE = Path(__file__).with_name("schema_alloydb.sql")
