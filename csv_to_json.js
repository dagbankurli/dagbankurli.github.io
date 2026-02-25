#!/usr/bin/env node
/**
 * Convert CSV templates to dictionary_import.json for Import Data.
 * Reads all three templates and outputs a single dictionary_import.json.
 *
 * Usage: node csv_to_json.js
 *
 * Templates:
 *   - dagbani_dictionary_template.csv  (words)
 *   - dagbani_phrases_template.csv     (phrases)
 *   - dagbani_idioms_proverbs_template.csv (idioms & proverbs)
 *
 * Optional: dagbani_adverbs_template.csv (merged into words if present)
 */
const fs = require('fs');

const OUTPUT = 'dictionary_import.json';

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

const result = { words: [], phrases: [], idioms: [] };

// Words: keep ALL rows with dagbani+english (no dedup - same word can have multiple senses)
try {
  const csv = fs.readFileSync('dagbani_dictionary_template.csv', 'utf8');
  const rows = parseCSV(csv);
  let words = rows.filter(r => r.dagbani && r.english);
  if (fs.existsSync('dagbani_adverbs_template.csv')) {
    const advCsv = fs.readFileSync('dagbani_adverbs_template.csv', 'utf8');
    const advRows = parseCSV(advCsv);
    const seen = new Set(words.map(r => String(r.dagbani).trim().toLowerCase()));
    advRows.filter(r => r.dagbani && r.english).forEach(r => {
      const key = String(r.dagbani).trim().toLowerCase();
      if (!seen.has(key)) { seen.add(key); words.push(r); }
    });
  }
  result.words = words.map((r, i) => ({
    id: i + 1,
    dagbani: String(r.dagbani).trim(),
    english: String(r.english).trim(),
    dialect: (r.dialect || 'standard').trim(),
    category: (r.category || 'general').trim(),
    grammar: r.grammar ? String(r.grammar).trim() : null,
    example: r.example ? String(r.example).trim() : null,
    verified: true,
    dateAdded: new Date().toISOString(),
    ...(r.picture && !/^picture$/i.test(String(r.picture).trim()) ? { picture: String(r.picture).trim() } : {}),
    ...(r.audio ? { audio: String(r.audio).trim() } : {})
  }));
} catch (e) {
  console.error('Words error:', e.message);
}

// Phrases
try {
  const csv = fs.readFileSync('dagbani_phrases_template.csv', 'utf8');
  const rows = parseCSV(csv);
  result.phrases = rows.filter(r => r.dagbani && r.english).map((r, i) => ({
    id: Date.now() + i,
    dagbani: String(r.dagbani).trim(),
    english: String(r.english).trim(),
    usage: r.usage ? String(r.usage).trim() : null,
    category: (r.category || 'general').trim(),
    picture: (r.picture && !/^picture$/i.test(String(r.picture).trim())) ? String(r.picture).trim() : null,
    audio: r.audio ? String(r.audio).trim() : null
  }));
} catch (e) {
  console.error('Phrases error:', e.message);
}

// Idioms & Proverbs
try {
  const csv = fs.readFileSync('dagbani_idioms_proverbs_template.csv', 'utf8');
  const rows = parseCSV(csv);
  result.idioms = rows.filter(r => r.dagbani && r.english).map((r, i) => ({
    id: Date.now() + i + 1000,
    dagbani: String(r.dagbani).trim(),
    english: String(r.english).trim(),
    usage: r.usage ? String(r.usage).trim() : null,
    category: (r.category || 'general').trim(),
    picture: (r.picture && !/^picture$/i.test(String(r.picture).trim())) ? String(r.picture).trim() : null,
    audio: r.audio ? String(r.audio).trim() : null
  }));
} catch (e) {
  console.error('Idioms error:', e.message);
}

fs.writeFileSync(OUTPUT, JSON.stringify(result, null, 2));
console.log(`Wrote ${OUTPUT}:`);
console.log(`  - ${result.words.length} words`);
console.log(`  - ${result.phrases.length} phrases`);
console.log(`  - ${result.idioms.length} idioms`);
console.log('Import: Profile → Preferences & Data → Import Data (Restore)');
