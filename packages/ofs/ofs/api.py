"""High-level programmatic API wrappers mirroring selected OFS CLI commands.

These functions provide a stable import surface so users can call the same
operations that the CLI exposes without scraping CLI handlers or duplicating
logic. Each function returns structured Python data (dicts / lists) instead
of printing to stdout, raising exceptions on hard errors.

Currently covered domains:
- Kriterien Synchronisation (kriterien-sync)
- Kriterien Audit Event Append / Show (kriterien-audit)
- Index management helpers delegate to underlying exported functions directly

Design principles:
- Pure functions (no prints) – caller decides how to render
- Return value contracts documented in docstrings
- Reuse existing lower-level helpers (no duplication of parsing logic)
"""
from __future__ import annotations

from typing import Optional, Dict, Any, List
import os

from .core import get_path, list_bidders
from .kriterien import (
    find_kriterien_file,
    get_kriterien_pop_json_bidder,
    get_kriterien_pop_json,
)
from .kriterien_sync import (
    load_kriterien_source,
    load_or_init_audit,
    reconcile_full,
    write_audit_if_changed,
    append_event,
)

# ---------------------------------------------------------------------------
# Kriterien Sync
# ---------------------------------------------------------------------------

def kriterien_sync(project: str, bidder: Optional[str] = None) -> Dict[str, Any]:
    """Synchronize project criteria into bidder audit file(s).

    Args:
        project: Project name (AUSSCHREIBUNGNAME)
        bidder: Optional bidder name. If omitted, all bidders are processed.

    Returns:
        Dict with summary: {
          'project': str,
          'mode': 'single'|'all',
          'count_bidders': int,
          'results': [ { 'bidder': str, 'created': int, 'updated': int,
                         'removed': int, 'unchanged': int,
                         'wrote_file': bool, 'total_entries': int } OR { 'bidder': str, 'error': str } ]
        }

    Raises:
        RuntimeError: if project or kriterien file not found.
    """
    project_path = get_path(project)
    if not project_path or not os.path.isdir(project_path):
        raise RuntimeError(f"Projekt '{project}' nicht gefunden")

    kriterien_file = find_kriterien_file(project)
    if not kriterien_file:
        raise RuntimeError(f"Keine kriterien.json für Projekt '{project}' gefunden")
    source = load_kriterien_source(kriterien_file)

    def _sync_one(b: str) -> Dict[str, Any]:
        audit = load_or_init_audit(project_path, b)
        stats = reconcile_full(audit, source)
        write_audit_if_changed(project_path, b, audit, stats.wrote_file)
        return {
            'bidder': b,
            'created': stats.created,
            'updated': stats.updated,
            'removed': stats.removed,
            'unchanged': stats.unchanged,
            'wrote_file': stats.wrote_file,
            'total_entries': len(audit.get('kriterien', [])),
        }

    results: List[Dict[str, Any]] = []
    if bidder:
        results.append(_sync_one(bidder))
    else:
        bidders = list_bidders(project)
        for b in bidders:
            try:
                results.append(_sync_one(b))
            except Exception as e:  # capture per-bidder error and proceed
                results.append({'bidder': b, 'error': str(e)})

    return {
        'project': project,
        'mode': 'single' if bidder else 'all',
        'count_bidders': len(results),
        'results': results,
    }


def kriterien_pop(project: str, limit: int = 1, bidder: Optional[str] = None) -> Dict[str, Any]:
    """Return next criteria for processing either project-level (source file) or bidder-level audit.

    Project-level semantics: unproven (source pruefung.status is None)
    Bidder-level semantics: audit.zustand == synchronisiert AND status != entfernt
    """
    if bidder:
        return get_kriterien_pop_json_bidder(project, bidder, limit)
    return get_kriterien_pop_json(project, limit)  # type: ignore[name-defined]

# ---------------------------------------------------------------------------
# Kriterien Audit
# ---------------------------------------------------------------------------

def kriterien_audit_event(ereignis: str, project: str, bidder: str, kriterium_id: str,
                          akteur: str = 'api', ergebnis: Optional[str] = None,
                          force_duplicate: bool = False) -> Dict[str, Any]:
    """Append (or show) an audit event for a bidder's criterion.

    Args:
        ereignis: One of 'ki','mensch','freigabe','ablehnung','reset','show'
        project: Project name
        bidder: Bidder name
        kriterium_id: Criterion ID
        akteur: Actor recorded in the event (default: 'api')
        ergebnis: Optional result payload
        force_duplicate: If True, disables dedupe to force identical event append

    Returns:
        If ereignis == 'show': {
            project,bidder,id,zustand,status,prio,bewertung,events_total,verlauf
        }
        Else (append path): {
            project,bidder,id,event,zustand?,events_total,skipped?,reason?
        }

    Raises:
        RuntimeError on missing project / bidder / criterion.
    """
    project_path = get_path(project)
    if not project_path or not os.path.isdir(project_path):
        raise RuntimeError(f"Projekt '{project}' nicht gefunden")

    audit = load_or_init_audit(project_path, bidder)
    entries = audit.get('kriterien', [])
    entry = next((e for e in entries if e.get('id') == kriterium_id), None)
    if not entry:
        raise RuntimeError(f"Kriterium '{kriterium_id}' nicht im Audit von Bieter '{bidder}' gefunden (vorher sync ausführen?)")

    if ereignis == 'show':
        verlauf = entry.get('audit', {}).get('verlauf', [])
        return {
            'project': project,
            'bidder': bidder,
            'id': kriterium_id,
            'zustand': entry.get('audit', {}).get('zustand'),
            'status': entry.get('status'),
            'prio': entry.get('prio'),
            'bewertung': entry.get('bewertung'),
            'events_total': len(verlauf),
            'verlauf': verlauf,
        }

    mapping = {
        'ki': 'ki_pruefung',
        'mensch': 'mensch_pruefung',
        'freigabe': 'freigabe',
        'ablehnung': 'ablehnung',
        'reset': 'reset',
    }
    if ereignis not in mapping:
        raise ValueError("Unsupported ereignis (expected ki|mensch|freigabe|ablehnung|reset|show)")
    full_event = mapping[ereignis]

    appended = append_event(
        entry,
        full_event,
        quelle_status=entry.get('status'),
        ergebnis=ergebnis,
        akteur=akteur,
        dedupe=not force_duplicate,
        update_state=True,
    )
    if not appended:
        return {
            'project': project,
            'bidder': bidder,
            'id': kriterium_id,
            'event': full_event,
            'skipped': True,
            'reason': 'duplicate',
        }

    # persist
    write_audit_if_changed(project_path, bidder, audit, True)
    return {
        'project': project,
        'bidder': bidder,
        'id': kriterium_id,
        'event': full_event,
        'zustand': entry.get('audit', {}).get('zustand'),
        'events_total': len(entry.get('audit', {}).get('verlauf', [])),
    }

__all__ = [
    'kriterien_sync',
    'kriterien_audit_event',
    'kriterien_pop',
]
