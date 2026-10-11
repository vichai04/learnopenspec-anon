"""In-memory snapshot of claims_hub.sqlite and the view data built from it.

The database is read once. Everything the pages show is computed from this
snapshot, so the Reflex state stays thin and the logic is testable without
running the web app.
"""

import sqlite3
from collections import defaultdict
from dataclasses import asdict

from .claims import build_claim_context, claim_list_row
from .dashboard import compute_dashboard
from .db import load_reference_data, query
from .normalize import ReferenceIndex, normalize_visit
from .rules import select_rule_version, unrecognized_rules
from .validate import validate_claim

# "ข้อมูล ณ วันที่: 8 ต.ค. 2569" from README.md
DATA_AS_OF = "2026-10-08"

# Rule types that only make sense with submission history. Shown in the rule
# view with a note; they are not checked before submission.
HISTORY_RULE_TYPES = {"resubmission_max_attempts", "resubmission_window_days"}


def _group(rows: list[dict], key: str) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[row[key]].append(row)
    return grouped


class ClaimsRepository:
    def __init__(self, conn: sqlite3.Connection):
        reference = load_reference_data(conn)
        self.reference = reference
        self.index = ReferenceIndex(reference)
        self.visits = {v["visit_id"]: v for v in query(conn, "SELECT * FROM visits")}
        self.patients = {(p["hcode"], p["hn"]): p for p in query(conn, "SELECT * FROM patients")}
        self.claims = query(conn, "SELECT * FROM claims")
        self.submissions = query(conn, "SELECT * FROM claim_submissions")
        self.reasons = query(conn, "SELECT * FROM claim_submission_reasons")
        self.diagnoses = _group(query(conn, "SELECT * FROM diagnoses"), "visit_id")
        self.procedures = _group(query(conn, "SELECT * FROM procedures"), "visit_id")
        self.charges = _group(query(conn, "SELECT * FROM charge_items"), "visit_id")
        self.documents = _group(query(conn, "SELECT * FROM documents"), "visit_id")

        self.icd10 = {r["code"]: r for r in reference["ref_icd10"]}
        self.icd9 = {r["code"]: r for r in reference["ref_icd9cm"]}
        self.drug_codes = {r["drug_code"] for r in reference["ref_drug"]}
        self.service_codes = {r["item_code"] for r in reference["ref_service_item"]}
        self.reject_reasons = {r["reason_code"]: r["description_th"] for r in reference["ref_reject_reason"]}
        self._claims_by_no = {c["claim_no"]: c for c in self.claims}

    # ---- lists ---------------------------------------------------------

    def payers(self) -> list[dict]:
        return self.reference["payers"]

    def hospitals(self) -> list[dict]:
        return self.reference["hospitals"]

    def claim_rows(self) -> list[dict]:
        return [claim_list_row(self.index, c, self.visits.get(c["visit_id"])) for c in self.claims]

    def dashboard(self, payer: str | None = None, hospital: str | None = None) -> dict:
        return compute_dashboard(
            self.claim_rows(),
            self.submissions,
            self.reasons,
            self.reject_reasons,
            payer=payer or None,
            hospital=hospital or None,
        )

    # ---- one claim -----------------------------------------------------

    def _context(self, claim_no: str):
        claim = self._claims_by_no.get(claim_no)
        if claim is None:
            return None, None
        visit = self.visits[claim["visit_id"]]
        patient = self.patients.get((visit["hcode"], visit["hn"]))
        ctx = build_claim_context(
            self.index,
            claim,
            visit,
            patient,
            self.diagnoses.get(visit["visit_id"], []),
            self.procedures.get(visit["visit_id"], []),
            self.charges.get(visit["visit_id"], []),
            self.documents.get(visit["visit_id"], []),
        )
        return claim, (visit, patient, ctx)

    def normalization(self, claim_no: str) -> dict | None:
        claim = self._claims_by_no.get(claim_no)
        if claim is None:
            return None
        visit = self.visits[claim["visit_id"]]
        patient = self.patients.get((visit["hcode"], visit["hn"]))
        normalized = normalize_visit(self.index, visit, patient)
        return {
            "visit_id": visit["visit_id"],
            "hcode": visit["hcode"],
            "hospital_name": self.index.hospitals[visit["hcode"]]["hospital_name"],
            "date_format": self.index.hospitals[visit["hcode"]]["date_format"],
            "fields": [asdict(f) for f in normalized.fields],
            "error_count": len(normalized.errors),
        }

    def validation(self, claim_no: str) -> dict | None:
        claim, parts = self._context(claim_no)
        if claim is None:
            return None
        _, _, ctx = parts
        result = validate_claim(
            ctx,
            self.reference["payer_rules"],
            self.icd10,
            self.icd9,
            self.drug_codes,
            self.service_codes,
        )
        return {
            "claim_no": result.claim_no,
            "status": result.status,
            "rule_version": result.rule_version,
            "elapsed_ms": result.elapsed_ms,
            "failures": [asdict(f) for f in result.failures],
        }

    def rules(self, claim_no: str) -> dict | None:
        claim, parts = self._context(claim_no)
        if claim is None:
            return None
        _, _, ctx = parts
        if ctx.payer_id is None or ctx.service_date is None:
            return {"payer_id": ctx.payer_id, "service_date": None, "version": None, "rows": [],
                    "unrecognized": [], "history_rules": []}
        version = select_rule_version(self.reference["payer_rules"], ctx.payer_id, ctx.service_date)
        if version is None:
            return {"payer_id": ctx.payer_id, "service_date": ctx.service_date.isoformat(), "version": None,
                    "rows": [], "unrecognized": [], "history_rules": []}
        rows = [
            {"rule_type": r["rule_type"], "rule_value": r["rule_value"], "description": r["description"]}
            for r in version.rows
        ]
        return {
            "payer_id": version.payer_id,
            "service_date": ctx.service_date.isoformat(),
            "version": version.version,
            "effective_from": version.effective_from.isoformat(),
            "rows": rows,
            "unrecognized": [r["rule_type"] for r in unrecognized_rules(version)],
            "history_rules": [r["rule_type"] for r in version.rows if r["rule_type"] in HISTORY_RULE_TYPES],
        }

    def claim_summary(self, claim_no: str) -> dict | None:
        claim = self._claims_by_no.get(claim_no)
        if claim is None:
            return None
        row = claim_list_row(self.index, claim, self.visits.get(claim["visit_id"]))
        return row
