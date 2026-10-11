"""Dashboard figures computed from plain records.

Inputs are the claim rows from claims.claim_list_row, submission rows, reason
rows, and the reject-reason reference. No database access happens here.
"""

from collections import Counter

FINAL_OUTCOMES = ("approved", "partial", "rejected")


def monthly_outcomes(subs: list[dict]) -> list[dict]:
    """Outcome counts per submission month (YYYY-MM), with the monthly reject rate.

    Uses the same reject-rate definition as the dashboard total: pended is excluded.
    """
    by_month: dict[str, Counter] = {}
    for s in subs:
        month = s["submitted_at"][:7]
        by_month.setdefault(month, Counter())[s["response_status"]] += 1
    rows = []
    for month in sorted(by_month):
        c = by_month[month]
        final = sum(c[k] for k in FINAL_OUTCOMES)
        rows.append(
            {
                "month": month,
                "approved": c["approved"],
                "partial": c["partial"],
                "rejected": c["rejected"],
                "pended": c["pended"],
                "reject_rate": (c["rejected"] / final) if final else None,
            }
        )
    return rows


def compute_dashboard(
    claim_rows: list[dict],
    submissions: list[dict],
    reasons: list[dict],
    reject_reasons: dict[str, str],
    payer: str | None = None,
    hospital: str | None = None,
) -> dict:
    """Return status counts, outcome counts, reject rate, and reason ranking.

    payer and hospital are optional filters; None means all.
    """
    claims = [
        c
        for c in claim_rows
        if (payer is None or c["payer_id"] == payer) and (hospital is None or c["hcode"] == hospital)
    ]
    claim_nos = {c["claim_no"] for c in claims}
    subs = [s for s in submissions if s["claim_no"] in claim_nos]
    sub_ids = {s["submission_id"] for s in subs}
    reason_rows = [r for r in reasons if r["submission_id"] in sub_ids]

    status_counts: dict[str, dict] = {}
    for c in claims:
        bucket = status_counts.setdefault(c["claim_status"], {"count": 0, "amount": 0.0})
        bucket["count"] += 1
        bucket["amount"] += float(c["claim_amount"] or 0)

    outcomes = Counter(s["response_status"] for s in subs)
    final = sum(outcomes[k] for k in FINAL_OUTCOMES)
    reject_rate = (outcomes["rejected"] / final) if final else None

    coded = Counter(r["reason_code"] for r in reason_rows if r["reason_code"])
    ranking = [
        {"code": code, "description": reject_reasons.get(code, ""), "count": n}
        for code, n in coded.most_common()
    ]
    uncoded = Counter(r["message_th"] for r in reason_rows if not r["reason_code"])
    unclassified = {
        "count": sum(uncoded.values()),
        "messages": [{"message": m, "count": n} for m, n in uncoded.most_common()],
    }

    return {
        "monthly": monthly_outcomes(subs),
        "status_counts": status_counts,
        "outcomes": dict(outcomes),
        "reject_rate": reject_rate,
        "reasons": ranking,
        "unclassified": unclassified,
    }
