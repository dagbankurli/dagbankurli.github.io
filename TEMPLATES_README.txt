Dagban Kurli - Excel/CSV templates for bulk entry

The app loads its dictionary data from dictionary_import.json (not dictionary_data.json).
These CSV files open in Excel. Use them to add words, phrases, and idioms.
Match the column headers exactly when adding rows.

=== WORDS (dagbani_dictionary_template.csv) ===
Matches the Add New Word form exactly:

dagbani       - Dagbani Word/Phrase (required) e.g. Antire
english       - English Translation (required) e.g. Hello
dialect       - Standard
category      - General, Greetings, Food, Family, Nature, Verbs, Adjectives, Nouns, Provision, Idioms, Phrases, Animals, Names, Plants, Other
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

  This creates dictionary_import.json with words, phrases, and idioms from all three CSVs.

  Optional - convert only one type:
    node csv_to_json.js words
    node csv_to_json.js phrases
    node csv_to_json.js idioms

  Output: dictionary_import.json (or dictionary_import_words.json etc. for single-type)

UPLOAD: Profile -> Preferences & Data -> Import Data (Restore) -> select dictionary_import.json
(Same place for words, phrases, and idioms - one JSON can contain all three.)

=== PHRASES (dagbani_phrases_template.csv) ===
dagbani   - Dagbani phrase (required)
english   - English translation (required)
usage     - When/where this phrase is used (optional)
category  - basics, common_signs, problems, numbers, time, clock_time, duration, days, months, transportation, money, eating, etc.

=== IDIOMS & PROVERBS (dagbani_idioms_proverbs_template.csv) ===
dagbani   - Dagbani idiom or proverb (required)
english   - English meaning (required)
usage     - When this idiom or proverb is used (optional)
category  - general, basics, common_signs, problems, eating, money, authority, provision, idioms, proverbs, etc.

To import: Convert all CSVs to JSON with "node csv_to_json.js", then Profile -> Import Data (Restore). One JSON file can include words, phrases, and idioms.
