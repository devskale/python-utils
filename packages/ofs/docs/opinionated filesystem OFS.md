# Opinionated Filesystem Structure

Ausschreibungsdokumente sind die Unterlagen, die ein Auftraggeber erstellt und veröffentlicht, um potenzielle Anbieter über eine geplante Vergabeleistung zu informieren. Sie enthalten u. a. die Leistungsbeschreibung, Teilnahmebedingungen, Vertragsbedingungen und Fristen.

Bieterdokumente sind die Unterlagen, die ein Bieter (Anbieter) im Rahmen einer Ausschreibung einreicht. Sie umfassen z. B. das Angebot, Preisblätter, Nachweise zur Eignung sowie ggf. Konzepte oder technische Lösungen.


## Supported Filetypes
- pdf (Textbasiert oder als Scan)
- Office-Dokumente (docx, xlsx, pptx)
- txt
- Bilder (jpg, jpeg, png)

# Verzeichnisstruktur

## Verzeichnisstruktur Top Level
Beinhaltet die aktuellen aktiven Ausschreibungsverzeichnisse (Projektordner):

- Ausschreibungsname
  - A (Ausschreibungsverzeichnis)
    - md (enthält Markdown-Versionen der Ausschreibungsdokumente)
  - B (Bieterverzeichnis)
    - BIETERNAME (dir, enthält Bieterdokumente)
       - md/ (enthält Markdown-Versionen der Bieterdokumente; unterstützte Dateitypen siehe "Supported Filetypes")
       - archive
- archive
  - Ausschreibungsname (archivierte ausschreibung)


## Reserved Directory Names
- A: Verzeichnisname, beinhaltet Ausschreibungsprojektdokumente
- B: Verzeichnisname, beinhaltet Bieterdokumente
- **md**: Für ein Verzeichnis, das Markdown-Dateien enthält.
- **proc**: Enthält verarbeitete Versionen von Dokumenten. 
- **archive**: Reserviert für ein Verzeichnis mit archivierten Projekten.

## Reserved Filenames
- **md/filename_PROCESSOR.md**: Datei, die die in Markdown konvertierte Version des Quelldokuments enthält. *PROCESSOR* steht für den verwendeten Konverter (z.B. docling, ocr, pdfplumber, ...).
- **md/filename/.**: Ein spezielles Unterverzeichnis, das extrahierte Inhalte (wie md, jpg, json) aus Quelldokumenten enthält.
- **PROJEKTNAME/PROJEKTNAME.md**
  - Enthält automatisch extrahierte Informationen von *PROJEKTNAME*.
- **PROJEKTNAME/PROJEKTNAME.json**
  - Enthält Informationen über das Projekt und zugehörige Dokumente.
  - Enthält zu jedem Dokument den original dateiname, die original dateigröße, den original hash wert.
  - enthält zu jedem

