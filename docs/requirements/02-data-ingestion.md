# 02 — Nonprofit source data and ingestion

**Status:** Design baseline, pending geographic/source approvals. **Milestone:** M01.

## Requirements

- **DAT-001** Use authoritative public identity and filing sources as feasible: IRS Exempt Organizations Business Master File, Form 990-series public filings/XML and relevant financial extracts. Record official dataset URL and source version/date. Do not presume all entities file the same return.
- **DAT-002** Maintain a canonical `organizations` registry keyed by internal ID, with EIN and source aliases/IDs; identify possible erroneous matches. Name/address alone must not be identity keys.
- **DAT-003** Store each source filing distinctly, including `tax_period_end`, fiscal year, form type, source return identifier, amended indicator when available, source URI, parser version, import run, and imported timestamp.
- **DAT-004** Derive curated annual financial facts with null/missing flags. Do not silently coerce non-comparable 990, 990-EZ, and 990-PF fields into a single definition.
- **DAT-005** Make repeated ingestion **idempotent**: same source snapshot/filing creates no duplicate organization or filing. Record amendments and supersession choices explicitly.
- **DAT-006** Support a controlled manual CSV import and reproducible batch ingestion. A scheduled public-data refresh is allowed only after cost/run limits and operations are approved.
- **DAT-007** Capture data provenance: source URL or file ID, reporting period, import run, collection timestamp, parser/code version, and quality-check outcomes. Keep raw/staged/curated separation or documented equivalent.
- **DAT-008** Distinguish missing, zero, inconsistent, out-of-range, amended, and stale financial values; surface anomalies for inspection instead of manufacturing data.
- **DAT-009** Use explicit, versioned metro/county inclusion lists configured in data, not hard-coded in application business logic. Record whether an address is mailing/HQ rather than service geography.
- **DAT-010** Geocode only to support approved map functionality. Record geocoding provider/precision/date and distinguish approximate addresses; do not imply the mapped point represents program reach.
- **DAT-011** Each import run records status, counts, failures, timings, and source version. A failed run must not silently replace trustworthy curated data.

## Expected entities (logical, not mandated DDL)

`organizations`, `organization_aliases` (if needed), `organization_filings`, `organization_financials`, `import_runs`, `source_references`; see architectural choices in 08 and the original reference spec.

## Testable examples

- Re-importing an identical filing returns one canonical filing and matching curated amounts.
- An amended filing remains auditable; method of selecting a current financial observation is documented.
- A 990-EZ record without a value needed for a particular ratio yields `unknown`, not zero.
- The same organization with a changed name is not silently duplicated.
- Importing out-of-scope geography does not fabricate in-scope status; source/address uncertainty is visible.

## Primary sources / implementation references

- https://www.irs.gov/charities-non-profits/public-disclosure-datasets-and-downloads
- https://www.irs.gov/charities-non-profits/form-990-series-downloads
- https://www.irs.gov/statistics/soi-tax-stats-irs-tax-exempt-organization-population-data

## Before collecting at scale

Agree on county lists, year range, forms/financial fields, source terms, data volume, and representative validation sample. These are in `../delivery/DECISIONS.md`.
