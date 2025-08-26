# Agentic Workflows für Vergabeprozesse

## Vorraussetzungen
- Python 3.8+
- OFS (Opinionated Filesystem) python package installiert
- LLM-Zugang (API-Key) konfiguriert über Umgebungsvariablen / Secrets

## DokDa Agent — Detaillierter Workflow zur Kriterien-Lesung und Dokumentenbewertung

Dieses Repository enthält den "DokDa"-Agent (`agentos/agentBieterDokDa.py`), der Bieter‑Dokumente gegen Vergabe‑Kriterien automatisch prüft und bewertet. Der Agent kombiniert Metadaten‑Analyse, eine kleine Terminal‑UI und LLM‑Aufrufe. Im Folgenden wird der Ablauf Schritt für Schritt beschrieben.

1) Vorbereitung und Datenzugriff
- Projektdaten und Bieter werden als Strings in `Projekt` und `Bieter` definiert.
- Die Bieter-Dokumentliste wird über die OFS‑API geladen:
  - `BieterDokumente = docs_list(f"{Projekt}@{Bieter}", meta=True)`
  - Audit-IDs / Kriterien-IDs werden via `list_kriterien_audit_ids(Projekt, Bieter)` geladen.
- Dokumentinhalte werden bei Bedarf mit `read_document` über die Funktion `load_document_content(filename, max_chars)` geladen (mit Trunkierung für sehr lange Texte).

2) Kriterien laden / darstellen
- Die Funktion `build_criteria(ids_cycle)` erzeugt eine Liste von Kriterienobjekten. Für jedes Kriterium wird die Beschreibung und ggf. die erwarteten Dokument‑Hinweise über `get_kriterium_description(Projekt, cid)` geholt.
- Jedes Kriterium enthält:
  - `id`, `name`, `beschreibung`, `anforderung`
  - ggf. `dokumente` (Hinweise auf erwartete Formular‑/Beilagenamen)

3) Interaktive Auswahl (TUI)
- Benutzer starten die textbasierte UI über `tui(stdscr, criteria)`.
- In der Liste navigierst du mit ↑/↓, Enter öffnet die Analyseansicht eines Kriteriums.
- Die UI-Funktionen sind:
  - `draw_list`: zeichnet die Kriteriums‑Übersicht
  - `show_results`: führt die Analyse eines ausgewählten Kriteriums aus und zeigt Ergebnisse

4) Finden relevanter Dokumente (LLM‑gestützte Metadatenanalyse)
- `llm_find_relevant_documents(kriterium, projektinfo, listing, ...)`:
  - Baut ein kompaktes JSON‑Kontextobjekt mit:
    - `projektbeschreibung` (Kurzinfo zum Projekt)
    - `kriterium` (id, name, beschreibung, anforderung, ggf. dokumente)
    - `dokumente`: Liste der Dokumente mit Metadaten (`docname`, `meta: { name, kategorie, begründung }`)
  - Wichtig: In der Standardkonfiguration wird hier NUR mit Metadaten gearbeitet (Inhalte nicht berücksichtigt), um eine erste Relevanzabschätzung durch das LLM zu bekommen.
  - Das System‑Prompt fordert das LLM auf, ausschließlich JSON mit folgendem Schema zurückzugeben:
    - {
        "relevante_dokumente": [
          { "filename": string, "relevance": number (0-1), "begruendung": string, "abgedeckte_aspekte": [...], "fehlende_aspekte": [...] }
        ],
        "zusammenfassung": string
      }
  - Das Ergebnis wird dann von `parse_llm_output` eingelesen und nach `relevance` sortiert.

5) Anzeige der Ergebnisse
- `show_results` zeigt:
  - Die zusammenfassende Begründung (`zusammenfassung`) falls vorhanden
  - Die Liste der gefundenen Dokumente mit Relevanzscore und Metadaten
- In der Anzeige kannst du ein einzelnes Dokument auswählen und mit `b` (bewerten) zur tiefergehenden, inhaltlichen Prüfung wechseln.

6) Detaillierte Dokumentbewertung (Inhaltliche Prüfung)
- `evaluate_and_show(stdscr, crit, filename)`:
  - Lädt den dokument‑Text via `load_document_content`
  - Baut ein Evaluations‑Kontextobjekt:
    - `projektbeschreibung`, `kriterium` und `dokument: { filename, inhalt }`
  - Sendet dies an das LLM mit dem Systemprompt, das eine präzise JSON‑Antwort erwartet:
    - { "bewertung": ("erfüllt"|"teilweise erfüllt"|"nicht erfüllt"|"unbekannt"), "begruendung": "..." }
  - Ergebnis wird angezeigt (Bewertung + Begründung).

7) Wichtige Implementierungsdetails und Hinweise
- Metadatenbasierte Vorselektion: Die erste LLM‑Abfrage arbeitet primär mit Metadaten (z.B. `meta.name`, `meta.kategorie`, `meta.begründung`), das beschleunigt Entscheidungen und reduziert Token‑Kosten.
- Inhaltsprüfung ist optional und wird nur für ausgewählte Dokumente ausgeführt, da sie teurer ist.
- Standard‑Antwortschema des LLM ist JSON; die Codebasis versucht, Ausgaben robust zu parsen (`json_cleanup=True`, Fallbacks).
- Environment / Model:
  - Erwartet Umgebungsvariablen: `PROVIDER`, `BASE_URL`, optional `MODEL`
  - API‑Key wird über `get_api_key(PROVIDER)` bezogen (siehe `credgoo` Integration).
- Fehlerbehandlung:
  - Laden von Dokumenten und LLM‑Calls sind in try/except‑Blöcken gekapselt und liefern verständliche Fallback‑Strings.
  - Wenn das LLM keine passenden Dokumente findet, wird eine leere Ergebnisliste gezeigt.

8) Sicherheit, Grenzen und Best Practices
- Vertrauliche Dokumente: Achte beim Einsatz von externen LLM‑Anbietern auf Datenschutz / DSGVO. Sende keine sensiblen Daten, es sei denn deine LLM‑Verträge erlauben es.
- Prompt‑Engineering: Die Qualität der Einschätzung hängt stark vom Prompt und den gelieferten Metadaten ab. Anpassungen im System‑Prompt verbessern Genauigkeit.
- Token‑Kosten: Begrenze `max_docs`, `max_chars_total` und `max_chars_per_doc` je nach Budget.
- Validierung: Die LLM‑Einschätzungen sind assistierend — rechtlich relevante Bewertungen sollten weiterhin durch Menschen geprüft werden.

9) Schnellstart
- Setze die Umgebungsvariablen (`PROVIDER`, `BASE_URL`, ggf. `MODEL`) und den API‑Key wie in deiner Umgebung üblich.
- Starte ein kleines Python‑TUI‑Programm, das `build_criteria(...)` nutzt, um die Liste zu erzeugen und dann `tui(stdscr, criteria)` aufzurufen (z. B. mit `curses.wrapper(tui, criteria)`).
- Wähle ein Kriterium, sieh dir die vorgeschlagenen Dokumente an und führe bei Bedarf die inhaltliche Prüfung durch.

10) Weiterführende Anpassungen
- Du kannst die Gewichtung von Dokumenten verbessern, indem du im Kontext zusätzliche Metadaten hinzufügst (Dateityp, Upload‑Datum, Seitenanzahl).
- Für höhere Präzision kannst du spezialisierte System‑Prompts oder ein feingetuntes Modell verwenden.
- Wenn viele Dokumente vorhanden sind, empfiehlt sich ein zwei‑stufiger Ansatz: schnelle Metadaten‑Filtration → inhaltliche Prüfung nur für Top‑N.

Bei Fragen zur Anpassung der Prompts, zur Reduktion der Token‑Kosten oder zur Integration in ein GUI/CI‑System helfe ich dir gerne weiter.
