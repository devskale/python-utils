import argparse
import os
import json
import re
import sys
from credgoo import get_api_key
from ofs.api import list_bidder_docs_json, get_bieterdokumente_list, get_kriterien_audit_json, get_kriterium_description, read_doc  # type: ignore
from ofs.kriterien import find_kriterien_file, load_kriterien  # type: ignore
# Agno framework pieces (used to construct the minimal workflow)
from agno.agent import Agent
from agno.models.vllm import VLLM
# from agno.tools import tool
# from agno.workflow.v2.workflow import Workflow

try:
    from tqdm import tqdm  # type: ignore
except ImportError:
    tqdm = None  # Fallback if tqdm not available

# Optional JSON repair for messy LLM outputs
try:
    from json_repair import repair_json  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    repair_json = None  # type: ignore

 # ---------------- Environment / Model selection -----------------
PROVIDER = "tu"
BASE_URL = "https://aqueduct.ai.datalab.tuwien.ac.at/v1"
MODEL = "glm-4.5-355b"


# AUSSCHREIBUNGSINFO will be retrieved dynamically from kriterien.json

api_key = get_api_key(PROVIDER)

def get_ausschreibungsinfo(project: str) -> str:
    """Retrieve AUSSCHREIBUNGSINFO from the project's kriterien.json metadata."""
    try:
        kriterien_file = find_kriterien_file(project)
        if not kriterien_file:
            # Fallback to default if no kriterien file found
            return """
  "vergabestelle": "Unknown",
  "projektName": "Unknown Project",
  "beschreibung": "No description available",
  "referenznummer": "Unknown"
"""

        data = load_kriterien(kriterien_file)
        meta = data.get('meta', {}).get('meta', {})

        # Extract fields from metadata
        vergabestelle = meta.get('auftraggeber', 'Unknown')
        # Use aktenzeichen as project name if available, otherwise derive from ausschreibungsgegenstand
        aktenzeichen = meta.get('aktenzeichen', '')
        if aktenzeichen:
            projekt_name = f"Projekt {aktenzeichen}"
        else:
            # Derive a shorter project name from the description
            ausschreibungsgegenstand = meta.get('ausschreibungsgegenstand', 'Unknown Project')
            # Take first part before comma or first 50 characters
            if ',' in ausschreibungsgegenstand:
                projekt_name = ausschreibungsgegenstand.split(',')[0].strip()
            else:
                projekt_name = ausschreibungsgegenstand[:50] + ('...' if len(ausschreibungsgegenstand) > 50 else '')

        beschreibung = meta.get('ausschreibungsgegenstand', 'No description available')
        referenznummer = meta.get('aktenzeichen', 'Unknown')
        datum = meta.get('datum', 'Unknown')

        # Format lose information if available
        lose_info = ""
        lose = meta.get('lose', [])
        if lose:
            lose_info = "\n  \"lose\": [\n"
            for los in lose:
                lose_info += f'    {{"nummer": "{los.get("nummer", "N/A")}", "bezeichnung": "{los.get("bezeichnung", "N/A")}", "beschreibung": "{los.get("beschreibung", "N/A")}", "bewertungsprinzip": "{los.get("bewertungsprinzip", "N/A")}"}},\n'
            lose_info = lose_info.rstrip(',\n') + "\n  ]"

        return f"""
  "vergabestelle": "{vergabestelle}",
  "projektName": "{projekt_name}",
  "beschreibung": "{beschreibung}",
  "referenznummer": "{referenznummer}",
  "dokumentdatum": "{datum}"{lose_info}
"""

    except Exception as e:
        # Fallback on error
        return f"""
  "vergabestelle": "Error loading metadata",
  "projektName": "Error loading metadata",
  "beschreibung": "Error: {str(e)}",
  "referenznummer": "Error"
"""

def findeDoks(id, kriteriumbeschreibung, doclist, runner = 1):
    prompt = f"""
Du bist ein hilfreicher Assistent, der dabei hilft, Ausschreibungskriterien zu überprüfen und passende Dokumente zu finden.

Wenn nicht anders angegeben gilt:
- das ausschreibende Unternehmen ist die "Wiener Wohnen Hausbetreuung Gmbh", ein Unternehmen aus Österreich.
- der Bieter ist ein Unternehmen aus Österreich.
- der Bieter ein Einzalbieter
- es gibt keine Bieter- oder Arbeitsgemeinschaft.
- es gibt keine Subunternehmer.
- sind die hochgeladenen Dokumente von einem Bieter, der an der Ausschreibung teilnimmt.
- sind die hochgeladenen Dokumente in deutscher Sprache.
- bietet der Bieter für alle Lose an.
- ist der Bieter der Hauptauftragnehmer

Das zu analysierende Kriterium ist:
{json.dumps(kriteriumbeschreibung, indent=2, ensure_ascii=False)}

Die liste mit den hochgeladenen Bieterdokumenten ist:
{json.dumps(doclist, indent=2, ensure_ascii=False)}

gib eine liste der am besten passenden hochgeladenen Dokumente zurück, die für die Bewertung des Kriteriums relevant sind.
Sollte kein Dokument passen, gib eine leere Liste zurück.
"matches": [
    {{
    "Dateiname": "...",    # der Dateiname des hochgeladenen Dokuments
     "Name": "...",         # der Name aus meta.name des hochgeladenen Dokuments
     "Kategorie": "...",    # die Kategorie aus meta.kategorie des hochgeladenen Dokuments
     "Begründung": "..."}},  # die Begründung für die Zuordnung
]

"""
    return prompt


def prüfeKriterium(id, kriteriumbeschreibung, kontext, ausschreibungsinfo, runner = 1):
    prompt = f"""
Du bist ein hilfreicher Assistent, der dabei hilft, Ausschreibungskriterien anhand Dokumenten zu überprüfen.
Ausschreibungsinformationen:
{ausschreibungsinfo}

Das zu analysierende Kriterium ist:
{json.dumps(kriteriumbeschreibung, indent=2, ensure_ascii=False)}

Der Kontext (Dokumente) zum Prüfen des Kriteriums ist:
{json.dumps(kontext, indent=2, ensure_ascii=False)}

Erstelle einen Plan, wie du das Kriterium anhand des Kontextes (Dokumente) überprüfen kannst. Überprüfe das Kriterium sorgfältig anhand des Kontextes (Dokumente).
Gib eine kurze Beurteilung ab, ob das Kriterium erfüllt ist (ja/nein) und eine kurze Begründung.
Antwort in der Form:
{{
  "erfüllt": "ja" | "nein" | "teilweise" | "nicht beurteilbar" | "benötigt Eingriff",
  "begründung": "..."
}}
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


def main():
    """Minimal utility:

    - Accepts one positional argument in the form project@bidder
    - Calls ofs.api.list_bidder_docs_json(project, bidder)
    - Prints the returned JSON nicely
    """
    parser = argparse.ArgumentParser(description="Automated criteria assessment with LLM")
    parser.add_argument("identifier", help="project@bidder")
    parser.add_argument("--limit", type=int, default=10, help="Number of criteria to process (default: 10)")
    parser.add_argument("--id", help="Specific criterion ID to check (optional)")
    parser.add_argument("--out", type=str, default=None, help="Optional path to write JSON results (default: ./logs/<project>.<bidder>.assessments.json)")
    parser.add_argument("--test", action="store_true", help="Test mode: simulate LLM calls without actual API hits")
    args = parser.parse_args()

    agent = Agent(
        model=VLLM(
            base_url=BASE_URL,
            api_key=api_key,
            id=MODEL,
            max_retries=3,
            #stream=True,
        ),
        tools=[],
    )

    identifier = args.identifier
    if "@" not in identifier:
        print("Expected identifier in the form project@bidder")
        sys.exit(2)
    project, bidder = identifier.split("@", 1)

    # Retrieve AUSSCHREIBUNGSINFO from kriterien.json
    ausschreibungsinfo = get_ausschreibungsinfo(project)
    print(f"AUSSCHREIBUNGSINFO für Projekt '{project}':")
    print(ausschreibungsinfo)

    try:
        hochgeladene_dokumente = list_bidder_docs_json(project, bidder, include_metadata=True)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    auditliste = get_kriterien_audit_json(project, bidder)
    print(f"Auditliste: {len(auditliste['kriterien'])}")
    # Build a matched list for the first N required docs
    limit = max(0, int(args.limit))
    # Container for JSON output per Kriterium
    ergebnisse = []

    if args.id:
        auditliste['kriterien'] = [k for k in auditliste['kriterien'] if k.get('id') == args.id]
        if not auditliste['kriterien']:
            print(f"Criterion {args.id} not found, skipping analysis")
            sys.exit(0)

    # loop through audit kriterien and print index and bezeichnung
    iterator = tqdm(enumerate(auditliste['kriterien'], start=1), total=len(auditliste['kriterien']), desc="Processing criteria") if tqdm else enumerate(auditliste['kriterien'], start=1)
    for i, audit_kriterium in iterator:
        if limit and i > limit:
            break
        # hole kriteriumsbeschreibung von ofs.api
        kriterium = get_kriterium_description(project, audit_kriterium.get('id', ''))
        typ = kriterium.get('typ') or kriterium.get('raw', {}).get('typ') or 'N/A'
        name = kriterium.get('name') or kriterium.get('raw', {}).get('name') or 'N/A'
        anforderung = kriterium.get('anforderung') or kriterium.get('raw', {}).get('anforderung') or ''

        print(f"{i}/{len(auditliste['kriterien'])} - {audit_kriterium.get('id', 'N/A')} [{typ}] {name}")
        #print(f"   {anforderung}")
        #exit(0)
        # ---------------------------------------------------------------------------------------------
        # Find relevant documents for assessing a kriterium
        # ---------------------------------------------------------------------------------------------
        prompt = findeDoks(audit_kriterium.get('id', ''), kriterium, hochgeladene_dokumente)
        print("---- STEP-1 - retrieve Kontext ----")
        if args.test:
            print("Test mode: simulating LLM call for document matching")
            print("Prompt:")
            print(prompt)
            match_result = {
                "matches": [
                    {
                        "Dateiname": "mock_document.pdf",
                        "Name": "Mock Document",
                        "Kategorie": "Test Category",
                        "Begründung": "Simulated match for testing"
                    }
                ]
            }
        else:
            response = agent.run(
                prompt,
                stream=False,  # capture final text only
                markdown=False,
                show_message=False
            )
            # Parse the response into JSON (clean) and extract the matches array
            content = getattr(response, "content", response)
            match_result = extract_json_clean(content if isinstance(content, str) else str(content))

        # Handle different possible return types from extract_json_clean
        if isinstance(match_result, list):
            # Direct matches array
            matches = match_result
        elif isinstance(match_result, dict):
            # Dict with matches key
            matches = match_result.get("matches", [])
        else:
            # None or other
            matches = []

        # if matches array is present, print matches list
        if not matches:
            print("  Keine passenden Dokumente gefunden.")
            print("")
            # Kein Kontext aus Schritt 1 -> nächstes Kriterium
            ergebnisse.append({
                "id": audit_kriterium.get('id', ''),
                "doc_names": [],
                "assessment": {
                    "erfüllt": "nicht beurteilbar",
                    "begründung": "Keine passenden Dokumente gefunden."
                }
            })
            continue
        print(f"  Gefundene passende Dokumente: {len(matches)}")
        # collect matched filenames (initial list from Step 1)
        matched_names: list[str] = []
        for m in matches:
            dateiname = m.get("Dateiname", "N/A")
            name = m.get("Name", "N/A")
            kategorie = m.get("Kategorie", "N/A")
            begruendung = m.get("Begründung", "N/A")
            print(f"    - {dateiname} (Name: {name}, Kategorie: {kategorie})")
            print(f"      Begründung: {begruendung}")
            if dateiname and dateiname != "N/A":
                matched_names.append(dateiname)
        print("")

        # ---------------------------------------------------------------------------------------------
        # If relevant documents are found let the agent assess the kriterium
        # ---------------------------------------------------------------------------------------------
        # build up kontext, its the documents found
        print("---- STEP-2 - Prüfe Kriterium (Kontext) ----")
        print(f"Kriterium: {name}")
        if anforderung:
            print(f"Anforderung: {anforderung}")
        print("")
        kontext = []
        used_doc_names: list[str] = []

        for m in matches:
            dateiname = m.get("Dateiname", "")
            if not dateiname or dateiname == "N/A":
                continue
            # read_doc from ofs.api expects a single identifier string
            identifier_doc = f"{project}@{bidder}@{dateiname}"
            doc = read_doc(identifier_doc)
            if doc:
#                print(f"  Kontext-Dokument: {dateiname}")
                # print(f"  Inhalt (erste 300 Zeichen): {doc.get('content', '')[:300]}")
                kontext.append(doc)
                used_doc_names.append(dateiname)

        if not kontext:
            print("  Kein Kontext (Dokumente) zum Prüfen gefunden, überspringe Kriterium.")
            print("")
            ergebnisse.append({
                "id": audit_kriterium.get('id', ''),
                "doc_names": matched_names,
                "assessment": {
                    "erfüllt": "nicht beurteilbar",
                    "begründung": "Kontext-Dokumente konnten nicht geladen werden."
                }
            })
            continue

        prompt = prüfeKriterium(audit_kriterium.get('id', ''), kriterium, kontext, ausschreibungsinfo)
        if args.test:
            print("Test mode: simulating LLM call for criterion assessment")
            print("Prompt:")
            print(prompt)
            assessment_result = {
                "erfüllt": "ja",
                "begründung": "Simulated assessment for testing"
            }
        else:
            response = agent.run(
                prompt,
                stream=False,  # capture final text only
                markdown=False,
                show_message=False
            )
            # Parse the response into JSON (clean) and extract the matches array
            content = getattr(response, "content", response)
            assessment_result = extract_json_clean(content if isinstance(content, str) else str(content))

        # assessment_result should be a dict with erfüllt and begründung keys
        if not isinstance(assessment_result, dict):
            assessment_result = {
                "erfüllt": "nicht beurteilbar",
                "begründung": f"Fehler beim Parsen der Antwort: {assessment_result}"
            }

        print("---- RESPONSE ----")
        print(json.dumps(assessment_result, indent=2, ensure_ascii=False))
        # Persist per-kriterium entry
        ergebnisse.append({
            "id": audit_kriterium.get('id', ''),
            "doc_names": used_doc_names if used_doc_names else matched_names,
            "assessment": assessment_result
        })
        print("")

    # ---------------------------------------------------------------------------------------------
    # Write aggregated results to JSON
    # ---------------------------------------------------------------------------------------------
    os.makedirs("logs", exist_ok=True)
    out_path = args.out or os.path.join("logs", f"{project}.{bidder}.assessments.json")
    payload = {
        "project": project,
        "bidder": bidder,
        "count": len(ergebnisse),
        "results": ergebnisse
    }
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        print(f"Ergebnisse gespeichert: {out_path}")
    except Exception as e:
        print(f"Warnung: Ergebnisse konnten nicht gespeichert werden: {e}")


if __name__ == "__main__":
    main()
