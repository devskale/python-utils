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

from .core import (
    get_path,
    list_bidders,
    get_paths_json,
    list_ofs_items,
    list_projects_json,
    find_bidder_in_project,
    list_bidder_docs_json,
    list_project_docs_json,
    get_bidder_document_json,
    get_project_document_json,
    read_doc,
)
from .kriterien import (
    find_kriterien_file,
    get_kriterien_pop_json_bidder,
    get_kriterien_pop_json,
    load_kriterien,
    extract_kriterien_list,
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

    Legacy / focused API: only a single project (optionally a single bidder).
    For global multi-project sync use kriterien_sync_all().
    """
    project_path = get_path(project)
    if not project_path or not os.path.isdir(project_path):
        raise RuntimeError(f"Projekt '{project}' nicht gefunden")

    kriterien_file = find_kriterien_file(project)
    if not kriterien_file:
        raise RuntimeError(f"Keine Kriterien-Datei für Projekt '{project}' gefunden")
    source = load_kriterien_source(kriterien_file)

    def _sync_one(b: str) -> Dict[str, Any]:
        audit = load_or_init_audit(project_path, b)
        stats = reconcile_full(audit, source, include_bdoks=True)
        write_audit_if_changed(project_path, b, audit, stats.wrote_file)
        base = stats.as_dict()
        base.update({
            'bidder': b,
            'total_entries': len(audit.get('kriterien', [])),
        })
        return base

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


def kriterien_sync_all() -> Dict[str, Any]:
    """Synchronize criteria for ALL projects and bidders.

    Returns structure:
    {
      mode: 'global',
      count_projects: N,
      projects: [ { project, count_bidders, results:[ ... per bidder stats ... ] } ]
    }
    """
    projects = list_projects()
    aggregate: List[Dict[str, Any]] = []
    for proj in projects:
        try:
            summary = kriterien_sync(proj)  # project-level all bidders
            aggregate.append(summary)
        except Exception as e:
            aggregate.append({'project': proj, 'error': str(e), 'results': []})
    return {
        'mode': 'global',
        'count_projects': len(aggregate),
        'projects': aggregate,
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

# ---------------------------------------------------------------------------
# Additional high-level wrappers mirroring CLI (non-kriterien sections)
# ---------------------------------------------------------------------------

def get_path_info(name: str) -> Dict[str, Any]:
    """Return JSON path resolution (CLI: ofs get-path <name>)."""
    return get_paths_json(name)


def list_items() -> list[str]:
    """List all items in OFS root (CLI: ofs list)."""
    return list_ofs_items()


def list_projects() -> Dict[str, Any]:
    """Return projects JSON (CLI: ofs list-projects)."""
    return list_projects_json()


def list_bidders_for_project(project: str) -> list[str]:
    """List bidder names for a project (CLI: ofs list-bidders <project>)."""
    return list_bidders(project)


def find_bidder(project: str, bidder: str) -> Optional[str]:
    """Find bidder directory path (CLI: ofs find-bidder <project> <bidder>)."""
    return find_bidder_in_project(project, bidder)


def docs_list(identifier: str, meta: bool = False) -> Dict[str, Any]:
    """Unified document listing analogous to CLI list-docs parsing.

    Accepts:
      project
      project@bidder
      project@filename
      project@bidder@filename
    """
    if '@' not in identifier:
        # project only
        return list_project_docs_json(identifier, include_metadata=meta)
    parts = identifier.split('@')
    if len(parts) == 2:
        project, second = parts
        # heuristic: second contains dot -> treat as filename
        if '.' in second and len(second.split('.')[-1]) <= 5:
            return get_project_document_json(project, second, include_metadata=meta)
        return list_bidder_docs_json(project, second, include_metadata=meta)
    if len(parts) == 3:
        project, bidder, filename = parts
        return get_bidder_document_json(project, bidder, filename, include_metadata=meta)
    raise ValueError("Unsupported identifier format (expected project[@bidder][@filename])")


def read_document(identifier: str, parser: Optional[str] = None, as_json: bool = False) -> Dict[str, Any] | str:
    """Read a document (CLI: ofs read-doc). Returns content or full JSON if as_json=True."""
    result = read_doc(identifier, parser=parser)
    if as_json:
        return result
    if not result.get('success', False):
        raise RuntimeError(result.get('error', 'Unknown error'))
    return result.get('content', '')

# Add new symbols to __all__
__all__ += [
    'get_path_info',
    'list_items',
    'list_projects',
    'list_bidders_for_project',
    'find_bidder',
    'docs_list',
    'read_document',
]

# ---------------------------------------------------------------------------
# Zusatz: Audit Helper
# ---------------------------------------------------------------------------

def list_kriterien_audit_ids(project: str, bidder: str) -> Dict[str, Any]:
    """Return all criterion IDs contained in the bidder's audit file.

    Structure:
        { project, bidder, count, ids:[...], zustand_counts:{zustand: n} }

    Raises RuntimeError if project path is missing.
    """
    project_path = get_path(project)
    if not project_path or not os.path.isdir(project_path):
        raise RuntimeError(f"Projekt '{project}' nicht gefunden")
    audit = load_or_init_audit(project_path, bidder)
    entries = audit.get('kriterien', [])
    ids: List[str] = []
    zustand_counts: Dict[str, int] = {}
    for e in entries:
        _id = e.get('id')
        if _id:
            ids.append(_id)
        zustand = e.get('audit', {}).get('zustand')
        if zustand:
            zustand_counts[zustand] = zustand_counts.get(zustand, 0) + 1
    return {
        'project': project,
        'bidder': bidder,
        'count': len(ids),
        'ids': ids,
        'zustand_counts': zustand_counts,
    }

__all__ += ['list_kriterien_audit_ids']

def get_kriterien_audit_json(project: str, bidder: str, must_exist: bool = False) -> Dict[str, Any]:
    """Return the complete audit.json structure for a bidder.

    Args:
        project: Project name
        bidder: Bidder name
        must_exist: If True, raises RuntimeError if audit.json file does not yet exist.

    Behavior:
        Uses existing loader (load_or_init_audit). If must_exist is False and file is
        missing, you'll get a freshly initialized empty structure (same as after first sync).
    """
    project_path = get_path(project)
    if not project_path or not os.path.isdir(project_path):
        raise RuntimeError(f"Projekt '{project}' nicht gefunden")
    if must_exist:
        audit_path = os.path.join(project_path, 'B', bidder, 'audit.json')
        if not os.path.isfile(audit_path):
            raise RuntimeError(f"audit.json für Bieter '{bidder}' in Projekt '{project}' nicht vorhanden (vorher sync ausführen?)")
    return load_or_init_audit(project_path, bidder)

__all__ += ['get_kriterien_audit_json']

def get_kriterium_description(project: str, kriterium_id: str) -> Dict[str, Any]:
    """Return a minimal description object for a criterion from the project source.

    Looks up criteria file (or equivalent) and searches for the matching id/tag.
    Returns { id, name, raw } where name may be derived from known fields; raw is the full dict.
    Raises RuntimeError if project or file not found; returns empty structure if ID missing.
    """
    project_path = get_path(project)
    if not project_path or not os.path.isdir(project_path):
        raise RuntimeError(f"Projekt '{project}' nicht gefunden")
    k_file = find_kriterien_file(project)
    if not k_file:
        raise RuntimeError(f"Keine Kriterien-Datei für Projekt '{project}' gefunden")
    data = load_kriterien(k_file)
    k_list = extract_kriterien_list(data)
    for k in k_list:
        kid = k.get('id') or k.get('tag')
        if kid == kriterium_id:
            name = k.get('name') or k.get('kriterium') or k.get('bezeichnung') or ''
            beschreibung = k.get('beschreibung') or k.get('description') or ''
            # Try to derive a requirement/"Anforderung" text if present in source
            anforderung = (
                k.get('anforderung')
                or k.get('anforderungen')
                or k.get('requirement')
                or k.get('requirements')
                or k.get('forderung')
                or k.get('forderungen')
            )
            return {
                'id': kriterium_id,
                'name': name,
                'beschreibung': beschreibung,
                'anforderung': anforderung,
                'raw': k,
            }
    return {'id': kriterium_id, 'missing': True}

__all__ += ['get_kriterium_description']

def get_bieterdokumente_list(project: str) -> List[Dict[str, Any]]:
    """Return the list of 'bdoks.bieterdokumente' from a project's criteria file.

    Args:
        project: Project name

    Returns:
        A list of dicts representing the required bidder documents as defined under
        the key path bdoks.bieterdokumente in criteria file. If the key is missing,
        returns an empty list.

    Raises:
        RuntimeError if the project path or criteria file is not found.
    """
    project_path = get_path(project)
    if not project_path or not os.path.isdir(project_path):
        raise RuntimeError(f"Projekt '{project}' nicht gefunden")
    k_file = find_kriterien_file(project)
    if not k_file:
        raise RuntimeError(f"Keine Kriterien-Datei für Projekt '{project}' gefunden")
    data = load_kriterien(k_file)
    bdoks = data.get('bdoks') if isinstance(data, dict) else None
    if not isinstance(bdoks, dict):
        return []
    bdocs = bdoks.get('bieterdokumente')
    if isinstance(bdocs, list):
        # ensure each entry is a dict (best-effort)
        return [x for x in bdocs if isinstance(x, dict)]
    return []

__all__ += ['get_bieterdokumente_list']
