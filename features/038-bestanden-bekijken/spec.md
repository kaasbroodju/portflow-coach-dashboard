# 038 – Bestanden bekijken

**Status:** klaar <!-- idee | uitgewerkt | in bouw | klaar -->
**Laatst bijgewerkt:** 2026-11-22

## Doel

Als **coach** of **gildemeester** wil ik een bewijsstuk dat een bestand is (afbeelding, pdf, Word, PowerPoint, Excel) in het dashboard kunnen bekijken, zodat ik weet waar een feedbackvraag of evaluatie over gaat zonder naar Portflow te gaan.

Vult [spec 036](../036-bewijsstuk-lezen/spec.md) aan; daar viel het bekijken van bestanden af omdat het downloadadres nog niet bekend was.

## Gebruikers

- [x] Coach
- [x] Gildemeester
- Geen verschil.

## Betrokken begrippen

- Bewijsstuk en zijn soorten: bestand, tekst, link ([spec 034](../034-bewijsstukken-tijdlijn/spec.md))

## Onderzoek (2026-11-22, alleen lezend, niets gedownload)

Gevonden in `docs/export_single_student.py` (werkend script van de gebruiker) en nagegaan met echte gegevens (alleen vorm en aantallen):

- `GET /portfolios/{portfolio_id}/evidence/{evidence_id}` geeft in `latest_version.files[]` per bestand een `id` (het versiebestand), `display_name` en `file` (`file_name`, `type`, `download_state`).
- `GET /portfolios/{portfolio_id}/evidence-version-files/{id}/preview-url` (met het token) geeft:
  - `mime_class`: `pdf`, `doc`, `xls`, `ppt`, `image`, `video`, …
  - `preview_state`: `available` of `inconvertible` (video);
  - `download_url`: het origineel, als bijlage;
  - `preview_url` (pdf, Word, Excel, PowerPoint): een **pdf**, inline. Portflow zet Word, Excel en PowerPoint dus zelf om naar pdf;
  - `object_url` (afbeeldingen): de afbeelding, inline.
  - Alle links zijn ondertekende S3-links op `portflow-euw1-production-storage.s3.eu-west-1.amazonaws.com`, **30 minuten** geldig, zonder token te openen.
- Van 190 bekeken bestanden: png 90, docx 62, mp4 40, pdf 10, pptx 4, xlsx 3, webp 3.

Gevolg: alles wat de gebruiker noemt is te tonen als **pdf** of **afbeelding**, met de pdf-viewer en de afbeeldingsweergave van de browser zelf. Er is geen extra pakket nodig en het bestand gaat niet naar een andere dienst (zoals Office Online).

## Functionele eisen

- [x] **F1 – Bestand bekijken.** Klik je in "Bewijsstukken per vaardigheid" op een bolletje van een bestand, dan toont het zijpaneel het bestand onder de naam van het bewijsstuk en boven de feedbackvragen: een afbeelding als afbeelding, een pdf, Word-, PowerPoint- of Excelbestand als pdf (de omzetting van Portflow).
  - *Acceptatie:* bolletje van een docx → in het zijpaneel staat het document als pdf, door te bladeren.
- [x] **F1a – Groot bekijken.** Bij elk getoond bestand een knop **"Groot bekijken"** die het bestand over bijna het hele scherm opent, boven het dashboard; sluiten met een sluitknop, Esc of een klik ernaast.
  - *Acceptatie:* "Groot bekijken" bij een PowerPoint → de pdf vult bijna het scherm; Esc sluit hem en het zijpaneel staat er nog.
- [x] **F2 – Ook in het feedbackpaneel.** Hetzelfde bovenaan het gesprek in het feedbackpaneel, zoals de tekst van een tekst-bewijsstuk ([spec 036](../036-bewijsstuk-lezen/spec.md), F1).
- [x] **F3 – Meerdere bestanden.** Heeft een bewijsstuk meer bestanden, dan staan ze onder elkaar, elk met zijn eigen knoppen.
- [x] **F4 – Origineel downloaden.** Bij elk bestand een knop **"Downloaden"** die het origineel (bijvoorbeeld de .pptx) opslaat.
- [x] **F5 – Video.** Een video (`mime_class` `video`) speel je af in het zijpaneel en bij Groot bekijken, met de afspeelknoppen van de browser. Portflow maakt van video geen voorbeeld; het dashboard gebruikt daarom het origineel.
- [x] **F5a – Niet te tonen.** Is er geen voorbeeld en is het geen video of afbeelding (`preview_state` niet `available`), dan staat er "Dit bestand kan niet in het dashboard worden getoond" met de knop Downloaden.
- [x] **F6 – Laden en fouten.** Tijdens het ophalen staat er "Bestand ophalen…". Lukt het niet (geen verbinding, verlopen token), dan een korte melding; de rest van het paneel blijft zichtbaar.
- [x] **F7 – Opruimen.** Bij het starten verwijdert het dashboard bewaarde bestanden die 30 dagen niet zijn geopend. **Alles verwijderen** ([spec 014](../014-alles-verwijderen/spec.md)) wist de hele map.
  - *Acceptatie:* een bestand dat 31 dagen niet is geopend, is na het starten weg; een bestand dat gisteren is geopend, blijft.
- [x] **F8 – Namen verbergen.** Met Namen verbergen ([spec 033](../033-namen-verbergen/spec.md)) aan worden bestanden gewoon getoond; hun inhoud kan niet worden geanonimiseerd (gekozen 2026-11-22). De bestandsnaam volgt wel de vervanging van namen.

### Buiten scope

- Afbeeldingen die in een tekst-bewijsstuk zijn ingevoegd.
- Oudere versies van een bewijsstuk.
- Bestanden vooraf ophalen bij Verversen.

## Schermen

Geen eigen ontwerp; in de stijl van het zijpaneel ([spec 037](../037-evaluaties-lezen/spec.md)).

## Data

- **Bron:** `GET /portfolios/{pid}/evidence/{eid}` en `GET /portfolios/{pid}/evidence-version-files/{id}/preview-url`, bij het openen; daarna de S3-link **zonder** token.
- **Bewaard:** het voorbeeld (pdf of afbeelding) of de video in een cache in de gegevensmap, zie *Opslag*.
- **Privacy:** bestanden van studenten blijven lokaal; het token gaat alleen naar `portfolio.drieam.app`, nooit naar S3; de S3-links worden niet bewaard en niet gelogd.

### Opslag (gekozen 2026-11-22)

Een map **`bestanden/` in de gegevensmap**, naast `dashboard.sqlite3` (in een git-checkout `data/bestanden/`, in een installatie `…/Portflow coach dashboard/data/bestanden/`):

- **Waarom daar:** alle gegevens van de app staan al op die plek; de map staat buiten git, wordt bij bijwerken niet aangeraakt, en Instellingen › Data toont al waar hij staat. Eén plek is ook eenvoudig uit te leggen ("alles van het dashboard staat in die ene map").
- **Waarom niet in de database:** bestanden als BLOB maken de database en elke reservekopie groot en traag.
- **Waarom niet in een tijdelijke of cachemap van het systeem:** die verschilt per macOS en Windows, de gebruiker ziet hem niet, en "Alles verwijderen" zou dan op een tweede plek moeten wissen.
- **Afspraken:**
  - alleen ophalen bij het openen, niet alles bij Verversen (alleen al 40 video's van mogelijk honderden MB);
  - het **voorbeeld** bewaren (pdf of afbeelding; bij video het origineel), niet het origineel van Word, Excel en PowerPoint; downloaden haalt het origineel live op;
  - bestandsnaam = id van het versiebestand (geen naam van de student in de bestandsnaam); een nieuwe versie heeft een nieuw id;
  - opruimen na 30 dagen niet geopend (F7);
  - **Alles verwijderen** ([spec 014](../014-alles-verwijderen/spec.md)) wist de map; **reservekopieën** bevatten hem niet.

Niet gekozen: niets bewaren en het bestand bij elk openen opnieuw ophalen (geen studentbestanden op de laptop, maar trager en niet zonder internet).

## Technische eisen

- Het dashboard haalt het voorbeeld op (de browser praat voor het bekijken niet zelf met S3) en serveert het vanaf de eigen route, met het juiste type en `inline`. Alleen pdf, afbeeldingen (geen svg) en video worden zo geserveerd. **Downloaden** (F4) stuurt de browser door naar een verse ondertekende link van Portflow; die wordt niet bewaard.
- Alleen S3-links op de Portflow-host volgen; geen redirects met het token.
- Geen nieuwe dependency; tests met een nep-Portflow.
- `docs/portflow-API-reverse-engineer.md` (§4.7) en `docs/architectuur.md` (privacy, gegevensmap) bijwerken.

## Open vragen

- [x] 1. Waar: in het zijpaneel, met een knop "Groot bekijken" (F1, F1a).
- [x] 2. Opslag: een cache in `bestanden/` in de gegevensmap.
- [x] 3. Opruimen: na 30 dagen niet geopend, en met Alles verwijderen (F7).
- [x] 4. Video's: ook afspelen (F5).
- [x] 5. Namen verbergen: bestanden toch tonen (F8).

## Logboek

- 2026-11-22 – spec aangemaakt op verzoek van de gebruiker, met onderzoek naar `preview-url` (Portflow zet Word, Excel en PowerPoint om naar pdf); advies over opslag; open vragen
- 2026-11-22 – vragen beantwoord door de gebruiker: zijpaneel met "Groot bekijken", cache in `bestanden/` naast de database, opruimen na 30 dagen, video's afspelen, bestanden tonen ook met Namen verbergen; status uitgewerkt
- 2026-11-22 – gebouwd: `evidence_files.py` (voorbeeld ophalen via `preview-url`, cache `bestanden/<portfolio>-<versiebestand>.<ext>` met een klein .json-bestand per bestand, opruimen na 30 dagen bij het starten, wissen bij Alles verwijderen), `portflow_api.preview_url`, routes `/studenten/<id>/bestand/<portfolio>/<bestand>` (met `/downloaden`), de bestanden bovenaan het gesprek in het zijpaneel (`_conversation.html`, ook in het feedbackpaneel) en "Groot bekijken" (`_side_panel.html`, `app.js`). Meer bestanden staan onder elkaar. Ook: `portflow_api.get_json` volgt geen doorverwijzingen meer met het token. Tests in `tests/test_evidence_files.py`; met echte gegevens nagekeken: Word, PowerPoint en pdf als pdf, afbeelding, video (doorspoelen werkt), Groot bekijken met Esc, downloaden. Status klaar
- 2026-11-22 – na controle door de gebruiker: de bestandsnaam was slecht leesbaar en de knoppen stonden tegen de bovenrand. Oorzaak: de klasse `evidence-file` bestond al (de kleur van een bestandsbolletje). Het bestand staat nu in een eigen kaart (`file-card`) met een witte kop en ruimte rondom de naam en de knoppen
