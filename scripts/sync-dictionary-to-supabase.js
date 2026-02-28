#!/usr/bin/env node
/**
 * Sync dictionary_import.json to Supabase dictionary table.
 * Used by: deploy workflow (on git push) and optionally run locally.
 *
 * Requires env: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
 * Run from repo root. Expects dictionary_import.json in cwd (create with: node csv_to_json.js).
 *
 * Usage: node scripts/sync-dictionary-to-supabase.js
 */
const fs = require('fs');
const path = require('path');

const SUPABASE_URL = process.env.SUPABASE_URL?.trim();
const SUPABASE_SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY?.trim();
const DICT_PATH = path.join(process.cwd(), 'dictionary_import.json');
const BATCH_SIZE = 100;

if (!SUPABASE_URL || !SUPABASE_SERVICE_ROLE_KEY) {
  console.log('SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set; skipping dictionary sync.');
  process.exit(0);
}

if (!fs.existsSync(DICT_PATH)) {
  console.error('dictionary_import.json not found. Run: node csv_to_json.js');
  process.exit(1);
}

const data = JSON.parse(fs.readFileSync(DICT_PATH, 'utf8'));
const rows = [];

const kindMap = { words: 'word', phrases: 'phrase', idioms: 'idiom' };
['words', 'phrases', 'idioms'].forEach(key => {
  const list = data[key] || [];
  const kind = kindMap[key];
  list.forEach(item => {
    const itemId = item?.id != null ? String(item.id) : '';
    if (!itemId) return;
    rows.push({
      kind,
      item_id: itemId,
      content: item,
      updated_at: new Date().toISOString()
    });
  });
});

if (rows.length === 0) {
  console.log('No dictionary entries to sync.');
  process.exit(0);
}

const base = SUPABASE_URL.replace(/\/$/, '');
const url = `${base}/rest/v1/dictionary?on_conflict=kind,item_id`;

async function upsertBatch(batch) {
  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'apikey': SUPABASE_SERVICE_ROLE_KEY,
      'Authorization': `Bearer ${SUPABASE_SERVICE_ROLE_KEY}`,
      'Prefer': 'resolution=merge-duplicates'
    },
    body: JSON.stringify(batch)
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Supabase upsert failed ${res.status}: ${text}`);
  }
}

(async () => {
  let synced = 0;
  for (let i = 0; i < rows.length; i += BATCH_SIZE) {
    const batch = rows.slice(i, i + BATCH_SIZE);
    await upsertBatch(batch);
    synced += batch.length;
    console.log(`Synced ${synced}/${rows.length}...`);
  }
  console.log(`Done. Synced ${rows.length} dictionary entries to Supabase.`);
})().catch(err => {
  console.error(err);
  process.exit(1);
});
