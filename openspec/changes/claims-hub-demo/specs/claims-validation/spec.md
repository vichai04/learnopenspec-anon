## Purpose

Checks a claim against the applicable payer rules and the reference tables before it is sent to a payer, returning each failure with its reason and the time the check took. This is the pre-submission check the PRD requires to reduce rejections caused by incomplete or incorrect data.

## ADDED Requirements

### Requirement: Pre-submission validation of a claim
The system SHALL validate a claim against the applicable payer rules (see `payer-rule-resolution`) and the reference tables before the claim is treated as ready to submit. Validation SHALL return a list of failures; an empty list means the claim passed. Each failure SHALL include a rule identifier, the field involved, and a human-readable message in Thai and English.

#### Scenario: Claim passes all checks
- **WHEN** a claim satisfies every applicable rule and reference check
- **THEN** validation returns no failures and the claim is marked `ready`

#### Scenario: Claim fails one or more checks
- **WHEN** a claim violates one or more applicable rules
- **THEN** validation returns every failure, not only the first, and the claim is marked `needs_correction`

### Requirement: Required field check
For each applicable `required_field` rule, the system SHALL check that the named canonical field has a non-empty value. Field names SHALL use the canonical claim names from the README (for example `patient.nationalId`, `encounter.attendingLicense`, `insurance.policyNumber`, `diagnosis.principal`, `encounter.chiefComplaint`).

#### Scenario: Missing required field
- **WHEN** a payer requires `insurance.policyNumber` and the claim's visit has no `policy_no`
- **THEN** validation reports a failure for `insurance.policyNumber`

#### Scenario: Required field present
- **WHEN** the required field has a non-empty value
- **THEN** no failure is reported for that field

### Requirement: ICD-10 sex and age restrictions
For each diagnosis code on a claim, the system SHALL check the code's `sex_restriction`, `min_age`, and `max_age` in `ref_icd10` against the patient's canonical sex and age on the service date. Codes that are absent from `ref_icd10` SHALL be reported as failures.

#### Scenario: Diagnosis restricted to one sex
- **WHEN** a claim has an ICD-10 code whose `sex_restriction` is `female` and the patient's canonical sex is `male`
- **THEN** validation reports a failure for that diagnosis

#### Scenario: Diagnosis code not in reference table
- **WHEN** a claim's diagnosis code does not exist in `ref_icd10`
- **THEN** validation reports a failure stating the code is unknown

### Requirement: ICD-9-CM procedure dependency
For each procedure whose `ref_icd9cm.requires_dx` is set, the system SHALL check that the claim includes that diagnosis code.

#### Scenario: Procedure without its required diagnosis
- **WHEN** a claim includes a procedure whose `requires_dx` is not among the claim's diagnoses
- **THEN** validation reports a failure for that procedure

### Requirement: Charge item code validity
For each charge item, the system SHALL check that `item_code` exists in `ref_drug` when `item_type` is `DRUG`, or in `ref_service_item` when `item_type` is `SERVICE`.

#### Scenario: Unknown drug code
- **WHEN** a `DRUG` charge item has an `item_code` not present in `ref_drug`
- **THEN** validation reports a failure for that line item

### Requirement: Amount consistency
The system SHALL check that each charge item's `amount` equals `qty` multiplied by `unit_price` within a tolerance of 0.01 baht, and that the claim amount equals the sum of its charge item amounts.

#### Scenario: Line amount does not match quantity times price
- **WHEN** a charge item has `amount` that differs from `qty × unit_price` by more than 0.01 baht
- **THEN** validation reports a failure for that line item

### Requirement: Timing measurement
The system SHALL measure and report the elapsed time of each validation run in milliseconds, so the processing latency can be compared with the PRD criterion.

#### Scenario: Validation run reports its duration
- **WHEN** validation completes for a claim
- **THEN** the result includes the elapsed time in milliseconds
