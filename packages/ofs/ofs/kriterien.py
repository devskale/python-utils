#!/usr/bin/env python3
"""
Backward-compatible kriterien module for OFS.

This module provides a set of functions expected by older callers
(e.g., `ofs.core`) while using a tolerant, unified internal extractor
that understands multiple JSON shapes (flat `kriterien` lists,
`ids` wrappers, `extractedCriteria` nested structures, repository-local
kriterien trees, ...).

Exports (backwards-compatible names):
- load_kriterien
- find_kriterien_file
- get_unproven_kriterien
- build_kriterien_tree
- get_kriterien_by_tag
- get_all_kriterien_tags
- format_kriterien_list
- format_kriterien_tree
- format_kriterien_tags
- format_kriterium_by_tag
- get_kriterien_pop_json
- get_kriterien_tree_json
- get_kriterien_tag_json
"""

from __future__ import annotations

import json
import os
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

# Import path helpers from the package
from .paths import get_path, get_ofs_root

Kriterium = Dict[str, Any]
KriterienList = List[Kriterium]


# --------------------
# Low-level helpers
# --------------------
def load_kriterien(file_path: str) -> Dict[str, Any]:
    """
    Read and parse a JSON kriterien file and return its content as a dict.

    This function keeps the legacy name used by other modules.
    """
    with open(file_path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _collect_repo_kriterien_candidates(project_name: str) -> List[str]:
    """
    Heuristic: look under repository-local "kriterien/" directory for matching folders.
    """
    candidates: List[str] = []
    try:
        repo_root = os.path.abspath(os.getcwd())
        repo_k_root = os.path.join(repo_root, "kriterien")
        if os.path.isdir(repo_k_root):
            # direct folder tries
            candidates.append(os.path.join(repo_k_root, project_name))
            candidates.append(os.path.join(repo_k_root, project_name.lower()))
            candidates.append(os.path.join(repo_k_root, project_name.replace(" ", "_")))
            candidates.append(os.path.join(repo_k_root, project_name.replace(" ", "-")))
            # fuzzy matches
            for entry in os.listdir(repo_k_root):
                entry_path = os.path.join(repo_k_root, entry)
                if os.path.isdir(entry_path):
                    if entry.lower() in project_name.lower() or project_name.lower() in entry.lower():
                        candidates.append(entry_path)
    except Exception:
        # best-effort heuristic, ignore problems
        pass
    return candidates


def find_kriterien_file(project_name: str) -> Optional[str]:
    """
    Find a kriterien JSON file for the given project name.

    Tries several locations, returning the first matching file path:
    - path / file returned by get_path(project_name)
    - common filenames inside candidate project folders under the OFS root
    - repository-local kriterien/* candidates
    """
    try:
        ofs_root = get_ofs_root()
        project_hint = get_path(project_name)
        candidates: List[str] = []

        # If get_path returned an absolute path, use it
        if project_hint:
            if os.path.isabs(project_hint):
                candidates.append(project_hint)
            else:
                # try the hint as-is (may include ".dir/...")
                candidates.append(project_hint)
                if ofs_root:
                    candidates.append(os.path.join(ofs_root, project_hint))
                    candidates.append(os.path.join(ofs_root, project_name))
                    candidates.append(os.path.join(ofs_root, ".dir", project_name))

        # Add repo-local heuristics
        candidates.extend(_collect_repo_kriterien_candidates(project_name))

        # Normalize and dedupe while preserving order
        seen = set()
        normalized: List[str] = []
        for c in candidates:
            if not c:
                continue
            # keep as given (may be file or directory)
            if c not in seen:
                normalized.append(c)
                seen.add(c)

        # For each candidate, if it's a file and JSON -> return
        # If it's a dir -> look for common filenames and any file with 'kriterien' in its name.
        common_filenames = [
            "projekt.json",
            "audit.json",
            os.path.join("kriterien", "projekt.json"),
            os.path.join("kriterien", "audit.json"),
            os.path.join("A", "projekt.json"),
            os.path.join("A", "audit.json"),
            "projekt.all.json",
            "audit.all.json",
            os.path.join("kriterien", "projekt.all.json"),
            os.path.join("kriterien", "audit.all.json"),
        ]

        for candidate in normalized:
            # If candidate points directly to a file
            if os.path.isfile(candidate) and candidate.lower().endswith(".json"):
                return os.path.abspath(candidate)

            if not os.path.isdir(candidate):
                continue

            # check explicit common filenames
            for fn in common_filenames:
                p = os.path.join(candidate, fn)
                if os.path.isfile(p):
                    return os.path.abspath(p)

        # nothing found
        return None
    except Exception:
        return None


# --------------------
# Unified extractor
# --------------------
def _flatten_extracted_criteria(extracted: Dict[str, Any]) -> KriterienList:
    """
    Flatten an 'extractedCriteria' nested structure into a flat list of kriterium dicts.
    """
    out: KriterienList = []
    for cat_name, cat_val in extracted.items():
        if isinstance(cat_val, dict):
            for sub_name, sub_list in cat_val.items():
                if isinstance(sub_list, list):
                    for item in sub_list:
                        if isinstance(item, dict):
                            enhanced = item.copy()
                            enhanced.setdefault("category", cat_name)
                            enhanced.setdefault("subcategory", sub_name)
                            out.append(enhanced)
        elif isinstance(cat_val, list):
            for item in cat_val:
                if isinstance(item, dict):
                    enhanced = item.copy()
                    enhanced.setdefault("category", cat_name)
                    enhanced.setdefault("subcategory", "General")
                    out.append(enhanced)
    return out


def extract_kriterien_list(data: Dict[str, Any]) -> KriterienList:
    """
    Return a unified flat list of kriterium dicts by searching the entire JSON
    structure for a node named "kriterien" that holds a list.

    Behavior:
    - Recursively search dictionaries and lists to find the first occurrence
      of a key "kriterien" whose value is a list. If found, return that list.
    - Also accept the common wrapper shapes encountered before (ids.kriterien,
      ids.extractedCriteria, top-level extractedCriteria).
    - If no explicit "kriterien" key is found anywhere, fall back to the older
      heuristics (ids.kriterien, extractedCriteria, or plausible list detection).
    """
    if not isinstance(data, (dict, list)):
        return []

    # Recursive search for any "kriterien" list anywhere in the structure
    def _find_kriterien_node(obj: Any) -> Optional[KriterienList]:
        if isinstance(obj, dict):
            # direct hit: 'kriterien' key with list value
            if 'kriterien' in obj and isinstance(obj['kriterien'], list):
                return obj['kriterien']
            # ids wrapper direct in this dict
            if 'ids' in obj and isinstance(obj['ids'], dict):
                ids_obj = obj['ids']
                if isinstance(ids_obj.get('kriterien'), list):
                    return ids_obj['kriterien']
                if isinstance(ids_obj.get('extractedCriteria'), dict):
                    return _flatten_extracted_criteria(ids_obj['extractedCriteria'])
            # extractedCriteria direct in this dict
            if isinstance(obj.get('extractedCriteria'), dict):
                return _flatten_extracted_criteria(obj['extractedCriteria'])
            # Recurse into values
            for v in obj.values():
                found = _find_kriterien_node(v)
                if found:
                    return found
        elif isinstance(obj, list):
            for item in obj:
                found = _find_kriterien_node(item)
                if found:
                    return found
        return None

    found = _find_kriterien_node(data)
    if found:
        return found

    # Backwards-compatible fallbacks (in case no explicit 'kriterien' key was present)
    # direct kriterien list at top-level
    if isinstance(data, dict):
        k = data.get("kriterien")
        if isinstance(k, list):
            return k

        ids = data.get("ids")
        if isinstance(ids, dict):
            k2 = ids.get("kriterien")
            if isinstance(k2, list):
                return k2
            if isinstance(ids.get("extractedCriteria"), dict):
                return _flatten_extracted_criteria(ids["extractedCriteria"])

        if isinstance(data.get("extractedCriteria"), dict):
            return _flatten_extracted_criteria(data["extractedCriteria"])

        # Heuristic: find first top-level list that looks like a kriterien list
        def looks_like_kriterien_list(lst: Any) -> bool:
            if not isinstance(lst, list) or not lst:
                return False
            first = lst[0]
            return isinstance(first, dict) and ("id" in first or "name" in first or "kriterium" in first)

        for key, val in data.items():
            if looks_like_kriterien_list(val):
                return val  # first plausible candidate

    return []


# --------------------
# Core helpers (operate on unified list)
# --------------------
def get_unproven_kriterien_from_list(kriterien: KriterienList) -> KriterienList:
    out: KriterienList = []
    for k in kriterien:
        pruefung = k.get("pruefung")
        if pruefung is None:
            out.append(k)
        else:
            status = pruefung.get("status")
            if status is None:
                out.append(k)
    return out


def build_kriterien_tree_from_list(kriterien: KriterienList) -> Dict[str, Dict[str, KriterienList]]:
    tree: Dict[str, Dict[str, KriterienList]] = defaultdict(lambda: defaultdict(list))
    for k in kriterien:
        typ = k.get("typ") or k.get("type") or k.get("category") or k.get("kategorie") or "General"
        kategorie = k.get("kategorie") or k.get("category") or k.get("subcategory") or k.get("gruppe") or "General"
        tree[str(typ)][str(kategorie)].append(k)
    # convert to regular dicts
    return {t: dict(tree[t]) for t in tree}


def get_kriterium_by_tag_from_list(kriterien: KriterienList, tag: str) -> Optional[Kriterium]:
    for k in kriterien:
        if k.get("id") == tag or k.get("tag") == tag:
            return k
    return None


def get_all_kriterien_tags_from_list(kriterien: KriterienList) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    for k in kriterien:
        tag_id = k.get("id") or k.get("tag")
        name = k.get("name") or k.get("kriterium") or k.get("bezeichnung") or ""
        if tag_id:
            out.append({"id": tag_id, "name": name})
    return out


# --------------------
# Backwards-compatible wrappers (names expected by core.py)
# --------------------
def get_unproven_kriterien(data: Dict[str, Any]) -> KriterienList:
    """
    Backwards-compatible wrapper: accepts loaded JSON data (file content).
    """
    k_list = extract_kriterien_list(data)
    return get_unproven_kriterien_from_list(k_list)


def build_kriterien_tree(data: Dict[str, Any]) -> Dict[str, Dict[str, KriterienList]]:
    k_list = extract_kriterien_list(data)
    return build_kriterien_tree_from_list(k_list)


def get_kriterien_by_tag(data: Dict[str, Any], tag_id: str) -> Optional[Kriterium]:
    k_list = extract_kriterien_list(data)
    return get_kriterium_by_tag_from_list(k_list, tag_id)


def get_all_kriterien_tags(data: Dict[str, Any]) -> List[Dict[str, str]]:
    k_list = extract_kriterien_list(data)
    return get_all_kriterien_tags_from_list(k_list)


# --------------------
# Formatters (string output)
# --------------------
def format_kriterien_list(kriterien: List[Dict[str, Any]],
                          limit: Optional[int] = None,
                          total_kriterien: int = 0,
                          proven_count: int = 0) -> str:
    if limit is not None:
        kriterien = kriterien[:limit]

    if not kriterien:
        return "No unproven criteria found."

    checked_num = proven_count
    total_num = total_kriterien

    output: List[str] = []
    output.append(f"\n{total_num - checked_num} von {total_num} Kriterien verbleiben zur Prüfung.")
    output.append("=" * 80)

    for i, kriterium in enumerate(kriterien, 1):
        output.append(f"{i:2d}. Complete Kriterium Data:")
        output.append("-" * 80)
        output.append(json.dumps(kriterium, indent=2, ensure_ascii=False))
        output.append("-" * 80)

    return "\n".join(output)


def format_kriterien_tree(data: Dict[str, Any]) -> str:
    """
    Human-friendly textual renderer that takes raw JSON data (file content).
    """
    k_list = extract_kriterien_list(data)
    tree = build_kriterien_tree_from_list(k_list)
    lines: List[str] = []
    lines.append("\nKriterien Tree (sorted by Typ and Kategorie):")
    lines.append("=" * 80)

    for typ in sorted(tree.keys()):
        lines.append(f"\n📁 Typ: {typ}")
        lines.append("-" * 40)
        for kategorie in sorted(tree[typ].keys()):
            kriterien_list = tree[typ][kategorie]
            unproven_count = sum(1 for k in kriterien_list if (k.get("pruefung") or {}).get("status") is None)
            proven_count = len(kriterien_list) - unproven_count

            lines.append(f"  📂 Kategorie: {kategorie}")
            lines.append(f"     Total: {len(kriterien_list)}, Unproven: {unproven_count}, Proven: {proven_count}")

            unproven_in_cat = [k for k in kriterien_list if (k.get("pruefung") or {}).get("status") is None]
            if unproven_in_cat:
                lines.append(f"     Unproven criteria:")
                for kriterium in unproven_in_cat:
                    lines.append(f"       • {kriterium.get('id','?')}: {kriterium.get('name', kriterium.get('kriterium','(no name)'))}")
            lines.append("")
    return "\n".join(lines)


def format_kriterien_tags(data: Dict[str, Any]) -> str:
    tags = get_all_kriterien_tags(data)
    if not tags:
        return "No criteria found in the data."

    output: List[str] = []
    output.append(f"\nAll available criterion tags ({len(tags)} total):")
    output.append("=" * 80)
    for tag in tags:
        output.append(f"  • {tag['id']}: {tag['name']}")
    output.append("=" * 80)
    return "\n".join(output)


def format_kriterium_by_tag(data: Dict[str, Any], tag_id: str) -> str:
    """
    Return a textual representation for a single criterion (or list available tags).
    This name is kept for backward compatibility (core.py expects format_kriterium_by_tag).
    """
    if not tag_id:
        return format_kriterien_tags(data)

    item = get_kriterien_by_tag(data, tag_id)
    if item:
        output: List[str] = []
        output.append(f"\nKriterium found: {tag_id}")
        output.append("=" * 80)
        output.append(json.dumps(item, indent=2, ensure_ascii=False))
        output.append("=" * 80)
        return "\n".join(output)
    else:
        output: List[str] = []
        output.append(f"\nError: Kriterium with ID '{tag_id}' not found.")
        output.append("Available IDs:")
        tags = get_all_kriterien_tags(data)
        for tag in tags:
            output.append(f"  • {tag['id']}: {tag['name']}")
        return "\n".join(output)


# --------------------
# JSON API functions (used by CLI)
# --------------------
def get_kriterien_pop_json(project_name: str, limit: int = 1) -> Dict[str, Any]:
    try:
        k_file = find_kriterien_file(project_name)
        if not k_file:
            return {"error": f"No kriterien file found for project '{project_name}'", "project": project_name}
        data = load_kriterien(k_file)
        k_list = extract_kriterien_list(data)
        unproven = get_unproven_kriterien_from_list(k_list)
        total = len(k_list)
        proven_count = total - len(unproven)

        # Sort unproven criteria by priority ('prio') descending so highest priority appears first.
        # Support both 'pruefung.prio' and top-level 'prio' and default to 0 when missing.
        def _prio_key(k):
            try:
                return int((k.get("pruefung") or {}).get("prio") or k.get("prio") or 0)
            except Exception:
                return 0

        sorted_unproven = sorted(unproven, key=_prio_key, reverse=True)
        displayed = sorted_unproven[:limit] if limit is not None else sorted_unproven

        return {
            "project": project_name,
            "kriterien_file": k_file,
            "total_kriterien": total,
            "proven_count": proven_count,
            "unproven_count": len(unproven),
            "displayed_count": len(displayed),
            "limit": limit,
            "kriterien": displayed,
        }
    except Exception as e:
        return {"error": str(e), "project": project_name}


def get_kriterien_pop_json_bidder(project_name: str, bidder: str, limit: int = 1) -> Dict[str, Any]:
    """Return next unreviewed (zustand == synchronisiert) criteria for a bidder audit file.

    Definition bidder-level unproven/unreviewed:
      - audit.zustand == 'synchronisiert'
      - status != 'entfernt'

    Sorting: prio desc (None last) then id asc.
    """
    try:
        from .kriterien_sync import load_or_init_audit  # local import to avoid cycle
        project_path = get_path(project_name)
        if not project_path or not os.path.isdir(project_path):
            return {"error": f"Project '{project_name}' not found", "project": project_name, "bidder": bidder}
        audit = load_or_init_audit(project_path, bidder)
        entries = audit.get("kriterien", [])
        total = len(entries)
        # Filter synchronisiert & not entfernt
        unreviewed = [e for e in entries if e.get("audit", {}).get("zustand") == "synchronisiert" and e.get("status") != "entfernt"]

        def _sort_key(e: Dict[str, Any]):
            prio = e.get("prio")
            prio_key = prio if isinstance(prio, int) else -1
            return (-prio_key, e.get("id") or "")

        unreviewed_sorted = sorted(unreviewed, key=_sort_key)
        displayed = unreviewed_sorted[:limit] if limit is not None else unreviewed_sorted

        # Reduce entries to a stable public shape
        def _public(e: Dict[str, Any]):
            return {
                "id": e.get("id"),
                "status": e.get("status"),
                "prio": e.get("prio"),
                "zustand": e.get("audit", {}).get("zustand"),
            }

        return {
            "scope": "bidder",
            "project": project_name,
            "bidder": bidder,
            "total_kriterien": total,
            "unreviewed_count": len(unreviewed),
            "displayed_count": len(displayed),
            "limit": limit,
            "definition": "zustand == synchronisiert AND status != entfernt",
            "kriterien": [_public(e) for e in displayed],
        }
    except Exception as e:
        return {"error": str(e), "project": project_name, "bidder": bidder}


def get_kriterien_tree_json(project_name: str) -> Dict[str, Any]:
    try:
        k_file = find_kriterien_file(project_name)
        if not k_file:
            return {"error": f"No kriterien file found for project '{project_name}'", "project": project_name}
        data = load_kriterien(k_file)
        k_list = extract_kriterien_list(data)
        tree = build_kriterien_tree_from_list(k_list)
        unproven = get_unproven_kriterien_from_list(k_list)
        total = len(k_list)
        proven_count = total - len(unproven)

        tree_summary: Dict[str, Dict[str, Any]] = {}
        for typ, cats in tree.items():
            tree_summary[typ] = {}
            for cat, items in cats.items():
                unprov = [{"id": it.get("id"), "name": it.get("name") or it.get("kriterium")} for it in items if (it.get("pruefung") or {}).get("status") is None]
                proven_ct = len(items) - len(unprov)
                tree_summary[typ][cat] = {
                    "total": len(items),
                    "proven": proven_ct,
                    "unproven": len(unprov),
                    "unproven_kriterien": unprov,
                }

        return {
            "project": project_name,
            "kriterien_file": k_file,
            "total_kriterien": total,
            "proven_count": proven_count,
            "unproven_count": len(unproven),
            "tree": tree_summary,
        }
    except Exception as e:
        return {"error": str(e), "project": project_name}


def get_kriterien_tag_json(project_name: str, tag_id: Optional[str] = None) -> Dict[str, Any]:
    try:
        k_file = find_kriterien_file(project_name)
        if not k_file:
            return {"error": f"No kriterien file found for project '{project_name}'", "project": project_name}
        data = load_kriterien(k_file)
        k_list = extract_kriterien_list(data)
        if tag_id:
            item = get_kriterium_by_tag_from_list(k_list, tag_id)
            if item:
                return {"project": project_name, "kriterien_file": k_file, "tag_id": tag_id, "kriterium": item}
            else:
                return {"error": f"Kriterium with ID '{tag_id}' not found", "project": project_name, "tag_id": tag_id, "available_tags": get_all_kriterien_tags_from_list(k_list)}
        else:
            tags = get_all_kriterien_tags_from_list(k_list)
            return {"project": project_name, "kriterien_file": k_file, "total_tags": len(tags), "tags": tags}
    except Exception as e:
        return {"error": str(e), "project": project_name}


def get_kriterien_md(project_name: str) -> str:
    """
    Generate a markdown-formatted output of the criteria list organized by typ and kategorie.
    
    Args:
        project_name (str): Project name
        
    Returns:
        str: Markdown-formatted criteria list or error message
    """
    try:
        k_file = find_kriterien_file(project_name)
        if not k_file:
            return f"Error: No kriterien file found for project '{project_name}'"
        
        data = load_kriterien(k_file)
        k_list = extract_kriterien_list(data)
        
        if not k_list:
            return f"# Kriterien für {project_name}\n\nNo criteria found in the data."
        
        tree = build_kriterien_tree_from_list(k_list)
        unproven = get_unproven_kriterien_from_list(k_list)
        total = len(k_list)
        proven_count = total - len(unproven)
        
        lines: List[str] = []
        lines.append(f"# Kriterien für {project_name}")
        lines.append("")
        
        # Add project metadata from data
        meta_info = data.get('meta', {})
        if isinstance(meta_info, dict) and 'meta' in meta_info:
            project_meta = meta_info['meta']
            if 'auftraggeber' in project_meta:
                lines.append(f"**Auftraggeber:** {project_meta['auftraggeber']}")
            if 'aktenzeichen' in project_meta:
                lines.append(f"**Aktenzeichen:** {project_meta['aktenzeichen']}")
            
            # Add lose information
            if 'lose' in project_meta and isinstance(project_meta['lose'], list):
                lines.append("")
                lines.append("**Lose:**")
                for los in project_meta['lose']:
                    if isinstance(los, dict):
                        nummer = los.get('nummer', 'N/A')
                        bezeichnung = los.get('bezeichnung', 'N/A')
                        beschreibung = los.get('beschreibung', '')
                        bewertung = los.get('bewertungsprinzip', '')
                        lines.append(f"- {nummer}: {bezeichnung}")
                        if beschreibung:
                            lines.append(f"  - Beschreibung: {beschreibung}")
                        if bewertung:
                            lines.append(f"  - Bewertungsprinzip: {bewertung}")
        
        lines.append("")
        lines.append(f"**Status:** {proven_count} von {total} Kriterien geprüft ({len(unproven)} verbleibend)")
        lines.append(f"**Quelle:** `{k_file}`")
        lines.append("")
        
        # Generate table of contents
        lines.append("## Inhaltsverzeichnis")
        lines.append("")
        for typ in sorted(tree.keys()):
            lines.append(f"- [Typ: {typ}](#{typ.lower().replace(' ', '-')})")
            for kategorie in sorted(tree[typ].keys()):
                lines.append(f"  - [Kategorie: {kategorie}](#{kategorie.lower().replace(' ', '-')})")
        lines.append("")
        
        # Generate detailed sections
        for typ in sorted(tree.keys()):
            # Calculate total criteria count for this typ
            typ_total = sum(len(kriterien_list) for kriterien_list in tree[typ].values())
            lines.append(f"## Typ: {typ} ({typ_total})")
#            lines.append("")
            
            for kategorie in sorted(tree[typ].keys()):
                kriterien_list = tree[typ][kategorie]
                unproven_in_cat = [k for k in kriterien_list if (k.get("pruefung") or {}).get("status") is None]
                proven_in_cat = len(kriterien_list) - len(unproven_in_cat)
                
                lines.append(f"   {kategorie} ({len(kriterien_list)}):")
#                lines.append("")
#                lines.append(f"**Status:** {proven_in_cat} von {len(kriterien_list)} geprüft")
#                lines.append("")
                
                # Sort criteria by ID for consistent output
                sorted_kriterien = sorted(kriterien_list, key=lambda k: k.get('id', ''))
                
                for kriterium in sorted_kriterien:
                    k_id = kriterium.get('id', 'N/A')
                    k_name = kriterium.get('name') or kriterium.get('kriterium') or kriterium.get('bezeichnung') or kriterium.get('anforderung', '(Kein Name)')
                    
                    # Determine status
                    pruefung = kriterium.get('pruefung', {})
                    status = pruefung.get('status')
                    prio = pruefung.get('prio') or kriterium.get('prio')
                    
                    if status is None:
                        status_icon = "❓"
                        status_text = "Ungeprüft"
                    elif status == "erfuellt":
                        status_icon = "✅"
                        status_text = "Erfüllt"
                    elif status == "nicht_erfuellt":
                        status_icon = "❌"
                        status_text = "Nicht erfüllt"
                    elif status == "teilweise_erfuellt":
                        status_icon = "⚠️"
                        status_text = "Teilweise erfüllt"
                    else:
                        status_icon = "❓"
                        status_text = f"Status: {status}"
                    
                    # Priority indicator
                    prio_text = ""
                    if prio:
                        if isinstance(prio, int) and prio > 0:
                            prio_text = f" (Priorität: {prio})"
                    
                    lines.append(f"      {k_id} | {k_name} ")
 #                   lines.append("")
 #                   lines.append(f"**Status:** {status_text}{prio_text}")
                    
                    # Add requirement/description if available
                    anforderung = kriterium.get('anforderung')
                    beschreibung = kriterium.get('beschreibung') or kriterium.get('description')
#                    if anforderung:
#                        lines.append(f"**Anforderung:** {anforderung}")
#                    elif beschreibung:
#                        lines.append(f"**Beschreibung:** {beschreibung}")
                    
                    # Add additional fields if available
#                    if 'schwellenwert' in kriterium and kriterium['schwellenwert']:
#                        lines.append(f"**Schwellenwert:** {kriterium['schwellenwert']}")
                    
#                    if 'gewichtung_punkte' in kriterium and kriterium['gewichtung_punkte']:
#                        lines.append(f"**Gewichtung:** {kriterium['gewichtung_punkte']} Punkte")
                    
#                    if 'geltung_lose' in kriterium and kriterium['geltung_lose']:
#                        lose_text = ', '.join(kriterium['geltung_lose'])
#                        lines.append(f"**Geltung Lose:** {lose_text}")
                    
#                    if 'quelle' in kriterium and kriterium['quelle']:
#                        lines.append(f"**Quelle:** {kriterium['quelle']}")
                    
                    # Add proof information if available
#                    if pruefung:
#                        if 'datum' in pruefung and pruefung['datum']:
#                            lines.append(f"**Prüfdatum:** {pruefung['datum']}")
#                        if 'bemerkung' in pruefung and pruefung['bemerkung']:
#                            lines.append(f"**Bemerkung:** {pruefung['bemerkung']}")
#                        if 'pruefer' in pruefung and pruefung['pruefer']:
#                            lines.append(f"**Prüfer:** {pruefung['pruefer']}")
                    
#                    lines.append("")
                
#                lines.append("---")
#                lines.append("")
        
        return "\n".join(lines)
        
    except Exception as e:
        return f"Error: {str(e)}"


# Provide legacy aliases for any callers expecting different names (defensive)
# These simply map to the functions above.
find_kriterien_file = find_kriterien_file
load_kriterien = load_kriterien
get_unproven_kriterien = get_unproven_kriterien
build_kriterien_tree = build_kriterien_tree
get_kriterien_by_tag = get_kriterien_by_tag
get_all_kriterien_tags = get_all_kriterien_tags
format_kriterien_list = format_kriterien_list
format_kriterien_tree = format_kriterien_tree
format_kriterien_tags = format_kriterien_tags
format_kriterium_by_tag = format_kriterium_by_tag
get_kriterien_pop_json = get_kriterien_pop_json
get_kriterien_pop_json_bidder = get_kriterien_pop_json_bidder
get_kriterien_tree_json = get_kriterien_tree_json
get_kriterien_tag_json = get_kriterien_tag_json
get_kriterien_md = get_kriterien_md
