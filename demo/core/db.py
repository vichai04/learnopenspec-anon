"""Read-only access to claims_hub.sqlite."""

import sqlite3
from pathlib import Path

from .settings import database_path

REFERENCE_TABLES = (
    "ref_icd10",
    "ref_icd9cm",
    "ref_drug",
    "ref_service_item",
    "ref_reject_reason",
    "payers",
    "payer_rules",
    "hospitals",
    "hospital_payer_map",
    "hospital_sex_map",
)


def connect(path: Path | None = None) -> sqlite3.Connection:
    """Open the database with mode=ro so any write fails at the driver level."""
    db_path = Path(path) if path else database_path()
    uri = f"{db_path.resolve().as_uri()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def query(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> list[dict]:
    """Run a SELECT and return each row as a plain dict."""
    return [dict(row) for row in conn.execute(sql, params).fetchall()]


def load_reference_data(conn: sqlite3.Connection) -> dict[str, list[dict]]:
    """Read every reference table once. Keys are table names."""
    return {table: query(conn, f"SELECT * FROM {table}") for table in REFERENCE_TABLES}
