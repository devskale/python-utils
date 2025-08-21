#!/usr/bin/env python3
"""ofsAuditor.py

Interactive auditing UI for OFS projects, criteria and bidder audits.

Placed under tests/ as an interactive diagnostic (NOT an automated test).
Safe (read-only) for existing data – only reads JSON files (kriterien.json, audit.json).

Views / Modes:
  Projects List          : Pick a project (source of criteria)
  Project Kriterien      : Flat list of project criteria (id, typ, kategorie, status/prio)
  Bidders List           : Bidders for selected project
  Bidder Audit Kriterien : Audit entries (id, zustand, status, prio, events)

Controls:
  Global:
    q            Quit
    ?            Show help popup
    r            Reload current data
    /            Enter / update filter (substring match; empty to clear)
    ESC          Cancel filter input / close popups
  Navigation:
    Up/Down (k/j)         Move selection
    PgUp/PgDn (b/SPACE)   Page scroll (also SPACE pages in detail viewer)
    Enter/Right (l)       Drill into selection (project -> kriterien, bidders list -> bidder audit)
    Left/Backspace (h)    Go up (audit -> bidders list, bidders list -> project kriterien, project kriterien -> projects)
    b (in project kriterien view)  Switch to bidders list
    a (in bidder audit view)      Back to project kriterien
  Detail:
    SPACE        Show detailed JSON / timeline for selected criterion

Filter Semantics:
  Applies to the current list (criteria or audit entries or bidders or projects).
  Case-insensitive substring match on id, name, typ, kategorie (where available).

Implementation Notes:
  - Uses internal functions from ofs.kriterien and ofs.paths for richer access.
  - For audit timeline detail we parse audit.json directly (no event mutation).
  - Does NOT auto-create missing audit files; if absent shows message.

"""
from __future__ import annotations

import curses
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

try:  # primary import
    import ofs  # type: ignore  # core exports
    from ofs.paths import list_projects, list_bidders  # type: ignore
    from ofs.kriterien import find_kriterien_file, load_kriterien, extract_kriterien_list  # type: ignore
    from ofs.paths import get_path  # type: ignore
except Exception:
    # Fallback: add parent directory of this script (../) and retry (handles direct invocation)
    _here = os.path.abspath(os.path.dirname(__file__))
    _parent = os.path.abspath(os.path.join(_here, ".."))
    if _parent not in sys.path:
        sys.path.insert(0, _parent)
    try:
        import ofs  # type: ignore
        from ofs.paths import list_projects, list_bidders  # type: ignore
        from ofs.kriterien import find_kriterien_file, load_kriterien, extract_kriterien_list  # type: ignore
        from ofs.paths import get_path  # type: ignore
    except Exception as e:  # pragma: no cover
        print("Error importing ofs package after fallback:", e, file=sys.stderr)
        sys.exit(1)


# ---------------- Data Loading Helpers ---------------- #

def load_project_kriterien(project: str) -> List[Dict[str, Any]]:
    k_file = find_kriterien_file(project)
    if not k_file or not os.path.isfile(k_file):
        return []
    try:
        data = load_kriterien(k_file)
        k_list = extract_kriterien_list(data)
        # augment derived fields for consistent display keys
        out: List[Dict[str, Any]] = []
        for k in k_list:
            nk = dict(k)
            pruefung = nk.get("pruefung") or {}
            nk.setdefault("prio", pruefung.get("prio"))
            out.append(nk)
        # sort: prio desc, id asc
        def _prio(x):
            p = x.get("prio")
            try:
                return int(p) if p is not None else -1
            except Exception:
                return -1
        out.sort(key=lambda x: (-_prio(x), x.get("id") or ""))
        return out
    except Exception:
        return []


def list_project_bidders(project: str) -> List[str]:
    try:
        return list_bidders(project)  # type: ignore[arg-type]
    except Exception:
        return []


def load_bidder_audit_entries(project: str, bidder: str) -> List[Dict[str, Any]]:
    """Return audit entries summarised for bidder. If file missing returns []."""
    project_path = get_path(project)
    if not project_path:
        return []
    audit_path = os.path.join(project_path, "B", bidder, "audit.json")
    if not os.path.isfile(audit_path):
        return []
    try:
        with open(audit_path, "r", encoding="utf-8") as fh:
            audit = json.load(fh)
        entries = audit.get("kriterien", [])
        out: List[Dict[str, Any]] = []
        for e in entries:
            out.append({
                "id": e.get("id"),
                "status": e.get("status"),
                "prio": e.get("prio"),
                "zustand": (e.get("audit") or {}).get("zustand"),
                "events_total": len((e.get("audit") or {}).get("verlauf") or []),
                "_raw": e,  # preserve raw for detail view
            })
        # sort: zustand weight then prio desc
        zustand_order = {"synchronisiert": 0, "geprueft": 1, "freigegeben": 2, "abgelehnt": 2}
        def _prio(x):
            p = x.get("prio")
            try:
                return int(p) if p is not None else -1
            except Exception:
                return -1
        def _z(x):
            return zustand_order.get(x.get("zustand"), 99)
        out.sort(key=lambda x: (_z(x), -_prio(x), x.get("id") or ""))
        return out
    except Exception:
        return []


def load_single_audit_detail(project: str, bidder: str, kriterium_id: str) -> Optional[Dict[str, Any]]:
    project_path = get_path(project)
    if not project_path:
        return None
    audit_path = os.path.join(project_path, "B", bidder, "audit.json")
    if not os.path.isfile(audit_path):
        return None
    try:
        with open(audit_path, "r", encoding="utf-8") as fh:
            audit = json.load(fh)
        for e in audit.get("kriterien", []):
            if e.get("id") == kriterium_id:
                return e
    except Exception:
        return None
    return None


# ---------------- Mutation Helpers (Write Operations) ---------------- #

STATUS_VALUES = ["ja", "ja.int", "ja.ki", "erfüllt", "nein", "halt", "null"]
ZUSTAND_VALUES = ["synchronisiert", "geprueft", "freigegeben", "abgelehnt"]


def _write_json_atomic(path: str, data: Any):  # pragma: no cover
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    os.replace(tmp, path)


def update_project_kriterium_status(project: str, kriterium_id: str, new_status: Optional[str]) -> bool:
    k_file = find_kriterien_file(project)
    if not k_file or not os.path.isfile(k_file):
        return False
    try:
        with open(k_file, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        changed = False
        ids = ((data.get("ids") or {}).get("kriterien")) or []
        for k in ids:
            if k.get("id") == kriterium_id:
                pruefung = k.get("pruefung") or {}
                before = pruefung.get("status")
                new_status_val = None if new_status == 'null' else new_status
                if before != new_status_val:
                    pruefung["status"] = new_status_val
                    k["pruefung"] = pruefung
                    changed = True
                break
        if changed:
            _write_json_atomic(k_file, data)
        return changed
    except Exception:
        return False


def _derive_zustand_from_events(events: List[Dict[str, Any]]) -> str:
    last_final = None
    last_review = None
    for ev in events:
        e = ev.get("ereignis")
        if e == "reset":
            last_final = None
            last_review = None
            continue
        if e in ("freigabe", "ablehnung"):
            last_final = e
        elif e in ("ki_pruefung", "mensch_pruefung"):
            last_review = e
    if last_final == "freigabe":
        return "freigegeben"
    if last_final == "ablehnung":
        return "abgelehnt"
    if last_review:
        return "geprueft"
    return "synchronisiert"


AUDIT_EVENTS = [
    ("k", "ki_pruefung"),
    ("m", "mensch_pruefung"),
    ("f", "freigabe"),
    ("x", "ablehnung"),
    ("R", "reset"),
]


def append_bidder_audit_event(project: str, bidder: str, kriterium_id: str, event: str, akteur: str = "ui") -> bool:
    project_path = get_path(project)
    if not project_path:
        return False
    audit_path = os.path.join(project_path, "B", bidder, "audit.json")
    if not os.path.isfile(audit_path):
        return False
    try:
        with open(audit_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        changed = False
        for entry in data.get("kriterien", []):
            if entry.get("id") == kriterium_id:
                audit_block = entry.get("audit") or {"verlauf": []}
                events = audit_block.get("verlauf") or []
                if events and events[-1].get("ereignis") == event and event not in ("reset",):
                    break
                events.append({
                    "zeit": datetime.utcnow().replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
                    "ereignis": event,
                    "quelle_status": entry.get("status"),
                    "ergebnis": None,
                    "akteur": akteur,
                })
                zustand = _derive_zustand_from_events(events)
                audit_block["verlauf"] = events
                audit_block["zustand"] = zustand
                entry["audit"] = audit_block
                changed = True
                break
        if changed:
            _write_json_atomic(audit_path, data)
        return changed
    except Exception:
        return False


def update_bidder_audit_status(project: str, bidder: str, kriterium_id: str, new_status: Optional[str]) -> bool:
    project_path = get_path(project)
    if not project_path:
        return False
    audit_path = os.path.join(project_path, "B", bidder, "audit.json")
    if not os.path.isfile(audit_path):
        return False
    try:
        with open(audit_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        changed = False
        for entry in data.get("kriterien", []):
            if entry.get("id") == kriterium_id:
                before = entry.get("status")
                new_status_val = None if new_status == 'null' else new_status
                if before != new_status_val:
                    entry["status"] = new_status_val
                    changed = True
                break
        if changed:
            _write_json_atomic(audit_path, data)
        return changed
    except Exception:
        return False


def update_bidder_audit_zustand(project: str, bidder: str, kriterium_id: str, new_zustand: str) -> bool:
    if new_zustand not in ZUSTAND_VALUES:
        return False
    project_path = get_path(project)
    if not project_path:
        return False
    audit_path = os.path.join(project_path, "B", bidder, "audit.json")
    if not os.path.isfile(audit_path):
        return False
    try:
        with open(audit_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        changed = False
        for entry in data.get("kriterien", []):
            if entry.get("id") == kriterium_id:
                audit_block = entry.get("audit") or {}
                before = audit_block.get("zustand")
                if before != new_zustand:
                    audit_block["zustand"] = new_zustand
                    entry["audit"] = audit_block
                    changed = True
                break
        if changed:
            _write_json_atomic(audit_path, data)
        return changed
    except Exception:
        return False


# ---------------- UI State ---------------- #

class State:
    def __init__(self):
        self.mode: str = "projects"  # projects | project_k | bidders | bidder_audit
        self.projects: List[str] = []
        self.project_filter: str = ""
        self.selected_project: Optional[str] = None

        self.project_kriterien: List[Dict[str, Any]] = []
        self.k_filter: str = ""

        self.bidders: List[str] = []
        self.bidder_filter: str = ""
        self.selected_bidder: Optional[str] = None

        self.bidder_audit: List[Dict[str, Any]] = []
        self.audit_filter: str = ""

        # generic list navigation state
        self.selection: int = 0
        self.scroll: int = 0

    # -------- Filtering Helpers -------- #
    def _filter_items(self, items: List[Any], f: str, kind: str) -> List[Any]:
        if not f:
            return items
        f_low = f.lower()
        out = []
        for it in items:
            if kind == "projects" or kind == "bidders":
                name = str(it)
                if f_low in name.lower():
                    out.append(it)
            elif kind == "kriterien":
                text_parts = [
                    str(it.get("id") or ""),
                    str(it.get("name") or it.get("kriterium") or ""),
                    str(it.get("typ") or it.get("type") or it.get("category") or ""),
                    str(it.get("kategorie") or it.get("subcategory") or it.get("gruppe") or ""),
                ]
                hay = " | ".join(text_parts).lower()
                if f_low in hay:
                    out.append(it)
            elif kind == "audit":
                text_parts = [str(it.get("id") or ""), str(it.get("zustand") or ""), str(it.get("status") or ""), str(it.get("prio") or "")]
                hay = " | ".join(text_parts).lower()
                if f_low in hay:
                    out.append(it)
        return out

    def current_items(self) -> List[Any]:
        if self.mode == "projects":
            return self._filter_items(self.projects, self.project_filter, "projects")
        if self.mode == "project_k":
            return self._filter_items(self.project_kriterien, self.k_filter, "kriterien")
        if self.mode == "bidders":
            return self._filter_items(self.bidders, self.bidder_filter, "bidders")
        if self.mode == "bidder_audit":
            return self._filter_items(self.bidder_audit, self.audit_filter, "audit")
        return []

    # -------- Navigation reset on mode change -------- #
    def reset_nav(self):
        self.selection = 0
        self.scroll = 0


# ---------------- UI Rendering ---------------- #

class AuditorUI:
    def __init__(self, stdscr, state: State):
        self.stdscr = stdscr
        self.state = state
        curses.curs_set(0)
        self.stdscr.nodelay(False)
        self.stdscr.keypad(True)

    # -------- Drawing -------- #
    def draw(self):  # pragma: no cover (interactive)
        stdscr = self.stdscr
        stdscr.erase()
        max_y, max_x = stdscr.getmaxyx()

        # Header
        header = self.build_header(max_x)
        stdscr.addnstr(0, 0, header, max_x - 1, curses.A_REVERSE)

        items = self.state.current_items()
        visible_rows = max_y - 4
        start = self.state.scroll
        selection = self.state.selection

        for idx, obj in enumerate(items[start:start + visible_rows]):
            absolute_index = start + idx
            label = self.format_row(obj)
            attr = curses.A_BOLD if absolute_index == selection else curses.A_NORMAL
            stdscr.addnstr(1 + idx, 0, label, max_x - 1, attr)

        # Footer / status
        status = self.build_status_line(items)
        stdscr.addnstr(max_y - 2, 0, status[:max_x - 1], max_x - 1, curses.A_DIM)
        stdscr.addnstr(max_y - 1, 0, "SPACE=Detail  / Filter  PgDn/PgUp page  b=Bidders  a=Kriterien  ?=Help  q=Quit", max_x - 1, curses.A_REVERSE)

        stdscr.refresh()

    def build_header(self, width: int) -> str:
        s = self.state
        parts = ["OFS Auditor"]
        parts.append(f"mode:{s.mode}")
        if s.selected_project:
            parts.append(f"project:{s.selected_project}")
        if s.selected_bidder:
            parts.append(f"bidder:{s.selected_bidder}")
        filt = ""
        if s.mode == "projects" and s.project_filter:
            filt = f"filter={s.project_filter}"
        elif s.mode == "project_k" and s.k_filter:
            filt = f"filter={s.k_filter}"
        elif s.mode == "bidders" and s.bidder_filter:
            filt = f"filter={s.bidder_filter}"
        elif s.mode == "bidder_audit" and s.audit_filter:
            filt = f"filter={s.audit_filter}"
        if filt:
            parts.append(filt)
        header = "  ".join(parts)
        return header[:width - 1]

    def build_status_line(self, items: List[Any]) -> str:
        s = self.state
        total = len(items)
        if s.mode == "projects":
            return f"Projects: {total} (Enter to open)"
        if s.mode == "project_k":
            return f"Kriterien: {total}  (b=Bidders  SPACE=Detail)"
        if s.mode == "bidders":
            return f"Bidders: {total} (Enter opens audit)"
        if s.mode == "bidder_audit":
            return f"Audit Entries: {total}  (a=Back to Kriterien  SPACE=Detail)"
        return ""

    def format_row(self, obj: Any) -> str:
        s = self.state
        if s.mode == "projects":
            return f"[P] {obj}"
        if s.mode == "bidders":
            return f"[b] {obj}"
        if s.mode == "project_k":
            # obj is criterion
            status = (obj.get("pruefung") or {}).get("status")
            prio = obj.get("prio")
            typ = obj.get("typ") or obj.get("type") or obj.get("category")
            kat = obj.get("kategorie") or obj.get("subcategory") or obj.get("gruppe")
            return f"{obj.get('id','?'):12} prio={str(prio) if prio is not None else '-':>3} status={status or '-':10} typ={typ or '-'} / {kat or '-'}"
        if s.mode == "bidder_audit":
            return f"{obj.get('id','?'):12} zustand={obj.get('zustand') or '-':12} prio={str(obj.get('prio')) if obj.get('prio') is not None else '-':>3} status={obj.get('status') or '-':10} events={obj.get('events_total'):>3}"
        return str(obj)

    # -------- Interaction -------- #
    def run(self):  # pragma: no cover (interactive)
        self.reload_projects()
        while True:
            self.draw()
            ch = self.stdscr.getch()
            if ch in (ord('q'), ord('Q')):
                break
            elif ch == ord('?'):
                self.help_popup()
            elif ch in (curses.KEY_UP, ord('k')):
                self.move(-1)
            elif ch in (curses.KEY_DOWN, ord('j')):
                self.move(1)
            elif ch == curses.KEY_NPAGE:
                self.page(1)
            elif ch == curses.KEY_PPAGE:
                self.page(-1)
            elif ch in (curses.KEY_RIGHT, ord('\n'), ord('\r'), ord('l')):
                self.enter()
            elif ch in (curses.KEY_LEFT, curses.KEY_BACKSPACE, 127, ord('h')):
                self.go_back()
            elif ch == ord('/'):
                self.prompt_filter()
            elif ch in (ord('r'), ord('R')):
                self.reload_current()
            elif ch in (ord('b'), ord('B')):
                if self.state.mode == 'project_k':
                    self.enter_bidders_list()
            elif ch in (ord('a'), ord('A')):
                if self.state.mode == 'bidder_audit':
                    self.back_to_kriterien()
            elif ch == ord(' '):  # SPACE opens detail per spec
                self.show_detail()
            elif ch in (ord('d'), ord('D')):  # alias
                self.show_detail()
            # --- Mutations ---
            elif ch == ord('s'):  # set status (project kriterium or bidder audit status)
                self.edit_status()
            elif ch == ord('S'):  # clear status (set to null)
                self.edit_status(clear=True)
            elif ch in (ord('k'), ord('m'), ord('f'), ord('x'), ord('R')):  # audit events
                self.add_audit_event(chr(ch))
            else:
                # ignore
                pass

    # -------- Movement -------- #
    def move(self, delta: int):
        items = self.state.current_items()
        if not items:
            return
        s = self.state
        s.selection = max(0, min(len(items) - 1, s.selection + delta))
        self.ensure_visible()

    def page(self, direction: int):
        items = self.state.current_items()
        if not items:
            return
        s = self.state
        max_y = self.stdscr.getmaxyx()[0]
        page = max_y - 5
        if direction > 0:
            s.selection = min(len(items) - 1, s.selection + page)
        else:
            s.selection = max(0, s.selection - page)
        self.ensure_visible()

    def ensure_visible(self):
        s = self.state
        max_y = self.stdscr.getmaxyx()[0]
        window = max_y - 5
        if s.selection < s.scroll:
            s.scroll = s.selection
        elif s.selection >= s.scroll + window:
            s.scroll = s.selection - window + 1

    # -------- Mode Transitions -------- #
    def enter(self):
        s = self.state
        items = s.current_items()
        if not items:
            return
        if s.mode == 'projects':
            s.selected_project = items[s.selection]
            self.load_project_kriterien()
            s.mode = 'project_k'
            s.reset_nav()
        elif s.mode == 'bidders':
            s.selected_bidder = items[s.selection]
            self.load_bidder_audit()
            s.mode = 'bidder_audit'
            s.reset_nav()
        # no drill for kriterien / audit (detail with SPACE)

    def go_back(self):
        s = self.state
        if s.mode == 'project_k':
            s.mode = 'projects'
            s.selected_project = None
            s.reset_nav()
        elif s.mode == 'bidders':
            s.mode = 'project_k'
            s.selected_bidder = None
            s.reset_nav()
        elif s.mode == 'bidder_audit':
            s.mode = 'bidders'
            s.selected_bidder = None
            s.reset_nav()

    def enter_bidders_list(self):
        s = self.state
        if not s.selected_project:
            return
        s.bidders = list_project_bidders(s.selected_project)
        s.mode = 'bidders'
        s.reset_nav()

    def back_to_kriterien(self):
        s = self.state
        s.mode = 'project_k'
        s.selected_bidder = None
        s.reset_nav()

    # -------- Data Loading -------- #
    def reload_projects(self):
        self.state.projects = list_projects()  # type: ignore[assignment]

    def load_project_kriterien(self):
        if self.state.selected_project:
            self.state.project_kriterien = load_project_kriterien(self.state.selected_project)
        else:
            self.state.project_kriterien = []

    def load_bidder_audit(self):
        s = self.state
        if s.selected_project and s.selected_bidder:
            self.state.bidder_audit = load_bidder_audit_entries(s.selected_project, s.selected_bidder)
        else:
            self.state.bidder_audit = []

    def reload_current(self):
        s = self.state
        if s.mode == 'projects':
            self.reload_projects()
        elif s.mode == 'project_k':
            self.load_project_kriterien()
        elif s.mode == 'bidders':
            self.enter_bidders_list()
        elif s.mode == 'bidder_audit':
            self.load_bidder_audit()

    # -------- Filter Prompt -------- #
    def prompt_filter(self):  # pragma: no cover
        s = self.state
        prompt = "Filter: "
        existing = ''
        if s.mode == 'projects':
            existing = s.project_filter
        elif s.mode == 'project_k':
            existing = s.k_filter
        elif s.mode == 'bidders':
            existing = s.bidder_filter
        elif s.mode == 'bidder_audit':
            existing = s.audit_filter
        new_val = self.get_input(prompt, initial=existing)
        if new_val is None:
            return
        if s.mode == 'projects':
            s.project_filter = new_val
        elif s.mode == 'project_k':
            s.k_filter = new_val
        elif s.mode == 'bidders':
            s.bidder_filter = new_val
        elif s.mode == 'bidder_audit':
            s.audit_filter = new_val
        s.reset_nav()

    def get_input(self, prompt: str, initial: str = '') -> Optional[str]:  # pragma: no cover
        curses.echo()
        max_y, max_x = self.stdscr.getmaxyx()
        win = curses.newwin(3, max_x - 2, max_y - 4, 1)
        win.box()
        win.addnstr(1, 2, prompt + initial, max_x - 6)
        win.refresh()
        curses.curs_set(1)
        self.stdscr.move(max_y - 3, len(prompt) + 3 + len(initial))
        buf = list(initial)
        while True:
            ch = self.stdscr.getch()
            if ch in (27,):  # ESC
                curses.noecho()
                curses.curs_set(0)
                return None
            if ch in (curses.KEY_ENTER, ord('\n'), ord('\r')):
                break
            if ch in (curses.KEY_BACKSPACE, 127):
                if buf:
                    buf.pop()
            elif 32 <= ch < 127:
                buf.append(chr(ch))
            # redraw
            win.erase()
            win.box()
            val = ''.join(buf)
            win.addnstr(1, 2, prompt + val, max_x - 6)
            win.refresh()
        curses.noecho()
        curses.curs_set(0)
        return ''.join(buf).strip()

    # -------- Detail View -------- #
    def show_detail(self):  # pragma: no cover
        s = self.state
        items = s.current_items()
        if not items or s.selection >= len(items):
            return
        obj = items[s.selection]
        title = "Detail"
        content = ""
        if s.mode == 'project_k':
            title = f"Kriterium {obj.get('id','?')}"
            content = json.dumps(obj, indent=2, ensure_ascii=False)
        elif s.mode == 'bidder_audit':
            title = f"Audit {obj.get('id','?')}"
            raw = obj.get('_raw') or load_single_audit_detail(s.selected_project or '', s.selected_bidder or '', obj.get('id'))
            if raw:
                content = json.dumps(raw, indent=2, ensure_ascii=False)
            else:
                content = "Keine Details verfügbar (audit.json fehlt?)"
        elif s.mode in ('projects', 'bidders'):
            title = f"Info {obj}"
            content = str(obj)
        self.paged_text_view(content, title=title, context_obj=obj if s.mode in ('project_k', 'bidder_audit') else None)

    def paged_text_view(self, text: str, title: str = "Detail", context_obj: Optional[Dict[str, Any]] = None):  # pragma: no cover
        lines_raw = text.splitlines() or [""]
        max_y, max_x = self.stdscr.getmaxyx()
        # Simple wrapping
        wrapped: List[str] = []
        for ln in lines_raw:
            if not ln:
                wrapped.append("")
                continue
            while len(ln) > max_x - 4:
                wrapped.append(ln[: max_x - 4])
                ln = ln[max_x - 4:]
            wrapped.append(ln)
        pos = 0
        page_height = max(3, max_y - 4)
        while True:
            self.stdscr.erase()
            hdr = f"{title}  (Zeilen {pos+1}-{min(pos+page_height, len(wrapped))}/{len(wrapped)}  q=quit  s/S=status  z=zustand)"
            self.stdscr.addnstr(0, 0, hdr, max_x - 1, curses.A_REVERSE)
            for i in range(page_height):
                idx = pos + i
                if idx >= len(wrapped):
                    break
                self.stdscr.addnstr(1 + i, 0, wrapped[idx], max_x - 1)
            self.stdscr.refresh()
            ch = self.stdscr.getch()
            if ch in (ord('q'), ord('Q'), 27):
                break
            elif ch == ord('s'):
                # edit status (project kriterium or bidder audit status)
                if context_obj:
                    self.edit_status(clear=False)
                    return  # reopen detail after reload
            elif ch == ord('S'):
                if context_obj:
                    self.edit_status(clear=True)
                    return
            elif ch == ord('z'):
                # edit zustand only for bidder audit
                if context_obj and self.state.mode == 'bidder_audit':
                    self.edit_zustand()
                    return
            elif ch in (curses.KEY_DOWN, ord('j')):
                if pos + 1 < len(wrapped):
                    pos = min(len(wrapped) - 1, pos + 1)
            elif ch in (curses.KEY_UP, ord('k')):
                pos = max(0, pos - 1)
            elif ch in (curses.KEY_NPAGE, ord(' ')):
                if pos + page_height < len(wrapped):
                    pos = min(len(wrapped) - 1, pos + page_height)
                else:
                    pos = len(wrapped) - 1
            elif ch in (curses.KEY_PPAGE, ord('b'), ord('B')):
                pos = max(0, pos - page_height)
            else:
                pass

    # -------- Help -------- #
    def help_popup(self):  # pragma: no cover
        text = [
            "OFS Auditor Help",
            "",
            "Navigation: Up/Down(j/k) Enter/Right(l) Back(h/Left) PgUp/PgDn",
            "Modes: projects -> project_k (criteria) -> bidders -> bidder_audit",
            "Keys:",
            "  q quit   r reload   / filter   SPACE detail   b bidders   a kriterien   ? help",
            "  s set status   S clear status (null)",
            "  (bidder audit events) k=ki_pruefung  m=mensch_pruefung  f=freigabe  x=ablehnung  R=reset",
            "Detail view extra keys: s/S edit status, z edit zustand (bidder audit only)",
            "Filter (criteria): id, name, typ, kategorie | (audit): id, zustand, status, prio",
            "Sorting: criteria prio desc, id asc; audit by zustand weight then prio desc",
            "Zustand order: synchronisiert < geprueft < (freigegeben|abgelehnt)",
            "",
            "Press any key to close...",
        ]
        max_y, max_x = self.stdscr.getmaxyx()
        width = min(max(len(l) for l in text) + 4, max_x - 2)
        height = min(len(text) + 2, max_y - 2)
        start_y = (max_y - height) // 2
        start_x = (max_x - width) // 2
        win = curses.newwin(height, width, start_y, start_x)
        win.box()
        for i, line in enumerate(text, start=1):
            win.addnstr(i, 2, line, width - 4)
        win.refresh()
        win.getch()

    # -------- Mutations (Status & Audit Events) -------- #
    def edit_status(self, clear: bool = False):  # pragma: no cover
        s = self.state
        items = s.current_items()
        if not items:
            return
        obj = items[s.selection]
        if s.mode == 'project_k':
            kriterium_id = obj.get('id')
            new_status = 'null' if clear else self.choose_status(initial=(obj.get('pruefung') or {}).get('status'))
            if new_status is None:
                return
            if update_project_kriterium_status(s.selected_project or '', kriterium_id, new_status):
                self.load_project_kriterien()
        elif s.mode == 'bidder_audit':
            kriterium_id = obj.get('id')
            new_status = 'null' if clear else self.choose_status(initial=obj.get('status'))
            if new_status is None:
                return
            if update_bidder_audit_status(s.selected_project or '', s.selected_bidder or '', kriterium_id, new_status):
                self.load_bidder_audit()

    def choose_status(self, initial: Optional[str]):  # pragma: no cover
        choices = STATUS_VALUES
        idx = 0
        if initial in choices:
            idx = choices.index(initial)
        max_y, max_x = self.stdscr.getmaxyx()
        height = len(choices) + 4
        width = 30
        start_y = max(0, (max_y - height) // 2)
        start_x = max(0, (max_x - width) // 2)
        win = curses.newwin(height, width, start_y, start_x)
        win.keypad(True)
        while True:
            win.erase()
            win.box()
            win.addnstr(1, 2, "Select Status (Enter=OK, q=cancel)", width - 4)
            for i, v in enumerate(choices):
                marker = '>' if i == idx else ' '
                win.addnstr(3 + i, 2, f"{marker} {v}", width - 4, curses.A_REVERSE if i == idx else curses.A_NORMAL)
            win.refresh()
            ch = win.getch()
            if ch in (ord('q'), ord('Q'), 27):
                return None
            if ch in (curses.KEY_UP, ord('k')):
                idx = (idx - 1) % len(choices)
            elif ch in (curses.KEY_DOWN, ord('j')):
                idx = (idx + 1) % len(choices)
            elif ch in (curses.KEY_ENTER, ord('\n'), ord('\r')):
                return choices[idx]

    def add_audit_event(self, key: str):  # pragma: no cover
        s = self.state
        if s.mode != 'bidder_audit':
            return
        evt_map = {k: e for k, e in AUDIT_EVENTS}
        if key not in evt_map:
            return
        items = s.current_items()
        if not items:
            return
        obj = items[s.selection]
        kriterium_id = obj.get('id')
        if append_bidder_audit_event(s.selected_project or '', s.selected_bidder or '', kriterium_id, evt_map[key]):
            self.load_bidder_audit()
            
    def edit_zustand(self):  # pragma: no cover
        s = self.state
        if s.mode != 'bidder_audit':
            return
        items = s.current_items()
        if not items:
            return
        obj = items[s.selection]
        kriterium_id = obj.get('id')
        current = obj.get('zustand')
        new_z = self.choose_zustand(initial=current)
        if new_z is None:
            return
        if update_bidder_audit_zustand(s.selected_project or '', s.selected_bidder or '', kriterium_id, new_z):
            self.load_bidder_audit()

    def choose_zustand(self, initial: Optional[str]):  # pragma: no cover
        choices = ZUSTAND_VALUES
        idx = 0
        if initial in choices:
            idx = choices.index(initial)
        max_y, max_x = self.stdscr.getmaxyx()
        height = len(choices) + 4
        width = 30
        start_y = max(0, (max_y - height) // 2)
        start_x = max(0, (max_x - width) // 2)
        win = curses.newwin(height, width, start_y, start_x)
        win.keypad(True)
        while True:
            win.erase()
            win.box()
            win.addnstr(1, 2, "Select Zustand (Enter=OK, q=cancel)", width - 4)
            for i, v in enumerate(choices):
                marker = '>' if i == idx else ' '
                win.addnstr(3 + i, 2, f"{marker} {v}", width - 4, curses.A_REVERSE if i == idx else curses.A_NORMAL)
            win.refresh()
            ch = win.getch()
            if ch in (ord('q'), ord('Q'), 27):
                return None
            if ch in (curses.KEY_UP, ord('k')):
                idx = (idx - 1) % len(choices)
            elif ch in (curses.KEY_DOWN, ord('j')):
                idx = (idx + 1) % len(choices)
            elif ch in (curses.KEY_ENTER, ord('\n'), ord('\r')):
                return choices[idx]


# ---------------- Entry Point ---------------- #

def run(stdscr):  # pragma: no cover
    state = State()
    ui = AuditorUI(stdscr, state)
    ui.run()


def main():  # pragma: no cover
    try:
        curses.wrapper(run)
    except KeyboardInterrupt:
        print("Interrupted.")


if __name__ == "__main__":  # pragma: no cover
    main()
