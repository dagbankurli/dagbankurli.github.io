#!/usr/bin/env node
/**
 * Sync activity_log_import.json to Supabase activity_log table.
 * Requires env: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
 * Expects activity_log_import.json in repo root: array of { type, kind, item_id?, dagbani?, by_username, created_at? }
 * Usage: node scripts/sync-activity-log-to-supabase.js
 */
const fs = require('fs');
const path = require('path');

const SUPABASE_URL = process.env.SUPABASE_URL?.trim();
const SUPABASE_SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY?.trim();
const ACTIVITY_PATH = path.join(process.cwd(), 'activity_log_import.json');
const BATCH_SIZE = 100;

if (!SUPABASE_URL || !SUPABASE_SERVICE_ROLE_KEY) {
  console.log('SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set; skipping activity log sync.');
  process.exit(0);
}

if (!fs.existsSync(ACTIVITY_PATH)) {
  console.log('activity_log_import.json not found; skipping.');
  process.exit(0);
}

const rows = JSON.parse(fs.readFileSync(ACTIVITY_PATH, 'utf8'));
if (!Array.isArray(rows) || rows.length === 0) {
  console.log('No activity log entries to sync.');
  process.exit(0);
}

const valid = rows.map(function (r) {
  return {
    type: r.type === 'rejected' ? 'rejected' : 'approved',
    kind: r.kind === 'phrase' || r.kind === 'idiom' ? r.kind : 'word',
    item_id: r.item_id != null ? String(r.item_id) : null,
    dagbani: r.dagbani != null ? String(r.dagbani) : null,
    by_username: r.by_username != null ? String(r.by_username) : 'unknown',
    created_at: r.created_at || new Date().toISOString()
  };
}).filter(function (r) { return r.by_username; });

if (valid.length === 0) {
  console.log('No valid activity log entries.');
  process.exit(0);
}

const base = SUPABASE_URL.replace(/\/$/, '');
const url = base + '/rest/v1/activity_log';

function insertBatch(batch) {
  return fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'apikey': SUPABASE_SERVICE_ROLE_KEY,
      'Authorization': 'Bearer ' + SUPABASE_SERVICE_ROLE_KEY,
      'Prefer': 'return=minimal'
    },
    body: JSON.stringify(batch)
  }).then(function (res) {
    if (!res.ok) return res.text().then(function (text) { throw new Error('Supabase activity_log insert failed ' + res.status + ': ' + text); });
  });
}

(async function () {
  var synced = 0;
  for (var i = 0; i < valid.length; i += BATCH_SIZE) {
    var batch = valid.slice(i, i + BATCH_SIZE);
    await insertBatch(batch);
    synced += batch.length;
    console.log('Synced ' + synced + '/' + valid.length + ' activity log entries...');
  }
  console.log('Done. Synced ' + valid.length + ' activity log entries to Supabase.');
})().catch(function (err) {
  console.error(err);
  process.exit(1);
});
