# Synthetic IRS-inspired fixture files

These **contain invented data**, not data downloaded from the IRS. See `../../../docs/requirements/IRS_SOURCE_CONTRACT.md`.

- `eo_bmf_sample.csv`: verified BMF column labels, selected subset; entirely fictional records.
- `soi_form990_legacy_sample.csv`: selected historical SOI Form 990 column labels; **not verified against 2025**; entirely fictional records.
- `soi_form990_repeat_sample.csv`: duplicate + conflicting observations to test provenance and review policy.

The tests should supply explicit external metadata such as `source_extract_year`, `source_file`, and `batch_id`. Do not add those as if they were IRS source CSV columns.
