from datetime import date

import pytest

from core.dates import DateParseError, parse_hospital_date
from core.db import connect, query

BE_DASH = "YYYY-MM-DD (พ.ศ.)"
BE_SLASH = "DD/MM/YYYY (พ.ศ.)"
BE_COMPACT = "YYYYMMDD (พ.ศ.)"
CE_DASH = "YYYY-MM-DD"


@pytest.mark.parametrize(
    "raw, fmt, expected",
    [
        ("25690801", BE_COMPACT, date(2026, 8, 1)),
        ("01/08/2569", BE_SLASH, date(2026, 8, 1)),
        ("2569-08-01", BE_DASH, date(2026, 8, 1)),
        ("2026-08-02", CE_DASH, date(2026, 8, 2)),
    ],
)
def test_full_year_formats(raw, fmt, expected):
    assert parse_hospital_date(raw, fmt) == expected


@pytest.mark.parametrize(
    "raw, fmt, expected",
    [
        ("690801", BE_COMPACT, date(2026, 8, 1)),
        ("21/09/69", BE_SLASH, date(2026, 9, 21)),
        ("69-08-01", BE_DASH, date(2026, 8, 1)),
    ],
)
def test_two_digit_buddhist_years(raw, fmt, expected):
    assert parse_hospital_date(raw, fmt) == expected


def test_unparseable_date_is_an_error_not_a_guess():
    with pytest.raises(DateParseError, match="does not match"):
        parse_hospital_date("21-09-2569", BE_SLASH)


def test_impossible_calendar_date_is_an_error():
    with pytest.raises(DateParseError, match="not a valid calendar date"):
        parse_hospital_date("31/02/2569", BE_SLASH)


def test_empty_value_is_an_error():
    with pytest.raises(DateParseError, match="empty"):
        parse_hospital_date("  ", BE_DASH)


def test_every_visit_date_in_the_bundled_database_parses():
    """Every date in the sample data must parse with its hospital's format."""
    conn = connect()
    try:
        hospitals = {h["hcode"]: h["date_format"] for h in query(conn, "SELECT * FROM hospitals")}
        rows = query(conn, "SELECT hcode, service_date, admit_date, discharge_date FROM visits")
        failures = []
        for row in rows:
            for field in ("service_date", "admit_date", "discharge_date"):
                if row[field] is None:
                    continue
                try:
                    parsed = parse_hospital_date(row[field], hospitals[row["hcode"]])
                except DateParseError as exc:
                    failures.append((row["hcode"], field, str(exc)))
                    continue
                assert date(2026, 1, 1) <= parsed <= date(2027, 12, 31), row
    finally:
        conn.close()
    assert failures == []
