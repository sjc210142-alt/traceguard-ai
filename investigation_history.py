import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

DATABASE_PATH = Path(__file__).resolve().parent / "traceguard_history.db"


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    """Create and return a SQLite database connection."""

    connection = sqlite3.connect(
        str(DATABASE_PATH),
        timeout=10
    )

    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


# ============================================================
# INITIALIZE DATABASE
# ============================================================

def initialize_database():
    """Create the investigation history table and indexes."""

    with get_connection() as connection:

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS investigation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id TEXT NOT NULL,
                risk_score INTEGER NOT NULL,
                risk_level TEXT NOT NULL,
                reasons TEXT NOT NULL,
                ai_report TEXT DEFAULT '',
                investigated_at TEXT NOT NULL
            )
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_investigation_transaction
            ON investigation_history(transaction_id)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_investigation_date
            ON investigation_history(investigated_at)
            """
        )

        connection.commit()


# ============================================================
# SAVE INVESTIGATION
# ============================================================

def save_investigation(
    transaction_id,
    risk_score,
    risk_level,
    reasons,
    ai_report=""
):
    """Save an investigation result and return its database ID."""

    if transaction_id is None or not str(transaction_id).strip():
        raise ValueError("Transaction ID cannot be empty.")

    try:
        risk_score = int(risk_score)
    except (TypeError, ValueError):
        raise ValueError("Risk score must be an integer.")

    if not 0 <= risk_score <= 100:
        raise ValueError("Risk score must be between 0 and 100.")

    risk_level = str(risk_level).strip().upper()

    allowed_levels = {"LOW", "MEDIUM", "HIGH", "UNKNOWN"}

    if risk_level not in allowed_levels:
        raise ValueError(
            "Risk level must be LOW, MEDIUM, HIGH, or UNKNOWN."
        )

    if reasons is None:
        reasons = []
    elif isinstance(reasons, str):
        reasons = [reasons]
    elif not isinstance(reasons, list):
        reasons = list(reasons)

    reasons_json = json.dumps(reasons, ensure_ascii=False)

    investigated_at = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:

        cursor = connection.execute(
            """
            INSERT INTO investigation_history (
                transaction_id,
                risk_score,
                risk_level,
                reasons,
                ai_report,
                investigated_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                str(transaction_id).strip(),
                risk_score,
                risk_level,
                reasons_json,
                str(ai_report or ""),
                investigated_at
            )
        )

        connection.commit()

        return cursor.lastrowid


# ============================================================
# GET INVESTIGATION HISTORY
# ============================================================

def get_investigation_history(limit=200):
    """Return the most recent investigation records."""

    try:
        limit = int(limit)
    except (TypeError, ValueError):
        limit = 200

    limit = max(1, min(limit, 1000))

    with get_connection() as connection:

        cursor = connection.execute(
            """
            SELECT *
            FROM investigation_history
            ORDER BY investigated_at DESC, id DESC
            LIMIT ?
            """,
            (limit,)
        )

        rows = cursor.fetchall()

    records = []

    for row in rows:

        record = dict(row)

        try:
            record["reasons"] = json.loads(
                record.get("reasons") or "[]"
            )
        except (json.JSONDecodeError, TypeError):
            record["reasons"] = []

        records.append(record)

    return records


# ============================================================
# SEARCH INVESTIGATIONS
# ============================================================

def search_investigations(transaction_id):
    """Search investigation history using a transaction ID."""

    if transaction_id is None or not str(transaction_id).strip():
        return []

    with get_connection() as connection:

        cursor = connection.execute(
            """
            SELECT *
            FROM investigation_history
            WHERE transaction_id = ?
            ORDER BY investigated_at DESC, id DESC
            """,
            (str(transaction_id).strip(),)
        )

        rows = cursor.fetchall()

    records = []

    for row in rows:

        record = dict(row)

        try:
            record["reasons"] = json.loads(
                record.get("reasons") or "[]"
            )
        except (json.JSONDecodeError, TypeError):
            record["reasons"] = []

        records.append(record)

    return records


# ============================================================
# DELETE ONE INVESTIGATION
# ============================================================

def delete_investigation(investigation_id):
    """Delete one investigation record. Return True if deleted."""

    try:
        investigation_id = int(investigation_id)
    except (TypeError, ValueError):
        return False

    with get_connection() as connection:

        cursor = connection.execute(
            """
            DELETE FROM investigation_history
            WHERE id = ?
            """,
            (investigation_id,)
        )

        connection.commit()

        return cursor.rowcount > 0


# ============================================================
# CLEAR ALL INVESTIGATION HISTORY
# ============================================================

def clear_investigation_history():
    """Delete all saved investigation records."""

    with get_connection() as connection:

        connection.execute(
            "DELETE FROM investigation_history"
        )

        connection.commit()