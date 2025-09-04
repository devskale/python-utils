import argparse
import json
import os
from typing import Any, Dict, List, Optional

try:
    # Optional enrichment of name/description
    from ofs.api import get_kriterium_description  # type: ignore
except Exception:  # pragma: no cover
    get_kriterium_description = None  # type: ignore


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_kriterium_meta(project: str, kriterium_id: str) -> Dict[str, str]:
    """Return {name, beschreibung} using ofs.api when available; fall back to N/A."""
    name = "N/A"
    beschreibung = ""
    if get_kriterium_description is not None:
        try:
            k = get_kriterium_description(project, kriterium_id)  # type: ignore[misc]
            name = k.get("name") or k.get("raw", {}).get("name") or "N/A"
            beschreibung = (
                k.get("beschreibung")
                or k.get("anforderung")
                or k.get("raw", {}).get("anforderung")
                or ""
            )
        except Exception:
            pass
    return {"name": name, "beschreibung": beschreibung}


def to_markdown(data: Dict[str, Any]) -> str:
    project = data.get("project", "")
    results: List[Dict[str, Any]] = data.get("results", [])
    total = len(results)

    lines: List[str] = []
    header = f"# Bewertungsergebnisse für {project} – {data.get('bidder','')}\n"
    lines.append(header)
    lines.append("")

    for idx, item in enumerate(results, start=1):
        kid = item.get("id", "")
        doc_names = item.get("doc_names", []) or []
        assessment = item.get("assessment", {}) or {}
        status = assessment.get("erfüllt", "")
        begruendung = assessment.get("begründung", "")

        meta = get_kriterium_meta(project, kid)
        name = meta.get("name", "N/A")
        beschreibung = meta.get("beschreibung", "")

        # Top-level bullet for the item
        lines.append(f"- {idx}/{total}: {kid}, {name}")
        # Indented details (no bullets as per example)
        if beschreibung:
            lines.append(f"   Kriteriumbeschreibung: {beschreibung}")
        else:
            lines.append(f"   Kriteriumbeschreibung: N/A")

        if doc_names:
            lines.append(f"   Kontext Dokumente: {', '.join(doc_names)}")
        else:
            lines.append("   Kontext Dokumente: –")

        lines.append(f"   Erfüllt: {status if status else 'N/A'}")
        lines.append(f"   Begründung: {begruendung if begruendung else 'N/A'}")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Konvertiere Assessments-JSON in Markdown")
    parser.add_argument("json_file", help="Pfad zur assessments.json")
    parser.add_argument("--out", help="Pfad zur Ausgabedatei (.md). Wenn nicht gesetzt, Ausgabe auf stdout.")
    args = parser.parse_args()

    data = load_json(args.json_file)
    md = to_markdown(data)

    if args.out:
        out_dir = os.path.dirname(args.out)
        if out_dir and not os.path.isdir(out_dir):
            os.makedirs(out_dir, exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"Markdown gespeichert: {args.out}")
    else:
        print(md)


if __name__ == "__main__":
    main()
