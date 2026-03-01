# Run from repo root. Fills Supabase "dictionary" table from dictionary_import.json.
# 1. Get your SERVICE ROLE key: Supabase Dashboard -> Project Settings -> API -> "service_role" (secret, not anon).
# 2. In PowerShell from repo root, set the key then run this script:
#    $env:SUPABASE_SERVICE_ROLE_KEY = "eyJ...your-service-role-key..."
#    .\scripts\run-sync.ps1
#    Or set SUPABASE_URL if different: $env:SUPABASE_URL = "https://YOUR_PROJECT.supabase.co"

if (-not $env:SUPABASE_URL) { $env:SUPABASE_URL = "https://urtmifisypcpaxbkbwac.supabase.co" }
if (-not $env:SUPABASE_SERVICE_ROLE_KEY -or $env:SUPABASE_SERVICE_ROLE_KEY -eq "YOUR_SERVICE_ROLE_KEY_HERE") {
    Write-Host "ERROR: Set your Supabase SERVICE ROLE key first." -ForegroundColor Red
    Write-Host "  1. Supabase Dashboard -> Project Settings -> API -> copy 'service_role' (the secret key, not anon)." -ForegroundColor Yellow
    Write-Host "  2. In PowerShell run:" -ForegroundColor Yellow
    Write-Host '     $env:SUPABASE_SERVICE_ROLE_KEY = "eyJ...paste-key-here..."' -ForegroundColor Cyan
    Write-Host "     .\scripts\run-sync.ps1" -ForegroundColor Cyan
    exit 1
}

Write-Host "Building dictionary_import.json from CSVs..."
Set-Location $PSScriptRoot\..
node csv_to_json.js
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Syncing to Supabase..."
node scripts/sync-dictionary-to-supabase.js
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Done. Check the dictionary table in Supabase Table Editor."
