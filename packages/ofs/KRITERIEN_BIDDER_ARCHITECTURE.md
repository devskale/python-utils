# Minimal: Übernahme freigegebener / relevanter Kriterien-TAGs in Bieter-Datei

## Ziel (sehr klein / erster Schritt)

Wenn ein Kriterium in der Projektdatei `kriterien.json` einen relevanten `pruefung.status` hat, wird dessen TAG (`id`) in die Bieter-Datei übernommen. Minimal: keine komplexen Merges, nur eine idempotente Synchronisation pro Bieter.

Der TAG verweist im Projekt auf die volle Definition; in der Bieter-Datei speichern wir eine reduzierte Repräsentation plus Audit-Verlauf.

## Status-Werte im Projekt (`pruefung.status`)

Mögliche Werte:

- `ja` – freigegeben zur prüfung(evtl. KI + Mensch)
- `ja.int` – intern/menschlich zu prüfen
- `ja.ki` – nur KI zu prüfen
- `nein` – nicht zu prüfen / nicht relevant
- `optional` – optional prüfbar
- `halt` – später prüfen (zur Zeit nicht relevant)
- (leer/sonst) – behandeln wie `nein`

Aktuelle Regel: Jeder Status, der exakt `ja` ist oder mit `ja.` beginnt, zählt als positiv (freigabe-relevant). Anpassbar.

## Priorität

Optionales Feld `prio` (z.B. `"prio": 10`). Sortierung: absteigend nach `prio`, danach alphabetisch `id`.

## Dateipfade

- Projekt: `{PROJECT}/kriterien.json` mit `ids.kriterien[]`
- Bieter: `{PROJECT}/B/{BIDDER}/audit.json`

## Bieter-Dateistruktur (erweitert)

Statt einer reinen ID-Liste enthält `kriterien` Objekte mit kopiertem Status und Auditdaten.

Beispiel (Sync legt neue Einträge immer mit `bewertung: null` an – Bewertungen entstehen erst durch Prüf-Ereignisse):

{
  "meta": { "schema_version": "1.0-bieter-kriterien", "projekt": "PROJECT_NAME", "bieter": "BIDDER_NAME" },
  "kriterien": [
    {
      "id": "F_DOK_001",
      "status": "ja",
      "prio": 10,
      "bewertung": null,
      "audit": {
        "zustand": "synchronisiert",
        "verlauf": [
          { "zeit": "2025-08-21T12:00:00Z", "ereignis": "kopiert", "quelle_status": "ja", "notiz": "Initiale Übernahme", "ergebnis": null, "akteur": "system" }
        ]
      }
    },
    {
      "id": "Z_PREIS_001",
      "status": "ja",
      "bewertung": null,
      "audit": {
        "zustand": "geprueft",
        "verlauf": [
          { "zeit": "2025-08-21T12:00:01Z", "ereignis": "kopiert", "quelle_status": "ja", "ergebnis": null, "akteur": "system" },
          { "zeit": "2025-08-21T12:05:00Z", "ereignis": "ki_pruefung", "quelle_status": "ja", "ergebnis": 650, "akteur": "ki" }
        ]
      },
      "bewertung": 650
    },
    {
      "id": "F_FORM_007",
      "status": "ja.ki",
      "bewertung": null,
      "audit": {
        "zustand": "geprueft",
        "verlauf": [
          { "zeit": "2025-08-21T12:00:02Z", "ereignis": "kopiert", "quelle_status": "ja.ki", "ergebnis": null, "akteur": "system" },
          { "zeit": "2025-08-21T12:10:00Z", "ereignis": "ki_pruefung", "quelle_status": "ja.ki", "ergebnis": "review_needed", "notiz": "Unsicherheit Score<0.6", "akteur": "ki" }
        ]
      },
      "bewertung": "review_needed"
    },
    {
      "id": "F_ALT_999",
      "status": "entfernt",
      "bewertung": "ok",  
      "audit": {
        "zustand": "synchronisiert",
        "verlauf": [
          { "zeit": "2025-08-20T08:00:00Z", "ereignis": "kopiert", "quelle_status": "ja", "ergebnis": null, "akteur": "system" },
          { "zeit": "2025-08-21T14:00:00Z", "ereignis": "entfernt", "quelle_status": null, "notiz": "Nicht mehr im Projekt", "akteur": "system" }
        ]
      }
      /* bewertung wurde NICHT auf null gesetzt – Historie bleibt */
    }
  ]
}


Feld-Notizen:

- `id`: Kriteriumstag.
- `status`: Kopierter Projektstatus.
- `prio`: Optionale Priorität.
- `bewertung`: Ergebnis/Entscheidung/Score für das Kriterium. (Wird beim Anlegen immer `null` gesetzt; Änderungen kommen ausschließlich durch Prüf-/Freigabe-/Ablehnungs-Ereignisse.) Zulässige Werte:
  - `ok` (positiv erfüllt)
  - `fail` (negativ/abgelehnt)
  - Zahl (z.B. 650, für Scoring-Kriterien)
  - `review_needed` (KI fordert menschliche Prüfung)
  - beliebige weitere textuelle Flags (z.B. `unsicher`, `pending`)
- `audit.zustand`: Verdichteter Zustand (`synchronisiert|geprueft|freigegeben|abgelehnt`).
- `audit.verlauf`: Liste chronologischer Ereignisse.

Ereignis-Felder (`verlauf[]`):
- `zeit` (ISO8601 UTC)
- `ereignis`: `kopiert|ki_pruefung|mensch_pruefung|freigabe|ablehnung|reset|entfernt`
- `quelle_status`: Status im Projekt zum Zeitpunkt (oder null bei `entfernt`)
- `ergebnis`: Wert/Entscheidung/Score (siehe oben, z.B. `ok`, `fail`, Zahl, `review_needed`)
- `akteur`: `ki|mensch|system`
- `notiz`: Freitext

## Bewertung & Audit-Zustände (Variante B)

Das Feld `bewertung` ergänzt den Audit-Zustand und transportiert die eigentliche Entscheidung, den Score oder die Review-Anforderung für das Kriterium. Die UI kann je nach Wert unterschiedliche Badges, Farben oder Aktionen anzeigen (z.B. Review-Button bei `review_needed`).

Wir verwenden bewusst nur 4 konsolidierte Zustände (kein separates Flag mehr).

Zustände (`audit.zustand`):
1. `synchronisiert` – Eintrag wurde angelegt / kopiert, noch keine Prüfung.
2. `geprueft` – Mindestens eine KI- oder Mensch-Prüfung erfolgt, aber keine finale Freigabe / Ablehnung.
3. `freigegeben` – Letztes finales Ereignis ist `freigabe` (nach letztem `reset`).
4. `abgelehnt` – Letztes finales Ereignis ist `ablehnung` (nach letztem `reset`).


### Ereignis-Typen (Deutsch)
`kopiert | ki_pruefung | mensch_pruefung | freigabe | ablehnung | reset | entfernt`

### Übergangs-/Ableitungslogik
Ableitung erfolgt aus dem Verlauf (von hinten nach vorne):
1. Teile den Verlauf logisch in Abschnitte: Alles nach dem letzten `reset` ist der aktuelle Abschnitt.
2. Suche im aktuellen Abschnitt das letzte finale Ereignis (`freigabe` oder `ablehnung`).
  - Falls `freigabe` → Zustand = `freigegeben`.
  - Sonst falls `ablehnung` → Zustand = `abgelehnt`.
3. Sonst falls mindestens ein Prüf-Ereignis (`ki_pruefung` oder `mensch_pruefung`) im Abschnitt → Zustand = `geprueft`.
4. Sonst → Zustand = `synchronisiert`.

### Beispiele

Verlauf:
1. `kopiert`
2. `ki_pruefung (ok)` → Zustand `geprueft`
3. `mensch_pruefung (ok)` → Zustand bleibt `geprueft`
4. `freigabe` → Zustand `freigegeben`

Reset-Szenario (nur wenn vorher final → jetzt anderer Status):
1. `kopiert`
2. `freigabe`
3. (Projekt ändert Status)
4. `reset`
5. `ki_pruefung (fail)` → jetzt `geprueft`

Entfernt-Szenario (Historie bleibt, bewertung unverändert):
1. `kopiert`
2. `ki_pruefung (ok)` → Zustand `geprueft`, `bewertung=ok`
3. Kriterium verschwindet aus Projekt
4. `entfernt`-Ereignis; `status = "entfernt"`; `bewertung` bleibt `ok`


### Vorteile Variante B
- Minimale kognitive Last
- Trail transportiert alle Detailnuancen (KI vs Mensch, ok/fail)
- Erweiterungen (z.B. zusätzliche Prüfarten) erfordern keine neuen Zustände

### Wann `reset`?
`reset` wird NUR ausgelöst, wenn der vorige Zustand final war (`freigegeben` oder `abgelehnt`) und sich der kopierte Projekt-Status ändert (final → anything). Bei nicht-finalen Zuständen erfolgt KEIN `reset`, sondern nur neues `kopiert`-Ereignis.

### Sync-Regeln (konkrete Entscheidungen)
- Alle IDs werden kopiert (kein Filter nach Status).
- Neues Kriterium: `bewertung = null`.
- Statusänderung: wenn vorher final → `reset` + neues `kopiert`; sonst nur neues `kopiert`.
- Entfernte IDs: `status = "entfernt"`, Ereignis `entfernt`, `bewertung` bleibt erhalten.
- `bewertung` wird NIEMALS vom Sync überschrieben (nur Prüf-/Final-Ereignisse ändern sie).

---

