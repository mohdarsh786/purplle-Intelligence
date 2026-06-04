"""
SQLite Connection & Helper Functions — Task 3.3

Thread-safe database access with context-managed connections
and auto-schema initialization on first run.

Usage:
    from api.db.sqlite import initialize_db, execute, fetchone, fetchall, fetchall_as_dict
"""

import logging
import os
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DB_PATH = os.environ.get("DATABASE_PATH", os.path.join("storage", "store.db"))
SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("sqlite")

# ---------------------------------------------------------------------------
# Thread-safety lock for schema initialization
# ---------------------------------------------------------------------------
_init_lock = threading.Lock()
_initialized = False


# ---------------------------------------------------------------------------
# Connection Management
# ---------------------------------------------------------------------------

@contextmanager
def get_connection(db_path: str | None = None) -> Generator[sqlite3.Connection, None, None]:
    """
    Context-managed SQLite connection.

    Ensures the storage directory exists, enables WAL mode for
    better concurrent-read performance, and commits on clean exit
    or rolls back on exception.
    """
    path = db_path or DB_PATH

    # Ensure the parent directory exists
    db_dir = os.path.dirname(path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    conn = sqlite3.connect(path, timeout=10.0)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Schema Initialization
# ---------------------------------------------------------------------------


def initialize_db(db_path: str | None = None) -> None:
    """
    Auto-create all tables and indexes from schema.sql.

    Safe to call multiple times — uses a module-level lock and
    flag so the schema is applied only once per process lifetime.
    """
    global _initialized

    if _initialized:
        return

    with _init_lock:
        if _initialized:  # double-check after acquiring lock
            return

        if not os.path.isfile(SCHEMA_PATH):
            logger.error("Schema file not found: %s", SCHEMA_PATH)
            raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")

        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            schema_sql = f.read()

        with get_connection(db_path) as conn:
            conn.executescript(schema_sql)
            logger.info("Database schema applied successfully from %s", SCHEMA_PATH)

        _initialized = True


# ---------------------------------------------------------------------------
# Query Helpers
# ---------------------------------------------------------------------------


def execute(
    sql: str,
    params: tuple[Any, ...] | dict[str, Any] = (),
    db_path: str | None = None,
) -> int:
    """
    Execute a write query (INSERT, UPDATE, DELETE).

    Returns the number of rows affected (cursor.rowcount).
    """
    with get_connection(db_path) as conn:
        cursor = conn.execute(sql, params)
        return cursor.rowcount


def fetchone(
    sql: str,
    params: tuple[Any, ...] | dict[str, Any] = (),
    db_path: str | None = None,
) -> sqlite3.Row | None:
    """
    Execute a read query and return a single row (sqlite3.Row)
    or None if no results.
    """
    with get_connection(db_path) as conn:
        cursor = conn.execute(sql, params)
        return cursor.fetchone()


def fetchall(
    sql: str,
    params: tuple[Any, ...] | dict[str, Any] = (),
    db_path: str | None = None,
) -> list[sqlite3.Row]:
    """
    Execute a read query and return all matching rows
    as a list of sqlite3.Row objects.
    """
    with get_connection(db_path) as conn:
        cursor = conn.execute(sql, params)
        return cursor.fetchall()


def fetchall_as_dict(
    sql: str,
    params: tuple[Any, ...] | dict[str, Any] = (),
    db_path: str | None = None,
) -> list[dict[str, Any]]:
    """
    Execute a read query and return all matching rows
    as a list of plain dicts (column_name → value).
    """
    with get_connection(db_path) as conn:
        cursor = conn.execute(sql, params)
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
