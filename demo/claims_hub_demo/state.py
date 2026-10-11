"""Reflex state: thin handlers that call the repository and format values for display.

Pages read flat variables with defaults, so a page renders correctly before its
data loads and never indexes a key that might be missing.
"""

import reflex as rx

from core.db import connect
from core.repository import ClaimsRepository
from core.settings import DatabaseMissingError

from .i18n import STRINGS

CLAIM_LIST_LIMIT = 100
CHART_REASON_LIMIT = 8

# Same palette as theme.COLORS, used for chart fills.
STATUS_COLORS = {
    "submitted": "#34d399",
    "pending": "#fbbf24",
}

_repo: ClaimsRepository | None = None
_load_error: str = ""


def load_repository() -> None:
    """Read the database once at startup. The error is kept so pages can show it."""
    global _repo, _load_error
    try:
        conn = connect()
        try:
            _repo = ClaimsRepository(conn)
        finally:
            conn.close()
        _load_error = ""
    except DatabaseMissingError as exc:
        _repo = None
        _load_error = str(exc)


def repository() -> ClaimsRepository | None:
    return _repo


def _pct(value: float | None) -> str:
    return "—" if value is None else f"{value * 100:.1f}%"


def _money(value: float | None) -> str:
    return "—" if value is None else f"{value:,.2f}"


def _claim_summary_row(summary: dict) -> dict:
    return {
        "claim_no": summary["claim_no"],
        "visit_id": summary["visit_id"],
        "hospital_name": summary["hospital_name"] or "",
        "payer_id": summary["payer_id"] or "—",
        "claim_status": summary["claim_status"],
        "amount": _money(summary["claim_amount"]),
    }


EMPTY_CLAIM = {
    "claim_no": "",
    "visit_id": "",
    "hospital_name": "",
    "payer_id": "",
    "claim_status": "",
    "amount": "",
}


class AppState(rx.State):
    lang: str = "th"
    error: str = ""
    payer: str = ""
    hospital: str = ""

    # dashboard
    payer_options: list[dict] = []
    hospital_options: list[dict] = []
    metric_claims: int = 0
    metric_pending: int = 0
    metric_reject_rate: str = "—"
    outcomes: list[dict] = []
    reasons: list[dict] = []
    unclassified: list[dict] = []
    unclassified_count: int = 0

    # chart data (numbers, not formatted strings)
    chart_status: list[dict] = []
    chart_monthly: list[dict] = []
    chart_reasons: list[dict] = []

    # claim list
    claims: list[dict] = []
    claims_total: int = 0

    # one claim
    claim_no: str = ""
    claim: dict = EMPTY_CLAIM

    # normalization
    norm_fields: list[dict] = []
    norm_hospital: str = ""
    norm_date_format: str = ""
    norm_error_count: int = 0

    # validation
    val_status: str = ""
    val_rule_version: str = ""
    val_elapsed_ms: str = ""
    failures: list[dict] = []

    # rules
    rule_payer: str = ""
    rule_service_date: str = ""
    rule_version: str = ""
    rule_effective_from: str = ""
    rule_rows: list[dict] = []
    rule_unrecognized: list[str] = []
    rule_history: list[str] = []

    @rx.var
    def s(self) -> dict:
        """Current-language UI strings."""
        return STRINGS[self.lang]

    def _ready(self) -> bool:
        if _repo is None:
            self.error = _load_error or "database not loaded"
            return False
        self.error = ""
        return True

    def _refresh_dashboard(self) -> None:
        d = repository().dashboard(payer=self.payer, hospital=self.hospital)
        self.metric_claims = sum(v["count"] for v in d["status_counts"].values())
        self.metric_pending = d["status_counts"].get("pending", {"count": 0})["count"]
        self.metric_reject_rate = _pct(d["reject_rate"])
        self.outcomes = [{"status": k, "count": v} for k, v in sorted(d["outcomes"].items())]
        self.reasons = [
            {"code": r["code"], "description": r["description"], "count": r["count"]} for r in d["reasons"]
        ]
        self.unclassified = d["unclassified"]["messages"]
        self.unclassified_count = d["unclassified"]["count"]
        self.chart_status = [
            {"name": k, "value": v["count"], "fill": STATUS_COLORS.get(k, "#8b9ab0")}
            for k, v in sorted(d["status_counts"].items())
        ]
        self.chart_monthly = [
            {
                "month": m["month"],
                "approved": m["approved"],
                "partial": m["partial"],
                "rejected": m["rejected"],
                "pended": m["pended"],
                "reject_rate": None if m["reject_rate"] is None else round(m["reject_rate"] * 100, 1),
            }
            for m in d["monthly"]
        ]
        self.chart_reasons = [
            {"code": r["code"], "count": r["count"]} for r in d["reasons"][:CHART_REASON_LIMIT]
        ]

    def on_load_dashboard(self):
        if not self._ready():
            return
        repo = repository()
        self.payer_options = [
            {"value": p["payer_id"], "label": f"{p['payer_name']} ({p['payer_id']})"} for p in repo.payers()
        ]
        self.hospital_options = [{"value": h["hcode"], "label": h["hospital_name"]} for h in repo.hospitals()]
        self._refresh_dashboard()

    def set_payer(self, value: str):
        self.payer = "" if value == "all" else value
        self._refresh_dashboard()

    def set_hospital(self, value: str):
        self.hospital = "" if value == "all" else value
        self._refresh_dashboard()

    def toggle_lang(self):
        self.lang = "en" if self.lang == "th" else "th"

    def on_load_claims(self):
        if not self._ready():
            return
        rows = repository().claim_rows()
        self.claims_total = len(rows)
        self.claims = [
            {
                **_claim_summary_row(r),
                "normalization_href": f"/claims/{r['claim_no']}/normalization",
                "validation_href": f"/claims/{r['claim_no']}/validation",
                "rules_href": f"/claims/{r['claim_no']}/rules",
            }
            for r in rows[:CLAIM_LIST_LIMIT]
        ]

    def _load_claim(self) -> str | None:
        """Load the claim named in the route. Returns its number, or None if not found."""
        claim_no = self.router.page.params.get("claim_no", "")
        summary = repository().claim_summary(claim_no)
        if summary is None:
            self.error = STRINGS[self.lang]["claim_not_found"].format(claim_no=claim_no)
            self.claim = EMPTY_CLAIM
            return None
        self.error = ""
        self.claim_no = claim_no
        self.claim = _claim_summary_row(summary)
        return claim_no

    def on_load_normalization(self):
        if not self._ready():
            return
        claim_no = self._load_claim()
        if claim_no is None:
            return
        n = repository().normalization(claim_no)
        self.norm_fields = [{k: "—" if v is None else str(v) for k, v in f.items()} for f in n["fields"]]
        self.norm_hospital = n["hospital_name"]
        self.norm_date_format = n["date_format"]
        self.norm_error_count = n["error_count"]

    def on_load_validation(self):
        if not self._ready():
            return
        claim_no = self._load_claim()
        if claim_no is None:
            return
        v = repository().validation(claim_no)
        self.val_status = v["status"]
        self.val_rule_version = v["rule_version"] or ""
        self.val_elapsed_ms = f"{v['elapsed_ms']:.3f}"
        self.failures = v["failures"]

    def on_load_rules(self):
        if not self._ready():
            return
        claim_no = self._load_claim()
        if claim_no is None:
            return
        r = repository().rules(claim_no)
        self.rule_payer = r["payer_id"] or ""
        self.rule_service_date = r["service_date"] or ""
        self.rule_version = r["version"] or ""
        self.rule_effective_from = r.get("effective_from") or ""
        self.rule_rows = r["rows"]
        self.rule_unrecognized = r["unrecognized"]
        self.rule_history = r["history_rules"]
