# Data unification – what you need to do

Dictionary data now syncs to Supabase in two cases: **on git push** (via the deploy workflow) and **when an admin imports JSON** in the app. Follow these steps so it works.

---

## 1. Create the `dictionary` table in Supabase

If you haven’t already, run the dictionary table SQL in your Supabase project:

1. Open [Supabase Dashboard](https://supabase.com/dashboard) → your project → **SQL Editor**.
2. Run the **“4. Dictionary”** block from `supabase_schema.sql` (the part that creates the `dictionary` table and its RLS policies).  
   Or run the SQL from **section 9** in `SUPABASE_SETUP.md`.

That’s the same table the app and the sync script use.

---

## 2. (Optional) Sync on every push to `main`

To have the deploy workflow push `dictionary_import.json` to Supabase on each deploy:

1. In Supabase: **Project Settings** → **API** → copy the **`service_role`** key (secret, not the anon key).
2. On GitHub: repo → **Settings** → **Secrets and variables** → **Actions**.
3. Add a secret: name **`SUPABASE_SERVICE_ROLE_KEY`**, value = the `service_role` key you copied.

After that, each push to `main` will:

- Run `node csv_to_json.js` (build `dictionary_import.json` from your CSVs).
- Run `node scripts/sync-dictionary-to-supabase.js` (upsert that data into the `dictionary` table).

If you don’t add this secret, deploys still work; the dictionary just won’t be synced from the repo on push.

---

## 3. App behaviour (no extra steps)

- **Load:** If Supabase is configured, the app first loads words/phrases/idioms from the `dictionary` table; if that fails or is empty, it uses localStorage and then `dictionary_import.json`.
- **Import:** When an **admin** imports a JSON file (Preferences → Import Data), the app syncs the imported dictionary data to Supabase after a successful import.

---

## 4. Local sync (PowerShell) – copy and run

Your project URL is already in `scripts/run-sync.ps1`. You only need to set the **service_role** key and run.

1. **Get the service_role key:** Supabase Dashboard → **Project Settings** → **API** → under "Project API keys" copy **`service_role`** (the secret one, not anon).

2. **From the repo root** in PowerShell, run:

```powershell
$env:SUPABASE_SERVICE_ROLE_KEY = "paste-your-service-role-key-here"
.\scripts\run-sync.ps1
```

That builds `dictionary_import.json` from your CSVs and syncs it to the `dictionary` table. Then check the dictionary table in Supabase Table Editor.

---

---

## 5. How to know data is connected

- **In the app:** Sign in → open **Profile** (or the view that has **Preferences & Data**). Under **Supabase connection** you’ll see:
  - **Supabase is not configured** — app is using only localStorage / `dictionary_import.json`.
  - **Supabase is connected** — app can talk to Supabase. Tap **Check dictionary in Supabase** to see whether the dictionary table has data (e.g. “X words, Y phrases, Z idioms”) or is empty.
- **In Supabase:** Dashboard → **Table Editor** → open the **dictionary** table. If sync has run (from deploy or from an admin import), you’ll see rows with `kind` (word/phrase/idiom) and `content` (JSON).

**Summary:** Run the dictionary table SQL in Supabase once. Add `SUPABASE_SERVICE_ROLE_KEY` in GitHub if you want sync-on-push. Use Profile → Preferences & Data → “Check dictionary in Supabase” to confirm data is in the cloud.
