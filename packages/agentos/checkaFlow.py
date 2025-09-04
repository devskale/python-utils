import argparse
import os
import json
import re
import sys
from credgoo import get_api_key
from ofs.api import list_bidder_docs_json, get_bieterdokumente_list, get_kriterien_audit_json, get_kriterium_description, read_doc  # type: ignore
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
MODEL = "deepseek-r1"


AUSSCHREIBUNGSINFO = """
  "vergabestelle": "Wiener Wohnen Hausbetreuung GmbH",
  "adresse": 1030 Wien, Erdbergstraße 202-206, Österreich,
  "projektName": "Gartengeräte Lieferauftrag",
  "startDatum": "NONE",
  "bieterabgabe": "2023-11-24",
  "endDatum": "2026-12-31",
  "beschreibung": "Öffentliches Vergabeverfahren über die Lieferung von Aufsitzrasenmähern, Laubbläsern, Rasenmähern, Heckenscheren, Trimmern und Handkehrmaschinen an den Auftraggeber.",
  "referenznummer": "2023_02002_AAB_EV",
  "schlagworte": "Ausschreibung, Rahmenvertrag, Beschaffung, Lieferauftrag, Gartengeräte, Aufsitzrasenmäher, Laubbläser, Rasenmäher, Heckenscheren, Trimmer, Handkehrmaschinen",
  "sprache": "Deutsch",
  "dokumentdatum": "2023-11-24"
"""

api_key = get_api_key(PROVIDER)

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


def prüfeKriterium(id, kriteriumbeschreibung, kontext, runner = 1):
    prompt = f"""
Du bist ein hilfreicher Assistent, der dabei hilft, Ausschreibungskriterien anhand Dokumenten zu überprüfen.
Ausschreibungsinformationen:
{AUSSCHREIBUNGSINFO}
Das zu analysierende Kriterium ist:
{json.dumps(kriteriumbeschreibung, indent=2, ensure_ascii=False)}
Der Kontext (Dokumente) zum Prüfen des Kriteriums ist:
{json.dumps(kontext, indent=2, ensure_ascii=False)}

Erstelle einen Plan, wie du das Kriterium anhand des Kontextes (Dokumente) überprüfen kannst.
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
    parser = argparse.ArgumentParser(description="List bidder docs JSON for project@bidder")
    parser.add_argument("identifier", help="project@bidder")
    parser.add_argument("--limit", type=int, default=10, help="Number of required docs to process (default: 3)")
    parser.add_argument("--out", type=str, default=None, help="Optional path to write JSON results (default: ./<project>.<bidder>.assessments.json)")
    args = parser.parse_args()

    agent = Agent(
        model=vLLM(
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

    # loop through audit kriterien and print index and bezeichnung
    for i, audit_kriterium in enumerate(auditliste['kriterien'], start=1):
        if limit and i > limit:
            break
        kriterium = get_kriterium_description(project, audit_kriterium.get('id', ''))
        typ = kriterium.get('typ') or kriterium.get('raw', {}).get('typ') or 'N/A'
        name = kriterium.get('name') or kriterium.get('raw', {}).get('name') or 'N/A'
        anforderung = kriterium.get('anforderung') or kriterium.get('raw', {}).get('anforderung') or ''

        print(f"{i}/{len(auditliste['kriterien'])} - {audit_kriterium.get('id', 'N/A')} [{typ}] {name}")
        # ---------------------------------------------------------------------------------------------
        # Find relevant documents for assessing a kriterium
        # ---------------------------------------------------------------------------------------------
        prompt = findeDoks(audit_kriterium.get('id', ''), kriterium, hochgeladene_dokumente)
        print("---- STEP-1 - retrieve Kontext ----")
        response = agent.run(
            prompt,
            stream=False,  # capture final text only
            markdown=False,
            show_message=False
        )
        # Parse the response into JSON (clean) and extract the matches array
        content = getattr(response, "content", response)
        match_result = extract_json_clean(content if isinstance(content, str) else str(content))
        # if matches array is present, print matches list
        matches = match_result.get("matches", []) if match_result else []
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

        prompt = prüfeKriterium(audit_kriterium.get('id', ''), kriterium, kontext)
        response = agent.run(
            prompt,
            stream=False,  # capture final text only
            markdown=False,
            show_message=False
        )
        # Parse the response into JSON (clean) and extract the matches array
        content = getattr(response, "content", response)
        assessment_result = extract_json_clean(content if isinstance(content, str) else str(content))
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
    out_path = args.out or os.path.join(os.path.dirname(__file__), f"{project}.{bidder}.assessments.json")
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



'''
kriterieum beschreibung
  Beschreibung: {'id': 'E_BERUFL_001', 'name': 'Zuverlässigkeit gemäß BVergG', 'beschreibung': '', 'anforderung': 'Der Bieter muss zuverlässig im Sinne des BVergG sein. Er erklärt, dass gegen ihn, seine Subunternehmer und die von ihm genannten sonstigen Dritten kein Ausschlussgrund gemäß § 78 Abs 1 BVergG vorliegt, insbesondere straf- und arbeitsrechtliche Unbescholtenheit, keine Liquidation, keine Einstellung gewerblicher Tätigkeiten und kein Insolvenzverfahren oder Abweisung mangels hinreichenden Vermögens.', 'raw': {'id': 'E_BERUFL_001', 'typ': 'Eignung', 'kategorie': 'Berufliche Zuverlässigkeit', 'name': 'Zuverlässigkeit gemäß BVergG', 'anforderung': 'Der Bieter muss zuverlässig im Sinne des BVergG sein. Er erklärt, dass gegen ihn, seine Subunternehmer und die von ihm genannten sonstigen Dritten kein Ausschlussgrund gemäß § 78 Abs 1 BVergG vorliegt, insbesondere straf- und arbeitsrechtliche Unbescholtenheit, keine Liquidation, keine Einstellung gewerblicher Tätigkeiten und kein Insolvenzverfahren oder Abweisung mangels hinreichenden Vermögens.', 'schwellenwert': None, 'gewichtung_punkte': None, 'dokumente': [], 'geltung_lose': ['alle'], 'pruefung': {'status': None, 'bemerkung': None, 'pruefer': None, 'datum': None}, 'quelle': 'Punkt 5.3. (1), Punkt 5.3. (2)'}}
'''

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

''' AUDITLISTE JSON BEISPIEL
{
  "meta": {
    "schema_version": "1.0-bieter-kriterien",
    "projekt": "Aufsitzrasenmäher",
    "bieter": "Bieter1"
  },
  "kriterien": [
    {
      "id": "E_BERUFL_001",
      "status": null,
      "prio": null,
      "bewertung": null,
      "audit": {
        "zustand": "synchronisiert",
        "verlauf": [
          {
            "zeit": "2025-08-21T12:02:59.434638Z",
            "ereignis": "kopiert",
            "quelle_status": null,
            "ergebnis": null,
            "akteur": "system"
          }
        ]
      }
    },
    {
      "id": "E_FORM_001",
      "status": null,
      "prio": null,
      "bewertung": null,
      "audit": {
        "zustand": "synchronisiert",
        "verlauf": [
          {
            "zeit": "2025-08-21T12:02:59.434629Z",
            "ereignis": "kopiert",
            "quelle_status": null,
            "ergebnis": null,
            "akteur": "system"
          }
        ]
      }
    },
    {
      "id": "E_FRIST_001",
      "status": null,
      "prio": null,
      "bewertung": null,
      "audit": {
        "zustand": "synchronisiert",
        "verlauf": [
          {
            "zeit": "2025-08-21T12:02:59.434632Z",
            "ereignis": "kopiert",
            "quelle_status": null,
            "ergebnis": null,
            "akteur": "system"
          }
        ]
      }
    },
    {
      "id": "E_FRIST_002",
      "status": null,
      "prio": null,
      "bewertung": null,
      "audit": {
        "zustand": "synchronisiert",
        "verlauf": [
          {
            "zeit": "2025-08-21T12:02:59.434636Z",
            "ereignis": "kopiert",
            "quelle_status": null,
            "ergebnis": null,
            "akteur": "system"
          }
        ]
      }
    },
    {
      "id": "E_FRIST_003",
      "status": null,
      "prio": null,
      "bewertung": null,
      "audit": {
        "zustand": "synchronisiert",
        "verlauf": [
          {
            "zeit": "2025-08-21T12:02:59.434642Z",
            "ereignis": "kopiert",
            "quelle_status": null,
            "ergebnis": null,
            "akteur": "system"
          }
        ]
      }
    },
    {
      "id": "E_FRIST_004",
      "status": null,
      "prio": null,
      "bewertung": null,
      "audit": {
        "zustand": "synchronisiert",
        "verlauf": [
          {
            "zeit": "2025-08-21T12:02:59.434646Z",
            "ereignis": "kopiert",
            "quelle_status": null,
            "ergebnis": null,
            "akteur": "system"
          }
        ]
      }
    },
    {
      "id": "E_FRIST_005",
      "status": null,
      "prio": null,
      "bewertung": null,
      "audit": {
        "zustand": "synchronisiert",
        "verlauf": [
          {
            "zeit": "2025-08-21T12:02:59.434649Z",
            "ereignis": "kopiert",
            "quelle_status": null,
            "ergebnis": null,
            "akteur": "system"
          }
        ]
      }
    },
    {
      "id": "E_FRIST_006",
      "status": "ja",
      "prio": null,
      "bewertung": null,
      "audit": {
        "zustand": "geprueft",
        "verlauf": [
          {
            "zeit": "2025-08-21T12:02:59.434653Z",
            "ereignis": "kopiert",
            "quelle_status": null,
            "ergebnis": null,
            "akteur": "system"
          },
          {
            "zeit": "2025-08-21T12:11:42.270104Z",
            "ereignis": "kopiert",
            "quelle_status": "ja",
            "ergebnis": null,
            "akteur": "system"
          },
          {
            "zeit": "2025-08-21T13:36:13.694761Z",
            "ereignis": "ki_pruefung",
            "quelle_status": "ja",
            "ergebnis": null,
            "akteur": "cli"
          },
          {
            "zeit": "2025-08-21T13:36:31.423036Z",
            "ereignis": "freigabe",
            "quelle_status": "ja",
            "ergebnis": null,
            "akteur": "cli"
          },
          {
            "zeit": "2025-08-21T13:36:50.276134Z",
            "ereignis": "ablehnung",
            "quelle_status": "ja",
            "ergebnis": null,
            "akteur": "cli"
          },
          {
            "zeit": "2025-08-21T13:36:58.560264Z",
            "ereignis": "reset",
            "quelle_status": "ja",
            "ergebnis": null,
            "akteur": "cli"
          },
          {
            "zeit": "2025-08-21T13:37:09.348703Z",
            "ereignis": "mensch_pruefung",
            "quelle_status": "ja",
            "ergebnis": null,
            "akteur": "cli"
          }
        ]
      }
    },
    {
      "id": "E_FRIST_007",
      "status": null,
      "prio": null,
      "bewertung": null,
      "audit": {
        "zustand": "synchronisiert",
        "verlauf": [
          {
            "zeit": "2025-08-21T12:02:59.434659Z",
            "ereignis": "kopiert",
            "quelle_status": null,
            "ergebnis": null,
            "akteur": "system"
          }
        ]
      }
    },
    {
      "id": "E_NACH_001",
      "status": null,
      "prio": null,
      "bewertung": null,
      "audit": {
        "zustand": "synchronisiert",
        "verlauf": [
          {
            "zeit": "2025-08-21T12:02:59.434630Z",
            "ereignis": "kopiert",
            "quelle_status": null,
            "ergebnis": null,
            "akteur": "system"
          }
        ]
      }
'''