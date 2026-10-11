"""Normalize one hospital visit into canonical values, with a trace of each step."""

from dataclasses import dataclass, field

from .dates import DateParseError, parse_hospital_date


@dataclass
class TraceField:
    """One canonical field: the raw source value, the rule used, and the result."""

    name: str
    raw: str | None
    rule: str
    canonical: str | None
    error: str | None = None


@dataclass
class NormalizedVisit:
    visit_id: str
    hcode: str
    fields: list[TraceField] = field(default_factory=list)

    @property
    def errors(self) -> list[TraceField]:
        return [f for f in self.fields if f.error]


class ReferenceIndex:
    """Lookups built once from the reference tables loaded at startup."""

    def __init__(self, reference: dict[str, list[dict]]):
        self.hospitals = {h["hcode"]: h for h in reference["hospitals"]}
        self.payer_map = {
            (m["hcode"], m["local_payer_code"]): m["payer_id"]
            for m in reference["hospital_payer_map"]
        }
        self.sex_map = {
            (m["hcode"], m["local_sex_code"]): m["sex"] for m in reference["hospital_sex_map"]
        }


def _date_field(name: str, raw: str | None, date_format: str) -> TraceField:
    rule = f"date: {date_format}"
    if raw is None:
        return TraceField(name, None, rule, None)
    try:
        return TraceField(name, raw, rule, parse_hospital_date(raw, date_format).isoformat())
    except DateParseError as exc:
        return TraceField(name, raw, rule, None, error=str(exc))


def resolve_payer(index: ReferenceIndex, hcode: str, pttype: str | None) -> TraceField:
    rule = "hospital_payer_map"
    payer = index.payer_map.get((hcode, pttype)) if pttype is not None else None
    if payer is None:
        return TraceField("payer_id", pttype, rule, None, error=f"unmapped payer code {pttype!r}")
    return TraceField("payer_id", pttype, rule, payer)


def resolve_sex(index: ReferenceIndex, hcode: str, local_sex: str | None) -> TraceField:
    rule = "hospital_sex_map"
    sex = index.sex_map.get((hcode, local_sex)) if local_sex is not None else None
    if sex is None:
        return TraceField("sex", local_sex, rule, None, error=f"unmapped sex code {local_sex!r}")
    return TraceField("sex", local_sex, rule, sex)


def normalize_visit(index: ReferenceIndex, visit: dict, patient: dict | None) -> NormalizedVisit:
    """Build the normalization trace for one visit and its patient.

    visit: a row from visits. patient: the matching row from patients, or None.
    """
    hcode = visit["hcode"]
    date_format = index.hospitals[hcode]["date_format"]
    result = NormalizedVisit(visit_id=visit["visit_id"], hcode=hcode)

    result.fields.append(resolve_payer(index, hcode, visit.get("pttype")))
    result.fields.append(_date_field("service_date", visit.get("service_date"), date_format))
    if visit.get("visit_type") == "IPD":
        result.fields.append(_date_field("admit_date", visit.get("admit_date"), date_format))
        result.fields.append(_date_field("discharge_date", visit.get("discharge_date"), date_format))

    if patient is not None:
        result.fields.append(resolve_sex(index, hcode, patient.get("sex")))
        result.fields.append(_date_field("birth_date", patient.get("birth_date"), date_format))
    else:
        result.fields.append(TraceField("patient", None, "patients", None, error="no matching patient"))

    return result
