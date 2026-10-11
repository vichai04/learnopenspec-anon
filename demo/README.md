# Claims Hub Demo

A read-only Reflex web app over `../claims_hub.sqlite`. It shows the three PRD layers
as screens: normalization, pre-submission validation, and payer rules, plus a claims
dashboard. Synthetic data only.

## Setup

```bash
cd demo
python -m pip install -r requirements.txt
```

The database is read from `../claims_hub.sqlite` by default. To use another file, set
`CLAIMS_HUB_DB` to its path. If the file is missing, every page shows the path that was tried.

## Run

```bash
python -m reflex run          # development, hot reload
python -m reflex run --env prod
```

Open http://localhost:3000.

## Test

```bash
python -m pytest
```

The tests read the bundled database. They include a check that writes through the
connection fail (`mode=ro`) and a check that every visit date in the sample data parses.

## Screens

| Route | What it shows |
|---|---|
| `/` | Claims dashboard: filters by payer and hospital, status count, outcome breakdown, reject rate (rejected ÷ approved + partial + rejected), rejection reasons, and uncoded portal messages |
| `/claims` | First 100 claims with hospital, payer, status, amount |
| `/claims/<claim_no>/normalization` | Each field from the HIS record: raw value, rule applied, canonical value |
| `/claims/<claim_no>/validation` | Every failure for the claim, the rule version used, and the validation time in ms |
| `/claims/<claim_no>/rules` | The payer rule version in effect on the service date, its rows, and any unrecognized rule types |

The UI switches between Thai and English with the EN/ไทย button.

## Demo script

Claims that show each capability (claim numbers come from the sample data):

- **Normalization, date formats:** pick a claim from `90002` (DD/MM/YYYY) and one from `90004` (Gregorian). Both should show canonical ISO dates.
- **Normalization, 2-digit years:** a `90003` claim with a `69-08-01`-style date shows it converted to 2026.
- **Validation, excluded diagnosis:** open a claim with diagnosis `Z41.1` under PRV-TSA or PRV-LTC. The `excluded_dx_prefix:Z41` failure appears.
- **Validation, timing:** every validation page shows the elapsed time in ms.
- **Rules, version change:** a PRV-TSA claim with a service date before 2026-09-15 uses `PRV-TSA@2026-01-01`. A later one uses `PRV-TSA@2026-09-15`.
- **Dashboard:** filter by PRV-LTC to see its reject rate and reason ranking. Uncoded portal messages appear under "No code".

## Notes

- The database is opened read-only and read once at startup. Replacing the file requires restarting the app.
- Payer rules are simplified for teaching and are not real payer rules.
- The ICD-10 and drug tables are subsets, so many sample claims fail the code-existence checks. That is the data, not the app.
