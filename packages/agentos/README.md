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

## AgentOS Python Utilities

This directory contains various Python utilities that leverage the AgentOS framework for document intelligence tasks in procurement and document assessment workflows.

### `agentBieterDokDa.py` - Interactive Document Assessment Agent

**Purpose:** The "DokDa" (Dokument-Datenanalyse) Agent provides an interactive terminal-based UI for assessing bidder documents against procurement criteria. It combines metadata analysis with LLM-powered document evaluation.

**Key Features:**
- Interactive terminal UI (TUI) for criteria navigation
- Metadata-based document pre-filtering
- Content-based document assessment
- Real-time LLM evaluation of document relevance

**Usage:**
```bash
python agentBieterDokDa.py
```

**Configuration:**
- Set environment variables: `PROVIDER`, `BASE_URL`, `MODEL`
- Configure project and bidder variables in the script
- Requires OFS API access for document retrieval

**Workflow:**
1. Load criteria and bidder documents via OFS API
2. Navigate criteria using arrow keys in TUI
3. Press Enter to analyze a criterion
4. View relevant documents with relevance scores
5. Press 'b' to perform detailed content evaluation

### `matchaFlow.py` - Document Matching Workflow

**Purpose:** Automatically matches required procurement documents with uploaded bidder documents using LLM analysis. Designed for procurement workflows where document compliance needs to be verified.

**Usage:**
```bash
python matchaFlow.py <project> <bidder> [--out output.json] [--limit N]
```

**Parameters:**
- `project`: Project identifier for document retrieval
- `bidder`: Bidder identifier for document scope
- `--out`: Optional output file path (default: `matcha.{project}.{bidder}.json`)
- `--limit`: Limit number of documents to process

**Features:**
- Retrieves required documents from OFS API
- Analyzes uploaded bidder documents
- Uses LLM to match documents based on content and metadata
- Outputs structured JSON with matching results

**Output Format:**
```json
{
  "matches": [
    {
      "required_doc": "Document Name",
      "matched_file": "uploaded_file.pdf",
      "confidence": 0.95,
      "reasoning": "Explanation of match"
    }
  ]
}
```

### `checkaFlow.py` - Criteria Assessment Workflow

**Purpose:** Systematically assesses bidder documents against predefined audit criteria using LLM analysis. Provides automated compliance checking for procurement processes.

**Usage:**
```bash
python checkaFlow.py <project> <bidder> [--out output.json] [--limit N]
```

**Parameters:**
- `project`: Project identifier
- `bidder`: Bidder identifier
- `--out`: Output file path (default: `{project}.{bidder}.assessments.json`)
- `--limit`: Limit number of criteria to process

**Workflow:**
1. Retrieves audit criteria from OFS API
2. For each criterion:
   - Finds relevant documents using LLM
   - Assesses criterion fulfillment based on document content
   - Generates structured assessment results

**Output Format:**
```json
{
  "project": "ProjectName",
  "bidder": "BidderName",
  "results": [
    {
      "id": "criterion_id",
      "name": "Criterion Name",
      "assessment": {
        "erfüllt": "ja|nein|teilweise|nicht beurteilbar",
        "begründung": "Detailed reasoning"
      },
      "doc_names": ["relevant_document.pdf"]
    }
  ]
}
```

### `assessments_to_md.py` - Assessment Report Generator

**Purpose:** Converts JSON assessment results from `checkaFlow.py` into human-readable Markdown reports for stakeholder review.

**Usage:**
```bash
python assessments_to_md.py <assessment_file.json> [--out report.md]
```

**Features:**
- Converts JSON assessments to formatted Markdown
- Enriches reports with criterion descriptions from OFS API
- Provides clear pass/fail status for each criterion
- Includes detailed reasoning for each assessment

**Output:** Generates a structured Markdown report with:
- Project and bidder information
- Assessment summary
- Detailed criterion-by-criterion evaluation
- Document references

### `json2table.py` - Matching Results Table Generator

**Purpose:** Converts document matching results from `matchaFlow.py` into formatted Markdown tables for easy review and reporting.

**Usage:**
```bash
python json2table.py <matcha.project.bidder.json> [--out output.md] [--max-reason-len 160]
```

**Parameters:**
- Input: JSON file from matchaFlow.py
- `--out`: Output Markdown file path
- `--max-reason-len`: Maximum length for reasoning text (default: 160)

**Features:**
- Generates clean Markdown tables
- Truncates long reasoning text for readability
- Preserves all matching information in tabular format
- Auto-derives output filename from input if not specified

### `llmcall.py` - LLM Integration Module

**Purpose:** Centralized LLM calling functionality with task-specific configuration and token management.

**Key Features:**
- Task-specific model configuration (default vs. kriterien tasks)
- Automatic token estimation and context management
- JSON response cleanup and repair
- Provider-agnostic LLM integration via uniinfer
- Credential management via credgoo

**Configuration:**
- Uses `config.json` for task-specific settings
- Environment variables: `PROVIDER`, `MODEL` (override config)
- Supports different token limits per task type

**Usage (as module):**
```python
from llmcall import call_ai_model

result = call_ai_model(
    prompt="System prompt",
    input_text="User input",
    task_type="kriterien",  # or "default"
    json_cleanup=True,
    verbose=True
)
```

## Environment Setup

### Required Environment Variables
```bash
export PROVIDER="tu"  # or your LLM provider
export BASE_URL="https://your-llm-endpoint/v1"
export MODEL="deepseek-r1"  # optional, uses config.json default
```

### Configuration File (`config.json`)
```json
{
  "provider": "tu",
  "model": "mistral-small-3.1-24b",
  "kriterien": {
    "provider": "tu",
    "model": "deepseek-r1",
    "max_context_tokens": 32768,
    "max_response_tokens": 16000,
    "max_safe_input_chars": 400000
  }
}
```

### Dependencies
```bash
pip install ofs credgoo agno uniinfer
pip install json-repair strukt2meta  # optional for JSON cleanup
```

## Workflow Integration

These utilities are designed to work together in a complete document intelligence pipeline:

1. **Document Matching**: Use `matchaFlow.py` to match required vs. uploaded documents
2. **Criteria Assessment**: Use `checkaFlow.py` to assess compliance against criteria
3. **Report Generation**: Use `assessments_to_md.py` and `json2table.py` for human-readable reports
4. **Interactive Review**: Use `agentBieterDokDa.py` for detailed manual review

## Security and Best Practices

- **Data Privacy**: Be cautious when using external LLM providers with sensitive procurement data
- **Token Management**: Monitor token usage to control costs
- **Validation**: LLM assessments are assistive - human review is recommended for legal compliance
- **Error Handling**: All utilities include robust error handling and fallback mechanisms
