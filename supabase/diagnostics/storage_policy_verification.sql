-- READ ONLY. Run after the separately approved initial policy setup.
select project_ref, included_bytes, stop_bytes, reserve_bytes,
       max_measurement_age_seconds, max_rows, approved_tax_years,
       max_payload_bytes, growth_multiplier, minimum_bytes_per_filing,
       approved_at, approval_reference
from nonprofit_ingest.storage_policy
where singleton;
