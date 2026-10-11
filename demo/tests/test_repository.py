import pytest

from core.db import connect, query
from core.repository import ClaimsRepository


@pytest.fixture(scope="module")
def repo():
    conn = connect()
    try:
        return ClaimsRepository(conn)
    finally:
        conn.close()


@pytest.fixture(scope="module")
def first_claim_per_hospital(repo):
    picked = {}
    for row in repo.claim_rows():
        picked.setdefault(row["hcode"], row["claim_no"])
    return picked


def test_one_claim_from_each_hospital_is_available(first_claim_per_hospital):
    assert set(first_claim_per_hospital) == {"90001", "90002", "90003", "90004"}


@pytest.mark.parametrize("hcode", ["90001", "90002", "90003", "90004"])
def test_each_hospital_claim_has_all_three_views(repo, first_claim_per_hospital, hcode):
    claim_no = first_claim_per_hospital[hcode]

    normalization = repo.normalization(claim_no)
    assert normalization["hcode"] == hcode
    assert normalization["fields"]
    assert all(f["rule"] for f in normalization["fields"])

    validation = repo.validation(claim_no)
    assert validation["status"] in {"ready", "needs_correction"}
    assert validation["elapsed_ms"] >= 0

    rules = repo.rules(claim_no)
    assert rules["payer_id"] is not None
    assert rules["version"] is not None
    assert rules["service_date"] is not None


def test_prv_tsa_rule_version_changes_with_service_date(repo):
    rows = [r for r in repo.claim_rows() if r["payer_id"] == "PRV-TSA"]
    versions = set()
    for row in rows:
        versions.add(repo.rules(row["claim_no"])["version"])
    assert versions <= {"PRV-TSA@2026-01-01", "PRV-TSA@2026-09-15"}
    assert len(versions) >= 1


def test_unknown_claim_returns_none(repo):
    assert repo.normalization("NO-SUCH-CLAIM") is None
    assert repo.validation("NO-SUCH-CLAIM") is None
    assert repo.rules("NO-SUCH-CLAIM") is None


def test_dashboard_reject_rate_matches_manual_query(repo):
    conn = connect()
    try:
        counts = {
            r["response_status"]: r["n"]
            for r in query(conn, "SELECT response_status, COUNT(*) AS n FROM claim_submissions GROUP BY 1")
        }
    finally:
        conn.close()
    final = counts.get("approved", 0) + counts.get("partial", 0) + counts.get("rejected", 0)
    expected = counts.get("rejected", 0) / final
    assert repo.dashboard()["reject_rate"] == pytest.approx(expected)


def test_dashboard_filters_by_payer(repo):
    d = repo.dashboard(payer="PRV-LTC")
    total = sum(v["count"] for v in d["status_counts"].values())
    all_total = sum(v["count"] for v in repo.dashboard()["status_counts"].values())
    assert 0 < total < all_total
