@echo off
REM Run from repo root. Syncs dictionary_import.json to Supabase.
REM 1. Set your service role key in this session (do not commit it):
REM    set SUPABASE_SERVICE_ROLE_KEY=eyJ...your-key...
REM 2. Run: scripts\run-sync.cmd

if not defined SUPABASE_URL set SUPABASE_URL=https://urtmifisypcpaxbkbwac.supabase.co
if not defined SUPABASE_SERVICE_ROLE_KEY (
  echo ERROR: SUPABASE_SERVICE_ROLE_KEY not set.
  echo In Command Prompt run:
  echo   set SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
  echo   scripts\run-sync.cmd
  exit /b 1
)

cd /d "%~dp0\.."
echo Building dictionary_import.json from CSVs...
node csv_to_json.js
if errorlevel 1 exit /b 1
echo Syncing dictionary to Supabase...
node scripts/sync-dictionary-to-supabase.js
if errorlevel 1 exit /b 1
echo Syncing activity_log (if activity_log_import.json exists)...
node scripts/sync-activity-log-to-supabase.js
echo Syncing pending_submissions (if pending_submissions_import.json exists)...
node scripts/sync-pending-submissions-to-supabase.js
echo Syncing profile updates (if profiles_import.json exists)...
node scripts/sync-profiles-to-supabase.js
echo Done. Check dictionary, activity_log, pending_submissions, profiles in Supabase Table Editor.
