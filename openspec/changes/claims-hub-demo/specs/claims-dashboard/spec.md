## Purpose

Summarizes claim status, submission outcomes, and payer rejection reasons from the claim history, so a user can see where claims are being rejected and why. It supports the PRD's goal of measuring and reducing the reject rate.

## ADDED Requirements

### Requirement: Claim status summary
The system SHALL show the number of claims by `claim_status` (`pending` and `submitted`), and the total claim amount for each status.

#### Scenario: Status counts are shown
- **WHEN** a user opens the dashboard
- **THEN** the system shows the count and total amount of claims for each `claim_status`

### Requirement: Submission outcome breakdown
The system SHALL show the number of submissions for each `response_status` (`approved`, `partial`, `rejected`, `pended`), and the reject rate defined as rejected submissions divided by all submissions with a final response. Submissions with `pended` status SHALL be excluded from the reject-rate denominator.

#### Scenario: Reject rate excludes pending decisions
- **WHEN** the history contains 10 submissions, of which 2 are `rejected` and 3 are `pended`
- **THEN** the reject rate is 2 divided by 7

### Requirement: Rejection reason ranking
The system SHALL list rejection reasons from `claim_submission_reasons`, ranked by count, with each reason's `reason_code` and its description from `ref_reject_reason`. Reasons with no `reason_code` (messages from payers that use a portal) SHALL be grouped under a separate "unclassified" entry that shows the most common `message_th` values.

#### Scenario: Coded reasons are ranked
- **WHEN** rejection reasons are present with codes
- **THEN** the system lists each code with its Thai description and count, highest count first

#### Scenario: Uncoded portal messages are not dropped
- **WHEN** a reason has no `reason_code`
- **THEN** it is counted under "unclassified" and is not omitted from the totals

### Requirement: Filter by payer and hospital
The dashboard SHALL allow filtering the status summary, outcome breakdown, and reason ranking by payer and by hospital.

#### Scenario: Filter by payer
- **WHEN** a user selects payer `PRV-LTC`
- **THEN** every figure on the dashboard counts only claims and submissions for `PRV-LTC`

### Requirement: Dashboard reads from the database
The dashboard SHALL compute all figures from `claims_hub.sqlite` at the time of viewing, and SHALL state the database's "data as of" date from the README.

#### Scenario: Data date is displayed
- **WHEN** the dashboard loads
- **THEN** it shows the data as-of date from the source database documentation

### Requirement: Dashboard charts
The dashboard SHALL show charts of the same figures as its tables: claim status distribution, response outcomes per submission month, reject rate per submission month, and the top rejection reasons ranked by count. Each chart SHALL use the same payer and hospital filters as the tables, and SHALL show a readable empty state when there is no data for the current filter.

#### Scenario: Monthly outcome chart follows the filter
- **WHEN** a user selects payer `PRV-LTC`
- **THEN** the monthly outcome chart counts only submissions for `PRV-LTC`

#### Scenario: Monthly reject rate uses the same definition
- **WHEN** a month has submissions with approved, partial, rejected, and pended responses
- **THEN** that month's reject rate is rejected divided by approved + partial + rejected, with pended excluded

#### Scenario: Empty filter shows an empty state
- **WHEN** the current filter matches no submissions
- **THEN** each chart shows a message instead of an empty axis
