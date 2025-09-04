import argparse
import json
import os
import re
import sys
from typing import List, Dict, Any

import credgoo
from credgoo import get_api_key
import ofs.api
from ofs.api import list_bidder_docs_json, get_bieterdokumente_list, list_bidders  # type: ignore
# Agno framework pieces (used to construct the minimal workflow)
from agno.agent import Agent
from agno.models.vllm import vLLM
# from agno.tools import tool
# from agno.workflow.v2.workflow import Workflow

# Optional JSON repair for messy LLM outputs
try:
    from json_repair import repair_json  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    repair_json = None  # type: ignore

 # ---------------- Environment / Model selection -----------------
PROVIDER = "tu"
BASE_URL = "https://aqueduct.ai.datalab.tuwien.ac.at/v1"
# MODEL = "deepseek-r1"

MODELS = {
    "mistral-large": "mistral-large-123b",
    "mistral-small": "mistral-small-3.1-24b",
    "deepseek-r1": "deepseek-r1",
    "qwen-large": "qwen-32b"
}

MODEL = MODELS["deepseek-r1"]

api_key = get_api_key(PROVIDER)


def condense_bieterdocs(bidder_docs):
    """Return a simple view of bidder docs focusing on meta.name and meta.kategorie.

    Accepts either:
      - a dict with a "files" (or "docs"/"items") list
      - or a plain list of file dicts

    Produces a list of entries with: filename, name (meta.name or name), kategorie (meta.kategorie).
    """
    # Normalize to a list of file entries
    items = []
    if isinstance(bidder_docs, dict):
        for key in ("files", "docs", "items", "results", "documents"):
            if key in bidder_docs and isinstance(bidder_docs[key], list):
                items = bidder_docs[key]
                break
    elif isinstance(bidder_docs, list):
        items = bidder_docs

    out = []
    for doc in items:
        if isinstance(doc, str):
            out.append({
                "filename": doc,
                "name": doc,
                "kategorie": None,
            })
            continue
        if not isinstance(doc, dict):
            continue
        meta = doc.get("meta") or {}
        filename = doc.get("name") or doc.get("filename") or ""
        name = meta.get("name") or filename or doc.get("title")
        kategorie = meta.get("kategorie")
        out.append({
            "name": name,
            "kategorie": kategorie,
            "filename": filename,
        })
    return out


def condense_geforderte_doks(required_docs):
    """Return only bezeichnung, beilage_nummer (if present), and kategorie.

    Input is expected to be a list of dicts as returned by get_bieterdokumente_list.
    """
    out = []
    if not isinstance(required_docs, list):
        return out
    for d in required_docs:
        if not isinstance(d, dict):
            continue
        out.append({
            "bezeichnung": d.get("bezeichnung"),
            "beilage_nummer": d.get("beilage_nummer"),
            "kategorie": d.get("kategorie"),
        })
    return out


def findMatches(geforderte_dokumente, hochgeladene_docs, runner=1):
    prompt = f"""
Du bist ein hilfreicher Assistent, der dabei hilft, geforderte Dokumente mit hochgeladenen Dokumenten abzugleichen.
Deine Aufgabe ist es, das am besten passende hochgeladene Dokument für jedes geforderte Dokument zu finden.
Du erhältst eine Liste von geforderten Dokumenten mit ihren Bezeichnungen.

Sofern nicht anders angegeben gilt standardmäßig: 
- das ausschreibende Unternehmen ist die "Wiener Wohnen Hausbetreuung Gmbh", ein Unternehmen aus Österreich.
- Der teilnehmende Bieter ist ein Unternehmen aus Österreich. Daher sind nur Dokumente für österreichische Unternehmen relevant.
- Der Bieter bietet für alle Lose an.
- Der Bieter ist der Hauptauftragnehmer.
- Die hochgeladenen Dokumente sind von einem Bieter, der an der Ausschreibung teilnimmt.
- Der Bieter ist ein Einzalbieter, es gibt keine Bieter- oder Arbeitsgemeinschaft. Daher sind keine Dokumente für BIEGE oder ARGE notwendig.
- Es gibt keine Subunternehmer. Daher sind Dokumente für Subunternehmer nicht notwendig.
- Die hochgeladenen Dokumente sind in deutscher Sprache verfasst.

Das geforderte Dokument ist:
{json.dumps(geforderte_dokumente, indent=2, ensure_ascii=False)}

Die liste mit den hochgeladenen Bieterdokumenten ist:
{json.dumps(hochgeladene_docs, indent=2, ensure_ascii=False)}

gib eine liste der am besten passenden hochgeladenen Dokumente zurück, die zu dem geforderten Dokument passen. Falls Dokumente nicht notwendig sind (zB ARGE oder Subunternehmer, ausländische Bieter, etc).
Der Bieter kann anstatt der Formblätter auch Listen oder Formulare in (zB Referenzlisten) in eigenem Format abgeben, bitte identifiziere diese ebenso und weise sie zu, wenn Sie zum geforderten Dokument passen.
Führe keine inhaltliche Bewertung durch. Erkenne nur ob das Dokument für als gefordertes Dokument relevant ist.
"matches": [
    {{
     "Dateiname": "...",    # der Dateiname des hochgeladenen Dokuments oder NONE
     "Name": "...",         # der Name aus meta.name des hochgeladenen Dokuments
     "Kategorie": "...",    # die Kategorie aus meta.kategorie des hochgeladenen Dokuments
     "Begründung": "..."}},  # die Begründung für die Zuordnung
]

"""
    return prompt


def extract_json_clean(text: str):
    """Try to extract/parse JSON from a possibly noisy LLM response.

    Strategy:
    - Try direct json.loads
    - Try fenced code blocks ```json ... ``` or ``` ... ```
    - Try extracting just the matches array
    - Try using json_repair.repair_json when available
    Returns a Python object (dict or list) or None.
    """
    if not text:
        return None
    # 1) Direct parse
    try:
        return json.loads(text)
    except Exception:
        pass

    # 2) Look for fenced json blocks
    for pattern in [r"```json\s*(.*?)```", r"```\s*(.*?)```"]:
        m = re.search(pattern, text, flags=re.DOTALL | re.IGNORECASE)
        if m:
            block = m.group(1).strip()
            try:
                return json.loads(block)
            except Exception:
                # Attempt repair on the block if available
                if repair_json:
                    try:
                        fixed = repair_json(block)
                        return json.loads(fixed)
                    except Exception:
                        pass
                continue

    # 3) Extract just the matches array and wrap it
    m2 = re.search(r'"matches"\s*:\s*(\[.*?\])', text, flags=re.DOTALL)
    if m2:
        arr_text = m2.group(1)
        try:
            matches = json.loads(arr_text)
            return {"matches": matches}
        except Exception:
            # Attempt repair on the array if available
            if repair_json:
                try:
                    fixed_arr = repair_json(arr_text)
                    matches = json.loads(fixed_arr)
                    return {"matches": matches}
                except Exception:
                    pass
            pass

    # 4) Last resort: try to repair the entire text
    if repair_json:
        try:
            fixed_all = repair_json(text)
            return json.loads(fixed_all)
        except Exception:
            pass

    return None


def view_matcha_results(filename):
    """Display matcha results in a readable format.

    Args:
        filename (str): Path to the matcha JSON file
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading file {filename}: {e}")
        return

    # Handle both old format (list) and new format (dict with metadata)
    if isinstance(data, list):
        # Old format - just the matched documents list
        matched_documents = data
        metadata = None
        print("Note: Using legacy format without metadata")
    elif isinstance(data, dict) and 'matched_documents' in data:
        # New format - with metadata
        matched_documents = data['matched_documents']
        metadata = data.get('metadata', {})
    else:
        print("Invalid file format: expected a list or dict with matched_documents")
        return

    # Separate matched and unmatched required docs
    matched_docs = []
    unmatched_docs = []
    all_matched_bidder_docs = set()

    for item in matched_documents:
        if not isinstance(item, dict) or 'gefordertes_doc' not in item:
            continue

        gefordertes_doc = item['gefordertes_doc']
        matches = gefordertes_doc.get('matches', [])

        # Check if this required doc has valid matches
        has_valid_matches = False
        if isinstance(matches, list):
            for match in matches:
                if isinstance(match, dict):
                    dateiname = match.get('Dateiname', '')
                    if dateiname and dateiname.upper() != 'NONE':
                        has_valid_matches = True
                        all_matched_bidder_docs.add(dateiname)

        if has_valid_matches:
            matched_docs.append(item)
        else:
            unmatched_docs.append(item)

    # Print results
    print(f"\n=== MATCHA RESULTS: {filename} ===")
    if metadata:
        print(
            f"Project: {metadata.get('ausschreibung', 'N/A')}, Bidder: {metadata.get('bieter', 'N/A')}")
    print(f"Total required documents: {len(matched_documents)}")

    # Show matched documents first
    if matched_docs:
        print(
            f"\n📋 MATCHED REQUIRED DOCUMENTS {len(matched_docs)}/{len(matched_documents)}:")
        print("=" * 50)
        for item in matched_docs:
            gefordertes_doc = item['gefordertes_doc']
            matches = gefordertes_doc.get('matches', [])

            print(f"\n🔹 {gefordertes_doc.get('bezeichnung', 'Unknown')}")
            print(f"   Category: {gefordertes_doc.get('kategorie', 'N/A')}")

            if isinstance(matches, list):
                for match in matches:
                    if isinstance(match, dict):
                        dateiname = match.get('Dateiname', '')
                        if dateiname and dateiname.upper() != 'NONE':
                            name = match.get('Name', 'N/A')
                            kategorie = match.get('Kategorie', 'N/A')
                            print(f"   ✅ {dateiname}")
                            print(f"      Name: {name}")
                            print(f"      Category: {kategorie}")

    # Show unmatched required documents
    if unmatched_docs:
        print(
            f"\n❌ UNMATCHED REQUIRED DOCUMENTS {len(unmatched_docs)}/{len(matched_documents)}:")
        print("=" * 50)
        for i, item in enumerate(unmatched_docs, 1):
            gefordertes_doc = item['gefordertes_doc']
            print(f"{i}. {gefordertes_doc.get('bezeichnung', 'Unknown')}")

    # Calculate bidder document counts
    total_bidder_docs = len(all_matched_bidder_docs)
    unmatched_bidder_count = 0

    if metadata and 'ausschreibung' in metadata and 'bieter' in metadata:
        try:
            # Retrieve bidder documents live using ofs command
            project = metadata['ausschreibung']
            bidder = metadata['bieter']
            hochgeladene_docs = list_bidder_docs_json(
                project, bidder, include_metadata=True)

            # Get all uploaded bidder documents
            all_bidder_docs = set()
            if isinstance(hochgeladene_docs, dict) and 'documents' in hochgeladene_docs:
                for doc in hochgeladene_docs['documents']:
                    if isinstance(doc, dict) and 'name' in doc:
                        all_bidder_docs.add(doc['name'])

            # Find unmatched bidder documents
            unmatched_bidder_docs = all_bidder_docs - all_matched_bidder_docs
            unmatched_bidder_count = len(unmatched_bidder_docs)
            total_bidder_docs = len(all_bidder_docs)

        except Exception as e:
            unmatched_bidder_docs = set()

    # Show matched bidder documents summary
    print(
        f"\n📄 MATCHED BIDDER DOCUMENTS SUMMARY {len(all_matched_bidder_docs)}/{total_bidder_docs}:")
    print("=" * 50)
    for i, doc in enumerate(sorted(all_matched_bidder_docs), 1):
        print(f"{i}. {doc}")

    # Show unmatched bidder documents section
    print(
        f"\n📄 UNMATCHED BIDDER DOCUMENTS {unmatched_bidder_count}/{total_bidder_docs}:")
    print("=" * 50)

    if metadata and 'ausschreibung' in metadata and 'bieter' in metadata:
        try:
            if unmatched_bidder_docs:
                for i, doc in enumerate(sorted(unmatched_bidder_docs), 1):
                    print(f"{i}. {doc}")
            else:
                print(
                    "(All uploaded bidder documents were matched to required documents)")

        except Exception as e:
            print(f"(Error retrieving bidder documents: {e})")
    else:
        print("(Note: This section requires metadata with project and bidder information)")

    print("\n" + "=" * 60)


def process_bidder(agent, project: str, bidder: str, limit: int):
    """Process a single bidder for a project and generate matcha results.

    Args:
        agent: The AI agent for processing
        project: Project name
        bidder: Bidder name
        limit: Number of required docs to process
    """
    print(f"\n=== Processing {project}@{bidder} ===")

    try:
        hochgeladene_dokumente = list_bidder_docs_json(
            project, bidder, include_metadata=True)
    except Exception as e:
        print(f"Error loading bidder documents for {bidder}: {e}")
        return

    geforderte_dokumente = get_bieterdokumente_list(project)
    print(f"Geforderte Bieterdokumente: {len(geforderte_dokumente)}")
    print(
        f"Hochgeladene Bieterdokumente: {len(hochgeladene_dokumente['documents'])}")

    # Build a matched list for the first N required docs
    limit = max(0, int(limit))
    matched_list = []

    # Add metadata to track project and bidder for unmatched document analysis
    metadata = {
        "ausschreibung": project,
        "bieter": bidder
    }

    # loop through geforderte_dokumente and print index and bezeichnung
    for i, gefordertes_doc in enumerate(geforderte_dokumente, start=1):
        if limit and i > limit:
            break

        # Print document info with inline progress indicator
        print(
            f"{i}/{len(geforderte_dokumente)} - {gefordertes_doc.get('bezeichnung')}", end="")
        print("    [...", end="", flush=True)

        # ask llm if bieterdoc matches a gefordertes_doc
        mPrompt = findMatches(
            gefordertes_doc, hochgeladene_dokumente, i)

        response = agent.run(
            mPrompt,
            stream=False,  # capture final text only
            markdown=False,
            show_message=False
        )

        # Parse the response into JSON (clean) and attach to current required doc
        content = getattr(response, "content", response)
        result = extract_json_clean(
            content if isinstance(content, str) else str(content))
        matches = None
        if isinstance(result, dict) and "matches" in result:
            matches = result["matches"]
        elif isinstance(result, list):
            matches = result
        else:
            print(" | ERROR]")  # Close the progress indicator on error
            print("Warning: Could not extract matches JSON cleanly; storing raw content.")
            matches = content
            continue

        # Count valid matches (not None, not empty string, not "NONE")
        match_count = 0
        if isinstance(matches, list):
            for match in matches:
                if isinstance(match, dict):
                    dateiname = match.get("Dateiname", "")
                    if dateiname and dateiname.upper() != "NONE":
                        match_count += 1

        # Complete the progress indicator with match count
        print(f" | {match_count}]")

        # Add matches to the current required doc and to the aggregate list
        gefordertes_doc["matches"] = matches
        matched_list.append({
            "gefordertes_doc": gefordertes_doc,
        })

    # Print the aggregated matched list for the processed items
    print("\nMatched list (first {} items):".format(limit or len(matched_list)))
    print(json.dumps(matched_list, indent=2, ensure_ascii=False))

    # Save matched list to file with metadata
    out_file = f"matcha.{project}.{bidder}.json"
    output_data = {
        "metadata": metadata,
        "matched_documents": matched_list
    }
    try:
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"Saved matched list to {out_file}")
    except Exception as e:
        print(f"Error saving matched list to {out_file}: {e}")


def main():
    """Minimal utility:

    - Accepts one positional argument in the form project@bidder or just project
    - For project@bidder: processes single bidder
    - For project only: processes all bidders in the project
    - Or views existing matcha results with --view
    """
    parser = argparse.ArgumentParser(
        description="List bidder docs JSON for project[@bidder] or view matcha results")
    parser.add_argument("identifier", nargs='?',
                        help="project[@bidder] (not needed with --view)")
    parser.add_argument("--limit", type=int, default=100,
                        help="Number of required docs to process (default: 100)")
    parser.add_argument("--view", type=str, metavar="FILENAME",
                        help="View matcha results from JSON file")
    args = parser.parse_args()

    # Handle view mode
    if args.view:
        view_matcha_results(args.view)
        return

    # Validate identifier for normal mode
    if not args.identifier:
        print(
            "Error: identifier (project[@bidder]) is required when not using --view")
        parser.print_help()
        sys.exit(2)

    agent = Agent(
        model=vLLM(
            base_url=BASE_URL,
            api_key=api_key,
            id=MODEL,
            max_retries=3,
            # stream=True,
        ),
        tools=[],
    )

    identifier = args.identifier

    # Check if identifier contains @ (project@bidder) or is just project
    if "@" in identifier:
        # Single bidder mode
        project, bidder = identifier.split("@", 1)
        process_bidder(agent, project, bidder, args.limit)
    else:
        # All bidders mode
        project = identifier
        try:
            bidders = list_bidders(project)
            if not bidders:
                print(f"No bidders found for project '{project}'")
                sys.exit(1)

            print(
                f"Found {len(bidders)} bidders for project '{project}': {', '.join(bidders)}")

            for bidder in bidders:
                process_bidder(agent, project, bidder, args.limit)

        except Exception as e:
            print(f"Error processing project '{project}': {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()


''' HOCHGELADENE DOKUMENTE JSON BEISPIEL
{
  "project": "Entrümpelung",
  "bidder": "Musterfirma",
  "documents": [
    {
      "name": "AN Entrümpel pp d12.pdf",
      "path": ".dir/Entrümpelung/B/Musterfirma/AN Entrümpel pp d12.pdf",
      "size": 168821,
      "type": ".pdf",
      "parsers": {
        "det": [
          "marker",
          "md",
          "ocr",
          "docling",
          "easyocr",
          "llamaparse",
          "pdfplumber"
        ],
        "default": "docling",
        "status": ""
      },
      "meta": {
        "name": "Umsatzzahlen_Bieter",
        "kategorie": "Nachweis Leistungsfähigkeit",
        "begründung": "Enthält explizit Umsatzzahlen pro Projekt oder Auftrag, was typisch für Nachweis Leistungsfähigkeit ist."
      }
    },
    '''

''' GEFORDERTE DOKUMENTE BEISPIEL
[
  {
    "kategorie": "Pflichtdokument",
    "bezeichnung": "Angebotshauptteil der Vergabeplattform",
    "beilage_nummer": null,
    "beschreibung": "Ausgefüllter und signierter Hauptteil des Angebots über die elektronische Vergabeplattform, in welchem der Gesamtpreis einzutragen ist.",
    "unterzeichnung_erforderlich": true,
    "fachliche_pruefung": false
  },
  {
    "kategorie": "Bedarfsfall",
    "bezeichnung": "Erklärung für Bieter- und Arbeitsgemeinschaften",
    "beilage_nummer": "Beilage 01",
    "beschreibung": "Erforderlich bei Bieter- oder Arbeitsgemeinschaften zur Auflistung der Mitglieder, Gründe für die Bildung und Aufgaben der einzelnen Unternehmer. Muss von sämtlichen Mitgliedern rechtsgültig elektronisch unterfertigt werden.",
    "unterzeichnung_erforderlich": true,
    "fachliche_pruefung": false
  },
'''
