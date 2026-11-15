# IRS nonprofit data: source-shaped synthetic fixture contract

**Status:** Provisional source contract for M01 planning and synthetic fixtures; **not** a production-approved 2025 IRS extract schema.

## Primary references

1. IRS annual SOI extracts and **2025 XLSX data dictionary**: https://www.irs.gov/statistics/soi-tax-stats-annual-extract-of-tax-exempt-organization-financial-data
2. IRS EO BMF (state CSV and official information sheet): https://www.irs.gov/charities-non-profits/exempt-organizations-business-master-file-extract-eo-bmf
3. Older published SOI Form 990 dictionary with exact column examples: https://github.com/Nonprofit-Open-Data-Collective/irs-990-statistics-of-income-extracts

**Before coding a real IRS importer:** obtain the 2025 IRS extract XLSX dictionary, check actual delivered archive header and formatting, and create a versioned source-column mapping. Do not claim that the legacy lowercase SOI columns are verified as 2025 columns. Do not download the full financial data extract as part of initial fixture/schema planning. An approved follow-up may retrieve the public XLSX dictionary only.

## Logical source files and grain

- `eo_bmf_sample.csv`: subset of **source-style uppercase BMF columns**, grain = one organization per current BMF snapshot, keyed by 9-character EIN. A BMF snapshot is **not** a multi-year financial history.
- `soi_form990_legacy_sample.csv`: subset of **documented historical SOI Form 990 source column names**, grain = one filing record. Its `tax_pd` is a six-character `YYYYMM` tax-period-end identifier; extract/processing year is **separate metadata**, NOT a source value used to infer tax year.
- `soi_form990_repeat_sample.csv`: second import batch containing an identical row and a changed version of a prior period; test idempotency and amendment/duplicate **review** without pretending every changed row is a confirmed amendment.
- Do not treat `EIN` alone as a unique financial-file key. Preserve all raw rows with a source batch ID, row number, input filename and raw-row hash. The latest usable record by `(ein, tax_period)` is selected only under an explicit, tested policy.

## BMF source fields (actual uppercase names)

| Source field | Canonical field | Suggested type |
|---|---|---|
| EIN | ein | string, 9 digits, preserve leading zeros |
| NAME | name | string |
| STREET | street | string |
| CITY | city | string |
| STATE | state | string (2 chars) |
| ZIP | zip_code | string (preserve ZIP+4/zeros) |
| NTEE_CD | ntee_code | nullable string |
| SUBSECTION | subsection_code | nullable string |
| STATUS | exemption_status_code | nullable string |
| TAX_PERIOD | latest_tax_period | nullable YYYYMM string |
| REVENUE_AMT | reported_revenue | nullable numeric, NOT revenue time series |

## SOI Form 990 source fields (verified historical names, 2025 pending confirmation)

| Historical SOI field | Canonical field | Type |
|---|---|---|
| EIN | ein | string(9) |
| tax_pd | tax_period | string YYYYMM |
| totrevenue | total_revenue | nullable numeric |
| totfuncexpns | total_expenses | nullable numeric |
| totcntrbgfts | contributions_grants | nullable numeric |
| totprgmrevnue | program_service_revenue | nullable numeric |
| totassetsend | total_assets_end | nullable numeric |
| totliabend | total_liabilities_end | nullable numeric |
| totnetassetend | net_assets_end | nullable numeric |

For numerical samples, use whole dollars, preserve negative values, and model blanks as `NULL`, not zero. For test data, `tax_period_end_year` can be computed from the first four characters of `tax_pd`, but the Form 990 tax-year label and the *extract filing/processing calendar year* must not be conflated. Some fiscal years straddle calendar years.

## Minimal canonical data model

- `organizations`: one row per EIN (plus source snapshot date); organization name, geographic fields, NTEE and exemption metadata.
- `financial_filings`: one row per raw source filing observation (internal surrogate key, `ein`, `tax_period`, financial metrics, `source_extract_year`, `source_file`, `source_row_number`, `raw_row_hash`, `ingested_at`, duplicate/review status). **Do not assume** EIN + tax_period uniquely identifies a raw return.
- `financial_metrics`: derived from the selected usable filing for each period; `revenue_minus_expenses`, `operating_margin` (NULL when revenue is 0/missing), year-over-year revenue growth (NULL when prior year missing/zero). Calculations should not be called audited operating results or proof of unrestricted funds.

## Fixture scenarios (100% fictional)

1. Stable nonprofit with 3 periods in the $1M–$5M segment and positive margins.
2. Declining revenue with consecutive expenses greater than revenue.
3. Missing one historical period; no implied zero or interpolated growth.
4. Zero revenue and blank financial fields; derived division metrics are NULL.
5. Duplicate identical filing observation in second batch; ingest must be idempotent.
6. Conflicting same-period record in second batch; flag for review instead of silently overwriting.
7. EIN and ZIP are always loaded as strings.

## Tests and acceptance conditions

- Header contracts for both fixture files match this documented source subset exactly; parsers reject unknown mandatory fields but may preserve additional real fields in raw storage.
- Ensure reproducible synthetic data (fixed values or fixed random seed).
- Validate `assets = liabilities + net assets` where all values present, as a **warning** not an unconditional rejection.
- No real organization names, addresses, or EINs are included in synthetic fixtures.
- Do not perform network access, Supabase writes, or deploy as part of fixture generation.
- When verified 2025 SOI header differs, update a version-specific **adapter/mapping**, not the internal financial table names or metric tests.
