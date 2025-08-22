

from ofs import list_bidder_docs_json, read_doc
from credgoo import get_api_key
from dotenv import load_dotenv
import os
from typing import List, Dict, Any
import json
import json as _json
from ofs.api import (
  get_path_info,
  list_items,
  list_projects,
  list_bidders_for_project,
  find_bidder,
  docs_list,
  read_document,
  kriterien_pop,
  kriterien_sync,
  kriterien_audit_event,
  list_kriterien_audit_ids,
  get_kriterien_audit_json,
  get_kriterium_description,
)
from llmcall import call_ai_model

load_dotenv()  # früh laden damit API-Keys für LLM verfügbar sind

 # ---------------- Environment / Model selection -----------------
PROVIDER = os.getenv("PROVIDER")
BASE_URL = os.getenv("BASE_URL")
MODEL = os.getenv("MODEL", "deepseek-r1")

if not PROVIDER or not BASE_URL:
    raise ValueError("PROVIDER and BASE_URL environment variables are required")

api_key = get_api_key(PROVIDER)



Projekt = "Aufsitzrasenmäher"
Bieter = "Mahrer"
Projektinfo = '''
Kurzbeschreibung: Abschluss von Rahmenverträgen zur Beschaffung von

Los 1: Aufsitzrasenmäher

Los 2: Laubbläser und Rasenmäher

Los 3: Heckenscheren und Trimmer

Los 4: Handkehrmaschinen

Vergabestelle / Auftraggeber:
Wiener Wohnen Hausbetreuung GmbH
1030 Wien, Erdbergstraße 200

Vergabeverfahren: Offenes Verfahren im Oberschwellenbereich nach BVergG 2018, elektronisch über www.vergabeportal.at

Nachprüfungsbehörde: Verwaltungsgericht Wien, 1190 Wien, Muthgasse 62

Abschlussfrist / Bindefrist:

Angebotsfrist: 24.11.2023, 10:00 Uhr

Angebotsöffnung: 24.11.2023, 10:00 Uhr

Abschlussfrist: 5 Monate nach Angebotsende (voraussichtlich Entscheidung bis Jänner 2024)

Laufzeit der Rahmenverträge: je Los bis 31.12.2026

Losaufteilung:

Los 1: Bestbieterprinzip (wirtschaftlich & technisch günstigstes Angebot)

Lose 2, 3, 4: Billigstbieterprinzip (niedrigster Preis) 
'''

# Bieter-Dokumente (mit Metadaten) – docs_list erwartet einen Identifier-String
# Format für Bieter-Dokument-Liste: project@bidder
BieterDokumente = docs_list(f"{Projekt}@{Bieter}", meta=True)

# Alle Audit-Kriterien-IDs für den Bieter laden
audit_info = list_kriterien_audit_ids(Projekt, Bieter)
print(f"Audit Kriterien IDs ({audit_info['count']}): {audit_info['ids']}")

# Optional: audit.json laden (nicht ausgeben)
_ = get_kriterien_audit_json(Projekt, Bieter, must_exist=False)

def _extract_docs_from_listing(listing: Dict[str, Any]) -> List[Dict[str, Any]]:
  """Try to normalize docs_list output into a list of doc metadata dicts.
  Accept several possible shapes: {'docs':[...]} or direct list or {'items':[...]}.
  """
  if isinstance(listing, dict):
    for key in ("docs", "items", "documents"):
      val = listing.get(key)
      if isinstance(val, list):
        return [v for v in val if isinstance(v, dict)]
  if isinstance(listing, list):
    return [v for v in listing if isinstance(v, dict)]
  return []


## Keine Heuristik – nur LLM-basierte Analyse


def load_document_content(filename: str, max_chars: int = 12000) -> str:
  ident = f"{Projekt}@{Bieter}@{filename}"
  try:
    doc_json = read_document(ident, as_json=True)  # type: ignore
    if isinstance(doc_json, dict):
      content = doc_json.get('content') or doc_json.get('text') or ''
      if isinstance(content, str):
        if len(content) > max_chars:
          return content[: max_chars//2] + "\n...[TRUNCATED]...\n" + content[- max_chars//2 :]
        return content
  except Exception as e:
    return f"[Fehler beim Laden des Dokuments {filename}: {e}]"
  return ""


## Keine Einzel-Dokumentanalyse – alles im Aggregat


def llm_find_relevant_documents(kriterium: Dict[str, Any], projektinfo: str, listing: Dict[str, Any], max_docs: int = 20, include_content: bool = False, max_chars_total: int = 20000, max_chars_per_doc: int = 0) -> Any:
  """LLM-Bewertung aller (oder Top-N) Dokumente für ein Kriterium in einem Aufruf.

  Baut einen kompakten JSON-Kontext:
    {
      "projektinfo": str,
      "kriterium": {...},
      "dokumente": [ { filename, meta, (optional) excerpt } ]
    }
  System-Prompt fordert reine JSON-Ausgabe:
    { "relevante_dokumente":[ {filename, relevance (0-1), begruendung, abgedeckte_aspekte[], fehlende_aspekte[]} ], "zusammenfassung":"..." }
  """
  docs_meta = _extract_docs_from_listing(listing)[:max_docs]
  reduced_docs: List[Dict[str, Any]] = []
  for d in docs_meta:
    docname = d.get('name') or d.get('filename') or d.get('file')
    if not docname:
      continue
    meta = d.get('meta') or {}
    # Normalize meta fields we care about
    meta_name = None
    meta_kategorie = None
    meta_begruendung = None
    if isinstance(meta, dict):
      meta_name = meta.get('name')
      meta_kategorie = meta.get('kategorie') or meta.get('category')
      meta_begruendung = meta.get('begründung') or meta.get('begruendung') or meta.get('reason')
    entry: Dict[str, Any] = {
      'docname': docname,
      'meta': {}
    }
    if meta_name:
      entry['meta']['name'] = meta_name
    if meta_kategorie:
      entry['meta']['kategorie'] = meta_kategorie
    if meta_begruendung:
      entry['meta']['begründung'] = meta_begruendung
    reduced_docs.append(entry)

  crit_public = {
    'id': kriterium.get('id'),
    'name': kriterium.get('name'),
    'beschreibung': kriterium.get('beschreibung'),
    'anforderung': kriterium.get('anforderung'),
  }
  context_obj = {
    'projektbeschreibung': projektinfo.strip(),
    'kriterium': crit_public,
    'dokumente': reduced_docs,
  }
  user_payload = _json.dumps(context_obj, ensure_ascii=False, indent=2)
  system_prompt = (
    "Du bist ein fachkundiger Assistent. Prüfe AUSSCHLIESSLICH anhand der übergebenen Metadaten, "
    "ob Dokumente relevante Informationen für das angegebene Kriterium enthalten KÖNNTEN. Inhalte werden NICHT betrachtet.\n"
    "Kontext-Struktur:\n"
    "- projektbeschreibung: Text\n"
    "- kriterium: { id, name, beschreibung, anforderung? }\n"
    "- dokumente: [ { docname, meta: { name?, kategorie?, begründung? } } ]\n"
    "Nutze insbesondere meta.name, meta.kategorie und meta.begründung zur Einschätzung.\n"
    "Gib NUR JSON zurück mit folgendem Schema: "
    "{ 'relevante_dokumente': [ { 'filename': string, 'relevance': number 0-1, 'begruendung': string } ], 'zusammenfassung': string }.\n"
    "Hinweise:\n"
    "- 'filename' soll dem 'docname' des Eingangs entsprechen.\n"
    "- Falls kein Dokument geeignet ist, gib 'relevante_dokumente': [] zurück.\n"
    "- Keine Texte außerhalb des JSON. Sprache: Deutsch."
  )
  try:
    result = call_ai_model(system_prompt, user_payload, verbose=False, json_cleanup=True, task_type="kriterien")
    return result
  except Exception as e:
    return { 'error': str(e) }


## ---------------- Einfache Ausgabe je Audit-ID -----------------
ids_cycle = audit_info['ids']
if not ids_cycle:
  print("Keine Kriterien IDs vorhanden.")
else:
  print("\nModus: Für jedes Kriterium: ID + Beschreibung + gefundene Dokumente. Enter=weiter, q=quit")

  def _parse_analysis(analysis: Any) -> Dict[str, Any]:
    if isinstance(analysis, str):
      try:
        return json.loads(analysis)
      except Exception:
        return { 'raw': analysis }
    return analysis if isinstance(analysis, dict) else {'raw': analysis}

  def _get_doc_meta_by_filename(filename: str) -> Dict[str, Any]:
    docs = _extract_docs_from_listing(BieterDokumente)
    for d in docs:
      fname = d.get('filename') or d.get('name') or d.get('file')
      if fname == filename:
        return d
    return {}

  for kriterium_id in ids_cycle:
    # 1) Kriterium anzeigen
    desc = get_kriterium_description(Projekt, kriterium_id)
    print("\n" + "="*80)
    print(f"ID: {kriterium_id}")
    if not desc.get('missing'):
      if desc.get('name'):
        print(f"Name: {desc.get('name')}")
      if desc.get('beschreibung'):
        print(f"Beschreibung: {desc.get('beschreibung')}")
      if desc.get('anforderung'):
        print(f"Anforderung: {desc.get('anforderung')}")
    else:
      print("(Nicht im Projekt-Quellkatalog gefunden)")

    # 2) LLM: relevante Dokumente ermitteln (nur Metadaten, keine Excerpts)
    print("LLM-Analyse der Dokumentenliste...")
    analysis = llm_find_relevant_documents(desc, Projektinfo, BieterDokumente, include_content=False, max_docs=20, max_chars_total=20000)
    # 3) Ergebnis kompakt darstellen
    parsed = analysis if isinstance(analysis, dict) else {}
    if not parsed and isinstance(analysis, str):
      try:
        parsed = json.loads(analysis)
      except Exception:
        parsed = { 'raw': analysis }

    rel_list = parsed.get('relevante_dokumente') or parsed.get('relevant_docs') or []
    if not isinstance(rel_list, list):
      rel_list = []
    try:
      rel_list.sort(key=lambda x: x.get('relevance', x.get('score', 0)), reverse=True)
    except Exception:
      pass

    print("Gefundene Dokumente:")
    if rel_list:
      for i, item in enumerate(rel_list, 1):
        fname = item.get('filename') or '(unbekannt)'
        rel = item.get('relevance') if item.get('relevance') is not None else item.get('score')
        rel_str = f"{rel:.2f}" if isinstance(rel, (int,float)) else str(rel)
        print(f"  {i}. {fname}  relevance={rel_str}")
    else:
      print("KEINE DOKUMENTE")

    if 'error' in parsed:
      print("Fehler:")
      print(parsed['error'])

    # 4) Weiter mit Enter, q für Abbruch
    nxt = input("[Enter=weiter, q=quit] > ").strip().lower()
    if nxt == 'q':
      break

