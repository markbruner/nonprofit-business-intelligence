# IRS EO BMF code mappings

Source document: [Exempt Organizations Business Master File Extract (EO BMF)](https://www.irs.gov/pub/irs-soi/eo-info.pdf), November 2023. These mappings apply only to the EO BMF CSV contract.

## Affiliation codes

| Code | Meaning |
|---|---|
| `1` | Central organization without a group exemption |
| `2` | Intermediate organization without a group exemption |
| `3` | Independent organization or independent auxiliary |
| `6` | Parent organization under a group ruling, not a church or 501(c)(1) organization |
| `7` | Group-exemption intermediate organization |
| `8` | Parent organization under a group ruling that is a church or 501(c)(1) organization |
| `9` | Subordinate organization in a group ruling |

Source pages 2-3.

## Exemption, deductibility, and foundation codes

| Field | Code | Meaning |
|---|---|---|
| `STATUS` | `01` | Unconditional exemption |
| `STATUS` | `02` | Conditional exemption |
| `STATUS` | `12` | Trust described in IRC 4947(a)(2) |
| `STATUS` | `25` | Organization terminating private-foundation status under IRC 507(b)(1)(B) |
| `DEDUCTIBILITY` | `1` | Contributions are deductible |
| `DEDUCTIBILITY` | `2` | Contributions are not deductible |
| `DEDUCTIBILITY` | `4` | Contributions are deductible by treaty for foreign organizations |
| `FOUNDATION` | `00` | All organizations except 501(c)(3) |
| `FOUNDATION` | `02` | Private operating foundation exempt from investment-income excise tax |
| `FOUNDATION` | `03` | Other private operating foundation |
| `FOUNDATION` | `04` | Private non-operating foundation |
| `FOUNDATION` | `09` | Suspense |
| `FOUNDATION` | `10` | Church under 170(b)(1)(A)(i) |
| `FOUNDATION` | `11` | School under 170(b)(1)(A)(ii) |
| `FOUNDATION` | `12` | Hospital or medical research organization under 170(b)(1)(A)(iii) |
| `FOUNDATION` | `13` | College or university benefit organization owned or operated by a governmental unit under 170(b)(1)(A)(iv) |
| `FOUNDATION` | `14` | Governmental unit under 170(b)(1)(A)(v) |
| `FOUNDATION` | `15` | Organization receiving substantial support from a government unit or the general public under 170(b)(1)(A)(vi) |
| `FOUNDATION` | `16` | Organization described in 509(a)(2) |
| `FOUNDATION` | `17` | Supporting organization described in 509(a)(3) |
| `FOUNDATION` | `18` | Organization testing for public safety under 509(a)(4) |
| `FOUNDATION` | `21` | 509(a)(3) Type I |
| `FOUNDATION` | `22` | 509(a)(3) Type II |
| `FOUNDATION` | `23` | 509(a)(3) Type III functionally integrated |
| `FOUNDATION` | `24` | 509(a)(3) Type III not functionally integrated |

Source pages 3-4. The document contains a fuller subsection and classification table beginning on page 6. This contract retains those fields without duplicating that table.

## Asset and income codes

`ASSET_CD` and `INCOME_CD` use the same ranges. `ASSET_CD` represents book value of assets and `INCOME_CD` represents income from the most recent Form 990-series return.

| Code | Dollar range |
|---|---:|
| `0` | 0 |
| `1` | 1-9,999 |
| `2` | 10,000-24,999 |
| `3` | 25,000-99,999 |
| `4` | 100,000-499,999 |
| `5` | 500,000-999,999 |
| `6` | 1,000,000-4,999,999 |
| `7` | 5,000,000-9,999,999 |
| `8` | 10,000,000-49,999,999 |
| `9` | 50,000,000 or greater |

Source page 5.

## Filing requirement codes

| Field | Code | Meaning |
|---|---|---|
| `FILING_REQ_CD` | `01` | Form 990 or 990-EZ return |
| `FILING_REQ_CD` | `02` | Form 990-N requirement for income below $50,000 per year |
| `FILING_REQ_CD` | `03` | Form 990 group return |
| `FILING_REQ_CD` | `04` | Form 990-BL requirement for Black Lung Trusts |
| `FILING_REQ_CD` | `06` | No Form 990 filing requirement for a church |
| `FILING_REQ_CD` | `07` | Government 501(c)(1) |
| `FILING_REQ_CD` | `13` | No Form 990 filing requirement for a religious organization |
| `FILING_REQ_CD` | `14` | No Form 990 filing requirement for state or political-subdivision instrumentalities |
| `FILING_REQ_CD` | `00` | No Form 990 filing requirement for all other organizations |
| `PF_FILING_REQ_CD` | `1` | Form 990-PF return |
| `PF_FILING_REQ_CD` | `0` | No Form 990-PF return |

Source page 5.
