# 036 – Bewijsstuk lezen

**Status:** klaar <!-- idee | uitgewerkt | in bouw | klaar -->
**Laatst bijgewerkt:** 2026-11-18

## Doel

Als **coach** of **gildemeester** wil ik vanuit een feedbackvraag ([spec 035](../035-feedbackvragen/spec.md)) het bijbehorende bewijsstuk kunnen lezen, zodat ik de vraag en de reacties begrijp zonder naar Portflow te gaan.

## Gebruikers

- [x] Coach
- [x] Gildemeester
- Geen verschil.

## Betrokken begrippen

- Bewijsstuk en zijn soorten: bestand, tekst, link ([spec 034](../034-bewijsstukken-tijdlijn/spec.md))

## Onderzoek (2026-11-18, alleen lezend, niets gedownload)

- `GET /portfolios/{portfolio_id}/evidence/{evidence_id}` geeft **geen bestand** (zoals §4.7 van de API-documentatie zegt), maar JSON met de details: `name`, `description`, `feedback_status`, `created_at`, `updated_at`, `versions_count`, `goals_count`, `collections_count`, `date`, `latest_version_type`, en `latest_version` met `files`:
  - bij **tekst**: `files[0].free_text` met `free_text` (de tekst als HTML), `images` (ingevoegde afbeeldingen) en `has_pending_embedded_files`;
  - bij een **bestand**: `files[0].file` met `file_name`, `type` (bestandstype), `download_state` en `signed_id` (een ondertekende verwijzing); **geen downloadlink**.
- `…/versions/{id}`, `…/content` en `…/download` geven 404. Hoe een bestand te downloaden is, is nog onbekend (zie Buiten scope).

## Functionele eisen

*Gewijzigd op 2026-11-18 op verzoek van de gebruiker: geen tweede zijpaneel meer; de tekst van een tekst-bewijsstuk staat bovenaan het gesprek. Bestanden downloaden lukt niet en vervalt.*

- [x] **F1 – Tekst bovenaan het gesprek.** Is het bewijsstuk van een feedbackvraag van het soort **tekst**, dan staat in het feedbackpaneel ([spec 035](../035-feedbackvragen/spec.md), F4) de tekst van het bewijsstuk als **eerste** item van het gesprek, vóór de vraag van de student en de reacties: *tekst van het bewijsstuk → vraag van de student → reacties*.
  - *Acceptatie:* bij een feedbackvraag op een tekst-bewijsstuk staat bovenaan het gesprek de tekst, daarna de vraag en daarna de reacties.
- [x] **F2 – Andere soorten.** Is het bewijsstuk geen tekst (een bestand of een link), dan verandert er niets aan het gesprek.
- [x] **F3 – Ophalen bij het openen.** De tekst wordt bij het openen van het feedbackpaneel live uit Portflow gehaald (`GET /portfolios/{id}/evidence/{id}`) en niet bewaard. Lukt dat niet, dan staat er op die plek een korte melding en blijft de rest van het gesprek zichtbaar.
- [x] **F4 – Veilig tonen.** De tekst behoudt alleen eenvoudige opmaak (alinea, regelafbreking, opsomming, vet, cursief, kopje, citaat, link naar http(s)); al het andere wordt tekst of weggelaten. Ingevoegde afbeeldingen worden niet getoond; er staat hoeveel het er zijn.
- [x] **F5 – Namen verbergen.** Met Namen verbergen ([spec 033](../033-namen-verbergen/spec.md)) aan geldt de vervanging ook voor deze tekst.

### Buiten scope

- Een tweede zijpaneel met het bewijsstuk en de knop "Openen in Portflow" (gebouwd en weer weggehaald op verzoek van de gebruiker, 2026-11-18).

- Bestanden downloaden en tonen (pdf, Word, …): het downloadadres is niet gevonden (geraden adressen gaven 404; de verzoeken van Portflow binnen Canvas zijn in de ingebouwde browser niet te zien). De gebruiker liet dit los op 2026-11-18.
- Een bewijsstuk openen vanuit de stippen in de tijdlijn (niet gekozen).
- Oudere versies van een bewijsstuk.

## Schermen

Geen eigen ontwerp: een tweede zijpaneel in de stijl van het feedbackpaneel.

## Data

- **Bron:** `GET /portfolios/{portfolio_id}/evidence/{evidence_id}`, alleen lezen, bij het openen.
- **Bewaard:** niets.
- **Privacy:** de tekst van het bewijsstuk wordt alleen getoond; het Portflow-token gaat alleen naar Portflow zelf.

## Technische eisen

- De tekst wordt veilig getoond: alleen een vaste set eenvoudige opmaak blijft over (alinea, regelafbreking, opsomming, vet, cursief, link), al het andere wordt tekst.
- §4.7 van `docs/portflow-API-reverse-engineer.md` wordt gecorrigeerd met wat hierboven staat.
- Tests met een nep-Portflow.

## Open vragen

- [x] Waar: bovenaan het gesprek in het feedbackpaneel, alleen bij tekst (F1, F2; gewijzigd 2026-11-18).
- [x] Ophalen: bij het openen, live, niet bewaren (F3).
- [x] Bestanden: vervallen (2026-11-18).

## Logboek

- 2026-11-18 – spec aangemaakt op verzoek van de gebruiker, met het onderzoek naar de API; vragen beantwoord; status uitgewerkt
- 2026-11-18 – gebouwd: `portflow_api.evidence_detail`, `evidence.detail` en `evidence.safe_html` (alleen p, br, lijsten, vet, cursief, kopjes, citaat en http(s)-links; script, style en vermeldingen van andere bewijsstukken worden weggelaten of als "[naam]" getoond), route `/studenten/<id>/bewijsstukken/<id>`, tweede zijpaneel. F4: het adres van één bewijsstuk in de webapp van Portflow kon niet worden nagegaan zonder in te loggen; "Openen in Portflow" opent daarom het portfolio (`https://portfolio.drieam.app/portfolio/{id}`). §4.7 van de API-documentatie gecorrigeerd. Tests in `tests/test_evidence_detail.py`; in de browser met echte gegevens een bestand en een tekst geopend. Status klaar
- 2026-11-18 – gemeld door de gebruiker: "Openen in Portflow" gaf een foutmelding. Oorzaak: Portflow draait als tool in Canvas en heeft buiten Canvas geen sessie; het adres was bovendien niet gecontroleerd. De knop opent nu Portflow via het Canvas-adres uit Instellingen (F4). Door de gebruiker gedeeld voorbeeld van een download: Portflow geeft voor een bestand een tijdelijke, ondertekende S3-link (30 minuten geldig, zonder inloggen); hoe het dashboard zo'n link opvraagt, is nog niet onderzocht
- 2026-11-18 – de gebruiker gaf het adres van een bewijsstukpagina in Portflow; de knop gebruikt nu dat patroon, met Canvas als terugval. Kolommen `collection_id` en `portfolio_id` in `evidence_items` (met migratie voor bestaande databases); ze worden gevuld bij het volgende ophalen
- 2026-11-18 – aangepast op verzoek van de gebruiker: geen tweede zijpaneel; de tekst van een tekst-bewijsstuk staat bovenaan het gesprek in het feedbackpaneel (F1–F5 herschreven); bestanden downloaden vervalt. Status in bouw
- 2026-11-18 – omgebouwd: het feedbackpaneel haalt bij een tekst-bewijsstuk de tekst live op en zet die bovenaan het gesprek; het tweede paneel, de route `/studenten/<id>/bewijsstukken/<id>`, de knop "Openen in Portflow" en de bewaarde collectie per bewijsstuk zijn weggehaald. Tests in `tests/test_evidence_detail.py`; met echte gegevens gecontroleerd: tekst → vraag → reactie. Status klaar
