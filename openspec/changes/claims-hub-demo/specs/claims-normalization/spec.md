## Purpose

Converts raw HIS records from each connected hospital into one canonical claim representation, so the validation and rule views work on consistent data. Each conversion is visible so a reviewer can trace any canonical value back to its source.

## ADDED Requirements

### Requirement: Canonical date conversion
The system SHALL convert every date value from a hospital's source format to ISO 8601 in the Gregorian calendar (ค.ศ.). The source format for each hospital SHALL be taken from `hospitals.date_format`. Buddhist Era years (พ.ศ.) SHALL be converted by subtracting 543. The system SHALL also accept 2-digit Buddhist Era years and interpret them with the same offset.

#### Scenario: Buddhist Era date with slashes is converted
- **WHEN** hospital `90002` (format `DD/MM/YYYY (พ.ศ.)`) provides a service date `01/08/2569`
- **THEN** the canonical service date is `2026-08-01`

#### Scenario: Compact Buddhist Era date is converted
- **WHEN** hospital `90001` (format `YYYYMMDD (พ.ศ.)`) provides a date `25690801`
- **THEN** the canonical date is `2026-08-01`

#### Scenario: Unparseable date is reported, not guessed
- **WHEN** a date value does not match the hospital's declared format
- **THEN** the system SHALL leave the canonical date empty and record a normalization error naming the field and the raw value

### Requirement: Payer code resolution
The system SHALL map each hospital's local payer code (`pttype`) to a canonical `payer_id` using `hospital_payer_map`. A local code with no mapping SHALL be reported as unresolved and SHALL NOT be assigned a payer.

#### Scenario: Local code resolves to canonical payer
- **WHEN** a visit from hospital `90001` has `pttype` mapped to `NHSO-UCS` in `hospital_payer_map`
- **THEN** the canonical payer for that visit is `NHSO-UCS`

#### Scenario: Unmapped local code is flagged
- **WHEN** a visit has a `pttype` with no row in `hospital_payer_map` for its hospital
- **THEN** the system SHALL mark the payer as unresolved and list it among the normalization errors

### Requirement: Sex code resolution
The system SHALL map each hospital's local sex code to `male` or `female` using `hospital_sex_map`. A local code with no mapping SHALL be reported as unresolved.

#### Scenario: Local sex code is mapped
- **WHEN** a patient record from a hospital carries a local sex code listed in `hospital_sex_map`
- **THEN** the canonical sex is the mapped value (`male` or `female`)

### Requirement: Normalization trace
For every canonical field the system SHALL show the raw source value, the rule applied (date format, mapping table, or pass-through), and the canonical value. The trace SHALL be viewable per visit.

#### Scenario: Reviewer inspects a visit
- **WHEN** a user opens the normalization view for a visit
- **THEN** the system displays each converted field with its raw value, the rule applied, and the canonical value

### Requirement: Source data is not modified
Normalization SHALL be computed on read. The system SHALL NOT write canonical values back to `claims_hub.sqlite`.

#### Scenario: Normalization leaves the database unchanged
- **WHEN** a user runs normalization across all visits
- **THEN** the file `claims_hub.sqlite` has the same content before and after the run
