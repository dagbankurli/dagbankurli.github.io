#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Best-effort Dagbani Dictionary Extractor
Source: Dagbani_Dictionary_24_Oct_2014.pdf (Tony Naden)

Uses PyMuPDF for layout-aware PDF extraction when available, then a robust
parser to extract: headword, definitions, grammar, examples, etymology.
Outputs app-ready JSON with maximum extracted data.

Usage:
    python extract_dagbani_dictionary.py              # Extract from PDF
    python extract_dagbani_dictionary.py --text       # Parse extracted_text.txt (faster)
    python extract_dagbani_dictionary.py --json [--limit N]   # Parse "Dagbani dictionary.json"
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

# Dagbani word chars
DAGBANI = r"[a-zɛɔŋɣʒɲʼʼəA-ZƐƆŊƔƷɲ\-]"
POS = r"n\.|v\.|adj\.|adv\.|excl\.|num\.|id\.|pron\.|cj\.|prep\.|ptc\.|disc\.|aux\.|n\.phr\.|n\.pr\.|n\.st\.|num\.sx|pl\.|pn\.|postpos\.|pred\.|px\.|qnt\.|rel\.|sg\.|st\.|sx\.|tmp\.|v\.n\."
INTRO_END = ["alibarika Variant:", "alibarika     Variant:", "a excl.", "a 1     pn.", "abada adv."]
DEF_STOP = r"\s(From:|Syn:|Sim:|Colloc:|Note:|See:|Cpart:|Gen:|Etym:|Lit:|InvNinst:|\s\[(?:MRK|GEN|EXO|PRO|PSA|LUK|MAT|JHN|ACT|ROM|DB|ISA|1KI|2KI|COL|JER|JAS|DEU|REV|NEH|DAN|EPH|ZEC|HAB|HEB|LEV|NAM)\s)"


def extract_from_pdf_layout(pdf_path: str) -> str:
    """Extract text using PyMuPDF with block/position info for better ordering."""
    if not HAS_PYMUPDF:
        raise ImportError("pip install pymupdf")
    doc = fitz.open(pdf_path)
    all_blocks = []
    for page in doc:
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    line_text = "".join(s["text"] for s in line["spans"])
                    if line_text.strip():
                        all_blocks.append(line_text)
    doc.close()
    return "\n".join(all_blocks)


def extract_from_pdf_simple(pdf_path: str) -> str:
    """Simple PDF text extraction."""
    if not HAS_PYMUPDF:
        raise ImportError("pip install pymupdf")
    doc = fitz.open(pdf_path)
    text = "\n".join(page.get_text() for page in doc)
    doc.close()
    return text


def preprocess_json_page_text(text: str) -> str:
    """
    Split page content from Dagbani dictionary.json into entry lines.
    In JSON format, entries run together; insert newlines before each new headword.
    """
    # Split only before headword+POS (not between "a 1" and "pn.").
    # Match: 3+ spaces before (Dagbani headword + optional " 1" + spaces + Variant/Pl/Forms/POS)
    # Use minimal alternation for speed
    pat = re.compile(
        r"\s{3,}(?=[a-zɛɔŋɣʒɲʼə][a-zɛɔŋɣʒɲʼə\-]*(?:\s+\d+)?\s+(?:Variant:|Pl:|Forms:|n\.|v\.|pn\.|adj\.|adv\.|excl\.))",
        re.I
    )
    return pat.sub("\n", text)


def parse_entries(text: str) -> list[dict]:
    """
    Parse dictionary text. Extracts headword, primary definition, grammar, example, etymology.
    Handles multi-line entries and multiple patterns.
    """
    lines = text.split("\n")
    entries = []
    seen = set()
    in_body = False
    headword_re = re.compile(r"^(" + DAGBANI + r"+)\s")

    for i, raw_line in enumerate(lines):
        line = raw_line.strip()
        if not line or len(line) < 3:
            continue

        # Skip cross-refs
        if line.startswith("See main entry:"):
            continue
        if re.match(r"^\d+\s*$", line):  # Page numbers
            continue

        # Start of dictionary
        if not in_body:
            for m in INTRO_END:
                if m in line:
                    in_body = True
                    break
            if not in_body:
                continue

        # ---- Entry pattern matching ----
        dagbani = None
        definition = None
        grammar_parts = []
        example = None
        etymology = None

        # Pattern: "headword n. definition" (simple)
        m = re.match(r"^(" + DAGBANI + r"+)\s+(?:" + POS + r")\s+(.+)$", line, re.I)
        if m:
            dagbani, def_raw = m.group(1).strip(), m.group(2)
            definition, grammar_parts, example, etymology = split_definition(def_raw)
            if not definition:
                continue

        # Pattern: "headword Pl: X. n. definition"
        if not dagbani:
            m = re.match(r"^(" + DAGBANI + r"+)\s+(?:Pl:\s*[^.]*\.\s*)(?:" + POS + r")\s+(.+)$", line, re.I)
            if m:
                dagbani, def_raw = m.group(1).strip(), m.group(2)
                definition, grammar_parts, example, etymology = split_definition(def_raw)
                if definition:
                    grammar_parts.insert(0, line[line.find("Pl:"):line.find(".", line.find("Pl:"))+1])

        # Pattern: "headword Variant: X. Forms: Y. n. definition"
        if not dagbani:
            m = re.match(
                r"^(" + DAGBANI + r"+)\s+(?:Variant:|Pl:|Forms:)[^.]*\.\s*(?:.*?\.\s*)*(?:" + POS + r")\s+(?:\d\s*•\s*(?:" + POS + r")\s+)?(.+)$",
                line, re.I
            )
            if m:
                dagbani, def_raw = m.group(1).strip(), m.group(2)
                definition, grammar_parts, example, etymology = split_definition(def_raw)
                if definition:
                    variant_match = re.search(r"Variant:\s*[^.;]+", line)
                    forms_match = re.search(r"Forms:+\s*[^.;]+", line)
                    if variant_match:
                        grammar_parts.insert(0, variant_match.group(0).rstrip(".;"))
                    if forms_match:
                        grammar_parts.append(forms_match.group(0).rstrip(".;"))

        # Pattern: "headword 1 n. 1 • prayer." (homophone)
        if not dagbani:
            m = re.match(
                r"^(" + DAGBANI + r"+)\s+\d\s+(?:Note:.*?\.\s*)?(?:" + POS + r")\s+(?:\d\s*•\s*(?:" + POS + r")\s+)?(.+)$",
                line, re.I
            )
            if m:
                dagbani, def_raw = m.group(1).strip(), m.group(2)
                definition, grammar_parts, example, etymology = split_definition(def_raw)

        # Pattern: "headword n. 1 • sense."
        if not dagbani:
            m = re.match(
                r"^(" + DAGBANI + r"+)\s+(?:" + POS + r")\s+\d\s*•\s*(?:" + POS + r")\s+(.+)$",
                line, re.I
            )
            if m:
                dagbani, def_raw = m.group(1).strip(), m.group(2)
                definition, grammar_parts, example, etymology = split_definition(def_raw)

        # Validate and add
        if dagbani and definition:
            key = (dagbani.lower(), definition[:80])
            if key not in seen and len(dagbani) < 60 and len(definition) < 500:
                seen.add(key)
                grammar_str = "; ".join(grammar_parts) if grammar_parts else None
                entries.append({
                    "dagbani": dagbani,
                    "english": definition,
                    "grammar": grammar_str,
                    "example": example,
                    "etymology": etymology,
                })

    return entries


def split_definition(raw: str) -> tuple:
    """Split definition into: main def, grammar parts, example, etymology."""
    definition = raw
    grammar_parts = []
    example = None
    etymology = None

    # Etymology (From:)
    from_m = re.search(r"\sFrom:\s*([^.]+(?:\.[^A-Z][^.]*)?)", raw)
    if from_m:
        etymology = from_m.group(1).strip()[:150]
        definition = raw[:from_m.start()].strip()

    # Stop definition at metadata
    for stop in [" Syn:", " Sim:", " Colloc:", " InvNinst:", " Cpart:", " Gen:", " Etym:", " Lit:", " See:"]:
        idx = definition.find(stop)
        if idx > 15:
            definition = definition[:idx].strip()

    # Bible/verse refs - truncate but try to keep example before
    verse = re.search(r"\s\[([A-Z0-9]+ \d+:\d+(?:\-\d+)?)\]", definition)
    if verse and verse.start() > 30:
        before = definition[:verse.start()]
        # Look for example: "Dagbani text. English trans. [REF]"
        last_period = before.rfind(". ")
        if last_period > 10:
            potential_ex = before[last_period+2:].strip()
            if len(potential_ex) < 120 and not potential_ex.startswith("Note"):
                example = potential_ex
        definition = before.strip()

    # Remove PDF artifacts
    definition = re.sub(r"\(cid:\d+\)", "", definition)
    definition = re.sub(r"\s+", " ", definition).strip()
    # Strip trailing punctuation
    definition = definition.rstrip(".,;")
    if len(definition) > 400:
        definition = definition[:400].rstrip(".,; ")

    return definition, grammar_parts, example, etymology


def to_app_format(entries: list[dict]) -> list[dict]:
    """Convert to Dagban Kurli app format (Dagbani leading)."""
    out = []
    for i, e in enumerate(entries, 1):
        row = {
            "id": i,
            "dagbani": e["dagbani"],
            "english": e["english"],
            "dialect": "standard",
            "category": "general",
            "grammar": e.get("grammar"),
            "example": e.get("example"),
            "verified": True,
            "dateAdded": datetime.now().isoformat(),
        }
        if e.get("etymology"):
            row["grammar"] = (row["grammar"] + " | " if row["grammar"] else "") + ("From: " + e["etymology"])
        out.append(row)
    return out


def main():
    script_dir = Path(__file__).parent
    pdf_path = script_dir / "Dagbani_Dictionary_24_Oct_2014.pdf"
    text_path = script_dir / "extracted_text.txt"
    dagbani_json_path = script_dir / "Dagbani dictionary.json"
    output_path = script_dir / "dagbani_dictionary_from_pdf.json"

    print("=" * 60)
    print("Dagbani Dictionary Extractor")
    print("=" * 60)

    if "--json" in sys.argv:
        if not dagbani_json_path.exists():
            print(f"Error: {dagbani_json_path} not found.")
            return
        limit = None
        for i, a in enumerate(sys.argv):
            if a == "--limit" and i + 1 < len(sys.argv):
                try:
                    limit = int(sys.argv[i + 1])
                except ValueError:
                    pass
                break
        print(f"\n[1] Reading: {dagbani_json_path}")
        with open(dagbani_json_path, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            if limit:
                data = data[:limit]
                print(f"    (limit: first {limit} pages)")
            chunks = [preprocess_json_page_text(item.get("content", "")) for item in data if isinstance(item, dict)]
            text = "\n".join(chunks)
            print(f"    {len(data)} pages, {len(text):,} chars (preprocessed for entry splitting)")
        else:
            text = preprocess_json_page_text(data.get("content", str(data)))
            print(f"    {len(text):,} chars")
    elif "--text" in sys.argv or "--from-text" in sys.argv:
        if not text_path.exists():
            print(f"Error: {text_path} not found. Run without --text to extract from PDF first.")
            return
        print(f"\n[1] Reading: {text_path}")
        with open(text_path, encoding="utf-8") as f:
            text = f.read()
        print(f"    {len(text):,} chars")
    elif pdf_path.exists() and HAS_PYMUPDF:
        print(f"\n[1] Extracting from PDF: {pdf_path}")
        try:
            text = extract_from_pdf_layout(str(pdf_path))
        except Exception:
            text = extract_from_pdf_simple(str(pdf_path))
        print(f"    {len(text):,} chars")
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"    Saved to {text_path}")
    else:
        if not pdf_path.exists():
            print(f"Error: PDF not found: {pdf_path}")
        else:
            print("Error: pip install pymupdf")
        return

    print("\n[2] Parsing entries...")
    entries = parse_entries(text)
    print(f"    Found {len(entries):,} entries")

    if not entries:
        print("No entries parsed. Check format.")
        return

    words = to_app_format(entries)
    output_data = {
        "words": words,
        "source": "Dagbani_Dictionary_24_Oct_2014.pdf (Tony Naden)",
        "exportDate": datetime.now().isoformat(),
        "totalEntries": len(words),
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"\n[SUCCESS] {output_path}")
    print(f"    Total: {len(words):,} entries")
    print("\nSample:")
    for w in words[:6]:
        d = w["dagbani"]
        e = (w["english"][:45] + "...") if len(w["english"]) > 45 else w["english"]
        print(f"    {d} -> {e}")
    print("\nImport: Settings > Import Data > Select the JSON file")


if __name__ == "__main__":
    main()
