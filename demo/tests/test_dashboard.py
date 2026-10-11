from core.dashboard import compute_dashboard


def _claim(no, payer="NHSO-UCS", hcode="90001", status="submitted", amount=100.0):
    return {"claim_no": no, "payer_id": payer, "hcode": hcode, "claim_status": status,
            "claim_amount": amount}


def _sub(sid, no, status, submitted_at="2026-08-01"):
    return {"submission_id": sid, "claim_no": no, "response_status": status, "submitted_at": submitted_at}


REJECTS = {"R01": "Missing field"}


def test_status_counts_and_amounts():
    claims = [_claim("A", amount=100.0), _claim("B", status="pending", amount=50.5)]
    d = compute_dashboard(claims, [], [], REJECTS)
    assert d["status_counts"]["submitted"] == {"count": 1, "amount": 100.0}
    assert d["status_counts"]["pending"] == {"count": 1, "amount": 50.5}


def test_reject_rate_excludes_pended():
    claims = [_claim(str(i)) for i in range(10)]
    subs = [_sub(i, str(i), "rejected") for i in range(2)]
    subs += [_sub(10 + i, str(i + 2), "pended") for i in range(3)]
    subs += [_sub(20 + i, str(i + 5), "approved") for i in range(5)]
    d = compute_dashboard(claims, subs, [], REJECTS)
    assert d["reject_rate"] == 2 / 7
    assert d["outcomes"]["pended"] == 3


def test_reject_rate_is_none_without_final_outcomes():
    d = compute_dashboard([_claim("A")], [_sub(1, "A", "pended")], [], REJECTS)
    assert d["reject_rate"] is None


def test_reasons_ranked_with_descriptions():
    claims = [_claim("A")]
    subs = [_sub(1, "A", "rejected"), _sub(2, "A", "rejected")]
    reasons = [
        {"submission_id": 1, "reason_code": "R01", "message_th": "x"},
        {"submission_id": 2, "reason_code": "R01", "message_th": "y"},
    ]
    d = compute_dashboard(claims, subs, reasons, REJECTS)
    assert d["reasons"] == [{"code": "R01", "description": "Missing field", "count": 2}]


def test_uncoded_portal_messages_are_kept_as_unclassified():
    claims = [_claim("A")]
    subs = [_sub(1, "A", "rejected")]
    reasons = [{"submission_id": 1, "reason_code": None, "message_th": "กรุณาแนบเอกสาร"}]
    d = compute_dashboard(claims, subs, reasons, REJECTS)
    assert d["unclassified"]["count"] == 1
    assert d["unclassified"]["messages"] == [{"message": "กรุณาแนบเอกสาร", "count": 1}]


def test_payer_and_hospital_filters_apply_to_every_figure():
    claims = [_claim("A", payer="PRV-LTC", hcode="90002"), _claim("B", payer="NHSO-UCS", hcode="90001")]
    subs = [_sub(1, "A", "rejected"), _sub(2, "B", "approved")]
    assert compute_dashboard(claims, subs, [], REJECTS, payer="PRV-LTC")["outcomes"] == {"rejected": 1}
    assert compute_dashboard(claims, subs, [], REJECTS, hospital="90001")["outcomes"] == {"approved": 1}
    assert compute_dashboard(claims, subs, [], REJECTS, payer="PRV-LTC", hospital="90001")["outcomes"] == {}


def _dated(sid, no, status, submitted_at):
    return {"submission_id": sid, "claim_no": no, "response_status": status, "submitted_at": submitted_at}


def test_monthly_outcomes_group_by_submission_month_and_exclude_pended_from_rate():
    claims = [_claim("A"), _claim("B")]
    subs = [
        _dated(1, "A", "rejected", "2026-08-03"),
        _dated(2, "A", "approved", "2026-08-20"),
        _dated(3, "B", "pended", "2026-08-25"),
        _dated(4, "B", "partial", "2026-09-01"),
    ]
    monthly = compute_dashboard(claims, subs, [], REJECTS)["monthly"]
    assert [m["month"] for m in monthly] == ["2026-08", "2026-09"]
    aug, sep = monthly
    assert aug["rejected"] == 1 and aug["approved"] == 1 and aug["pended"] == 1
    assert aug["reject_rate"] == 1 / 2  # pended excluded
    assert sep["reject_rate"] == 0.0
    assert sep["partial"] == 1


def test_monthly_reject_rate_is_none_when_month_has_only_pended():
    claims = [_claim("A")]
    subs = [_dated(1, "A", "pended", "2026-10-01")]
    assert compute_dashboard(claims, subs, [], REJECTS)["monthly"][0]["reject_rate"] is None


def test_monthly_respects_payer_filter():
    claims = [_claim("A", payer="PRV-LTC"), _claim("B", payer="NHSO-UCS")]
    subs = [_dated(1, "A", "rejected", "2026-08-01"), _dated(2, "B", "approved", "2026-08-02")]
    monthly = compute_dashboard(claims, subs, [], REJECTS, payer="PRV-LTC")["monthly"]
    assert monthly == [{"month": "2026-08", "approved": 0, "partial": 0, "rejected": 1, "pended": 0, "reject_rate": 1.0}]
