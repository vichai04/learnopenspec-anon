## 1. Project setup

- [x] 1.1 Install Reflex and pytest, confirm a minimal Reflex app compiles and runs on this machine, and check whether a custom Tailwind theme config is accepted, before writing demo code
- [x] 1.2 Create the `demo/` project with `demo/claims_hub_demo/` (Reflex app package: pages, state, components, theme), `demo/core/` (pure logic), and `demo/tests/`
- [x] 1.3 Add `requirements.txt` with the pinned Reflex version and pytest, and document the install and run commands in `demo/README.md`
- [x] 1.4 Add a database path setting that defaults to `../claims_hub.sqlite` and fails with a clear message if the file is missing

## 2. Read-only data access

- [x] 2.1 Implement a connection helper that opens `claims_hub.sqlite` with `mode=ro` and returns rows as dictionaries
- [x] 2.2 Load reference tables (`ref_icd10`, `ref_icd9cm`, `ref_drug`, `ref_service_item`, `ref_reject_reason`, `payers`, `payer_rules`, `hospitals`, `hospital_payer_map`, `hospital_sex_map`) into memory at startup
- [x] 2.3 Add a test that writing through the connection raises an error, confirming the read-only mode

## 3. Normalization (claims-normalization)

- [x] 3.1 Implement date parsers for `YYYYMMDD`, `DD/MM/YYYY`, and `YYYY-MM-DD`, each with Buddhist Era conversion and 2-digit year handling
- [x] 3.2 Implement payer code resolution through `hospital_payer_map`, returning an unresolved result for unmapped codes
- [x] 3.3 Implement sex code resolution through `hospital_sex_map`
- [x] 3.4 Build the normalization trace for one visit: raw value, rule applied, and canonical value for each field
- [x] 3.5 Add tests covering each hospital's date format, a 2-digit year, an unparseable date, and an unmapped payer code

## 4. Rule resolution (payer-rule-resolution)

- [x] 4.1 Implement version selection: latest `effective_from` on or before the service date, with no fallback to later versions
- [x] 4.2 Implement the rule-type catalogue with one handler per type, and an "unrecognized" result for unknown types
- [x] 4.3 Add tests for PRV-TSA before and after its 2026-09-15 version, a service date before all versions, and an unknown rule type

## 5. Validation (claims-validation)

- [x] 5.1 Implement the required field check using canonical field names from the README
- [x] 5.2 Implement ICD-10 sex and age restriction checks and the unknown-code failure
- [x] 5.3 Implement the ICD-9-CM `requires_dx` check
- [x] 5.4 Implement charge item code validity checks for `DRUG` and `SERVICE`
- [x] 5.5 Implement amount consistency checks with the 0.01 baht tolerance, including the claim total
- [x] 5.6 Return all failures per claim, and the elapsed time in milliseconds
- [x] 5.7 Add tests for each check, including a claim with several failures at once

## 6. Reflex state and data loading (all capabilities)

- [x] 6.1 Implement the app `State` that loads reference tables and the database at startup, and holds the selected payer, hospital, and claim
- [x] 6.2 Add a dashboard computation (status counts, outcome breakdown, reject rate, reason ranking) that takes optional payer and hospital filters and is covered by unit tests
- [x] 6.3 Add a claim list computation with payer, hospital, status, and amount
- [x] 6.4 Add per-claim computations for the normalization trace, validation result with timing, and selected rule version with its rows
- [x] 6.5 Add state tests against the bundled database for one claim from each hospital

## 7. Dark dashboard theme and Reflex pages

- [x] 7.1 Define the custom Tailwind theme (dark slate background, surface levels, one accent, status colors) in the Tailwind config and `demo/claims_hub_demo/theme.py`
- [x] 7.2 Build shared components (sidebar navigation, status tag, metric tile, data table, notice banner) that use only theme tokens
- [x] 7.3 Build the dashboard page with payer and hospital filters, status summary, outcome breakdown, reason ranking, and the data as-of date from the README
- [x] 7.4 Build the claim list page with links to the three claim pages
- [x] 7.5 Build the normalization page showing raw and canonical values side by side
- [x] 7.6 Build the validation page listing failures and the timing
- [x] 7.7 Build the rule page showing the selected version and its rows, with the synthetic-rules notice
- [ ] 7.8 Put all UI strings in one Thai/English dictionary with a language toggle, and check the layout at phone width

## 8. Verification

- [x] 8.1 Run the full test suite and record the results
- [ ] 8.2 Start the app, open each screen for at least one claim from each hospital, and confirm that `claims_hub.sqlite` is unchanged (compare file hash before and after)
- [x] 8.3 Check that the validation timing is displayed and that the reject rate matches a manual query against `claim_submissions`
- [x] 8.4 Write a short demo script in `demo/README.md` listing the claims to show for each capability

## 9. Dashboard charts (added after first apply)

- [x] 9.1 Add monthly outcome series (count per response status by submission month, and reject rate per month) to `core/dashboard.py`, with unit tests for the reject-rate definition and filters
- [x] 9.2 Add chart data to the Reflex state: claim status distribution, monthly outcomes, monthly reject rate, and top rejection reasons
- [x] 9.3 Build the dashboard charts with Recharts in the dark theme colors: status donut, monthly stacked outcome bars, reject-rate line, top reasons bar, each with an empty state
- [x] 9.4 Verify the charts in the browser and rerun the test suite
