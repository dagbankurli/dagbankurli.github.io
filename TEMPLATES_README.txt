Dagban Kurli - Excel/CSV templates for bulk entry

The app loads its dictionary data from dictionary_import.json (not dictionary_data.json).
There are THREE main templates:
  1. Words      → dagbani_dictionary_template.csv
  2. Phrases    → dagbani_phrases_template.csv
  3. Idioms & Proverbs → dagbani_idioms_proverbs_template.csv

Optional: dagbani_adverbs_template.csv (merged into words if present)

=== WORDS (dagbani_dictionary_template.csv) ===
Matches the Add New Word form exactly:

dagbani       - Dagbani Word/Phrase (required) e.g. Antire
english       - English Translation (required) e.g. Hello
dialect       - Standard
category      - Nouns, Verbs, Adjectives, Adverbs, Numbers, Pronouns, Expressions, Food, Animals, Basics, General (app normalizes variants like noun, adj, etc.)
grammar       - Grammar Notes (optional) e.g. Noun class: 1, Plural: Antireba
example       - Example Sentence (optional) e.g. Antire, be ni tooi song ma?
allowComments - true or false. Allow others to discuss or ask questions
picture       - Image (optional) - Paste image URL here. Use "picture" to match JSON.
audio         - Audio (optional) - Paste audio URL if hosted. Use "audio" to match JSON.

HOW TO CONVERT CSV TO JSON (Command Prompt / CMD):

  Prerequisite: Node.js installed (https://nodejs.org)
  Open cmd: Win+R, type cmd, Enter

  --- Copy and paste these commands (edit the path if needed) ---

cd "C:\Users\YourName\OneDrive\Desktop\Dagban Kurli"
node csv_to_json.js

  --- End ---

  This reads all three CSV templates and creates dictionary_import.json
  (words + phrases + idioms/proverbs). All entries are preserved; no deduplication.

UPLOAD: Profile -> Preferences & Data -> Import Data (Restore) -> select dictionary_import.json

  NOTE: Large dictionaries (10,000+ words) may exceed browser storage (~5MB limit).

=== PHRASES (dagbani_phrases_template.csv) ===
dagbani   - Dagbani phrase (required)
english   - English translation (required)
usage     - When/where this phrase is used (optional)
category  - basics, eating, transportation, money, time, numbers, shopping, general (app normalizes legacy values)

=== IDIOMS & PROVERBS (dagbani_idioms_proverbs_template.csv) ===
dagbani   - Dagbani idiom or proverb (required)
english   - English meaning (required)
usage     - When this idiom or proverb is used (optional)
category  - proverb, idiom, general (distinct from phrase categories; app normalizes Proverb, Idioms, etc.)

To import: Run "node csv_to_json.js" to convert all templates to one JSON, then Profile -> Import Data (Restore). One JSON file includes words, phrases, and idioms/proverbs.

=== ADVERBS (dagbani_adverbs_template.csv) ===
Optional. If this file exists, csv_to_json.js merges its entries into words (only those not already in the dictionary template).
