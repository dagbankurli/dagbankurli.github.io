#!/usr/bin/env node
/**
 * Sync pending_submissions_import.json to Supabase pending_submissions table.
 * Use this to backfill or restore pending submissions so they appear in Table Editor.
 *
 * Requires env: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
 * Expects pending_submissions_import.json in repo root: array of
 *   { id, kind, user_id?, content, created_at? }
 *
 * Usage: node scripts/sync-pending-submissions-to-supabase.js
 */
const fs = require('fs');
const path = require('path');

const SUPABASE_URL = process.env.SUPABASE_URL?.trim();
const SUPABASE_SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY?.trim();
const PENDING_PATH = path.join(process.cwd(), 'pending_submissions_import.json');
const BATCH_SIZE = 50;

if (!SUPABASE_URL || !SUPABASE_SERVICE_ROLE_KEY) {
  console.log('SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set; skipping pending submissions sync.');
  process.exit(0);
}

if (!fs.existsSync(PENDING_PATH)) {
  console.log('pending_submissions_import.json not found; skipping.');
  process.exit(0);
}

const rows = JSON.parse(fs.readFileSync(PENDING_PATH, 'utf8'));
if (!Array.isArray(rows) || rows.length === 0) {
  console.log('No pending submissions to sync.');
  process.exit(0);
}

const valid = rows.map(function (r) {
  var id = r.id != null ? String(r.id).trim() : null;
  var kind = r.kind === 'phrase' || r.kind === 'idiom' ? r.kind : 'word';
  var content = r.content && typeof r.content === 'object' ? r.content : (r.dagbani != null ? { dagbani: r.dagbani, english: r.english } : null);
  if (!id || !content) return null;
  return {
    id: id,
    kind: kind,
    user_id: r.user_id || null,
    content: content,
    created_at: r.created_at || new Date().toISOString()
  };
}).filter(Boolean);

if (valid.length === 0) {
  console.log('No valid pending submissions (need id and content).');
  process.exit(0);
}

const base = SUPABASE_URL.replace(/\/$/, '');
const url = base + '/rest/v1/pending_submissions';

function upsertBatch(batch) {
  return fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'apikey': SUPABASE_SERVICE_ROLE_KEY,
      'Authorization': 'Bearer ' + SUPABASE_SERVICE_ROLE_KEY,
      'Prefer': 'resolution=merge-duplicates'
    },
    body: JSON.stringify(batch)
  }).then(function (res) {
    if (!res.ok) return res.text().then(function (text) { throw new Error('Supabase pending_submissions upsert failed ' + res.status + ': ' + text); });
  });
}

(async function () {
  var synced = 0;
  for (var i = 0; i < valid.length; i += BATCH_SIZE) {
    var batch = valid.slice(i, i + BATCH_SIZE);
    await upsertBatch(batch);
    synced += batch.length;
    console.log('Synced ' + synced + '/' + valid.length + ' pending submissions...');
  }
  console.log('Done. Synced ' + valid.length + ' pending submissions to Supabase.');
})().catch(function (err) {
  console.error(err);
  process.exit(1);
});
