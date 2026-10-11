import sqlite3

import pytest

from core.db import REFERENCE_TABLES, connect, load_reference_data
from core.settings import DB_ENV_VAR, DatabaseMissingError, database_path


def test_reference_tables_load_with_expected_counts():
    conn = connect()
    try:
        data = load_reference_data(conn)
    finally:
        conn.close()
    assert set(data) == set(REFERENCE_TABLES)
    assert len(data["hospitals"]) == 4
    assert len(data["payers"]) == 5


def test_connection_rejects_writes():
    conn = connect()
    try:
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            conn.execute("DELETE FROM hospitals")
    finally:
        conn.close()


def test_missing_database_reports_how_to_fix(monkeypatch, tmp_path):
    monkeypatch.setenv(DB_ENV_VAR, str(tmp_path / "absent.sqlite"))
    with pytest.raises(DatabaseMissingError, match=DB_ENV_VAR):
        database_path()
