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

## 4. Local test (optional)

From the repo root:

```bash
node csv_to_json.js
```

Then, with your Supabase project URL and service_role key set:

```bash
set SUPABASE_URL=https://your-project.supabase.co
set SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
node scripts/sync-dictionary-to-supabase.js
```

(On macOS/Linux use `export` instead of `set`.)

---

**Summary:** Run the dictionary table SQL in Supabase once. Add `SUPABASE_SERVICE_ROLE_KEY` in GitHub if you want sync-on-push. The rest is already in the app and workflow.
