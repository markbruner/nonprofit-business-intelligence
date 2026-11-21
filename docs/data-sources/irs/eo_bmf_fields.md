# IRS EO BMF CSV fields

Source document: [Exempt Organizations Business Master File Extract (EO BMF)](https://www.irs.gov/pub/irs-soi/eo-info.pdf), November 2023. The IRS describes this as a monthly cumulative snapshot containing its most recent information. It is organized by filing address, which generally represents headquarters and may not represent operational geography. Source pages 1-2.

The contract in [`config/schemas/irs_eo_bmf.yaml`](../../../config/schemas/irs_eo_bmf.yaml) preserves every CSV column in the documented order. The document says every record contains these data fields. It does not state whether individual values can be blank, so `nullable` is `unverified` for every field.

| # | CSV field | IRS definition | Source page |
|---:|---|---|---:|
| 1 | `EIN` | Employer Identification Number (EIN), a nine-digit number assigned by the IRS to identify an organization's account | 1-2 |
| 2 | `NAME` | Primary Name of Organization | 1 |
| 3 | `ICO` | In Care of Name, the person to whose attention correspondence should be directed | 1-2 |
| 4 | `STREET` | Street Address | 1 |
| 5 | `CITY` | City | 1 |
| 6 | `STATE` | State | 1 |
| 7 | `ZIP` | Zip Code | 1 |
| 8 | `GROUP` | Group Exemption Number, a four-digit internal number for central or parent organizations holding group exemption letters | 2 |
| 9 | `SUBSECTION` | Subsection Code | 2-3 |
| 10 | `AFFILIATION` | Affiliation Code | 2 |
| 11 | `CLASSIFICATION` | Classification Code(s), with one to four codes possible | 2-3 |
| 12 | `RULING` | Ruling Date, month and year in `YYYYMM` on the ruling or determination letter recognizing exempt status | 2-3 |
| 13 | `DEDUCTIBILITY` | Deductibility Code | 2-3 |
| 14 | `FOUNDATION` | Foundation Code | 2-3 |
| 15 | `ACTIVITY` | Activity Codes | 2 |
| 16 | `ORGANIZATION` | Organization Code | 2, 4 |
| 17 | `STATUS` | Exempt Organization Status Code | 2, 4 |
| 18 | `TAX_PERIOD` | Tax period of the latest return filed, in `YYYYMM` | 2, 4 |
| 19 | `ASSET_CD` | Asset Code for the book value of assets on the most recent Form 990-series return | 2, 5 |
| 20 | `INCOME_CD` | Income Code for income on the most recent Form 990-series return | 2, 5 |
| 21 | `FILING_REQ_CD` | Filing Requirement Code | 2, 5 |
| 22 | `PF_FILING_REQ_CD` | PF Filing Requirement Code | 2, 5 |
| 23 | `ACCT_PD` | Accounting Period or fiscal year-ending month in `MM` | 2, 5 |
| 24 | `ASSET_AMT` | Asset Amount from the most recent Form 990-series return, expressed in dollars | 2, 5 |
| 25 | `INCOME_AMT` | Income Amount from the most recent Form 990-series return, expressed in dollars and including a negative sign when negative | 2, 6 |
| 26 | `REVENUE_AMT` | Form 990 Revenue Amount, including a negative sign when negative | 2, 6 |
| 27 | `NTEE_CD` | National Taxonomy of Exempt Entities (NTEE) Code | 2 |
| 28 | `SORT_NAME` | Sort Name, the secondary name line | 2, 6 |

`ASSET_AMT`, `INCOME_AMT`, and `REVENUE_AMT` are snapshot values. This BMF contract does not define the annual Form 990 financial-extract schema or a multi-year filing history.
