#!/usr/bin/env node
/**
 * Convert CSV templates to JSON for Import Data.
 * Usage: node csv_to_json.js [mode]
 *        node csv_to_json.js          -> all (words, phrases, idioms from CSVs)
 *        node csv_to_json.js words    -> words only from CSV
 *        node csv_to_json.js phrases  -> phrases only from CSV
 *        node csv_to_json.js idioms   -> idioms only from CSV
 */
const fs = require('fs');

const mode = process.argv[2] || 'all';
const output = (mode === 'words' || mode === 'phrases' || mode === 'idioms')
  ? `dictionary_import_${mode}.json` : 'dictionary_import.json';

function parseCSV(csv) {
  const lines = csv.trim().split(/\r?\n/);
  if (lines.length < 2) return [];
  const headers = lines[0].split(',').map(h => h.trim());
  const rows = [];
  for (let i = 1; i < lines.length; i++) {
    const vals = parseCSVLine(lines[i]);
    const row = {};
    headers.forEach((h, j) => { row[h] = vals[j] !== undefined ? vals[j] : ''; });
    rows.push(row);
  }
  return rows;
}

function parseCSVLine(line) {
  const out = [];
  let cur = '', inQuotes = false;
  for (let i = 0; i < line.length; i++) {
    const c = line[i];
    if (c === '"') inQuotes = !inQuotes;
    else if (c === ',' && !inQuotes) { out.push(cur.trim()); cur = ''; }
    else cur += c;
  }
  out.push(cur.trim());
  return out;
}

const result = {};

if (mode === 'all' || mode === 'words') {
  try {
    const csv = fs.readFileSync('dagbani_dictionary_template.csv', 'utf8');
    const rows = parseCSV(csv);
    result.words = rows.filter(r => r.dagbani && r.english).map((r, i) => ({
      id: i + 1,
      dagbani: String(r.dagbani).trim(),
      english: String(r.english).trim(),
      dialect: (r.dialect || 'standard').trim(),
      category: (r.category || 'general').trim(),
      grammar: r.grammar ? String(r.grammar).trim() : null,
      example: r.example ? String(r.example).trim() : null,
      verified: true,
      dateAdded: new Date().toISOString(),
      ...(r.picture ? { picture: String(r.picture).trim() } : {}),
      ...(r.audio ? { audio: String(r.audio).trim() } : {})
    }));
  } catch (e) { result.words = []; }
}

if (mode === 'all' || mode === 'phrases') {
  try {
    const csv = fs.readFileSync('dagbani_phrases_template.csv', 'utf8');
    const rows = parseCSV(csv);
    result.phrases = rows.filter(r => r.dagbani && r.english).map((r, i) => ({
      id: Date.now() + i,
      dagbani: String(r.dagbani).trim(),
      english: String(r.english).trim(),
      usage: r.usage ? String(r.usage).trim() : null,
      category: (r.category || 'general').trim(),
      picture: r.picture ? String(r.picture).trim() : null,
      audio: r.audio ? String(r.audio).trim() : null
    }));
  } catch (e) { result.phrases = []; }
}

if (mode === 'all' || mode === 'idioms') {
  try {
    const csv = fs.readFileSync('dagbani_idioms_proverbs_template.csv', 'utf8');
    const rows = parseCSV(csv);
    result.idioms = rows.filter(r => r.dagbani && r.english).map((r, i) => ({
      id: Date.now() + i + 1000,
      dagbani: String(r.dagbani).trim(),
      english: String(r.english).trim(),
      usage: r.usage ? String(r.usage).trim() : null,
      category: (r.category || 'general').trim(),
      picture: r.picture ? String(r.picture).trim() : null,
      audio: r.audio ? String(r.audio).trim() : null
    }));
  } catch (e) { result.idioms = []; }
}

fs.writeFileSync(output, JSON.stringify(result, null, 2));
console.log(`Wrote to ${output}:`);
if (result.words) console.log(`  - ${result.words.length} words`);
if (result.phrases) console.log(`  - ${result.phrases.length} phrases`);
if (result.idioms) console.log(`  - ${result.idioms.length} idioms`);
console.log('Import: Profile → Preferences & Data → Import Data (Restore)');
