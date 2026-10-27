# Version 5 – Finale PNG im MCP und Transfer nach Amber

## Update

1. ZIP entpacken und alle Dateien in die GitHub-Repository-Wurzel hochladen.
2. Neu sind png_export.py und transfer_files.py. server.py und requirements.txt
   müssen ersetzt werden. Pillow wird beim Render-Build zusätzlich installiert.
3. Render neu deployen lassen. Token/URL bleiben gleich.
4. MCP in Amber neu verbinden. Das neue Tool export_logo_package muss erscheinen.
5. AGENT-ERGAENZUNG.txt an die Agentenanweisung anhängen. Diese Regeln ersetzen
   die frühere Anweisung, PNG selbst mit einem SVG-Renderer in Amber zu erstellen.

## Neuer Ablauf

Nach geprüftem SVG-Export:
`export_logo_package(export_id, trim_transparent=True, padding=1)`.

Antwortfelder:
- svg_text: vollständiges UTF-8-SVG (unverändert).
- png_base64: vollständige PNG-Dateidaten, base64-kodiert.
- svg_sha256, png_sha256: SHA-256 über die jeweiligen Dateibytes.
- svg_size_bytes, png_size_bytes: erwartete Dateigrößen.
- png: tatsächliche Maße und Exportparameter.
- svg_download_url, png_download_url: temporäre Download-Links.

Amber übernimmt die vollständigen strukturierten Felder in run_code, schreibt
SVG als UTF-8 und dekodiert PNG mit Python base64. Kein SVG-Renderer nötig.
Der optionale Helper transfer_files.py zeigt das Speichern und Prüfen; er läuft
im Amber-Arbeitsbereich und wird nicht automatisch dorthin übertragen.
Amber kann den Algorithmus mit vorhandenen Standardbibliotheken/Pillow ausführen.
Kein Zugriff auf Render-Dateipfade oder Render-Pythonmodule voraussetzen.

Wenn Amber strukturierte Tool-Ergebnisse nicht vollständig an run_code übergeben
kann, löst diese Erweiterung das nicht automatisch. Dann Daten erneut übertragen
oder die temporären Links manuell herunterladen. Die Hash-Prüfung verhindert,
dass unbemerkt gekürzte oder veränderte Daten als korrekte Datei verwendet werden.

## PNG-Regeln

- Höchstens 300 Pixel breit und 36 Pixel hoch, proportional skaliert.
- RGBA mit Alpha, ohne grauen/weißen Vorschau-Hintergrund.
- Supersampling und Lanczos-Downsampling.
- Standard: vollständig transparente Außenränder entfernen, 1 Pixel transparenten
  Rand ergänzen. Dieser Rand ist bereits in den maximalen Abmessungen enthalten.
- trim_transparent=False erhält den SVG-Zeichenbereich; padding 0 bis 5 erlaubt.
- Original-SVG bleibt unverändert. Es wird kein Slogan automatisch erkannt.
- Farbreferenz und Slogan müssen vor dem Export geprüft werden.

## Technischer Testauftrag in Amber

```text
Importiere das KaVo-Weblogo ohne Umfärbung. Prüfe und entferne den Slogan mit
inspect_svg_export, preview_svg_elements und edit_svg_export.
Erzeuge aus der neuesten SVG-Revision mit export_logo_package eine transparente
PNG. Übertrage svg_text und png_base64 vollständig in deinen Code-Arbeitsbereich.
Speichere SVG und PNG, prüfe beide SHA-256 und die tatsächlichen PNG-Maße.
Zeige die weiße PNG auf dunklem Hintergrund als Vorschau.
Status: Farbprüfung offen. Gib beide Dateien aus, noch kein SharePoint-Upload.
Wenn du die Tool-Daten nicht vollständig an run_code übergeben kannst, benenne
exakt diesen fehlenden Übergabeschritt.
```

## Lokal geprüft

Echtes KaVo-Logo ohne Slogan: PNG 118 × 36 Pixel, RGBA mit Transparenz.
PNG-Erzeugung, extreme Seitenverhältnisse, Leerbild-Ablehnung, Base64-Roundtrip,
Hash-/Größenprüfung und Transferhelper wurden lokal getestet.
SVG- und PNG-Ausgabe werden getrennt von den Vorschau-PNGs gespeichert.
Python-Syntax und ZIP geprüft. Kein Live-Deployment, keine MCP-Registrierung,
keine Amber-Dateiübergabe und kein SharePoint-Upload in dieser Umgebung getestet.

Finale PNGs liegen temporär auf Render. Neustarts/Inaktivität können Dateien
löschen. Links enthalten eine zufällige ID; jeder mit dem Link kann herunterladen.
SVG maximal 512 KB für die Textübergabe, höchstens 20 finale PNGs pro Prozess.
Für PNG-Erzeugung wird Pillow zusätzlich zu PyMuPDF verwendet.

---

## Vorherige Funktionen und Konfiguration

# Version 4: SVG-Farben und gezielte Bearbeitung

Enthält alle bisherigen PDF- und Webseiten-Werkzeuge. Neu:

- `inspect_svg_export(export_id, offset=0, limit=150)` listet Elemente mit IDs,
  Gruppenbeziehungen, Attributen, Klassen und deklarierte Farbwerte auf.
- `preview_svg_elements(export_id, element_ids)` zeigt eine Auswahl isoliert an.
- `edit_svg_export(export_id, remove_element_ids=None, color_map=None,
  element_colors=None)` erzeugt eine neue bearbeitete SVG-Revision.

## Update des bestehenden Dienstes

1. Alle Dateien aus diesem ZIP in die GitHub-Repository-Wurzel hochladen.
2. Insbesondere `svg_edit.py` neu hinzufügen und server.py/web_logos.py ersetzen.
3. Änderungen speichern und Render neu deployen lassen.
4. MCP in Amber erneut verbinden und prüfen, ob die drei neuen Tools erscheinen.
5. Den Inhalt von `AGENT-ERGAENZUNG.txt` an die Agentenanweisungen anhängen.
6. Token und MCP-URL bleiben unverändert.

## Neue Domains ohne Codeänderung freigeben

In Render eine Umgebungsvariable anlegen:

```
EXTRA_ALLOWED_HOSTS=www.hersteller.de,medien.hersteller.de,commons.wikimedia.org,upload.wikimedia.org
```

Nur tatsächlich benötigte, vertrauenswürdige Hostnamen einsetzen. Die
Herstelleradressen im Beispiel sind Platzhalter. Kein https://, kein Pfad,
keine Wildcards und keine IP-Adressen. Jede Subdomain separat nennen.
Diese zusätzlichen Hosts gelten für Web-SVGs und PDF-Downloads. PDF-Downloads
folgen weiterhin keinen Weiterleitungen. Nach Änderung neu deployen.
Domain-Freigabe bedeutet nicht, dass Commons-Dateiseiten oder jede Website
automatisch unterstützt werden: SVGs müssen als unterstützte HTML-Kandidaten
vorliegen; JavaScript-/CSS-only-Suche und PNG-Import sind nicht enthalten.

## Farben prüfen

Offizielle Referenz mit `import_website_logo` ohne color importieren.
Dann `inspect_svg_export` aufrufen. Die Angaben sind deklarierte Farbwerte,
keine vollständige CSS-Berechnung und kein Beweis einer verbindlichen Markenfarbe.
Amber muss die Referenz und Variante selbst prüfen. Bei Rasterreferenzen
liest diese Version keine Pixelwerte aus. Es gibt keine automatische Markensuche.

## Beispiel für Änderungen

```
edit_svg_export(
  export_id="AKTUELLE_ID",
  remove_element_ids=["e7"],
  color_map={"#ffffff": "#005CA9"}
)
```

Dieses Beispiel demonstriert ausschließlich die Technik. #005CA9 ist KEIN
bestätigter Markenfarbwert. e7 ist KEINE allgemeingültige Slogan-ID.
IDs immer aus der aktuellen SVG-Version lesen und visuell kontrollieren!
Bei der lokal geprüften KaVo-Datei war e7 der separate Sloganpfad.
Der jeweilige Export kann bei geänderter Quelldatei anders aufgebaut sein.

`color_map` ersetzt exakte deklarierte Farben in Attributen und Styles.
`element_colors={"e8":"#112233"}` setzt sichtbare Füll-/Linienfarben
gezielt auf einem Element oder den Grafikelementen einer Gruppe.
Nicht alle CSS-Vererbungen und !important-Regeln werden vollständig aufgelöst.
Transparenz none/transparent und interne Referenzen bleiben beim globalen
Farbersatz unverändert. Gruppen-/Symbolreferenzen können Sonderfälle enthalten.

Die Originaldatei bleibt bestehen. Jede Bearbeitung erhält eine neue export_id;
Element-IDs dafür neu ermitteln. SVG-Ansichtsbereich/viewBox bleibt erhalten.
Nach Sloganentfernung kann Leerraum verbleiben: Amber soll beim PNG-Export den
sichtbaren Inhalt prüfen und vorsichtig zuschneiden, ohne Schutzraum zu verlieren.
Kein automatisches Zerschneiden von zusammenhängenden Pfaden; solche Slogans
sind mit diesem Werkzeug nicht unabhängig entfernbar.

PNG-Finalexport (300 × 36 maximal) und SharePoint-Upload erfolgen weiterhin in
Amber, nicht in diesem MCP. Vorschau-PNGs sind nicht die Produktionsdateien.

## Tests Version 4

Lokal geprüft: CSS-/Attribut-Farben auslesen, globaler Farbersatz,
Elemententfernung, Isolationsvorschau, unveränderte Originaldatei, ungültige
Element-IDs/Farben und Domain-Konfiguration. An der echten KaVo-SVG wurde der
Slogan separat angezeigt und entfernt; die Vorschauen wurden visuell geprüft.
Farbersatz wurde als technischer Test durchgeführt, nicht als Markenfreigabe.

Reine SVG-Funktionen wurden mit einem HTTPX-Import-Platzhalter getestet;
HTTPX/FastMCP waren hier nicht installiert. Python-Syntax und ZIP sind geprüft.
Live-Deployment, Registrierung der MCP-Tools und Amber-Integration stehen aus.

---

## Dokumentation der vorherigen Basisfunktionen

# Neu: SVG-Logos direkt aus Hersteller-Webseiten

Diese Version enthält alle bisherigen PDF-Werkzeuge und zusätzlich:

- `inspect_website_logos(page_url)`: SVG-Bildquellen und Inline-SVGs im HTML finden.
- `import_website_logo(page_url, svg_url=None, inline_index=None, color=None)`:
  gefundenes SVG herunterladen/bereinigen, optional einfärben und bereitstellen.
- `preview_export(export_id)`: wie bisher die Vorschau prüfen.

Freigegeben sind vorerst nur `www.kavo.com`, `kavo.com`,
`www.germany.nsk-dental.com`, `germany.nsk-dental.com`.
Für SVG-Webabrufe kann `WEB_HOSTS` in `web_logos.py` um vertrauenswürdige
Herstellerhosts ergänzt werden. Externe CDN-Kandidaten werden zwar angezeigt,
aber erst nach expliziter Host-Freigabe heruntergeladen.
Die PDF-Download-Freigabe bleibt separat auf NSK beschränkt.

## Update

Alle Dateien aus dem ZIP in die Wurzel des bestehenden GitHub-Repositorys laden.
`web_logos.py` muss neu hinzugefügt, `server.py` ersetzt werden. Danach Render
neu deployen und in Amber die Tool-Liste durch erneutes Verbinden aktualisieren.
Token und Server-URL bleiben gleich. Keine Zugangsdaten ins Repository laden.

## Auftrag für Amber

```text
Nutze inspect_website_logos für https://www.kavo.com/de-de.
Wähle die SVG-Quelle des KaVo-Herstellerlogos aus der Kandidatenliste.
Importiere sie mit import_website_logo in #005CA9.
Prüfe das Ergebnis mit preview_export.
Gib download_url exakt und vollständig einschließlich .svg zurück.
Nutze die MCP-Werkzeuge und nicht nur die Textausgabe der Websuche.
```

Für Originalfarben color weglassen oder null verwenden. Das KaVo-Weblogo ist
in der hier geprüften Datei weiß und auf weißem Hintergrund kaum sichtbar.
Die neue Web-SVG-Vorschau hat deshalb einen grauen Hintergrund; das SVG selbst
wird dadurch nicht mit einem Hintergrund versehen.

## Funktionsgrenzen und Schutz

Es wird HTML abgerufen, kein Browser oder JavaScript ausgeführt. Unterstützt
werden SVG-URLs in img/object/embed/link/a/source und SVG direkt im HTML.
Logos ausschließlich aus CSS-Hintergründen, JavaScript, externen Sprites,
Rasterbildern oder nicht freigegebenen CDN-Hosts werden nicht automatisch
extrahiert. Komplexe Filter werden entfernt; Darstellung deshalb prüfen.
Keine automatische Zuschneidung: ursprünglicher SVG-Zeichenbereich bleibt erhalten.

Weiterleitungen nur zu erneut geprüften freigegebenen HTTPS-Hosts, maximal
fünf Abrufe pro URL, 2 MB pro HTML/SVG und 45 Sekunden pro Abrufkette.
DTD/Entities werden abgelehnt; aktive Inhalte, nicht unterstützte Elemente
und Attribute werden entfernt. Externe SVG-Ressourcen werden abgelehnt.
Farbe #RRGGBB ersetzt sichtbare Füll-/Linienfarben sowie Verlaufsfarben.
Bei mehrfarbigen Logos ist das eine einfarbige Umfärbung.

Wie bisher sind Exportlinks temporär, mit jedem Link öffentlich abrufbar und
nach Neustart möglicherweise ungültig. Token ist nur für MCP-Aufrufe nötig.

## Tests dieser Version

Mit echtem KaVo-HTML wurde die Logo-URL gefunden. SVG in Originalfarben und
Blau wurde lokal bereinigt und gerendert; die blaue Vorschau wurde visuell
geprüft. DTD, externe Referenzen und nicht erlaubte URLs wurden abgelehnt;
Script-/Event-Attribute wurden entfernt. Python-Syntax und ZIP wurden geprüft.
Die lokalen Tests der reinen HTML-/SVG-Funktionen ersetzten das nicht verfügbare
HTTPX-Modul durch einen Import-Platzhalter. Netzwerkcode, FastMCP-Laufzeit,
Deployment und Amber-Integration sind hier nicht live getestet.
Ein Versuch, die Test-Abhängigkeiten zu installieren, scheiterte an einem
Hash-/Downloadfehler der Umgebung. Das bestehende funktionierende Deployment
wurde nicht verändert.

---

# Amber PDF-Werkzeuge – Version 3

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
