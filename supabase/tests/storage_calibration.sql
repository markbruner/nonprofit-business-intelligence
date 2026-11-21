-- LOCAL SYNTHETIC BENCHMARK ONLY. Never run against Supabase/cloud.
-- Requires the migration in a new isolated database named nbi_local_storage_test.
-- All rows and operational values are fictional test fixtures, NOT approved budgets.
begin;
set local statement_timeout = '60s';
do $$ begin
    if current_database() <> 'nbi_local_storage_test'
       or exists (select 1 from nonprofit_ingest.import_runs)
       or exists (select 1 from nonprofit_ingest.storage_policy) then
        raise exception 'empty_named_local_test_database_required';
    end if;
end $$;

create temporary table sizing_baseline as
select pg_database_size(current_database()) as database_bytes,
       sum(pg_total_relation_size(c.oid))::bigint as schema_bytes
from pg_class c join pg_namespace n on n.oid=c.relnamespace
where n.nspname='nonprofit_ingest' and c.relkind='r';

insert into nonprofit_ingest.storage_policy values (
    true,'SYNTHETIC-LOCAL',2147483648,1073741824,134217728,300,250,
    array[2023,2024,2025],2097152,4,65536,now(),'SYNTHETIC BENCHMARK ONLY');
insert into nonprofit_ingest.capacity_measurement values (
    true,'SYNTHETIC-LOCAL',now(),pg_database_size(current_database()),134217728,2147483648);
insert into nonprofit_ingest.approved_eins
select 'synthetic-sizing-v1',lpad(i::text,9,'0'),'SYNTHETIC TEST ONLY'
from generate_series(1,1000) i;

do $$
declare offset_row integer; payload jsonb; receipt jsonb;
begin
    for offset_row in 0..11 loop
        with numbered as (
            select i, lpad((1+(i-1)/3)::text,9,'0') as ein,
                   2023+(i-1)%3 as tax_year,
                   'synthetic-'||i::text as filing_id,
                   encode(sha256(convert_to('synthetic XML '||i::text,'UTF8')),'hex') as xml_hash
            from generate_series(offset_row*250+1, offset_row*250+250) i
        )
        select jsonb_build_object(
            'parser_version','form990-xml-provisional-v2',
            'scope_version','synthetic-sizing-v1',
            'manifest_sha256',encode(sha256(convert_to('synthetic manifest '||offset_row::text,'UTF8')),'hex'),
            'filings',jsonb_agg(jsonb_build_object(
                'filing_key',encode(sha256(convert_to(filing_id,'UTF8')||decode('00','hex')||convert_to(xml_hash,'UTF8')),'hex'),
                'source_filing_id',filing_id,'xml_sha256',xml_hash,'ein',ein,
                'tax_period_end',tax_year::text||'-12-31','tax_year',tax_year,
                'form_type','990','amended',null,
                'total_revenue',999999999999999999::bigint,
                'total_expenses',case when i%2=0 then null else -999999999999999999::bigint end,
                'sources',jsonb_build_array(jsonb_build_object(
                    'archive_path','2026/'||md5(i::text)||'.zip',
                    'archive_sha256',xml_hash,
                    'source_url','https://example.invalid/'||repeat(md5(i::text),3)||'.zip',
                    'downloaded_at','2026-11-21T12:00:00+00:00',
                    'member',filing_id||'_public.xml'))
            ) order by i)) into payload from numbered;
        receipt := nonprofit_ingest.load_990(payload);
        if receipt->>'status' <> 'complete' then raise exception 'synthetic_import_failed'; end if;
    end loop;
    if (select count(*) from nonprofit_ingest.organizations) <> 1000
       or (select count(*) from nonprofit_ingest.organization_filings) <> 3000
       or (select count(*) from nonprofit_ingest.import_runs) <> 12
       or (select count(*) from nonprofit_ingest.import_run_filings) <> 3000 then
        raise exception 'synthetic_counts_mismatch';
    end if;
end $$;

with after_sizes as (
    select sum(pg_total_relation_size(c.oid))::bigint as schema_bytes
    from pg_class c join pg_namespace n on n.oid=c.relnamespace
    where n.nspname='nonprofit_ingest' and c.relkind='r'
)
select 1000 as synthetic_organizations,3000 as synthetic_filings,12 as batches,
       a.schema_bytes-b.schema_bytes as schema_growth_bytes_including_indexes,
       round((a.schema_bytes-b.schema_bytes)::numeric/3000,2) as amortized_bytes_per_filing,
       pg_database_size(current_database())-b.database_bytes as database_growth_bytes,
       (select max(projected_bytes-database_bytes_before-268435456) from nonprofit_ingest.import_runs)
          as largest_admitted_batch_estimate_bytes,
       'NOT a cloud/WAL/system measurement or approved operating threshold' as limitation
from after_sizes a cross join sizing_baseline b;
rollback;
