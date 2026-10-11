from datetime import date

import pytest

from core.db import connect, load_reference_data
from core.validate import validate_claim
from tests.helpers import make_ctx


@pytest.fixture(scope="module")
def ref():
    conn = connect()
    try:
        data = load_reference_data(conn)
    finally:
        conn.close()
    return {
        "rules": data["payer_rules"],
        "icd10": {r["code"]: r for r in data["ref_icd10"]},
        "icd9": {r["code"]: r for r in data["ref_icd9cm"]},
        "drug": {r["drug_code"] for r in data["ref_drug"]},
        "service": {r["item_code"] for r in data["ref_service_item"]},
    }


def _run(ref, ctx):
    return validate_claim(ctx, ref["rules"], ref["icd10"], ref["icd9"], ref["drug"], ref["service"])


def _codes(result):
    return {f.rule_id for f in result.failures}


def test_clean_claim_is_ready(ref):
    ctx = make_ctx(
        payer_id="NHSO-UCS",
        service_date=date(2026, 8, 1),
        charges=[{"item_type": "SERVICE", "item_code": "SV-OPD", "qty": 1,
                  "unit_price": 100.0, "amount": 100.0}],
        claim_amount=100.0,
    )
    result = _run(ref, ctx)
    assert result.status == "ready", result.failures
    assert result.failures == []
    assert result.rule_version == "NHSO-UCS@2026-01-01"


def test_missing_required_field_is_reported(ref):
    result = _run(ref, make_ctx(payer_id="PRV-TSA", service_date=date(2026, 8, 1), policy_no=None,
                                claim_amount=0.0))
    assert "required_field:insurance.policyNumber" in _codes(result)
    assert result.status == "needs_correction"


def test_all_failures_returned_together(ref):
    ctx = make_ctx(
        payer_id="PRV-TSA",
        service_date=date(2026, 8, 1),
        doctor_license=None,
        preauth_no=None,
        visit_type="IPD",
        diagnoses=[{"icd10": "N40", "diag_type": "1"}, {"icd10": "Z41.1", "diag_type": "2"}],
        claim_amount=25000.0,
        charges=[],
    )
    codes = _codes(_run(ref, ctx))
    assert "required_field:encounter.attendingLicense" in codes
    assert "icd10:sex:N40" in codes  # N40 is restricted to male, patient is female
    assert "excluded_dx_prefix:Z41" in codes
    assert "preauth_required_for:IPD" in codes
    assert len(codes) >= 4


def test_unknown_icd10_code_is_a_failure(ref):
    result = _run(ref, make_ctx(payer_id="NHSO-UCS", service_date=date(2026, 8, 1),
                                diagnoses=[{"icd10": "ZZZ.9", "diag_type": "1"}]))
    assert "icd10:unknown:ZZZ.9" in _codes(result)


def test_icd10_age_out_of_range_is_a_failure(ref):
    result = _run(ref, make_ctx(payer_id="NHSO-UCS", service_date=date(2026, 8, 1), age=8,
                                diagnoses=[{"icd10": "O80", "diag_type": "1"}]))
    assert "icd10:age:O80" in _codes(result)


def test_icd9_requires_dx(ref):
    result = _run(ref, make_ctx(payer_id="NHSO-UCS", service_date=date(2026, 8, 1),
                                procedures=[{"icd9cm": "74.1"}],
                                diagnoses=[{"icd10": "J06.9", "diag_type": "1"}]))
    assert "icd9cm:requires_dx:74.1" in _codes(result)


def test_unknown_drug_code_is_a_failure(ref):
    ctx = make_ctx(payer_id="NHSO-UCS", service_date=date(2026, 8, 1), claim_amount=10.0,
                   charges=[{"item_type": "DRUG", "item_code": "NOT-A-DRUG", "qty": 1,
                             "unit_price": 10.0, "amount": 10.0}])
    assert "charge:unknown:NOT-A-DRUG" in _codes(_run(ref, ctx))


def test_line_amount_mismatch_is_a_failure(ref):
    ctx = make_ctx(payer_id="NHSO-UCS", service_date=date(2026, 8, 1), claim_amount=100.0,
                   charges=[{"item_type": "SERVICE", "item_code": "SV-OPD", "qty": 2,
                             "unit_price": 100.0, "amount": 100.0}])
    assert "amount:line:SV-OPD" in _codes(_run(ref, ctx))


def test_claim_total_mismatch_is_a_failure(ref):
    ctx = make_ctx(payer_id="NHSO-UCS", service_date=date(2026, 8, 1), claim_amount=150.0,
                   charges=[{"item_type": "SERVICE", "item_code": "SV-OPD", "qty": 1,
                             "unit_price": 100.0, "amount": 100.0}])
    assert "amount:total" in _codes(_run(ref, ctx))


def test_missing_claim_amount_is_a_failure(ref):
    ctx = make_ctx(payer_id="NHSO-UCS", service_date=date(2026, 8, 1), claim_amount=None)
    assert "amount:missing" in _codes(_run(ref, ctx))


def test_unresolved_payer_stops_rule_checks_and_reports(ref):
    ctx = make_ctx(payer_id=None, service_date=date(2026, 8, 1))
    result = _run(ref, ctx)
    assert "normalization" in _codes(result)
    assert result.rule_version is None


def test_elapsed_time_is_reported(ref):
    result = _run(ref, make_ctx(payer_id="NHSO-UCS", service_date=date(2026, 8, 1)))
    assert result.elapsed_ms >= 0
