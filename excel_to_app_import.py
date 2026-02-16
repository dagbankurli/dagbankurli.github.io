#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Convert Excel dictionary to Dagbani Korli app import format.

Excel columns (first row = header):
  dagbani | english | word_class | etymology | example | voice | picture

Usage:
  python excel_to_app_import.py your_dictionary.xlsx
  python excel_to_app_import.py your_dictionary.xlsx -o output.json

Output: dagbani_import.json (or -o path)
Import via: Settings > Import Data in the app.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

try:
    import openpyxl
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


def excel_to_json(excel_path: Path, output_path: Path | None = None, media_dir: Path | None = None) -> Path:
    """Read Excel and output app-ready JSON."""
    excel_path = Path(excel_path)
    if not excel_path.exists():
        raise FileNotFoundError(f"File not found: {excel_path}")

    if output_path is None:
        output_path = excel_path.parent / "dagbani_import.json"
    output_path = Path(output_path)

    if str(excel_path).lower().endswith(".csv"):
        import csv
        for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
            try:
                with open(excel_path, encoding=enc) as f:
                    r = csv.DictReader(f)
                    rows = list(r)
                break
            except UnicodeDecodeError:
                continue
        else:
            raise ValueError("Could not read CSV. Save as 'CSV UTF-8' in Excel.")
        headers = list(rows[0].keys()) if rows else []
    elif HAS_PANDAS:
        df = pd.read_excel(excel_path, dtype=str)
        rows = [row.to_dict() for _, row in df.iterrows()]
        headers = list(df.columns)
    elif HAS_OPENPYXL:
        wb = openpyxl.load_workbook(excel_path, read_only=True, data_only=True)
        ws = wb.active
        rows_raw = list(ws.iter_rows(values_only=True))
        wb.close()
        if not rows_raw:
            raise ValueError("Excel file is empty")
        headers = [str(h).strip() if h else "" for h in rows_raw[0]]
        rows = [dict(zip(headers, [str(v).strip() if v is not None else "" for v in r])) for r in rows_raw[1:]]
    else:
        raise ImportError("Install: pip install openpyxl  (or pandas for xlsx)")

    def _get(row, *keys):
        for k in keys:
            v = row.get(k, row.get(k.replace("_", " "), ""))
            if v is not None:
                return str(v).strip()
        return ""

    words = []
    for i, row in enumerate(rows):
        dagbani = _get(row, "dagbani", "Dagbani")
        english = _get(row, "english", "English")
        if not dagbani or not english:
            continue

        word_class = _get(row, "word_class", "Word class", "grammar", "Grammar")
        etymology = _get(row, "etymology", "Etymology")
        example = _get(row, "example", "Example")
        voice = _get(row, "voice", "Voice", "audio", "Audio")
        picture = _get(row, "picture", "Picture", "image", "Image")

        grammar = word_class
        if etymology:
            grammar = f"{grammar}. From: {etymology}" if grammar else f"From: {etymology}"

        audio_url = None
        if voice and media_dir:
            audio_file = media_dir / voice
            if audio_file.exists():
                try:
                    import base64
                    with open(audio_file, "rb") as f:
                        b64 = base64.b64encode(f.read()).decode()
                    mime = "audio/mpeg" if voice.lower().endswith(".mp3") else "audio/webm"
                    audio_url = f"data:{mime};base64,{b64}"
                except Exception:
                    pass

        picture_url = None
        if picture:
            if picture.startswith(("http://", "https://")):
                picture_url = picture
            elif media_dir:
                pic_file = media_dir / picture
                if pic_file.exists():
                    try:
                        import base64
                        with open(pic_file, "rb") as f:
                            b64 = base64.b64encode(f.read()).decode()
                        mime = "image/jpeg" if picture.lower().endswith(".jpg") else "image/png"
                        picture_url = f"data:{mime};base64,{b64}"
                    except Exception:
                        pass

        words.append({
            "id": f"excel-{i + 1}",
            "dagbani": dagbani,
            "english": english,
            "dialect": "standard",
            "category": "general",
            "grammar": grammar or None,
            "example": example or None,
            "etymology": etymology or None,
            "audio": audio_url,
            "picture": picture_url,
            "verified": True,
            "dateAdded": datetime.now().isoformat(),
        })

    data = {"words": words, "source": excel_path.name, "totalEntries": len(words)}
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return output_path


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        print("\nExample: python excel_to_app_import.py my_dictionary.xlsx")
        return
    excel_path = Path(args[0])
    output_path = None
    media_dir = excel_path.parent
    i = 1
    while i < len(args):
        if args[i] == "-o" and i + 1 < len(args):
            output_path = Path(args[i + 1])
            i += 2
        elif args[i] == "--media" and i + 1 < len(args):
            media_dir = Path(args[i + 1])
            i += 2
        else:
            i += 1
    out = excel_to_json(excel_path, output_path, media_dir)
    print(f"Converted {excel_path.name} -> {out}")
    print("Import: Settings > Import Data > Select the JSON file")
    if str(excel_path).lower().endswith(".csv"):
        print("\nTip: If ŋ, ɛ, ɔ are lost, in Excel use Save As > 'CSV UTF-8 (Comma delimited)'")


if __name__ == "__main__":
    main()
