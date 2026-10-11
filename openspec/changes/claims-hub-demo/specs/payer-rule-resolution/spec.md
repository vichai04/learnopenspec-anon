## Purpose

Determines which version of a payer's rules applies to a claim, based on the payer and the service date, and presents the conditions that version imposes. This lets the platform support payers whose rules change over time without changing validation code.

## ADDED Requirements

### Requirement: Versioned rule selection
For a given payer and service date, the system SHALL select the rule version whose `effective_from` is the latest date that is on or before the service date. Only rows of that version SHALL apply. If no version has `effective_from` on or before the service date, the system SHALL report that no rules apply and SHALL NOT fall back to a later version.

#### Scenario: Newer rule version applies after its effective date
- **WHEN** payer `PRV-TSA` has versions effective `2026-01-01` and `2026-09-15`, and the service date is `2026-10-01`
- **THEN** the rules of the `2026-09-15` version are applied

#### Scenario: Older rule version applies before a change takes effect
- **WHEN** payer `PRV-TSA` has the same versions and the service date is `2026-08-01`
- **THEN** the rules of the `2026-01-01` version are applied

#### Scenario: No version is effective yet
- **WHEN** the service date is earlier than every `effective_from` for the payer
- **THEN** the system reports that no rules apply to the claim

### Requirement: Rule type catalogue
The system SHALL recognize the following `rule_type` values and interpret `rule_value` as described for each: `required_field` (a canonical field name), `required_document_ipd` and `required_document_surgery` (a document type from `documents.doc_type`), `preauth_required_for` (a condition that requires prior authorization), `preauth_min_total_thb` (a baht threshold at or above which prior authorization is required), `opd_limit_per_visit_thb` and `room_limit_per_day_thb` (baht limits), `excluded_dx_prefix` (an ICD-10 prefix that the payer does not cover), `resubmission_max_attempts` and `resubmission_window_days` (limits on resubmission). A `rule_type` not in this list SHALL be reported as unrecognized and SHALL NOT be silently ignored.

#### Scenario: Known rule type is interpreted
- **WHEN** a version contains a `room_limit_per_day_thb` rule with `rule_value` `5000`
- **THEN** the system treats the room charge per day above 5000 baht as a limit violation

#### Scenario: Unknown rule type is surfaced
- **WHEN** a version contains a `rule_type` not in the catalogue
- **THEN** the system lists it as unrecognized in the rule view

### Requirement: Rule view shows the applied version
For a selected claim, the system SHALL display the payer, the service date, the selected rule version and its `effective_from`, and every rule row in that version with its `rule_type`, `rule_value`, and `description`.

#### Scenario: Reviewer checks which rules applied
- **WHEN** a user opens the rule view for a claim
- **THEN** the system shows the selected version, its effective date, and all of its rule rows

### Requirement: Payer addition without code change
Adding a payer with its rules SHALL require only new rows in `payers` and `payer_rules` (and `hospital_payer_map` for hospital codes). The system SHALL NOT require changes to validation code for a new payer, provided its rule types are in the catalogue.

#### Scenario: New payer with existing rule types
- **WHEN** a new payer is inserted with rules using only catalogued rule types
- **THEN** the system validates claims for that payer without code changes
