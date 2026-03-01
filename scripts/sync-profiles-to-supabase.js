#!/usr/bin/env node
/**
 * Update existing Supabase profiles from profiles_import.json.
 * Use this to bulk-update role/attribution so Table Editor stays in sync.
 * Does NOT create new profiles (those come from Supabase Auth signup).
 *
 * Requires env: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
 * Expects profiles_import.json in repo root: array of
 *   { username, role?, attribution_name? }
 * Only existing profiles (by username) are updated.
 *
 * Usage: node scripts/sync-profiles-to-supabase.js
 */
const fs = require('fs');
const path = require('path');

const SUPABASE_URL = process.env.SUPABASE_URL?.trim();
const SUPABASE_SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY?.trim();
const PROFILES_PATH = path.join(process.cwd(), 'profiles_import.json');

const ROLES = ['visitor', 'user', 'contributor', 'admin'];

if (!SUPABASE_URL || !SUPABASE_SERVICE_ROLE_KEY) {
  console.log('SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set; skipping profiles sync.');
  process.exit(0);
}

if (!fs.existsSync(PROFILES_PATH)) {
  console.log('profiles_import.json not found; skipping. Create it with an array of { username, role?, attribution_name? }.');
  process.exit(0);
}

const rows = JSON.parse(fs.readFileSync(PROFILES_PATH, 'utf8'));
if (!Array.isArray(rows) || rows.length === 0) {
  console.log('No profile updates to apply.');
  process.exit(0);
}

const base = SUPABASE_URL.replace(/\/$/, '');
const selectUrl = `${base}/rest/v1/profiles?select=id,username`;

async function fetchExistingProfiles() {
  const res = await fetch(selectUrl, {
    method: 'GET',
    headers: {
      'apikey': SUPABASE_SERVICE_ROLE_KEY,
      'Authorization': `Bearer ${SUPABASE_SERVICE_ROLE_KEY}`
    }
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Supabase profiles select failed ${res.status}: ${text}`);
  }
  return res.json();
}

async function updateProfile(id, payload) {
  const res = await fetch(`${base}/rest/v1/profiles?id=eq.${id}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      'apikey': SUPABASE_SERVICE_ROLE_KEY,
      'Authorization': `Bearer ${SUPABASE_SERVICE_ROLE_KEY}`
    },
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Supabase profiles update failed ${res.status}: ${text}`);
  }
}

(async () => {
  const existing = await fetchExistingProfiles();
  const byUsername = new Map(existing.map((p) => [p.username, p]));

  let updated = 0;
  for (const r of rows) {
    const username = r.username != null ? String(r.username).trim() : null;
    if (!username || !byUsername.has(username)) continue;

    const payload = {};
    if (r.role && ROLES.includes(r.role)) payload.role = r.role;
    if (r.attribution_name !== undefined) payload.attribution_name = r.attribution_name == null ? null : String(r.attribution_name);
    payload.updated_at = new Date().toISOString();

    if (Object.keys(payload).length <= 1) continue; // only updated_at

    const id = byUsername.get(username).id;
    await updateProfile(id, payload);
    updated++;
    console.log(`Updated profile: ${username}`);
  }
  console.log(`Done. Updated ${updated} profile(s) in Supabase.`);
})().catch((err) => {
  console.error(err);
  process.exit(1);
});
