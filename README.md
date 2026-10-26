# Amber PDF-Downloader

Python-MCP-Server zum Herunterladen öffentlich zugänglicher NSK-PDFs.

## Umfang und Grenze

Das Werkzeug `download_pdf(url)` lädt die PDF auf den MCP-Server und gibt Datei-ID,
Größe und Seitenzahl zurück. Es überträgt keine Datei in Ambers Arbeitsbereich.
Logo-Extraktion und SVG-Export sind nicht enthalten. Dafür müssen weitere Tools
auf demselben Server oder eine separate Dateiübergabe ergänzt werden.

## GitHub

1. ZIP entpacken.
2. Auf GitHub ein neues Repository anlegen.
3. Den Inhalt dieses Ordners in die Wurzel des Repositorys hochladen.
   `server.py`, `requirements.txt` und `render.yaml` müssen direkt dort liegen.
4. Keine Zugangstoken oder PDF-Dateien ins Repository hochladen.

## Render: manuelle Einrichtung

1. Render öffnen und `New > Web Service` wählen.
2. GitHub-Repository verbinden; Runtime `Python 3` auswählen.
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `python server.py`
5. Umgebungsvariable `PYTHON_VERSION` auf `3.11.11` setzen.
6. `MCP_AUTH_TOKEN` als geheime Umgebungsvariable setzen (mindestens 32 Zeichen).
   Einen Zufallswert lokal erzeugen:

   ```sh
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

7. Passenden Tarif auswählen und bereitstellen. Preise im Render-Dashboard prüfen.

Alternativ `New > Blueprint` verwenden und dieses Repository auswählen.
`render.yaml` erzeugt dann den Dienst und einen zufälligen Token. Den generierten
Token im Render-Dashboard unter den Umgebungsvariablen des Dienstes nachsehen.

## Amber verbinden

Mit Entwickler-Rolle: `Benutzereinstellungen > Konnektoren > Apps > MCP hinzufügen`.
Mit Admin-Rolle: entsprechend in den Admin-Einstellungen.

- Name: `PDF-Downloader`
- Server-URL: `https://DEIN-DIENST.onrender.com/mcp`
- Authentifizierung: Bearer-Token
- Token: derselbe Wert wie `MCP_AUTH_TOKEN` auf Render

Anschließend verbinden und im Amber-Chat unter Apps aktivieren.
Transport-Kompatibilität und Dateiverarbeitung müssen in eurer Amber-Umgebung
praktisch getestet werden.

## Test in Amber

```text
Nutze download_pdf für diese URL und melde Datei-ID und Seitenzahl:
https://www.germany.nsk-dental.com/admin/wp-content/uploads/PR-D1371DEv1_230421.pdf
```

## Betrieb

- Nur die beiden in `ALLOWED_HOSTS` aufgeführten NSK-Domains sind erlaubt.
- Nur HTTPS an Port 443; keine Weiterleitungen und keine Zugangsdaten in URLs.
- 20 MB pro Datei, höchstens 20 gespeicherte Dateien, Download-Limit 45 Sekunden.
- Abgelaufene Dateien werden beim nächsten Werkzeugaufruf nach einer Stunde gelöscht.
- Speicher ist temporär. Neustarts oder neue Deployments können Dateien löschen.
- Der Token gehört ausschließlich in Render und in Ambers Verbindungseinstellungen.
- Freigaben weiterer Domains nur für vertrauenswürdige öffentliche Anbieter ergänzen.
  Für beliebige URLs sind zusätzliche Netzwerkschutzmaßnahmen notwendig.
- PyMuPDF wird zur PDF-Prüfung verwendet; seine AGPL-/kommerziellen Lizenzbedingungen
  sind für die beabsichtigte Nutzung zu prüfen: https://pymupdf.readthedocs.io/en/latest/about.html

## Prüfung dieses Pakets

Python-Syntax und ZIP-Inhalt wurden geprüft. Kein Live-Deployment und kein
Integrationstest mit Amber durchgeführt. Abhängigkeiten sind als Versionsbereiche
angegeben; für produktiven Betrieb nach erfolgreichem Test feste Versionen verwenden.
