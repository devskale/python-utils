import argparse
import json
import sys
from credgoo import get_api_key
from ofs.api import list_bidder_docs_json, get_bieterdokumente_list  # type: ignore
# Agno framework pieces (used to construct the minimal workflow)
from agno.agent import Agent
from agno.models.vllm import vLLM
from agno.tools import tool
from agno.workflow.v2.workflow import Workflow
from agno.utils.pprint import pprint_run_response



 # ---------------- Environment / Model selection -----------------
PROVIDER = "tu"
BASE_URL = "https://aqueduct.ai.datalab.tuwien.ac.at/v1"
MODEL = "deepseek-r1"

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


def findMatches(geforderte_dokumente, hochgeladene_docs, runner = 1):
    prompt = f"""
Du bist ein hilfreicher Assistent, der dabei hilft, geforderte Dokumente mit hochgeladenen Dokumenten abzugleichen.
Deine Aufgabe ist es, das am besten passende hochgeladene Dokument für jedes geforderte Dokument zu finden.
Du erhältst eine Liste von geforderten Dokumenten mit ihren Bezeichnungen.

Wenn nicht anders angegeben gilt: 
- ist das ausschreibende Unternehmen die "Wiener Wohnen Hausbetreuung Gmbh", ein Unternehmen aus Österreich.
- ist der Bieter ein Unternehmen aus Österreich, das an der Ausschreibung teilnimmt.
- ist der Bieter ein Einzalbieter, keine Bieter- oder Arbeitsgemeinschaft.
- sind die hochgeladenen Dokumente von einem Bieter, der an der Ausschreibung teilnimmt.
- sind die hochgeladenen Dokumente in deutscher Sprache.
- bietet der Bieter für alle Lose an.
- ist der Bieter der Hauptauftragnehmer
- Es gibt keine Subunternehmer.

Das geforderte Dokument ist:
{json.dumps(geforderte_dokumente, indent=2, ensure_ascii=False)}

Die liste mit den hochgeladenen Bieterdokumenten ist:
{json.dumps(hochgeladene_docs, indent=2, ensure_ascii=False)}

gib eine liste der am besten passenden hochgeladenen Dokumente zurück, die zu dem geforderten Dokument passen.
"matches": [
    {{
    "Dateiname": "...",    # der Dateiname des hochgeladenen Dokuments 
     "Name": "...",         # der Name aus meta.name des hochgeladenen Dokuments
     "Kategorie": "...",    # die Kategorie aus meta.kategorie des hochgeladenen Dokuments
     "Begründung": "..."}},  # die Begründung für die Zuordnung
]

"""
    return prompt


def main():
    """Minimal utility:

    - Accepts one positional argument in the form project@bidder
    - Calls ofs.api.list_bidder_docs_json(project, bidder)
    - Prints the returned JSON nicely
    """
    parser = argparse.ArgumentParser(description="List bidder docs JSON for project@bidder")
    parser.add_argument("identifier", help="project@bidder")
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

    geforderte_dokumente = get_bieterdokumente_list(project)
    print(f"Geforderte Bieterdokumente: {len(geforderte_dokumente)}")
    print(f"Hochgeladene Bieterdokumente: {len(hochgeladene_dokumente['documents'])}")
    #print(json.dumps(hochgeladene_dokumente, indent=2, ensure_ascii=False))
    #print(json.dumps(geforderte_dokumente, indent=2, ensure_ascii=False))
    # loop through geforderte_dokumente and print index and bezeichnung
    for i, gefordertes_doc in enumerate(geforderte_dokumente, start=1):
        print(f"{i}/{len(geforderte_dokumente)} - {gefordertes_doc.get('bezeichnung')}")
        # ask llm if bieterdoc matches a gefordertes_doc
        # if yes, print match, if no, print no match
        mPrompt = findMatches(
              gefordertes_doc, hochgeladene_dokumente, i)
        # Show only the first 100 characters of the prompt for preview
        preview = mPrompt[:100].replace("\n", " ") + ("..." if len(mPrompt) > 100 else "")
        print(f"Prompt preview: {preview}")
        response = agent.run(
            mPrompt,
            stream=True,
            markdown=True,
            show_message=False
        )
        pprint_run_response(response, markdown=True)
        input("Press Enter to continue...")
        i += 1

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