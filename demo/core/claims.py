"""Canonical claim context: one claim with its visit, patient, and related rows.

The context is the input to rule selection and validation. It is built from
normalized values so the checks never see hospital-specific codes or dates.
"""

from dataclasses import dataclass, field
from datetime import date

from .amounts import AmountParseError, parse_amount
from .normalize import ReferenceIndex, normalize_visit


@dataclass
class ClaimContext:
    claim_no: str
    visit_id: str
    hcode: str
    visit_type: str
    payer_id: str | None
    service_date: date | None
    birth_date: date | None
    sex: str | None
    age: int | None
    claim_amount: float | None
    cid: str | None
    chief_complaint: str | None
    doctor_license: str | None
    policy_no: str | None
    preauth_no: str | None
    diagnoses: list[dict] = field(default_factory=list)  # {icd10, diag_type}
    procedures: list[dict] = field(default_factory=list)  # {icd9cm}
    charges: list[dict] = field(default_factory=list)  # {item_type, item_code, qty, unit_price, amount}
    document_types: set[str] = field(default_factory=set)
    normalization_errors: list[str] = field(default_factory=list)


def _age_on(birth: date | None, on: date | None) -> int | None:
    if birth is None or on is None:
        return None
    years = on.year - birth.year
    if (on.month, on.day) < (birth.month, birth.day):
        years -= 1
    return years


def _amount_or_none(claim: dict, errors: list[str]) -> float | None:
    try:
        return parse_amount(claim["claim_amount"])
    except AmountParseError as exc:
        errors.append(f"claim_amount: {exc}")
        return None


def build_claim_context(
    index: ReferenceIndex,
    claim: dict,
    visit: dict,
    patient: dict | None,
    diagnoses: list[dict],
    procedures: list[dict],
    charges: list[dict],
    documents: list[dict],
) -> ClaimContext:
    normalized = normalize_visit(index, visit, patient)
    errors = [f"{f.name}: {f.error}" for f in normalized.errors]

    payer_field = next(f for f in normalized.fields if f.name == "payer_id")
    service_field = next(f for f in normalized.fields if f.name == "service_date")
    service_date = (
        date.fromisoformat(service_field.canonical) if service_field.canonical else None
    )

    birth_date = None
    sex = None
    if patient is not None:
        birth_field = next((f for f in normalized.fields if f.name == "birth_date"), None)
        if birth_field is not None and birth_field.canonical:
            birth_date = date.fromisoformat(birth_field.canonical)
        sex_field = next((f for f in normalized.fields if f.name == "sex"), None)
        sex = sex_field.canonical if sex_field else None

    return ClaimContext(
        claim_no=claim["claim_no"],
        visit_id=visit["visit_id"],
        hcode=visit["hcode"],
        visit_type=visit["visit_type"],
        payer_id=payer_field.canonical,
        service_date=service_date,
        birth_date=birth_date,
        sex=sex,
        age=_age_on(birth_date, service_date),
        claim_amount=_amount_or_none(claim, errors),
        cid=patient.get("cid") if patient else None,
        chief_complaint=visit.get("chief_complaint"),
        doctor_license=visit.get("doctor_license"),
        policy_no=visit.get("policy_no"),
        preauth_no=visit.get("preauth_no"),
        diagnoses=[{"icd10": d["icd10"], "diag_type": d["diag_type"]} for d in diagnoses],
        procedures=[{"icd9cm": p["icd9cm"]} for p in procedures],
        charges=[
            {
                "item_type": c["item_type"],
                "item_code": c["item_code"],
                "qty": c["qty"],
                "unit_price": c["unit_price"],
                "amount": c["amount"],
            }
            for c in charges
        ],
        document_types={d["doc_type"] for d in documents},
        normalization_errors=errors,
    )


def claim_list_row(index: ReferenceIndex, claim: dict, visit: dict | None) -> dict:
    """One row for the claim list: payer, hospital, status, and amount."""
    payer = None
    if visit is not None:
        payer = index.payer_map.get((visit["hcode"], visit["pttype"]))
    return {
        "claim_no": claim["claim_no"],
        "visit_id": claim["visit_id"],
        "hcode": visit["hcode"] if visit else None,
        "hospital_name": index.hospitals[visit["hcode"]]["hospital_name"] if visit else None,
        "payer_id": payer,
        "claim_status": claim["claim_status"],
        "claim_amount": _amount_or_none(claim, []),
    }
