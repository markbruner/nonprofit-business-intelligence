# IRS nonprofit data: source contracts and verification

**Status:** Partial live CSV and documentation verification; XML mapping remains
provisional and legacy SOI fixtures remain synthetic. No production ingestion approval.

## Primary references

1. IRS annual SOI extracts and **2025 XLSX data dictionary**: https://www.irs.gov/statistics/soi-tax-stats-annual-extract-of-tax-exempt-organization-financial-data
2. IRS EO BMF (state CSV and official information sheet): https://www.irs.gov/charities-non-profits/exempt-organizations-business-master-file-extract-eo-bmf
3. Older published SOI Form 990 dictionary with exact column examples: https://github.com/Nonprofit-Open-Data-Collective/irs-990-statistics-of-income-extracts

**For the legacy SOI CSV route below:** obtain the 2025 IRS extract XLSX dictionary,
check actual delivered archive headers and create a versioned source-column mapping
before a real SOI importer. These are not verified 2025 SOI columns. The separately
selected full-990 XML route uses the following contract instead; no SOI financial
data extract is needed to verify an XML mapping.

## Full-990 XML verification — 2026-11-21

### Actual tax-2023 local sample — subsequent checkpoint

The existing approved January 2026 archive contains actual 2023 filings; no new
download was required. The reproducible `scripts/check_2023_coverage.py` checks
snapshot/ZIP provenance, selects 52 regional index candidates with period-end
years 2023/2024, and gates actual coverage on XML TaxYr. All 52 staged without
parser findings: 39 tax-2024 and 13 tax-2023. Tax-2023 examples: OH 4 / KY 2 / IN 7,
all returnVersion 2023v6.0. Six period ends are in 2023 and seven in 2024.

Seven fields per target record matched direct XML paths (91 comparisons): EIN,
TaxYr, period end, form, total revenue, total expenses and amendment indicator.
No index identity/period mismatches or missing core fields; one amended X and
twelve absent indicators retained as true/null. The explicit 13-record tax-2023
view passes offline loader validation (8,842 compact payload bytes). No upload,
SQL execution artifact or cloud access. Report and staging remain ignored under
data/irs-tax2023-check-20261121-03/.

This adds limited 2023v6.0 core-mapping and actual-availability evidence, not full
XSD validation, all-version/form coverage, statewide completeness or a current
filing selection rule. Earlier statements that no 2023 sample was verified are
historical. See ../delivery/TAX2023-COVERAGE-PREFLIGHT.md for scope and tests.

Selected scope: XML tax years 2023–2025 (DAT-003), organizations from OH/KY/IN
source snapshots (DAT-013). This is partial verification, not live-import approval.

Official documentation inspected:

- [IRS XML archive catalog](https://www.irs.gov/charities-non-profits/form-990-series-downloads):
  lists publication years through 2026. Discovery must consider later publication
  years; never equate directory/index year with XML tax year. No index rows or
  filing archives were downloaded during this review, so selected-year coverage
  and index header/member-ID reconciliation remain unverified.
- [IRS EO BMF](https://www.irs.gov/charities-non-profits/exempt-organizations-business-master-file-extract-eo-bmf):
  cumulative current snapshot; state is determined by filing address/headquarters,
  not program reach. Page posting date observed: 2026-11-10. Actual three-state
  snapshot headers/counts/hashes and historical coverage remain unverified.
- [IRS public TEOS schemas](https://www.irs.gov/charities-non-profits/tax-exempt-organization-search-teos-schemas):
  inspected two small documentation ZIPs in memory only, capped at 5 MiB each.
  No local source files, credentials, nonprofit records or private data were used.

| Package | Bytes | SHA-256 |
|---|---:|---|
| [2023v5.1](https://www.irs.gov/pub/irs-tege/990x-schema-2023v5-1.zip) | 236218 | `b51a8472e5254572eb1cb165c2c485f8110aebcacce7211474776ba83850407c` |
| [2024v5.0](https://www.irs.gov/pub/irs-tege/990x-schema-2024v5.0.zip) | 264514 | `c25a343426f5a1cb4ac06020357a9f6e8f97a639c897b540f5098eea87b49e0c` |

Observed target namespace: `http://www.irs.gov/efile`.

| Extracted value | XML path from Return | Verification |
|---|---|---|
| EIN | ReturnHeader/Filer/EIN | 2024 header element/type observed; leading zeros remain text |
| Tax year | ReturnHeader/TaxYr | 2024 header YearType; distinct from end date |
| Period end | ReturnHeader/TaxPeriodEndDt | 2024 header DateType |
| Form | ReturnHeader/ReturnTypeCd | 2024 header; parser accepts full 990 only |
| Revenue | ReturnData/IRS990/CYTotalRevenueAmt | 2023/2024 IRS990.xsd, USAmountType |
| Expenses | ReturnData/IRS990/CYTotalExpensesAmt | 2023/2024 IRS990.xsd, USAmountType |
| Amendment | ReturnData/IRS990/AmendedReturnInd | 2023/2024 IRS990.xsd; 2024 CheckboxType is literal X |

This review found the old parser incorrectly read amendment status from the header
and expected boolean values. Parser `form990-xml-provisional-v2` reads the body
checkbox (`X` becomes true); absence remains null. Unexpected nonempty header
indicators and unsupported body values are review findings. Regenerate old v1
staging rather than loading it under the revised contract. Typed extraction is
not full XSD validation; schema package versions do not prove every filing variant.

The public TEOS page inspected lists packages through 2024. The
[2025 MeF version page](https://www.irs.gov/e-file-providers/ty-2025-xml-schemas-and-business-rules-for-exempt-organizations-and-other-tax-exempt-entities-modernized-e-file)
lists 2025 schema versions, but an equivalent public redacted package was not found.
Do not claim 2025 field mapping or actual filing availability is verified. Before
live use, obtain appropriate public schema/sample evidence for each selected
version/year, reconcile IDs and amounts, and agree on download volume/terms.
That documentation-only phase did not authorize IRS sign-in, SOR mailbox access,
or bulk download. Subsequent explicit sample approvals are recorded below.

### Local January XML sample — 2026-11-21

Mark explicitly approved the January sample after clarifying that local storage
is separate from the Supabase allowance. Downloaded one official
`2026_TEOS_XML_01A.zip` (71,497,607 bytes) into ignored
`data/irs-xml-sample-20261121-01/`, with one attempt and an 80 MB operational cap.
The existing downloader records source/hash/time/size/header provenance.

Selected one candidate per state from the completed local index, ordered by latest
tax-period end then object ID. The extractor skipped 12,242 unselected XML members
BEFORE decompression/parsing. Three records staged without review findings, and
all three matched the index EIN and tax period. Offline loader preparation passed.

Actual XML variants: one tax-year-2024 filing using `2024v5.0`, and two
tax-year-2025 filings using `2025v4.0`. Independent direct-source checks of EIN,
tax year, period end, revenue and expenses passed for all three (15 comparisons);
none of those sample fields was missing. No identities, names, addresses or amounts
were copied into chat, tests or tracked documentation.

This supplies limited actual-XML evidence for those core mappings/variants; it is
NOT full XSD validation, a test of every amendment variant, proof of statewide
completeness or a 2023 sample. The earlier statement that 2025 lacked evidence
describes the documentation-only phase, now supplemented by these two filings.
Raw ZIP, local selection, staging and aggregate report remain ignored. No
credentials, database connections or Supabase uploads were used.

### Endpoint metadata and approved source sample

Seven official-source HEAD requests returned HTTP 200 on 2026-11-21. Index
Content-Length observations for publication years 2023/2024/2025/2026 were
77,519,435 / 91,056,866 / 93,053,080 / 64,408,416 bytes (326,037,797 total).
State CSV HEAD responses reported only 20 bytes, not credible as statewide data
size; treat that as unreliable metadata, not verified CSV content. No bodies were
requested. HTTP status alone does not verify a source contract.

Mark approved the following one-time sample on 2026-11-21:

- Retrieve only official `eo_oh.csv`, `eo_ky.csv`, `eo_in.csv`, plus the official
  2026 publication index. No XML archives or Supabase writes.
- Hard transfer caps: 25,000,000 bytes per state file, 100,000,000 bytes for the
  index; 175,000,000 bytes total including partial attempts. Stop on cap, redirect,
  invalid header, status failure or unexpected content; no automatic retries.
- Write one NEW ignored local snapshot with URL/time/headers/byte count/hash
  provenance. No overwriting existing files.
- Check headers, derive state EIN candidates and count matching full-990 index
  rows. Index TAX_PERIOD does not establish XML TaxYr or selected-year coverage.
- Report only aggregate counts/quality findings, no names/addresses/raw rows.
  No credentials, cloud writes or third-party services.
- Separate approval for subsequent exact XML sample sources and volume. Existing
  extractor needs bounded scope selection before large-archive use; do not fetch
  a monthly ZIP merely to find a few candidates.
- Recovery: retain completed evidence; remove only task-owned incomplete files
  after review. No database recovery or cloud spending is involved.

Execution completed in ignored `data/irs-source-sample-20261121-01/` using the
existing downloader after adding tested byte caps and one-attempt support.

| File | Payload bytes | Data rows |
|---|---:|---:|
| Ohio EO | 13,582,204 | 77,808 |
| Kentucky EO | 4,017,310 | 22,972 |
| Indiana EO | 7,855,267 | 44,852 |
| 2026 publication index | 64,408,416 | 516,019 |
| Total | 89,863,197 | — |

The state files contain 145,632 distinct candidate EINs. This index matches 17,177
full-990 rows for 16,605 candidate EINs. Checked EIN/state/index-shape fields have
zero invalid rows; this is NOT comprehensive financial/source validation. No
within-state duplicate EINs were observed. All three EO headers matched the
documented BMF fields. The observed index header is:

`RETURN_ID,FILING_TYPE,EIN,TAX_PERIOD,SUB_DATE,TAXPAYER_NAME,RETURN_TYPE,DLN,OBJECT_ID,XML_BATCH_ID`

`XML_BATCH_ID` provides a batch reference for subsequent approved archive planning;
its member-ID relationship has not yet been verified. One publication index does
not establish complete 2023–2025 tax-year coverage, and other forms/missing filings
must not silently exclude organizations from the candidate registry. No XML
archives, database writes, credentials or retries were used. URL/time/response
headers/bytes/hash provenance and aggregate results are in `source-sample.json`.
Raw CSVs and manifests are ignored locally, not committed. This approval is spent;
additional downloads or reruns need a new source/volume decision.

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
