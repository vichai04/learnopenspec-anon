import pytest

from core.db import connect, load_reference_data, query
from core.normalize import ReferenceIndex, normalize_visit, resolve_payer, resolve_sex


@pytest.fixture(scope="module")
def index():
    conn = connect()
    try:
        return ReferenceIndex(load_reference_data(conn))
    finally:
        conn.close()


def _visit_row(hcode, service_date, pttype="UC", visit_type="OPD", **extra):
    row = {
        "visit_id": f"V-{hcode}",
        "hcode": hcode,
        "hn": "HN1",
        "visit_type": visit_type,
        "service_date": service_date,
        "admit_date": None,
        "discharge_date": None,
        "pttype": pttype,
    }
    row.update(extra)
    return row


def _field(normalized, name):
    return next(f for f in normalized.fields if f.name == name)


@pytest.mark.parametrize(
    "hcode, service_date, expected",
    [
        ("90001", "25690809", "2026-08-09"),
        ("90002", "21/09/2569", "2026-09-21"),
        ("90003", "2569-09-19", "2026-09-19"),
        ("90004", "2026-09-14", "2026-09-14"),
    ],
)
def test_each_hospital_date_format_normalizes(index, hcode, service_date, expected):
    normalized = normalize_visit(index, _visit_row(hcode, service_date), None)
    field = _field(normalized, "service_date")
    assert field.canonical == expected
    assert field.error is None


def test_two_digit_buddhist_year_normalizes(index):
    normalized = normalize_visit(index, _visit_row("90003", "69-08-01"), None)
    assert _field(normalized, "service_date").canonical == "2026-08-01"


def test_unparseable_date_is_reported_as_error(index):
    local_code = next(local for (h, local) in index.payer_map if h == "90002")
    normalized = normalize_visit(index, _visit_row("90002", "2569-09-21", pttype=local_code), None)
    field = _field(normalized, "service_date")
    assert field.canonical is None
    assert "does not match" in field.error
    assert field in normalized.errors


def test_unmapped_payer_code_is_unresolved(index):
    field = resolve_payer(index, "90001", "NOT-A-CODE")
    assert field.canonical is None
    assert "unmapped payer code" in field.error


def test_mapped_payer_code_resolves(index):
    assert resolve_payer(index, "90001", "UC").canonical == "NHSO-UCS"
    assert resolve_payer(index, "90004", "11").canonical == "PRV-TSA"


def test_sex_codes_resolve_per_hospital(index):
    assert resolve_sex(index, "90003", "2").canonical == "female"
    assert resolve_sex(index, "90004", "M").canonical == "male"


def test_unmapped_sex_code_is_unresolved(index):
    field = resolve_sex(index, "90004", "X")
    assert field.canonical is None
    assert field.error is not None


def test_trace_lists_raw_rule_and_canonical_for_each_field(index):
    patient = {"sex": "M", "birth_date": "1959-01-09"}
    normalized = normalize_visit(index, _visit_row("90004", "2026-09-14"), patient)
    names = [f.name for f in normalized.fields]
    assert names == ["payer_id", "service_date", "sex", "birth_date"]
    for f in normalized.fields:
        assert f.rule
        assert f.raw is not None


def test_every_patient_and_visit_in_sample_data_normalizes_without_error(index):
    conn = connect()
    try:
        visits = query(conn, "SELECT * FROM visits")
        patients = {(p["hcode"], p["hn"]): p for p in query(conn, "SELECT * FROM patients")}
    finally:
        conn.close()
    errors = []
    for visit in visits:
        normalized = normalize_visit(index, visit, patients.get((visit["hcode"], visit["hn"])))
        errors.extend((visit["visit_id"], f.name, f.error) for f in normalized.errors)
    assert errors == []
