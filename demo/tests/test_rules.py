from datetime import date

import pytest

from tests.helpers import make_ctx
from core.db import connect, load_reference_data
from core.rules import CATALOGUE, evaluate_rules, select_rule_version, unrecognized_rules
from core.rules import RuleVersion


@pytest.fixture(scope="module")
def payer_rules():
    conn = connect()
    try:
        return load_reference_data(conn)["payer_rules"]
    finally:
        conn.close()


def _version(payer_rules, payer, effective):
    version = select_rule_version(payer_rules, payer, effective)
    assert version is not None
    return version


def test_prv_tsa_before_change_uses_january_version(payer_rules):
    version = _version(payer_rules, "PRV-TSA", date(2026, 8, 1))
    assert version.version == "PRV-TSA@2026-01-01"
    assert version.effective_from == date(2026, 1, 1)


def test_prv_tsa_after_change_uses_september_version(payer_rules):
    version = _version(payer_rules, "PRV-TSA", date(2026, 10, 1))
    assert version.version == "PRV-TSA@2026-09-15"


def test_service_date_on_effective_day_uses_new_version(payer_rules):
    assert _version(payer_rules, "PRV-TSA", date(2026, 9, 15)).version == "PRV-TSA@2026-09-15"


def test_no_version_before_first_effective_date(payer_rules):
    assert select_rule_version(payer_rules, "PRV-TSA", date(2025, 12, 31)) is None


def test_unknown_payer_has_no_rules(payer_rules):
    assert select_rule_version(payer_rules, "NOPE", date(2026, 8, 1)) is None


def test_unknown_rule_type_is_reported_not_ignored():
    rows = [{"rule_type": "mystery_rule", "rule_value": "x", "payer_id": "P", "rule_version": "v",
             "effective_from": "2026-01-01", "description": ""}]
    version = RuleVersion("P", "v", date(2026, 1, 1), rows)
    assert unrecognized_rules(version) == rows
    assert "mystery_rule" not in CATALOGUE


def test_known_rule_types_are_all_catalogued(payer_rules):
    types = {r["rule_type"] for r in payer_rules}
    assert types - CATALOGUE == set()


def test_room_limit_violation_is_reported():
    rows = [{"rule_type": "room_limit_per_day_thb", "rule_value": "3000", "payer_id": "P",
             "rule_version": "v", "effective_from": "2026-01-01", "description": ""}]
    version = RuleVersion("P", "v", date(2026, 1, 1), rows)
    ctx = make_ctx(charges=[{"item_type": "SERVICE", "item_code": "SV-ROOM", "qty": 1,
                             "unit_price": 4500.0, "amount": 4500.0}])
    failures = evaluate_rules(version, ctx)
    assert [f.rule_id for f in failures] == ["room_limit_per_day_thb:3000"]


def test_preauth_required_for_ipd_without_number():
    rows = [{"rule_type": "preauth_required_for", "rule_value": "IPD", "payer_id": "P",
             "rule_version": "v", "effective_from": "2026-01-01", "description": ""}]
    version = RuleVersion("P", "v", date(2026, 1, 1), rows)
    assert evaluate_rules(version, make_ctx(visit_type="IPD")) != []
    assert evaluate_rules(version, make_ctx(visit_type="IPD", preauth_no="PA1")) == []
    assert evaluate_rules(version, make_ctx(visit_type="OPD")) == []


def test_excluded_prefix_matches_any_diagnosis():
    rows = [{"rule_type": "excluded_dx_prefix", "rule_value": "Z41", "payer_id": "P",
             "rule_version": "v", "effective_from": "2026-01-01", "description": ""}]
    version = RuleVersion("P", "v", date(2026, 1, 1), rows)
    ctx = make_ctx(diagnoses=[{"icd10": "Z41.1", "diag_type": "1"}])
    assert [f.rule_id for f in evaluate_rules(version, ctx)] == ["excluded_dx_prefix:Z41"]


def test_resubmission_rules_are_not_checked_before_submission():
    rows = [{"rule_type": "resubmission_max_attempts", "rule_value": "2", "payer_id": "P",
             "rule_version": "v", "effective_from": "2026-01-01", "description": ""}]
    version = RuleVersion("P", "v", date(2026, 1, 1), rows)
    assert evaluate_rules(version, make_ctx()) == []
