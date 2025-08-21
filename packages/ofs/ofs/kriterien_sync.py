"""Kriterien → Bieter Audit Sync

Implemented Schritte 1–4:
1. Erstellung neuer Einträge (kopiert)
2. Idempotenz (kein doppeltes Event bei erneutem Lauf)
3. Updates von Status / Prio aus Quelle (inkl. optional reset bei finalem Zustand)
4. Entfernen nicht mehr vorhandener IDs (Markierung mit status="entfernt" + Event "entfernt")

Noch offen (spätere Schritte):
- KI / Mensch Prüfungs-Events verarbeiten
- Final-Zustände freigegeben / abgelehnt aktiv setzen
- Ableitung zustand aus Verlauf vollständig nach Spezifikation verankern
- Hash / mtime Optimierung

Public Funktionen:
- load_kriterien_source
- load_or_init_audit
- reconcile_create (nur Create-Pfad; rückwärtskompatibel)
- reconcile_full (Create + Update + Remove)
- write_audit_if_changed
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timezone

# Reuse existing kriterien loader
from .kriterien import load_kriterien, extract_kriterien_list

ISOFormat = str


@dataclass
class SourceKriterium:
    id: str
    status: Optional[str]
    prio: Optional[int]


@dataclass
class SyncStats:
    created: int = 0
    updated: int = 0
    removed: int = 0  # Anzahl Einträge, die auf status="entfernt" gesetzt wurden
    unchanged: int = 0
    wrote_file: bool = False

    def as_dict(self) -> Dict[str, Any]:
        """Return public stats representation.

        External JSON output (CLI/API) now uses a derived field 'changed'
        instead of exposing the large 'unchanged' count the user found
        less useful.  'changed' aggregates created + updated + removed.
        The internal 'unchanged' counter is kept for test assertions
        and potential future diagnostics but is intentionally omitted
        here.
        """
        return {
            "created": self.created,
            "updated": self.updated,
            "removed": self.removed,
            "changed": self.created + self.updated + self.removed,
            "wrote_file": self.wrote_file,
        }


SCHEMA_VERSION = "1.0-bieter-kriterien"


def _now_iso() -> ISOFormat:
    # Use timezone-aware now() to avoid deprecation warnings
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def append_event(entry: Dict[str, Any], ereignis: str, quelle_status: Optional[str] = None,
                 ergebnis: Optional[Any] = None, akteur: str = "system", dedupe: bool = True,
                 update_state: bool = True) -> bool:
    """Append an event to an audit entry.

    Returns True if event appended, False if skipped by dedupe.
    Dedupe rule: If last event has same ereignis AND same quelle_status → skip.
    If update_state=True the audit.zustand is recalculated immediately.
    """
    audit = entry.setdefault("audit", {})
    verlauf: List[Dict[str, Any]] = audit.setdefault("verlauf", [])
    if dedupe and verlauf:
        last = verlauf[-1]
        if last.get("ereignis") == ereignis and last.get("quelle_status") == quelle_status:
            return False
    verlauf.append({
        "zeit": _now_iso(),
        "ereignis": ereignis,
        "quelle_status": quelle_status,
        "ergebnis": ergebnis,
        "akteur": akteur,
    })
    if update_state:
        audit["zustand"] = derive_zustand(entry)
    return True


FINAL_ZUSTAENDE = {"freigegeben", "abgelehnt"}


def derive_zustand(entry: Dict[str, Any]) -> str:
    """Finale Ableitung des Zustands aus dem Ereignisverlauf.

    Regeln (Segment-Logik mit Reset):
    - reset: löscht Bedeutung aller vorherigen Events
    - freigabe / ablehnung: letzter Final-Event im aktuellen Segment entscheidet
    - mensch_pruefung / ki_pruefung (nach letztem reset, ohne Final danach): geprueft
    - sonst synchronisiert
    - entfernt beeinflusst Zustand nicht
    """
    verlauf: List[Dict[str, Any]] = entry.get("audit", {}).get("verlauf", [])

    last_final_state: Optional[str] = None
    last_final_index = -1
    last_review_index = -1

    def do_reset():
        nonlocal last_final_state, last_final_index, last_review_index
        last_final_state = None
        last_final_index = -1
        last_review_index = -1

    do_reset()
    for idx, ev in enumerate(verlauf):
        e = ev.get("ereignis")
        if e == "reset":
            do_reset()
            continue
        if e == "freigabe":
            last_final_state = "freigegeben"
            last_final_index = idx
        elif e == "ablehnung":
            last_final_state = "abgelehnt"
            last_final_index = idx
        elif e in ("ki_pruefung", "mensch_pruefung"):
            last_review_index = idx
        # kopiert / entfernt / andere: keine direkte Auswirkung

    if last_final_index != -1:
        return last_final_state or "synchronisiert"
    if last_review_index != -1:
        return "geprueft"
    return "synchronisiert"


def load_kriterien_source(kriterien_file: str) -> Dict[str, SourceKriterium]:
    """Parse the project kriterien.json and return mapping id -> SourceKriterium.

    Only the fields needed for sync (id, status, prio) are extracted.
    Missing status/prio tolerated.
    """
    data = load_kriterien(kriterien_file)
    k_list = extract_kriterien_list(data)
    out: Dict[str, SourceKriterium] = {}
    for k in k_list:
        kid = k.get("id") or k.get("tag")
        if not kid:
            continue
        pruefung = k.get("pruefung") or {}
        status = pruefung.get("status") if isinstance(pruefung, dict) else None
        # 'prio' could be at top-level OR inside pruefung
        prio = None
        raw_prio = k.get("prio") or pruefung.get("prio")
        if raw_prio is not None:
            try:
                prio = int(raw_prio)
            except Exception:
                prio = None
        out[str(kid)] = SourceKriterium(id=str(kid), status=status, prio=prio)
    return out


def _audit_file_path(project_path: str, bidder: str) -> str:
    return os.path.join(project_path, "B", bidder, "audit.json")


def load_or_init_audit(project_path: str, bidder: str) -> Dict[str, Any]:
    """Load existing audit.json or return initialized structure."""
    path = _audit_file_path(project_path, bidder)
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            # Fallback: re-init on parse error
            pass
    return {
        "meta": {
            "schema_version": SCHEMA_VERSION,
            "projekt": os.path.basename(project_path.rstrip(os.sep)),
            "bieter": bidder,
        },
        "kriterien": [],
    }


def _index_audit_entries(audit: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    index: Dict[str, Dict[str, Any]] = {}
    for entry in audit.get("kriterien", []):
        eid = entry.get("id")
        if eid and eid not in index:
            index[str(eid)] = entry
    return index


def reconcile_create(audit: Dict[str, Any], source: Dict[str, SourceKriterium]) -> SyncStats:
    """Ensure all source IDs exist in audit with an initial kopiert event.

    - If entry missing → create with bewertung=null and initial event
    - If entry exists → unchanged (no new event)
    """
    stats = SyncStats()
    idx = _index_audit_entries(audit)
    changed = False
    for kid, sk in source.items():
        if kid in idx:
            stats.unchanged += 1
            continue
        # create new entry
        entry = {
            "id": sk.id,
            "status": sk.status,
            "prio": sk.prio,
            "bewertung": None,
            "audit": {
                "zustand": "synchronisiert",
                "verlauf": [],
            },
        }
        append_event(entry, "kopiert", quelle_status=sk.status)
        audit.setdefault("kriterien", []).append(entry)
        idx[kid] = entry
        stats.created += 1
        changed = True

    # Sort deterministically (prio desc NULL last, then id asc)
    def _sort_key(e: Dict[str, Any]):
        prio = e.get("prio")
        prio_key = prio if isinstance(prio, int) else -1
        return (-prio_key, e.get("id") or "")

    if changed:
        audit["kriterien"].sort(key=_sort_key)
    stats.wrote_file = changed
    return stats


def _update_entry_from_source(entry: Dict[str, Any], sk: SourceKriterium) -> bool:
    """Apply status/prio changes from source to existing entry.

    Returns True if something changed.
    Implements reset logic: If previous zustand final und status ändert → add reset event & clear final zustand.
    """
    changed = False
    old_status = entry.get("status")
    old_prio = entry.get("prio")
    status_changed = old_status != sk.status
    prio_changed = old_prio != sk.prio
    if not (status_changed or prio_changed):
        return False

    zustand = entry.get("audit", {}).get("zustand", "synchronisiert")
    if status_changed and zustand in FINAL_ZUSTAENDE:
        # Reset final state
        append_event(entry, "reset", quelle_status=old_status)
    # Apply fields
    entry["status"] = sk.status
    entry["prio"] = sk.prio
    # New snapshot event
    append_event(entry, "kopiert", quelle_status=sk.status)
    # Recompute zustand (likely synchronisiert or final cleared by reset)
    entry["audit"]["zustand"] = derive_zustand(entry)
    return True


def reconcile_full(audit: Dict[str, Any], source: Dict[str, SourceKriterium]) -> SyncStats:
    """Create + Update + Remove reconciliation.

    - Creates missing entries (kopiert)
    - Updates status/prio changes (kopiert + evtl. reset)
    - Marks entries absent in source with status="entfernt" (adds entfernt event once)
    - Maintains idempotence: repeated run without changes yields unchanged counts
    """
    stats = SyncStats()
    idx = _index_audit_entries(audit)
    changed_any = False

    # Create & Update pass
    for kid, sk in source.items():
        if kid not in idx:
            # create
            entry = {
                "id": sk.id,
                "status": sk.status,
                "prio": sk.prio,
                "bewertung": None,
                "audit": {"zustand": "synchronisiert", "verlauf": []},
            }
            append_event(entry, "kopiert", quelle_status=sk.status)
            audit.setdefault("kriterien", []).append(entry)
            idx[kid] = entry
            stats.created += 1
            changed_any = True
        else:
            entry = idx[kid]
            if _update_entry_from_source(entry, sk):
                stats.updated += 1
                changed_any = True
            else:
                stats.unchanged += 1

    # Removal pass: entries present in audit but not in source
    source_ids = set(source.keys())
    for entry in audit.get("kriterien", []):
        eid = entry.get("id")
        if not eid:
            continue
        if eid not in source_ids:
            # Already marked entfernt?
            if entry.get("status") == "entfernt":
                stats.unchanged += 1
                continue
            entry["status"] = "entfernt"
            # Keep bewertung as-is
            appended = append_event(entry, "entfernt", quelle_status=None, update_state=False)
            if appended:
                # Zustand nicht neu berechnen – behält alten (oder könnte optional gesetzt werden)
                stats.removed += 1
                changed_any = True
            else:
                stats.unchanged += 1

    # Resort if any structural changes (create/update/removal marking can affect prio ordering)
    if changed_any:
        def _sort_key(e: Dict[str, Any]):
            prio = e.get("prio")
            prio_key = prio if isinstance(prio, int) else -1
            return (-prio_key, e.get("id") or "")
        audit["kriterien"].sort(key=_sort_key)
        # Update zustand values for all (cheap) to reflect any resets or final changes
        for e in audit.get("kriterien", []):
            e.setdefault("audit", {})["zustand"] = derive_zustand(e)

    stats.wrote_file = changed_any
    return stats


def write_audit_if_changed(project_path: str, bidder: str, audit: Dict[str, Any], changed: bool) -> bool:
    """Persist audit.json atomically if changed flag is True."""
    if not changed:
        return False
    path = _audit_file_path(project_path, bidder)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(audit, fh, ensure_ascii=False, indent=2)
    os.replace(tmp, path)
    return True

__all__ = [
    "SourceKriterium",
    "SyncStats",
    "load_kriterien_source",
    "load_or_init_audit",
    "reconcile_create",
    "reconcile_full",
    "write_audit_if_changed",
    "append_event",
    "derive_zustand",
]
