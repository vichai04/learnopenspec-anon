"""Pre-submission validation: payer rules plus reference-table checks.

Every failure is returned, not only the first. The elapsed time covers the
validation itself, not data loading, so it can be compared with the PRD target.
"""

import time
from dataclasses import dataclass, field

from .claims import ClaimContext
from .rules import Failure, RuleVersion, evaluate_rules, select_rule_version

AMOUNT_TOLERANCE = 0.01

# Canonical field name -> getter on the claim context.
REQUIRED_FIELD_GETTERS = {
    "patient.nationalId": lambda c: c.cid,
    "encounter.attendingLicense": lambda c: c.doctor_license,
    "encounter.hcode": lambda c: c.hcode,
    "encounter.chiefComplaint": lambda c: c.chief_complaint,
    "insurance.policyNumber": lambda c: c.policy_no,
    "diagnosis.principal": lambda c: next((d for d in c.diagnoses if d["diag_type"] == "1"), None),
}


@dataclass
class ValidationResult:
    claim_no: str
    status: str  # "ready" or "needs_correction"
    failures: list[Failure] = field(default_factory=list)
    rule_version: str | None = None
    elapsed_ms: float = 0.0


def _required_fields(version: RuleVersion, ctx: ClaimContext) -> list[Failure]:
    failures = []
    for row in version.rows:
        if row["rule_type"] != "required_field":
            continue
        name = row["rule_value"]
        getter = REQUIRED_FIELD_GETTERS.get(name)
        if getter is None:
            failures.append(
                Failure(f"required_field:{name}", name, f"ไม่รู้จักฟิลด์ {name}", f"Unknown required field {name}")
            )
            continue
        if not getter(ctx):
            failures.append(
                Failure(f"required_field:{name}", name, f"ขาดข้อมูลที่บังคับ: {name}", f"Missing required field: {name}")
            )
    return failures


def _icd10_checks(ctx: ClaimContext, icd10_ref: dict[str, dict]) -> list[Failure]:
    failures = []
    for d in ctx.diagnoses:
        code = d["icd10"]
        ref = icd10_ref.get(code)
        if ref is None:
            failures.append(
                Failure(f"icd10:unknown:{code}", "diagnosis", f"ไม่พบรหัสโรค {code} ในตาราง", f"Unknown ICD-10 code {code}")
            )
            continue
        if ref["sex_restriction"] and ctx.sex != ref["sex_restriction"]:
            failures.append(
                Failure(
                    f"icd10:sex:{code}",
                    "patient.sex",
                    f"รหัสโรค {code} จำกัดเพศ {ref['sex_restriction']}",
                    f"ICD-10 {code} is restricted to {ref['sex_restriction']}",
                )
            )
        if ctx.age is not None and not (ref["min_age"] <= ctx.age <= ref["max_age"]):
            failures.append(
                Failure(
                    f"icd10:age:{code}",
                    "patient.age",
                    f"รหัสโรค {code} ใช้ได้กับอายุ {ref['min_age']}-{ref['max_age']} ปี (ผู้ป่วยอายุ {ctx.age})",
                    f"ICD-10 {code} applies to ages {ref['min_age']}-{ref['max_age']} (patient is {ctx.age})",
                )
            )
    return failures


def _icd9_checks(ctx: ClaimContext, icd9_ref: dict[str, dict]) -> list[Failure]:
    diagnosis_codes = {d["icd10"] for d in ctx.diagnoses}
    failures = []
    for p in ctx.procedures:
        ref = icd9_ref.get(p["icd9cm"])
        if ref and ref["requires_dx"] and ref["requires_dx"] not in diagnosis_codes:
            failures.append(
                Failure(
                    f"icd9cm:requires_dx:{p['icd9cm']}",
                    "procedure",
                    f"หัตถการ {p['icd9cm']} ต้องมีการวินิจฉัย {ref['requires_dx']}",
                    f"Procedure {p['icd9cm']} requires diagnosis {ref['requires_dx']}",
                )
            )
    return failures


def _charge_code_checks(ctx: ClaimContext, drug_ref: set[str], service_ref: set[str]) -> list[Failure]:
    failures = []
    for c in ctx.charges:
        known = drug_ref if c["item_type"] == "DRUG" else service_ref if c["item_type"] == "SERVICE" else set()
        if c["item_code"] not in known:
            failures.append(
                Failure(
                    f"charge:unknown:{c['item_code']}",
                    "charge_items",
                    f"ไม่พบรหัส {c['item_code']} ({c['item_type']}) ในตาราง",
                    f"Unknown {c['item_type']} code {c['item_code']}",
                )
            )
    return failures


def _amount_checks(ctx: ClaimContext) -> list[Failure]:
    failures = []
    for c in ctx.charges:
        expected = (c["qty"] or 0) * (c["unit_price"] or 0)
        if abs(expected - (c["amount"] or 0)) > AMOUNT_TOLERANCE:
            failures.append(
                Failure(
                    f"amount:line:{c['item_code']}",
                    "charge_items",
                    f"ยอด {c['item_code']} ไม่เท่ากับ จำนวน × ราคา",
                    f"Amount for {c['item_code']} does not equal qty × unit price",
                )
            )
    total = sum(c["amount"] or 0 for c in ctx.charges)
    if ctx.claim_amount is None:
        failures.append(
            Failure("amount:missing", "claim_amount", "ไม่มียอดเคลม", "Claim amount is missing")
        )
    elif abs(total - ctx.claim_amount) > AMOUNT_TOLERANCE:
        failures.append(
            Failure(
                "amount:total",
                "claim_amount",
                f"ยอดเคลม {ctx.claim_amount:g} บาท ไม่เท่ากับผลรวมรายการ {total:g} บาท",
                f"Claim amount {ctx.claim_amount:g} THB does not equal charge total {total:g} THB",
            )
        )
    return failures


def validate_claim(
    ctx: ClaimContext,
    rules: list[dict],
    icd10_ref: dict[str, dict],
    icd9_ref: dict[str, dict],
    drug_ref: set[str],
    service_ref: set[str],
) -> ValidationResult:
    started = time.perf_counter()
    failures: list[Failure] = []

    if ctx.normalization_errors or ctx.payer_id is None or ctx.service_date is None:
        failures.append(
            Failure(
                "normalization",
                "payer_id/service_date",
                "ข้อมูลยังแปลงมาตรฐานไม่สำเร็จ: " + "; ".join(ctx.normalization_errors or ["payer or date unresolved"]),
                "Normalization failed: " + "; ".join(ctx.normalization_errors or ["payer or date unresolved"]),
            )
        )
        version = None
    else:
        version = select_rule_version(rules, ctx.payer_id, ctx.service_date)
        if version is None:
            failures.append(
                Failure(
                    "rules:none",
                    "service_date",
                    "ไม่มีกฎของ payer ที่มีผลในวันที่รับบริการ",
                    "No payer rules are in effect on the service date",
                )
            )
        else:
            failures.extend(_required_fields(version, ctx))
            failures.extend(evaluate_rules(version, ctx))

    failures.extend(_icd10_checks(ctx, icd10_ref))
    failures.extend(_icd9_checks(ctx, icd9_ref))
    failures.extend(_charge_code_checks(ctx, drug_ref, service_ref))
    failures.extend(_amount_checks(ctx))

    elapsed_ms = (time.perf_counter() - started) * 1000
    return ValidationResult(
        claim_no=ctx.claim_no,
        status="ready" if not failures else "needs_correction",
        failures=failures,
        rule_version=version.version if version else None,
        elapsed_ms=round(elapsed_ms, 3),
    )
