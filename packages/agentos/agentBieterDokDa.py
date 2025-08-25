

from ofs import list_bidder_docs_json, read_doc
from credgoo import get_api_key
from dotenv import load_dotenv
import os
from typing import List, Dict, Any
import curses
import textwrap
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



Projekt = "Entrümpelung"
Bieter = "Alpenglanz"
Projektinfo = '''
Kurzbeschreibung: Abschluss eines Rahmenvertrags zur Lieferung von Entrümpelungsleistungen.

Vergabestelle / Auftraggeber: Wiener Wohnen Hausbetreuung GmbH, Erdbergstraße 200, 1030 Wien.

Vergabeverfahren: Offenes Verfahren im Oberschwellenbereich gemäß BVergG 2018, Abwicklung über das Vergabeportal.

Angebots-/Abschlussfrist: Angebotsfrist 08.09.2023, 10:00 Uhr; Bindefrist ca. 5 Monate nach Angebotsende.

Laufzeit des Rahmenvertrags: Bis 31.12.2027.

Lose: Ein Los (Elektro-Nutzfahrzeuge, inkl. Serviceleistungen).q
'''
Projektinfo_Fahrzeugeinrichtung = '''
Kurzbeschreibung: Abschluss eines Rahmenvertrags zur Lieferung und Wartung von Elektro-Nutzfahrzeugen für den städtischen Einsatz.

Vergabestelle / Auftraggeber: Wiener Wohnen Hausbetreuung GmbH, Erdbergstraße 200, 1030 Wien.
q
Vergabeverfahren: Offenes Verfahren im Oberschwellenbereich gemäß BVergG 2018, Abwicklung über das Vergabeportal.

Angebots-/Abschlussfrist: Angebotsfrist 08.09.2023, 10:00 Uhr; Bindefrist ca. 5 Monate nach Angebotsende.

Laufzeit des Rahmenvertrags: Bis 31.12.2027.

Lose: Ein Los
'''

Projektinfo_Rasenmäher = '''
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
  # Falls das Kriterium eine Liste erwarteter/benannter Dokumente enthält (z.B. Beilagen), mitgeben
  try:
    docs_hint = kriterium.get('dokumente')
    if isinstance(docs_hint, list) and docs_hint:
      crit_public['dokumente'] = docs_hint
  except Exception:
    pass
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
    "- kriterium: { id, name, beschreibung, anforderung?, dokumente? }\n"
    "- dokumente: [ { docname, meta: { name?, kategorie?, begründung? } } ]\n"
    "Nutze insbesondere meta.name, meta.kategorie und meta.begründung zur Einschätzung.\n"
    "Falls im Kriterium unter 'dokumente' konkrete Formblätter/Beilagen genannt sind, gewichte Übereinstimmungen entsprechend höher.\n"
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


## ---------------- Kriterien-TUI -----------------
def _short(text: str, limit: int = 80) -> str:
  t = (text or '').strip()
  if len(t) <= limit:
    return t
  return t[:limit-1] + "…"


def build_criteria(ids_cycle: List[str]) -> List[Dict[str, Any]]:
  items: List[Dict[str, Any]] = []
  for cid in ids_cycle:
    desc = get_kriterium_description(Projekt, cid)
    short_src = desc.get('beschreibung') or desc.get('anforderung') or ''
    items.append({
      'id': cid,
      'name': desc.get('name') or '',
      'beschreibung': desc.get('beschreibung') or '',
      'anforderung': desc.get('anforderung') or '',
      'short': _short(short_src, 80),
      'desc_full': desc,
    })
  return items


def draw_list(stdscr, items: List[Dict[str, Any]], idx: int, top: int, projekt: str, bieter: str):
  stdscr.clear()
  h, w = stdscr.getmaxyx()
  title = f"Kriterien auswählen – {projekt} / {bieter}  (↑/↓ bewegen, Enter anzeigen, q beenden)"
  stdscr.addnstr(0, 0, title, w-1, curses.A_BOLD)
  header = "ID          Name                          Short Descr (max 80)"
  stdscr.addnstr(1, 0, header, w-1, curses.A_UNDERLINE)
  visible = h - 4
  for i in range(visible):
    j = top + i
    if j >= len(items):
      break
    it = items[j]
    id_part = str(it['id'])[:12].ljust(12)
    name_part = (it['name'] or '')[:28].ljust(28)
    short_part = it['short']
    line = f"{id_part}  {name_part}  {short_part}"
    attr = curses.A_REVERSE if j == idx else curses.A_NORMAL
    stdscr.addnstr(2+i, 0, line, w-1, attr)
  footer = f"{len(items)} Kriterien. Enter: Analyse anzeigen, q: beenden"
  stdscr.addnstr(h-1, 0, footer, w-1, curses.A_DIM)
  stdscr.refresh()


def parse_llm_output(analysis: Any) -> List[Dict[str, Any]]:
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
  return rel_list


def show_results(stdscr, crit: Dict[str, Any]):
  stdscr.clear()
  h, w = stdscr.getmaxyx()
  # Pre-draw message while LLM runs
  stdscr.addnstr(0, 0, f"Analyse läuft für ID {crit['id']} – bitte warten…", w-1, curses.A_BOLD)
  # Placeholder lines requested by user
  stdscr.addnstr(1, 0, "Begründung: …", w-1)
  stdscr.addnstr(2, 0, "Gefundene Dokumente: …", w-1)
  stdscr.refresh()
  # Run LLM
  analysis = llm_find_relevant_documents(crit['desc_full'], Projektinfo, BieterDokumente, include_content=False, max_docs=20, max_chars_total=20000)
  rel_list = parse_llm_output(analysis)

  # Try to parse a summary/justification if provided by the model
  parsed: Dict[str, Any] = analysis if isinstance(analysis, dict) else {}
  if not parsed and isinstance(analysis, str):
    try:
      parsed = json.loads(analysis)
    except Exception:
      parsed = {}
  summary = parsed.get('zusammenfassung') or parsed.get('summary') or ''

  # Build a map filename -> meta for quick lookup to display meta fields
  doc_meta_map: Dict[str, Dict[str, Any]] = {}
  try:
    for d in _extract_docs_from_listing(BieterDokumente):
      nm = d.get('name') or d.get('filename') or d.get('file')
      if nm:
        meta = d.get('meta') or {}
        if isinstance(meta, dict):
          doc_meta_map[nm] = meta
  except Exception:
    pass

  # Interactive results view with selection and evaluation
  sel_idx = 0
  while True:
    stdscr.clear()
    y = 0
    stdscr.addnstr(y, 0, f"Ergebnis – Kriterium {crit['id']}: {crit['name']}", w-1, curses.A_BOLD); y += 1
    # Wrap the long description for display
    long_desc = crit.get('beschreibung') or crit.get('anforderung') or ''
    for line in textwrap.wrap(long_desc, width=max(20, w-2)):
      stdscr.addnstr(y, 0, line, w-1); y += 1
    y += 1
    # Show Begründung (summary) if available
    stdscr.addnstr(y, 0, "Begründung:", w-1, curses.A_UNDERLINE); y += 1
    if summary:
      for line in textwrap.wrap(str(summary), width=max(20, w-2)):
        if y >= h-3:
          break
        stdscr.addnstr(y, 0, line, w-1); y += 1
    else:
      stdscr.addnstr(y, 0, "(keine Zusammenfassung vom Modell)", w-1); y += 1
    y += 1
    stdscr.addnstr(y, 0, "Gefundene Dokumente:", w-1, curses.A_UNDERLINE); y += 1
    list_start_y = y
    if rel_list:
      for i, item in enumerate(rel_list):
        if y >= h-2:
          break
        fname = item.get('filename') or '(unbekannt)'
        rel = item.get('relevance') if item.get('relevance') is not None else item.get('score')
        rel_str = f"{rel:.2f}" if isinstance(rel, (int,float)) else str(rel)
        meta = doc_meta_map.get(fname, {}) if isinstance(doc_meta_map, dict) else {}
        m_name = str(meta.get('name') or '') if isinstance(meta, dict) else ''
        m_kat = str(meta.get('kategorie') or meta.get('category') or '') if isinstance(meta, dict) else ''
        m_begr = str(meta.get('begründung') or meta.get('begruendung') or meta.get('reason') or '') if isinstance(meta, dict) else ''
        meta_parts = []
        if m_name:
          meta_parts.append(m_name)
        if m_kat:
          meta_parts.append(f"Kat: {m_kat}")
        if m_begr:
          meta_parts.append(f"Grund: {m_begr}")
        meta_desc = " | ".join(meta_parts)
        line_txt = f"{i+1}. {fname}  relevance={rel_str}"
        if meta_desc:
          line_txt += f"  – {meta_desc}"
        attr = curses.A_REVERSE if i == sel_idx else curses.A_NORMAL
        stdscr.addnstr(y, 0, line_txt, w-1, attr); y += 1
    else:
      stdscr.addnstr(y, 0, "KEINE DOKUMENTE", w-1); y += 1
    stdscr.addnstr(h-1, 0, "↑/↓ wählen, b: bewerten, Enter/ESC/q: zurück", w-1, curses.A_DIM)
    stdscr.refresh()

    ch = stdscr.getch()
    if ch in (ord('q'), ord('Q'), 27, 10, 13):  # q/Q, ESC, Enter
      break
    elif ch in (curses.KEY_UP, 65):
      if rel_list:
        sel_idx = (sel_idx - 1) % len(rel_list)
    elif ch in (curses.KEY_DOWN, 66):
      if rel_list:
        sel_idx = (sel_idx + 1) % len(rel_list)
    elif ch in (ord('b'), ord('B')):
      if rel_list and 0 <= sel_idx < len(rel_list):
        fname = rel_list[sel_idx].get('filename')
        if fname:
          evaluate_and_show(stdscr, crit, fname)
    else:
      # ignore
      pass


def evaluate_and_show(stdscr, crit: Dict[str, Any], filename: str):
  """Read the selected document, ask the LLM to evaluate the criterion, and show the result."""
  stdscr.clear()
  h, w = stdscr.getmaxyx()
  stdscr.addnstr(0, 0, f"Bewertung läuft für {filename} …", w-1, curses.A_BOLD)
  stdscr.refresh()

  content = load_document_content(filename, max_chars=20000)
  # Build evaluation prompt
  crit_public = {
    'id': crit.get('id'),
    'name': crit.get('name'),
    'beschreibung': crit.get('beschreibung'),
    'anforderung': crit.get('anforderung'),
  }
  try:
    full = crit.get('desc_full') or {}
    docs_hint = full.get('dokumente') if isinstance(full, dict) else None
    if isinstance(docs_hint, list) and docs_hint:
      crit_public['dokumente'] = docs_hint
  except Exception:
    pass
  eval_context = {
    'projektbeschreibung': Projektinfo.strip(),
    'kriterium': crit_public,
    'dokument': {
      'filename': filename,
      'inhalt': content,
    }
  }
  user_payload = _json.dumps(eval_context, ensure_ascii=False, indent=2)
  system_prompt = (
    "Bewerte, ob das angegebene Dokument das Kriterium erfüllt.\n"
    "Vorgehen: Prüfe inhaltlich gegen die 'anforderung' bzw. 'beschreibung' des Kriteriums.\n"
    "Antworte NUR als JSON mit: { 'bewertung': ('erfüllt'|'teilweise erfüllt'|'nicht erfüllt'|'unbekannt'), 'begruendung': string }.\n"
    "Nutze kurze prägnante Begründung; keine zusätzlichen Felder. Sprache: Deutsch."
  )
  try:
    result = call_ai_model(system_prompt, user_payload, verbose=False, json_cleanup=True, task_type="kriterien")
  except Exception as e:
    result = { 'error': str(e) }

  # Parse simple result
  parsed: Dict[str, Any] = result if isinstance(result, dict) else {}
  if not parsed and isinstance(result, str):
    try:
      parsed = json.loads(result)
    except Exception:
      parsed = { 'raw': result }
  bewertung = parsed.get('bewertung') or parsed.get('ergebnis') or parsed.get('status') or '(unbekannt)'
  begr = parsed.get('begruendung') or parsed.get('begründung') or parsed.get('begruendung_text') or parsed.get('reason') or ''

  stdscr.clear()
  y = 0
  stdscr.addnstr(y, 0, f"Bewertung – {crit.get('id')}: {crit.get('name')} – Dok: {filename}", w-1, curses.A_BOLD); y += 1
  stdscr.addnstr(y, 0, f"Bewertung: {bewertung}", w-1); y += 1
  stdscr.addnstr(y, 0, "Begründung:", w-1, curses.A_UNDERLINE); y += 1
  if begr:
    for line in textwrap.wrap(str(begr), width=max(20, w-2)):
      if y >= h-2:
        break
      stdscr.addnstr(y, 0, line, w-1); y += 1
  else:
    stdscr.addnstr(y, 0, "(keine Begründung)", w-1); y += 1
  stdscr.addnstr(h-1, 0, "Taste drücken um zurückzukehren…", w-1, curses.A_DIM)
  stdscr.refresh()
  stdscr.getch()


def tui(stdscr, criteria: List[Dict[str, Any]]):
  curses.curs_set(0)
  stdscr.nodelay(False)
  idx = 0
  top = 0
  while True:
    h, w = stdscr.getmaxyx()
    visible = max(1, h - 4)
    if idx < top:
      top = idx
    elif idx >= top + visible:
      top = idx - visible + 1
    draw_list(stdscr, criteria, idx, top, Projekt, Bieter)
    ch = stdscr.getch()
    if ch in (ord('q'), ord('Q')):
      break
    elif ch in (curses.KEY_UP, 65):  # 65 sometimes for arrow up
      if idx > 0:
        idx -= 1
    elif ch in (curses.KEY_DOWN, 66):
      if idx < len(criteria) - 1:
        idx += 1
    elif ch in (curses.KEY_ENTER, 10, 13):
      if 0 <= idx < len(criteria):
        show_results(stdscr, criteria[idx])
    else:
      # ignore other keys
      pass


# ---------------- Main ----------------
ids_cycle = audit_info['ids']
if not ids_cycle:
  print("Keine Kriterien IDs vorhanden.")
else:
  criteria = build_criteria(ids_cycle)
  curses.wrapper(lambda stdscr: tui(stdscr, criteria))

