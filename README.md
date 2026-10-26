# Amber PDF-Werkzeuge – Version 2

Download, Seitenvorschau und SVG-Export direkt auf Render.

## Bestehendes GitHub-Projekt aktualisieren

1. ZIP entpacken.
2. In deinem GitHub-Repository `Add file > Upload files` öffnen.
3. Alle Dateien aus diesem ZIP direkt in die Repository-Wurzel hochladen.
   Insbesondere `server.py` ersetzen und `pdf_tools.py` neu hinzufügen.
4. Änderungen mit `Commit changes` speichern.
5. Render stellt bei aktiviertem Auto-Deploy die neue Version bereit.
   Andernfalls in Render `Manual Deploy > Deploy latest commit` wählen.
6. Den vorhandenen `MCP_AUTH_TOKEN` unverändert als Geheimnis bei Render behalten.
7. In Amber die MCP-Verbindung aktualisieren oder trennen und erneut verbinden,
   damit die neuen Werkzeuge geladen werden. Die genaue Schaltfläche kann variieren.

Server-URL: `https://download-pdf-n1pq.onrender.com/mcp`
Authentifizierung: Header `Authorization`, Wert `Bearer DEIN_TOKEN`.
Token niemals auf GitHub hochladen.

## Werkzeuge

- `download_pdf(url)`: PDF von einer freigegebenen NSK-Domain laden.
- `inspect_pdf(file_id, page_number=1, offset=0)`: Seitentext, Maße und bis zu
  200 Vektorpfade mit IDs, Positionen und Farben abrufen. Weitere Pfade über offset.
- `preview_page(file_id, page_number=1)`: Seite als PNG an Amber senden.
- `export_logo_svg(file_id, page_number, drawing_ids, color=None)`: ausgewählte
  Vektorpfade isolieren, optional mit #RRGGBB umfärben. Liefert SVG-Text und Link.
- `preview_export(export_id)`: Ergebnis als PNG visuell prüfen.

## Testauftrag für Amber

```text
Lade diese PDF mit download_pdf:
https://www.germany.nsk-dental.com/admin/wp-content/uploads/PR-D1371DEv1_230421.pdf
Untersuche Seite 1 mit inspect_pdf und preview_page.
Suche das NSK-Herstellerlogo unten rechts. Wähle nur die zugehörigen Vektorpfade.
Exportiere diese mit export_logo_svg in #005CA9.
Prüfe das Ergebnis mit preview_export und gib mir den SVG-Download-Link.
Wenn die Bildvorschau nicht angezeigt werden kann, sage das ausdrücklich.
```

Bei der hier geprüften Version dieser Broschüre ist das NSK-Logo auf Seite 1
Pfad-ID 12, ungefähr bei x=1040–1144 und y=461–499 PDF-Punkten.
Bei geänderter PDF muss diese Auswahl neu geprüft werden.
Seitenzählung beginnt bei 1; Pfad-IDs beginnen bei 0.

## Download-Links

Render setzt normalerweise `RENDER_EXTERNAL_URL`. Wenn download_url leer ist,
bei Render `PUBLIC_BASE_URL=https://download-pdf-n1pq.onrender.com` ergänzen.
Die resultierende Adresse sieht so aus:
`https://download-pdf-n1pq.onrender.com/files/ZUFAELLIGE_ID.svg`.

Jeder mit diesem Link kann das SVG herunterladen. Link-IDs sind zufällig und
werden nicht als öffentliche Liste angeboten. Die Links benötigen keinen
Bearer-Token. Nach Ablauf einer Stunde sind sie nicht mehr abrufbar;
abgelaufene Dateien werden beim nächsten Aufruf bereinigt. Neustarts und das
Einschlafen von Render Free können Dateien schon früher löschen.
Die ursprüngliche PDF ist nicht öffentlich abrufbar.

Wenn Amber keinen klickbaren Dateianhang erzeugt, den zurückgegebenen Link
verwenden. Falls Amber keine Bildantworten unterstützt, ist eine visuelle
Auswahl im Chat eingeschränkt. Das muss in eurer Amber-Umgebung getestet werden.

## Grenzen

- Bearbeitung erfolgt auf Render, nicht in Ambers eigenem Code-Arbeitsbereich.
- Keine automatische Logoerkennung: Amber muss die passenden Pfad-IDs auswählen.
- Nur vorhandene Vektorpfade. Rasterlogos und normale Textobjekte werden nicht
  automatisch vektorisiert oder mit exportiert.
- Komplexe Masken, Verläufe und Ebenen werden nicht vollständig rekonstruiert.
  Deshalb Exportvorschau prüfen. Gedrehte PDF-Seiten werden abgelehnt.
- Nur zwei NSK-Domains, HTTPS-Port 443, keine Weiterleitungen.
- Maximal 20 MB pro PDF, 20 PDFs und 20 SVG-Exporte pro Serverprozess.
- Download-Zeitlimit 45 Sekunden. Eingabeprüfung ersetzt keine vollständige
  Sandbox für fremde PDFs. Nur vertrauenswürdige Dokumentquellen freigeben.
- Die Python-Werkzeuge teilen den Server mit dem Downloader.
- PyMuPDF-Lizenzbedingungen (AGPL/kommerzielle Lizenz) für die eigene Nutzung prüfen:
  https://pymupdf.readthedocs.io/en/latest/about.html

## Neue Render-Installation

Python 3.11 oder neuer, Build `pip install -r requirements.txt`, Start
`python server.py`. `MCP_AUTH_TOKEN` muss mindestens 32 Zeichen enthalten.
In `render.yaml` ist der kostenlose Tarif ausdrücklich ausgewählt.
Bei Blueprint-Einrichtung wird ein zufälliger Token erzeugt. Bei manueller
Einrichtung einen eigenen Zufallswert als geheime Umgebungsvariable setzen.

## Prüfung

Python-Syntax und ZIP geprüft. Der Vektorexport wurde lokal mit der NSK-PDF
getestet und die PNG-Vorschau visuell geprüft. Ungültige Farben und Pfad-IDs
wurden geprüft. FastMCP-Laufzeit, öffentliches Deployment, Download-Route und
Amber-Integration wurden hier nicht live getestet. Abhängigkeiten sind
Versionsbereiche; nach erfolgreichem Integrationstest feste Versionen verwenden.
