# 034 – Tijdlijn van bewijsstukken

**Status:** klaar <!-- idee | uitgewerkt | in bouw | klaar -->
**Laatst bijgewerkt:** 2026-11-18

## Doel

Als **coach** of **gildemeester** wil ik op de pagina van één student ([spec 032](../032-studentpagina/spec.md)) zien welke **bewijsstukken** de student in de loop van het semester heeft toegevoegd en aan welke vaardigheden hij ze heeft gekoppeld, zodat ik zie waar hij aan werkt, ook als er (nog) geen evaluatie is. Het vorige systeem ("The Markers") had zo'n tijdlijn met alle datapunten (evaluaties, feedback, reflecties, documenten, check-ins).

## Gebruikers

- [x] Coach
- [x] Gildemeester
- Geen verschil.

## Betrokken begrippen

- Collectie en bewijsstuk (Portflow); de tien vaardigheden OC … RE ([vaardigheden-openict.md](../../docs/vaardigheden-openict.md)); de koppeling van doelnamen aan vaardigheden ([spec 005](../005-gegevens-ophalen/spec.md), F14)

## Onderzoek (2026-11-18, alleen lezend)

Niet beschreven in [portflow-API-reverse-engineer.md](../../docs/portflow-API-reverse-engineer.md); live gevonden:

- `GET /portfolios/{portfolio_id}/collections` (gepagineerd): de collecties van een portfolio die de gebruiker mag zien, met onder andere `id`, `name`, `is_private`, `evidence_count`, `goals_count`.
- `GET /portfolios/{portfolio_id}/collections/{collection_id}/evidence` (gepagineerd): per item `evidence` met `id`, `name`, `created_at`, `latest_version_created_at`, `latest_version_type` (`file`, `free_text`, `url`), `versions_count`, `date` (leeg in de steekproef) en `goals` (lijst van `{id, name, nickname, status}`).
- `GET /shares/shared-with-me` bevat per deling `share_type` en een lijst `collections` (bij delen van losse collecties).
- Steekproef van 3 portfolio's: 13 collecties, 624 bewijsstukken (396 bestanden, 226 vrije teksten, 2 links), 650 koppelingen aan de tien vaardigheden en 181 aan andere doelen. Koppelen aan een vaardigheid kan met dezelfde naamregels als bij evaluaties.
- `GET /portfolios/{portfolio_id}/evidence` (lijst van alles) geeft 403; per collectie ophalen is dus nodig.

## Functionele eisen

- [x] **F1 – Ophalen bij het openen van de studentpagina.** Opent de gebruiker de pagina van een student, dan toont die meteen wat er al bewaard is, en haalt het dashboard op de achtergrond de collecties en bewijsstukken van die student op (alleen lezen; zie Onderzoek). Is dat klaar, dan wordt de tijdlijn bijgewerkt zonder de pagina te herladen. Bij de tijdlijn staat wanneer de bewijsstukken voor het laatst zijn opgehaald ("Bijgewerkt om 14:32", of "Bewijsstukken ophalen…"). Per bewijsstuk wordt lokaal bewaard: de datum van toevoegen (`created_at`), de laatste versie, de soort (bestand, tekst, link), de naam, de collectie en de gekoppelde vaardigheden. Verversen ([spec 005](../005-gegevens-ophalen/spec.md)) blijft zoals het is.
  - Lukt ophalen niet (geen verbinding, geen toegang), dan blijft wat er bewaard is staan, met een korte melding.
  - *Acceptatie:* bij het openen van een studentpagina met een nep-Portflow met 2 collecties en 3 bewijsstukken staan die na het ophalen in de tijdlijn; zonder verbinding staat er een melding en blijft de rest van de pagina werken.
- [x] **F2 – Stippen per vaardigheid.** Onder de tijdlijn met evaluaties een tijdlijn zoals in The Markers: een **rij per vaardigheid** (OC … RE, in die volgorde) en een rij **Overig**, en van links naar rechts de semesterperiode met dezelfde weken als de tijdlijn met evaluaties. Elk bewijsstuk dat in de periode is **toegevoegd**, is een **stip** op de datum van toevoegen, in elke rij van een vaardigheid waaraan het gekoppeld is (een bewijsstuk met drie vaardigheden staat dus in drie rijen). De kleur van de stip hangt af van de soort: **bestand**, **tekst** of **link**, met een legenda. Staan er in één rij meer bewijsstukken op dezelfde dag, dan is dat één grotere stip met het aantal erin.
  - *Acceptatie:* een bewijsstuk (bestand) van 7 oktober, gekoppeld aan PL en SW, geeft een stip op 7 oktober in de rijen PL en SW, in de kleur van "bestand".
- [x] **F3 – Details.** Bij hover over een stip: de naam van het bewijsstuk (of de namen, bij een stip met een aantal), de soort, de collectie, de datum van toevoegen en van de laatste versie, en de gekoppelde vaardigheden.
- [x] **F4 – Overig.** Bewijsstukken die aan geen van de tien vaardigheden gekoppeld zijn (alleen aan een ander doel, of aan niets), staan in de rij **Overig**.
- [x] **F5 – Lege toestand.** Zonder bewijsstukken in de periode: "Nog geen bewijsstukken in deze semesterperiode."; zonder zichtbare collecties: "De student heeft (nog) geen collecties met je gedeeld."

### Buiten scope

- Bewijsstukken openen of downloaden.
- Feedback, reflecties en check-ins als aparte soorten datapunten zoals in The Markers (kan later; Portflow kent "vrije tekst", niet die soorten).

## Schermen

| Scherm | Bestand | Opmerking |
|---|---|---|
| Tijdlijn uit The Markers | — | Getoond door de gebruiker in de chat (2026-11-18), niet opgeslagen. Rijen: evaluaties per niveau, feedback, reflecties, documenten, check-ins; stippen per datapunt, kleur per bron. |

## Data

- **Bron:** Portflow API (zie Onderzoek), alleen lezen.
- **Privacy:** namen van bewijsstukken kunnen persoonlijke informatie bevatten; ze blijven lokaal en vallen onder Namen verbergen ([spec 033](../033-namen-verbergen/spec.md)) waar ze een studentnaam bevatten. De inhoud van bewijsstukken wordt niet opgehaald.

## Technische eisen

- De nieuwe endpoints komen in `docs/portflow-API-reverse-engineer.md` en `docs/architectuur.md`.
- Tests met een nep-Portflow, zoals bij [spec 005](../005-gegevens-ophalen/spec.md).

## Open vragen

- [x] Ophalen: bij het openen van de studentpagina, voor die student (F1).
- [x] Vorm: stippen per vaardigheid, zoals The Markers (F2).
- [x] Zonder vaardigheid: tonen in de rij Overig (F4).
- [x] Datum: de datum van toevoegen (F2); de laatste versie staat in de details (F3).

## Logboek

- 2026-11-18 – spec aangemaakt op verzoek van de gebruiker, met het onderzoek naar de Portflow-API en een voorstel
- 2026-11-18 – open vragen beantwoord door de gebruiker; status uitgewerkt
- 2026-11-18 – gebouwd: API-aanroepen in `portflow_api.py`, ophalen en stippen in `dashboard/evidence.py`, tabellen `evidence_items` en `evidence_fetches`, route `POST /studenten/<id>/bewijsstukken` (aangeroepen door `app.js` bij het openen), template `_evidence_timeline.html`. Endpoints vastgelegd in de API-documentatie (§4.8, §4.9) en `architectuur.md`. Tests met een nep-Portflow in `tests/test_evidence.py`; in de browser met echte gegevens gecontroleerd (een student met 31 stippen). Status klaar
