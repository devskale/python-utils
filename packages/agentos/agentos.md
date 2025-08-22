# Agent Playground

## agentBieterDokDa
das ist ein agent der

projektverzeichnis@bieterverzeichnis (variable)
liest die auditliste
loopt durch die audit tags
   - wenn das kriterium mit einem dokument prüfbar ist, dann 
       - suche dokumentenliste (inkl. metadaten) des bieters 
       - nutze uniinfer mit einem modell zb tu@deepseek-r1
           - prompte kriterium, projektbeschreibung (kurz, dokumentenliste)
       - liste die passenden dokumente (mit konfidenz)
print summary



nutzt
- ofs package
- uniinfer package
- credgoo package