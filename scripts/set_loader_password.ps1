<# User-run secure password setup ONLY. No activation, grants or import.
   Needs cached postgres:17 and the public CA certificate from this dev project.
   Passwords are entered at hidden psql prompts, never command-line arguments.
   Do not run from an agent tool or enable PowerShell transcription/debug tracing.
#>
[CmdletBinding()]
param([Parameter(Mandatory = $true)][string]$CaCert)
$ErrorActionPreference = 'Stop'
$certificatePath = (Resolve-Path -LiteralPath $CaCert).ProviderPath
if (-not (Test-Path -LiteralPath $certificatePath -PathType Leaf) -or $certificatePath.Contains(',')) {
    throw 'Choose a public CA certificate file without commas in its path.'
}
$guard = @'
do $$ begin
    if current_user <> 'postgres' or not exists(
        select 1 from pg_roles where rolname='nb_loader_dev' and not rolcanlogin
          and not rolsuper and not rolbypassrls and not rolcreaterole
          and not rolcreatedb and not rolreplication and rolconnlimit=1)
        or not exists(select 1 from nonprofit_ingest.storage_policy
            where project_ref='yxtslaaboriakfvpeedi' and singleton) then
        raise exception 'expected_dev_owner_and_disabled_loader_required';
    end if;
end $$;
'@
$connection = 'host=aws-1-us-east-2.pooler.supabase.com port=5432 dbname=postgres user=postgres.yxtslaaboriakfvpeedi sslmode=verify-full sslrootcert=/etc/ssl/certs/nbi-supabase-ca.crt connect_timeout=10 passfile=/dev/null'
$dockerArgs = @(
    'run', '--rm', '--interactive', '--tty', '--pull=never', '--read-only',
    '--cap-drop=ALL', '--security-opt=no-new-privileges',
    '--mount', "type=bind,source=$certificatePath,target=/etc/ssl/certs/nbi-supabase-ca.crt,readonly",
    '--env', 'PSQL_HISTORY=/dev/null', 'postgres:17',
    'psql', '-X', '-W', '--set=ON_ERROR_STOP=1', '--single-transaction',
    $connection, '-c', $guard, '-c', "set password_encryption='scram-sha-256';",
    '-c', 'password nb_loader_dev'
)
Write-Host 'Enter the existing dev database owner password, then the new loader password twice.'
& docker @dockerArgs
if ($LASTEXITCODE -ne 0) { throw 'Password setup failed; do not activate or retry blindly.' }
Write-Host 'Password command completed. Loader LOGIN is still disabled; no records imported.'
