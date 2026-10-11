from datetime import date

from core.claims import ClaimContext


def make_ctx(**overrides) -> ClaimContext:
    base = dict(
        claim_no="T1",
        visit_id="V1",
        hcode="90001",
        visit_type="OPD",
        payer_id="PRV-TSA",
        service_date=date(2026, 9, 20),
        birth_date=date(1990, 1, 1),
        sex="female",
        age=36,
        claim_amount=1000.0,
        cid="1234567890123",
        chief_complaint="fever",
        doctor_license="D123",
        policy_no="P1",
        preauth_no=None,
        diagnoses=[{"icd10": "J06.9", "diag_type": "1"}],
        procedures=[],
        charges=[],
        document_types=set(),
    )
    base.update(overrides)
    return ClaimContext(**base)
