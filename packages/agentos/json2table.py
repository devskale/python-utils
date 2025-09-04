#!/usr/bin/env python3
"""
json2table.py

Reads a matcha.<project>.<bidder>.json file and generates a Markdown table
saved as matcha.<project>.<bidder>.md in the same directory.

Usage:
  python json2table.py path/to/matcha.<project>.<bidder>.json
  # Optional flags:
  #   --out path/to/output.md
  #   --max-reason-len 160  # truncate the Begründung column
"""
from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict, List, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert matcha JSON to Markdown table")
    parser.add_argument("json_path", help="Path to matcha.<project>.<bidder>.json")
    parser.add_argument("--out", dest="out_path", default=None, help="Output Markdown file path")
    parser.add_argument(
        "--max-reason-len",
        type=int,
        default=160,
        help="Truncate Begründung to this many characters (0 to disable)",
    )
    return parser.parse_args()


def derive_names_from_filename(json_path: str) -> Tuple[str, str, str]:
    """Return (dir, project, bidder) derived from matcha.<project>.<bidder>.json.
    If not derivable, returns basename without extension as project and empty bidder.
    """
    directory = os.path.dirname(os.path.abspath(json_path))
    base = os.path.basename(json_path)
    name, ext = os.path.splitext(base)
    project = name
    bidder = ""

    # Expect prefix 'matcha.' and two parts: project and bidder
    if name.startswith("matcha."):
        rest = name[len("matcha."):]
        parts = rest.split(".")
        if len(parts) >= 2:
            bidder = parts[-1]
            project = ".".join(parts[:-1])
        else:
            project = rest
    return directory, project, bidder


def load_json(json_path: str) -> List[Dict[str, Any]]:
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def md_escape(text: str) -> str:
    """Basic markdown escaping for pipes and backticks in table cells.

    Also replace newlines with <br> to keep table rows intact.
    """
    if not isinstance(text, str):
        text = str(text)
    return (
        text.replace("|", "\\|")
        .replace("`", "\\`")
        .replace("\n", "<br>")
    )


def truncate(text: str, max_len: int) -> str:
    if max_len and max_len > 0 and len(text) > max_len:
        return text[: max_len - 1] + "…"
    return text


def build_table(data: List[Dict[str, Any]], max_reason_len: int) -> str:
    """Build a markdown table from matcha data.

    Columns:
    - Nr (1..N by required doc)
    - Beilage (gefordertes_doc.beilage_nummer)
    - Gefordertes Dokument (bezeichnung)
    - Kategorie (gefordertes_doc.kategorie)
    - Match-Dateiname
    - Match-Name
    - Match-Kategorie
    - Begründung
    """
    headers = [
        "Nr",
        "Beilage",
        "Gefordertes Dokument",
        "Kategorie",
        "Match-Dateiname",
        "Match-Name",
        "Match-Kategorie",
        "Begründung",
    ]
    md_lines = ["| " + " | ".join(headers) + " |",
                "| " + " | ".join(["---"] * len(headers)) + " |"]

    for idx, item in enumerate(data, start=1):
        req = item.get("gefordertes_doc", {}) or {}
        beilage = req.get("beilage_nummer")
        bezeichnung = req.get("bezeichnung")
        kategorie = req.get("kategorie")
        matches = item.get("matches") or []
        # Ensure list for uniform processing
        if not isinstance(matches, list):
            matches = [matches]

        if not matches:
            row = [
                str(idx),
                md_escape(beilage) if beilage is not None else "—",
                md_escape(bezeichnung) if bezeichnung is not None else "—",
                md_escape(kategorie) if kategorie is not None else "—",
                "—",
                "—",
                "—",
                "—",
            ]
            md_lines.append("| " + " | ".join(row) + " |")
            continue

        # One row per match; blank out repeated req fields for subsequent rows
        for m_i, m in enumerate(matches):
            if not isinstance(m, dict):
                m = {"Dateiname": str(m)}
            dateiname = m.get("Dateiname")
            m_name = m.get("Name")
            m_kat = m.get("Kategorie")
            begr = m.get("Begründung")
            begr_s = md_escape(truncate(begr, max_reason_len)) if begr else "—"

            row = [
                str(idx) if m_i == 0 else "",
                md_escape(beilage) if (m_i == 0 and beilage is not None) else ("" if m_i > 0 else "—"),
                md_escape(bezeichnung) if (m_i == 0 and bezeichnung is not None) else ("" if m_i > 0 else "—"),
                md_escape(kategorie) if (m_i == 0 and kategorie is not None) else ("" if m_i > 0 else "—"),
                md_escape(dateiname) if dateiname else "—",
                md_escape(m_name) if m_name else "—",
                md_escape(m_kat) if m_kat else "—",
                begr_s,
            ]
            md_lines.append("| " + " | ".join(row) + " |")

    return "\n".join(md_lines)


def main() -> None:
    args = parse_args()
    directory, project, bidder = derive_names_from_filename(args.json_path)

    data = load_json(args.json_path)

    # Heading: "Projektname Bietername"
    heading = f"# {project} {bidder}".strip()

    table_md = build_table(data, max_reason_len=args.max_reason_len)

    # Output path
    if args.out_path:
        out_path = args.out_path
    else:
        # Default same folder with .md extension
        out_base = f"matcha.{project}.{bidder}.md" if bidder else f"{project}.md"
        out_path = os.path.join(directory, out_base)

    # Write file
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(heading + "\n\n")
        # Optional: add a short list summary
        # f.write(f"- Einträge: {len(data)}\n\n")
        f.write(table_md)

    print(f"Saved Markdown table to: {out_path}")


if __name__ == "__main__":
    main()
