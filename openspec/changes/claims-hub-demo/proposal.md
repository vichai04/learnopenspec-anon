## Why

The claims hub PRD describes a middleware layer that normalizes HIS data, validates claims before they reach payers, and applies per-payer rules. Stakeholders need a working web demo to see that flow end to end on realistic data before the platform is built. The synthetic `claims_hub.sqlite` database (4 hospitals, 5 payers, 412 claims) already reproduces the mismatches the PRD targets: mixed date formats (พ.ศ./ค.ศ.), hospital-specific payer and sex codes, and payer rejection reasons.

## What Changes

- Add a read-only web application that loads `claims_hub.sqlite` and presents the three PRD layers as screens:
  - **Normalization view**: shows each hospital's raw HIS record next to its canonical form (dates converted to ค.ศ. ISO format, `hospital_payer_map` resolving local `pttype` to `payer_id`, `hospital_sex_map` resolving sex codes).
  - **Validation view**: runs pre-submission checks on a selected claim and lists failures with the PRD's categories: required fields (`payer_rules` `required_field`), ICD-10 sex and age restrictions (`ref_icd10`), ICD-9-CM requirements (`ref_icd9cm.requires_dx`), and drug and service code validity (`ref_drug`, `ref_service_item`).
  - **Rule view**: shows which `payer_rules` version applies to a claim, chosen by `effective_from` ≤ service date.
- Add a claims dashboard: submission history per claim, `response_status` breakdown, and top rejection reasons from `claim_submission_reasons` joined to `ref_reject_reason`.
- Measure and display validation processing time per claim, so the PRD's latency criterion can be discussed against real numbers.
- Adding a new payer's rules requires only inserting `payer_rules` and `payers` rows. Nothing in the validation code is payer-specific.

Assumptions recorded for this demo (not requirements of the production platform):

- **Read-only**: the app never writes to `claims_hub.sqlite`. Submitting claims to payers is out of scope.
- **Single-user, no authentication**: the demo runs locally against the bundled database.
- **Synthetic data only**: the README states the data is synthetic and the rules are simplified. The UI must label them as demo rules.
- **Thai and English UI**: domain labels use the Thai terms from the README; column names stay in English.

## Capabilities

### New Capabilities
- `claims-normalization`: Converts raw HIS records from each hospital into the canonical claim model (dates, payer codes, sex codes) and shows the mapping for each record.
- `claims-validation`: Runs pre-submission validation for a claim against the payer rules and reference tables, returning pass/fail results with reasons and timing.
- `payer-rule-resolution`: Selects the applicable `payer_rules` version for a payer and service date, and lists the conditions that version imposes.
- `claims-dashboard`: Summarizes claim status, submission outcomes, and rejection reasons from the submission history.

### Modified Capabilities
<!-- None. This change adds the demo to an empty specs directory. -->

## Impact

- **New code**: a Python web application built with Reflex under `demo/` in the project root, styled with a custom Tailwind dark dashboard theme.
- **Data**: reads `claims_hub.sqlite` and `README.md` as the schema reference. No schema change.
- **Dependencies**: Reflex (pinned version) and Python's standard-library `sqlite3`. Details in design.md.
- **Systems**: none outside the local machine. No HIS, payer, or network integration.
- **Scope boundary**: the PRD's full platform requirements (HL7 v2 ingestion, FHIR API specification, high-concurrency throughput, plugin-based payer loading) are not implemented here. The demo illustrates the validation and rule logic only.
