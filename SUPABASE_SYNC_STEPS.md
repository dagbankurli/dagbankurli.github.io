# What to do: Get data into Supabase Table Editor

Follow these steps so your **dictionary**, **activity_log**, **pending_submissions**, and **profiles** show up (or stay in sync) in the Supabase Table Editor.

---

## Step 1: Set your Supabase keys (one time per terminal)

You need two things from **Supabase Dashboard → Project Settings → API**:

- **Project URL** (e.g. `https://urtmifisypcpaxbkbwac.supabase.co`)
- **service_role key** (the **secret** key, not the anon/public key)

**In PowerShell** (run from your project folder, e.g. `Dagban Kurli`):

```powershell
$env:SUPABASE_URL = "https://urtmifisypcpaxbkbwac.supabase.co"
$env:SUPABASE_SERVICE_ROLE_KEY = "eyJ...paste-your-SERVICE-ROLE-key-here..."
```

**In Command Prompt (cmd):**

```cmd
set SUPABASE_URL=https://urtmifisypcpaxbkbwac.supabase.co
set SUPABASE_SERVICE_ROLE_KEY=eyJ...paste-your-SERVICE-ROLE-key-here...
```

Use your real **service_role** key (starts with `eyJ...`). Do not use the anon key here.

---

## Step 2: Sync the dictionary (required)

This fills the **dictionary** table so the app (and Table Editor) has words, phrases, idioms.

1. Open a terminal in your project folder (`Dagban Kurli`).
2. Make sure you ran Step 1 in that same terminal.
3. Run:

**PowerShell:**

```powershell
.\scripts\run-sync.ps1
```

**Cmd:**

```cmd
scripts\run-sync.cmd
```

This will:

- Build `dictionary_import.json` from your CSVs (if you have `csv_to_json.js`).
- Upload that data to the **dictionary** table in Supabase.

After this, open **Supabase → Table Editor → dictionary** and you should see rows.

---

## Step 3 (optional): Sync activity log

Only if you want **activity_log** rows (approvals/rejections) in Table Editor from a file:

1. In your project folder, create a file named **`activity_log_import.json`** (same folder as `index.html`).
2. Put in it a JSON array of entries, for example:

```json
[
  { "type": "approved", "kind": "word", "by_username": "Admin" },
  { "type": "rejected", "kind": "phrase", "dagbani": "Example", "by_username": "Admin" }
]
```

3. In the same terminal (with Step 1 still set), run:

```powershell
node scripts/sync-activity-log-to-supabase.js
```

Then check **Supabase → Table Editor → activity_log**.

---

## Step 4 (optional): Sync pending submissions

Only if you want **pending_submissions** in Table Editor from a file:

1. In your project folder, create **`pending_submissions_import.json`** (same folder as `index.html`).
2. Put in it a JSON array, for example:

```json
[
  {
    "id": "my-phrase-1",
    "kind": "phrase",
    "content": { "dagbani": "Dasiba", "english": "Good morning" }
  }
]
```

3. Run:

```powershell
node scripts/sync-pending-submissions-to-supabase.js
```

Then check **Supabase → Table Editor → pending_submissions**.

---

## Step 5 (optional): Update profiles (role / attribution)

**Profiles** are normally created when users **sign up in the app**. You cannot create new users from a JSON file; you can only **update** existing profiles (e.g. role, attribution name).

1. In your project folder, create **`profiles_import.json`** (same folder as `index.html`).
2. Put in it a JSON array of **existing** usernames and the fields you want to change:

```json
[
  { "username": "mwumpini", "role": "admin", "attribution_name": "Dr. Name" },
  { "username": "Mamani 11", "role": "contributor", "attribution_name": "fggg" }
]
```

3. Run:

```powershell
node scripts/sync-profiles-to-supabase.js
```

Then check **Supabase → Table Editor → profiles**. Only rows that already exist (from app signup) will be updated.

---

## Quick reference

| What you want | What to do |
|---------------|------------|
| **Dictionary** in Table Editor | Set env (Step 1), then run `.\scripts\run-sync.ps1` (or `scripts\run-sync.cmd`). |
| **Activity log** in Table Editor | Create `activity_log_import.json`, run `node scripts/sync-activity-log-to-supabase.js`. |
| **Pending submissions** in Table Editor | Create `pending_submissions_import.json`, run `node scripts/sync-pending-submissions-to-supabase.js`. |
| **Update profiles** (role/attribution) | Create `profiles_import.json`, run `node scripts/sync-profiles-to-supabase.js`. |

All import JSON files go in the **project root** (same folder as `index.html`).  
You must set **SUPABASE_URL** and **SUPABASE_SERVICE_ROLE_KEY** in the same terminal before running any of the scripts.
