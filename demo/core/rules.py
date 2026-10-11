"""Payer rule selection and rule-type handlers.

A rule version applies when its effective_from is the latest date on or before
the service date. Each catalogued rule_type has one handler. Unknown types are
reported, never ignored.
"""

from dataclasses import dataclass
from datetime import date

from .claims import ClaimContext

ROOM_CODE = "SV-ROOM"


@dataclass(frozen=True)
class Failure:
    rule_id: str
    field: str
    message_th: str
    message_en: str


@dataclass
class RuleVersion:
    payer_id: str
    version: str
    effective_from: date
    rows: list[dict]


def select_rule_version(rules: list[dict], payer_id: str, service_date: date) -> RuleVersion | None:
    """Pick the latest version effective on or before service_date. No fallback to later versions."""
    candidates: dict[str, list[dict]] = {}
    for row in rules:
        if row["payer_id"] == payer_id and row["effective_from"] <= service_date.isoformat():
            candidates.setdefault(row["rule_version"], []).append(row)
    if not candidates:
        return None
    version, rows = max(candidates.items(), key=lambda kv: kv[1][0]["effective_from"])
    return RuleVersion(
        payer_id=payer_id,
        version=version,
        effective_from=date.fromisoformat(rows[0]["effective_from"]),
        rows=rows,
    )


def _excluded_prefix(row: dict, ctx: ClaimContext) -> list[Failure]:
    prefix = row["rule_value"]
    return [
        Failure(
            rule_id=f"excluded_dx_prefix:{prefix}",
            field="diagnosis",
            message_th=f"รหัสโรค {d['icd10']} อยู่ในกลุ่มที่ payer ไม่คุ้มครอง ({prefix})",
            message_en=f"Diagnosis {d['icd10']} is in a prefix this payer excludes ({prefix})",
        )
        for d in ctx.diagnoses
        if d["icd10"].startswith(prefix)
    ]


def _required_documents(row: dict, ctx: ClaimContext) -> list[Failure]:
    doc_type = row["rule_value"]
    if row["rule_type"] == "required_document_ipd":
        applies = ctx.visit_type == "IPD"
    else:
        applies = bool(ctx.procedures)
    if not applies or doc_type in ctx.document_types:
        return []
    return [
        Failure(
            rule_id=f"{row['rule_type']}:{doc_type}",
            field="documents",
            message_th=f"ขาดเอกสารประกอบ: {doc_type}",
            message_en=f"Missing required document: {doc_type}",
        )
    ]


def _room_limit(row: dict, ctx: ClaimContext) -> list[Failure]:
    limit = float(row["rule_value"])
    return [
        Failure(
            rule_id=f"room_limit_per_day_thb:{limit:g}",
            field="charge_items",
            message_th=f"ค่าห้องต่อวัน {c['unit_price']:g} บาท เกินวงเงิน {limit:g} บาท",
            message_en=f"Room charge {c['unit_price']:g} THB per day exceeds limit {limit:g} THB",
        )
        for c in ctx.charges
        if c["item_code"] == ROOM_CODE and c["unit_price"] is not None and c["unit_price"] > limit
    ]


def _opd_limit(row: dict, ctx: ClaimContext) -> list[Failure]:
    limit = float(row["rule_value"])
    if ctx.visit_type != "OPD" or ctx.claim_amount is None or ctx.claim_amount <= limit:
        return []
    return [
        Failure(
            rule_id=f"opd_limit_per_visit_thb:{limit:g}",
            field="claim_amount",
            message_th=f"ยอดเคลม OPD {ctx.claim_amount:g} บาท เกินวงเงิน {limit:g} บาทต่อครั้ง",
            message_en=f"OPD claim {ctx.claim_amount:g} THB exceeds {limit:g} THB per visit",
        )
    ]


def _preauth_required_for(row: dict, ctx: ClaimContext) -> list[Failure]:
    if ctx.visit_type != row["rule_value"] or ctx.preauth_no:
        return []
    return [
        Failure(
            rule_id=f"preauth_required_for:{row['rule_value']}",
            field="preauth_no",
            message_th=f"ต้องมีเลขอนุมัติล่วงหน้าสำหรับ {row['rule_value']}",
            message_en=f"Prior authorization is required for {row['rule_value']}",
        )
    ]


def _preauth_min_total(row: dict, ctx: ClaimContext) -> list[Failure]:
    threshold = float(row["rule_value"])
    if ctx.claim_amount is None or ctx.claim_amount < threshold or ctx.preauth_no:
        return []
    return [
        Failure(
            rule_id=f"preauth_min_total_thb:{threshold:g}",
            field="preauth_no",
            message_th=f"ยอดเคลม {ctx.claim_amount:g} บาท ถึงเกณฑ์ต้องขออนุมัติล่วงหน้า ({threshold:g} บาท)",
            message_en=f"Claim {ctx.claim_amount:g} THB reaches the prior-authorization threshold ({threshold:g} THB)",
        )
    ]


def _not_checked_before_submission(row: dict, ctx: ClaimContext) -> list[Failure]:
    """Resubmission limits need submission history, which pre-submission validation does not have."""
    return []


# rule_type -> handler(row, ctx) -> failures.
# required_field is checked by validate.py because it needs the canonical field getters.
HANDLERS = {
    "excluded_dx_prefix": _excluded_prefix,
    "required_document_ipd": _required_documents,
    "required_document_surgery": _required_documents,
    "room_limit_per_day_thb": _room_limit,
    "opd_limit_per_visit_thb": _opd_limit,
    "preauth_required_for": _preauth_required_for,
    "preauth_min_total_thb": _preauth_min_total,
    "resubmission_max_attempts": _not_checked_before_submission,
    "resubmission_window_days": _not_checked_before_submission,
}

CATALOGUE = HANDLERS.keys() | {"required_field"}


def unrecognized_rules(version: RuleVersion) -> list[dict]:
    return [row for row in version.rows if row["rule_type"] not in CATALOGUE]


def evaluate_rules(version: RuleVersion, ctx: ClaimContext) -> list[Failure]:
    failures: list[Failure] = []
    for row in version.rows:
        handler = HANDLERS.get(row["rule_type"])
        if handler is not None:
            failures.extend(handler(row, ctx))
    return failures
