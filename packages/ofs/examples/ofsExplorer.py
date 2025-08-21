#!/usr/bin/env python3
"""ofsExplorer.py

Interactive terminal explorer for an Opinionated Filesystem (OFS) tree using
`ofs.api` / `ofs` functions. This is a **read-only demo** showcasing how to
consume the programmatic API and navigate projects, bidders, and documents.

Controls:
  Up / Down          Move selection in current list
  Right / Enter      Drill into selected node (project / A / B / bidder). If a document: show info popup
  Left / Backspace   Go up one level
  r                  Reload (re-scan) the tree from disk
  i                  Show info panel for current item
  q                  Quit

Display semantics:
  [P] <project>          Project folder
  [A] (A directory)      Tender documents directory
  [B] (B directory)      Bidders directory container
  [D] <filename>         Document under A or bidder
  [b] <bidder>           Bidder folder under B

This script deliberately avoids any write operations and is safe to run against
production directories.

Note: Curses UI; if your terminal does not properly render, ensure it supports
basic ANSI control sequences. Resize is handled best-effort.
"""
from __future__ import annotations

import curses
import os
import sys
from typing import Any, Dict, List, Optional

try:
    import ofs  # noqa: F401 (ensures package import works)
    from ofs import generate_tree_structure, read_doc
except Exception as e:  # pragma: no cover
    print("Error: could not import ofs package:", e, file=sys.stderr)
    sys.exit(1)


# --------------------------- Data Model Helpers --------------------------- #

def build_navigation_model(directories_only: bool = False) -> Dict[str, Any]:
    """Return a normalized navigation tree based on `generate_tree_structure`.

    Structure (normalized):
    {
      'base_dir': str,
      'projects': [
         { 'kind': 'project', 'name': ..., 'path': ..., 'children': [
             { 'kind': 'A', 'name': 'A', 'path': ..., 'children': [ doc nodes ] },
             { 'kind': 'B', 'name': 'B', 'path': ..., 'children': [ bidder nodes ] }
         ] }
      ]
    }
    Document node: { 'kind': 'document', 'name': fname, 'path': path, 'size': int, 'type': ext }
    Bidder node: { 'kind': 'bidder', 'name': bidder, 'path': path, 'children': [ doc nodes ] }
    """
    raw = generate_tree_structure(directories_only=directories_only)
    norm: Dict[str, Any] = {"base_dir": raw.get("base_dir"), "projects": []}

    for project in raw.get("projects", []):
        pnode = {
            "kind": "project",
            "name": project.get("name"),
            "path": project.get("path"),
            "children": []
        }
        for directory in project.get("directories", []):
            if directory.get("name") == "A":
                a_children: List[Dict[str, Any]] = []
                for doc in (directory.get("documents") or []):
                    a_children.append({
                        "kind": "document",
                        "name": doc.get("name"),
                        "path": doc.get("path"),
                        "size": doc.get("size"),
                        "type": doc.get("type"),
                    })
                pnode["children"].append({
                    "kind": "A",
                    "name": "A",
                    "path": directory.get("path"),
                    "children": a_children,
                })
            elif directory.get("name") == "B":
                b_children: List[Dict[str, Any]] = []
                for bidder in directory.get("bidders", []):
                    bidder_docs: List[Dict[str, Any]] = []
                    for doc in (bidder.get("documents") or []):
                        bidder_docs.append({
                            "kind": "document",
                            "name": doc.get("name"),
                            "path": doc.get("path"),
                            "size": doc.get("size"),
                            "type": doc.get("type"),
                        })
                    b_children.append({
                        "kind": "bidder",
                        "name": bidder.get("name"),
                        "path": bidder.get("path"),
                        "children": bidder_docs,
                    })
                pnode["children"].append({
                    "kind": "B",
                    "name": "B",
                    "path": directory.get("path"),
                    "children": b_children,
                })
        norm["projects"].append(pnode)
    return norm


# --------------------------- UI Rendering Logic --------------------------- #

class Navigator:
    def __init__(self):
        self.tree = build_navigation_model(directories_only=False)
        # Stack elements: (list_ref, index) where list_ref is current node list
        self.stack: List[Dict[str, Any]] = []  # nodes leading to current list
        self.current_list: List[Dict[str, Any]] = self.tree["projects"]
        self.selection: int = 0
        self.scroll: int = 0

    # --------------- Data / State Helpers --------------- #
    def reload(self):
        base_path = self.current_path()
        self.tree = build_navigation_model(directories_only=False)
        # Reset to root for simplicity after reload
        self.stack = []
        self.current_list = self.tree["projects"]
        self.selection = 0
        self.scroll = 0
        return base_path

    def current_node(self) -> Optional[Dict[str, Any]]:
        if 0 <= self.selection < len(self.current_list):
            return self.current_list[self.selection]
        return None

    def current_path(self) -> str:
        parts = [self.tree.get("base_dir", "")] + [n.get("name") for n in self.stack]
        return os.path.join(*[p for p in parts if p])

    # --------------- Navigation --------------- #
    def enter(self):
        node = self.current_node()
        if not node:
            return ""
        if node.get("kind") in {"project", "A", "B", "bidder"}:
            children = node.get("children") or []
            if children:
                self.stack.append(node)
                self.current_list = children
                self.selection = 0
                self.scroll = 0
                return f"Entered {node.get('name')}"
            return f"(no children)"
        elif node.get("kind") == "document":
            # Show minimal doc info (handled by caller -> info popup)
            return f"Document: {node.get('name')}"
        return ""

    # --------------- Identifier Derivation --------------- #
    def derive_identifier(self, node: Dict[str, Any]) -> Optional[str]:
        """Build read-doc identifier (Project@Filename or Project@Bidder@Filename) from path.

        Returns None if path structure not recognized.
        """
        if node.get("kind") != "document":
            return None
        base_dir = os.path.abspath(self.tree.get("base_dir", ""))
        path = os.path.abspath(node.get("path", ""))
        if not path.startswith(base_dir):
            return None
        rel = os.path.relpath(path, base_dir)
        parts = rel.split(os.sep)
        if len(parts) < 2:
            return None
        project = parts[0]
        # Patterns:
        # project/A/file.ext  -> Project@file.ext
        # project/B/Bidder/file.ext -> Project@Bidder@file.ext
        if parts[1] == "A" and len(parts) >= 3:
            filename = parts[2]
            return f"{project}@{filename}"
        if parts[1] == "B" and len(parts) >= 4:
            bidder = parts[2]
            filename = parts[3]
            return f"{project}@{bidder}@{filename}"
        # Fallback: treat as project-level doc
        filename = parts[-1]
        return f"{project}@{filename}"

    # --------------- Document Preview --------------- #
    def preview_document(self, stdscr):  # pragma: no cover (interactive)
        node = self.current_node()
        if not node or node.get("kind") != "document":
            return
        identifier = self.derive_identifier(node)
        if not identifier:
            self._flash_message(stdscr, "Identifier konnte nicht abgeleitet werden")
            return
        try:
            result = read_doc(identifier)
        except Exception as e:  # noqa: BLE001
            # Graceful fallback: show minimal meta with error
            self._paged_text_view(
                stdscr,
                f"Fehler beim Lesen (Exception)\nID: {identifier}\nDatei: {node.get('path')}\nTyp: {node.get('type')}\n\n{e}",
                title="Lesefehler",
                allow_paging=False,
            )
            return
        if not result.get("success"):
            # Probably unsupported or unparsed file (e.g., image). Show summary instead of failing.
            err = result.get('error', '?')
            content_preview = result.get('content') or ''
            text = (
                "Nicht lesbar / keine Text-Extraktion verfügbar\n"
                f"ID: {identifier}\nDatei: {node.get('path')}\nTyp: {node.get('type')}\n"
                f"Fehler: {err}\n\n" + (content_preview[:400] if content_preview else "(kein Text)")
            )
            self._paged_text_view(stdscr, text, title="Kein Text", allow_paging=False)
            return
        content = result.get("content") or "(leer / keine extrahierte Inhalte)"
        # Heuristic: if content looks binary fallback
        if "\x00" in content[:200]:
            self._paged_text_view(
                stdscr,
                "Inhalt scheint binär oder nicht darstellbar zu sein. (Abbruch nach Heuristik)",
                title="Binär",
                allow_paging=False,
            )
            return
        self._paged_text_view(stdscr, content, title=node.get("name", "Dokument"))

    def _flash_message(self, stdscr, msg: str, duration_ms: int = 1200):  # pragma: no cover
        try:
            max_y, max_x = stdscr.getmaxyx()
            width = max(10, min(len(msg) + 4, max_x - 2))
            height = 3
            start_y = max(0, min(max_y - height, max_y // 2 - 1))
            start_x = max(0, min(max_x - width, (max_x - width) // 2))
            win = curses.newwin(height, width, start_y, start_x)
            win.box()
            win.addnstr(1, 2, msg, width - 4)
            win.refresh()
            curses.napms(duration_ms)
        except Exception:
            # Fallback: write on last line
            try:
                stdscr.addnstr(0, 0, msg[: stdscr.getmaxyx()[1] - 1], stdscr.getmaxyx()[1] - 1, curses.A_REVERSE)
                stdscr.refresh()
                curses.napms(duration_ms)
            except Exception:
                pass

    def _paged_text_view(self, stdscr, text: str, title: str = "Preview", allow_paging: bool = True):  # pragma: no cover
        lines_raw = text.splitlines() or [""]
        max_y, max_x = stdscr.getmaxyx()
        # Wrap lines respecting width
        wrapped: List[str] = []
        for ln in lines_raw:
            if not ln:
                wrapped.append("")
                continue
            while len(ln) > max_x - 4:
                wrapped.append(ln[: max_x - 4])
                ln = ln[max_x - 4 :]
            wrapped.append(ln)
        pos = 0
        page_height = max(3, max_y - 4)
        while True:
            stdscr.erase()
            header = f"{title}  (Zeilen {pos+1}-{min(pos+page_height, len(wrapped))}/{len(wrapped)}  q=quit)"
            if allow_paging:
                header += "  Pfeile/SPACE=scroll  b=up page"
            stdscr.addnstr(0, 0, header, max_x - 1, curses.A_REVERSE)
            for i in range(page_height):
                idx = pos + i
                if idx >= len(wrapped):
                    break
                stdscr.addnstr(1 + i, 0, wrapped[idx], max_x - 1)
            stdscr.refresh()
            ch = stdscr.getch()
            if ch in (ord('q'), ord('Q'), 27):
                break
            if not allow_paging:
                continue
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
            elif ch in (curses.KEY_RIGHT, curses.KEY_LEFT):
                # ignore in pager
                pass
            else:
                # any other key: continue loop
                pass

    def back(self):
        if not self.stack:
            return
        self.stack.pop()
        if not self.stack:
            self.current_list = self.tree["projects"]
        else:
            self.current_list = self.stack[-1].get("children") or []
        self.selection = 0
        self.scroll = 0

    def move(self, delta: int):
        n = len(self.current_list)
        if n == 0:
            return
        self.selection = max(0, min(n - 1, self.selection + delta))
        self.ensure_visible()

    def ensure_visible(self):
        height_window = self.visible_rows
        if self.selection < self.scroll:
            self.scroll = self.selection
        elif self.selection >= self.scroll + height_window:
            self.scroll = self.selection - height_window + 1

    # --------------- Drawing --------------- #
    def format_label(self, node: Dict[str, Any]) -> str:
        kind = node.get("kind")
        name = node.get("name")
        if kind == "project":
            return f"[P] {name}"
        if kind == "A":
            return "[A] Tender Docs"
        if kind == "B":
            return "[B] Bidders"
        if kind == "bidder":
            return f"[b] {name}"
        if kind == "document":
            return f"[D] {name}"
        return name or "?"

    def draw(self, stdscr):
        stdscr.erase()
        max_y, max_x = stdscr.getmaxyx()
        self.visible_rows = max_y - 4  # reserve lines for header & footer

        # Header
        base_dir = self.tree.get("base_dir", "<unknown>")
        path_parts = [n.get("name") for n in self.stack]
        breadcrumb = "/".join([p for p in path_parts]) or "<root>"
        header = f"OFS Explorer  base:{base_dir}  path:/{breadcrumb}  (q=quit, arrows navigate, enter/right=open, left/backspace=up, i=info, r=reload)"
        stdscr.addnstr(0, 0, header, max_x - 1, curses.A_REVERSE)

        # List window
        for idx, node in enumerate(self.current_list[self.scroll:self.scroll + self.visible_rows]):
            absolute_index = self.scroll + idx
            label = self.format_label(node)
            attr = curses.A_BOLD if absolute_index == self.selection else curses.A_NORMAL
            if node.get("kind") in {"project", "A", "B", "bidder"}:
                label = label + "/"  # indicate expandable
            stdscr.addnstr(1 + idx, 0, label, max_x - 1, attr)

        # Footer / status line
        node = self.current_node()
        if node:
            detail = self.describe_node(node)
        else:
            detail = "(empty)"
        stdscr.addnstr(max_y - 2, 0, detail[:max_x - 1], max_x - 1, curses.A_DIM)
        stdscr.refresh()

    def describe_node(self, node: Dict[str, Any]) -> str:
        k = node.get("kind")
        if k == "document":
            size = node.get("size")
            p = node.get("path")
            t = node.get("type")
            return f"Document: {node.get('name')}  type={t} size={size} path={p}"
        if k in {"project", "A", "B", "bidder"}:
            child_count = len(node.get("children") or [])
            return f"{k} {node.get('name')} children={child_count} path={node.get('path')}"
        return f"{k} {node.get('name')}"

    # --------------- Info Popup --------------- #
    def popup_info(self, stdscr):
        node = self.current_node()
        if not node:
            return
        lines = [
            "Node Information",
            "", self.describe_node(node),
            "", "Press any key to close."
        ]
        max_y, max_x = stdscr.getmaxyx()
        width = min(max(len(line) for line in lines) + 4, max_x - 2)
        height = min(len(lines) + 2, max_y - 2)
        start_y = (max_y - height) // 2
        start_x = (max_x - width) // 2
        win = curses.newwin(height, width, start_y, start_x)
        win.box()
        for i, line in enumerate(lines, start=1):
            win.addnstr(i, 2, line, width - 4)
        win.refresh()
        win.getch()


# --------------------------- Main Loop --------------------------- #

def run(stdscr):  # pragma: no cover (interactive)
    curses.curs_set(0)
    stdscr.nodelay(False)
    stdscr.keypad(True)

    nav = Navigator()

    while True:
        nav.draw(stdscr)
        ch = stdscr.getch()

        if ch in (ord('q'), ord('Q')):
            break
        elif ch in (curses.KEY_UP, ord('k')):
            nav.move(-1)
        elif ch in (curses.KEY_DOWN, ord('j')):
            nav.move(1)
        elif ch in (curses.KEY_RIGHT, ord('\n'), ord('\r'), ord('l')):
            msg = nav.enter()
            if msg.startswith("Document:"):
                nav.popup_info(stdscr)
        elif ch in (curses.KEY_LEFT, curses.KEY_BACKSPACE, 127, ord('h')):
            nav.back()
        elif ch == ord(' '):  # space for document preview
            nav.preview_document(stdscr)
        elif ch in (ord('i'), ord('I')):
            nav.popup_info(stdscr)
        elif ch in (ord('r'), ord('R')):
            nav.reload()
        else:
            # ignore unhandled keys
            pass


def main():  # pragma: no cover
    try:
        curses.wrapper(run)
    except KeyboardInterrupt:
        print("Interrupted.")


if __name__ == "__main__":  # pragma: no cover
    main()
