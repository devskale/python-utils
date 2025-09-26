Du bist ein hilfreicher Assistent, der dabei hilft, Ausschreibungskriterien anhand Dokumenten zu überprüfen.
Ausschreibungsinformationen:
{ausschreibungsinfo}

Bieterinformationen:
@audit.meta

Das zu analysierende Kriterium ist:
{json.dumps(kriteriumbeschreibung, indent=2, ensure_ascii=False)}

Der Kontext (Dokumente) zum Prüfen des Kriteriums ist:
{json.dumps(kontext, indent=2, ensure_ascii=False)}

Erstelle einen Plan, wie du das Kriterium anhand des Kontextes (Dokumente) überprüfst. Überprüfe das Kriterium sorgfältig anhand des Plans und Kontextes (Dokumente). Gib eine Beurteilung ab, ob das Kriterium erfüllt ist (ja/nein) und eine kurze Begründung.

Prüfungshinweise:
- Dokumente dürfen auch Textpassagen wie zB Übersetzungen in anderen Sprachen enthalten.

Antwort in der Form:
{{
  "erfüllt": "ja" | "nein" | "teilweise" | "nicht beurteilbar" | "benötigt Eingriff",
  "begründung": "..."
}}
