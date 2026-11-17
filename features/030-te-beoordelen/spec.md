# 030 – Te beoordelen

**Status:** klaar <!-- idee | uitgewerkt | in bouw | klaar -->
**Laatst bijgewerkt:** 2026-11-17

## Doel

Als **coach** of **gildemeester** wil ik op de pagina Evaluaties zien welke evaluatieverzoeken op mijn beoordeling wachten, sinds wanneer en voor welke vaardigheden, zodat ik weet wat ik in Portflow moet oppakken en niemand te lang laat wachten.

Het blok "Hier komen de evaluatieverzoeken die op jouw beoordeling wachten." onderaan de pagina Evaluaties ([spec 029](../029-tijdlijn-evaluaties/spec.md)) wordt deze lijst. Beoordelen zelf gebeurt in Portflow ([begrippen.md](../../docs/begrippen.md): *Te beoordelen*).

## Gebruikers

- [x] Coach
- [x] Gildemeester
- Geen verschil: de lijst bevat de verzoeken die aan de gebruiker gericht zijn, ongeacht zijn rol.

## Betrokken begrippen

- Evaluatieverzoek (review request), Te beoordelen: [begrippen.md](../../docs/begrippen.md)
- Openstaande evaluaties en eindassessment: [voortgangsregels.md](../../docs/voortgangsregels.md#openstaand)
- De vaardigheden OC … RE van een verzoek (uit de feedback-items met hetzelfde `review_request_id`)

## Functionele eisen

- [x] **F1 – Lijst "Te beoordelen".** Op de pagina Evaluaties staat, op de plek van de huidige plaatshouder onder de tijdlijn, een kaart **"Te beoordelen"** met de openstaande verzoeken die **aan de gebruiker** gericht zijn: status *niet begonnen* of *in uitvoering*. Verzoeken die zijn ingediend, beoordeeld of geweigerd staan er niet in. Per verzoek staat er:
  - de student (initialen-avatar en naam);
  - de titel van het verzoek (door de student gekozen);
  - de vaardigheden, als codes in de volgorde OC … RE;
  - de datum van indienen;
  - de wachttijd: "vandaag", "1 dag", "5 dagen".
  - *Acceptatie:* een verzoek "OC & KO 1ste evaluatie", 5 dagen geleden ingediend, staat in de lijst met OC en KO, de datum en "5 dagen".
- [x] **F2 – Oudste eerst.** Het verzoek dat het langst wacht, staat bovenaan.
  - *Acceptatie:* van verzoeken van 2 en 9 dagen oud staat dat van 9 dagen bovenaan.
- [x] **F3 – Los van de keuze "wie".** De lijst toont alle openstaande verzoeken aan de gebruiker; de keuzelijst "wie" van de tijdlijn ([spec 029](../029-tijdlijn-evaluaties/spec.md), F2) geldt er niet voor. Verzoeken van studenten die niet in het dashboard staan, worden **ook** getoond, met de naam uit Portflow; van zo'n student zijn de vaardigheden niet bekend, dan staat er "–".
  - *Acceptatie:* een verzoek van een student die niet in de studentenlijst staat, verschijnt met zijn naam uit Portflow en "–" bij de vaardigheden.
- [x] **F4 – Eindassessment.** Een verzoek dat alle tien vaardigheden bevat, staat als één regel met het label "Assessment ingeleverd" ([design-system.md](../../docs/design-system.md#niveaulabels)) in plaats van tien codes.
- [x] **F5 – Lege toestand.** Zonder openstaande verzoeken staat er "Er wachten geen evaluatieverzoeken op jouw beoordeling." Zijn de gegevens nog nooit opgehaald, dan staat er dat de lijst na "Verversen" verschijnt.
- [x] **F6 – Teller in het menu.** Achter "Evaluaties" in de zijbalk staat het aantal openstaande verzoeken aan de gebruiker, als dat groter is dan 0 (zoals in het Kompas-ontwerp, [design-system.md](../../docs/design-system.md#schermen)).
  - *Acceptatie:* met 3 openstaande verzoeken staat er "Evaluaties 3"; met 0 staat er geen teller.

### Buiten scope

- Beoordelen in het dashboard; dat blijft in Portflow.
- Een link naar het verzoek in Portflow (gekozen 2026-11-17: geen link).
- De gewenste datum van de student en de toelichting bij het verzoek (niet gekozen; de toelichting wordt niet bewaard).
- Verzoeken aan andere beoordelaars (daarvan is de status niet op te halen; [spec 005](../005-gegevens-ophalen/spec.md), F3). Die blijven als `?` zichtbaar in de voortgangstabel.

## Schermen

Geen eigen ontwerp. Het zijpaneel "Te beoordelen" uit het Kompas-ontwerp ([design-system.md](../../docs/design-system.md#schermen)) is het uitgangspunt. **Afwijkingen:** een kaart op de pagina Evaluaties in plaats van een zijpaneel; vaardigheden en wachttijd in plaats van de gewenste datum; geen klik naar Portflow en geen "Alle evaluaties bekijken →".

## Data

- **Bron:** `GET /portfolios/{eigen_portfolio_id}/progress-review/invitations/received` ([API §4.6](../../docs/portflow-API-reverse-engineer.md); [architectuur.md](../../docs/architectuur.md)). Dit verzoek doet "Verversen" al ([spec 005](../005-gegevens-ophalen/spec.md), F3), maar bewaart nu alleen de status. Nieuw: de verzoeken zelf bewaren in een lokale tabel: `review_request_id`, titel, naam en Portflow-id van de student, portfolio-id, status en `created_at`.
- **Vaardigheden:** uit de lokale tabel `evaluations` (zelfevaluaties met hetzelfde `review_request_id`).
- **Verversen:** met "Verversen", zoals de rest; geen eigen Portflow-verzoeken op de pagina.
- **Privacy:** de toelichting van de student (`review_request_note`) en de gewenste datum worden niet bewaard. Naam en titel staan alleen in de lokale database; "Alles verwijderen" ([spec 014](../014-alles-verwijderen/spec.md)) wist ook deze tabel, en een reservekopie volgt de bestaande regels. De profielfoto (tijdelijke S3-URL) wordt niet gebruikt; de avatar toont initialen.

## Technische eisen

- Het opslaan gebeurt in de bestaande ophaalronde; geen extra Portflow-verzoek.
- Tests voor F1–F6 met verzonnen namen, ook voor het opslaan in de ophaalronde.

## Open vragen

- [x] Welke verzoeken: alleen die aan de gebruiker (F1).
- [x] Volgorde: oudste eerst (F2).
- [x] Per verzoek: student, titel, vaardigheden, datum van indienen en wachttijd; geen toelichting en geen gewenste datum (F1).
- [x] Teller bij "Evaluaties" in het menu: ja (F6).
- [x] Link naar Portflow: nee (buiten scope).
- [x] Verzoeken van studenten die niet in het dashboard staan: wel tonen (F3).

## Logboek

- 2026-11-17 – spec aangemaakt op verzoek van de gebruiker, met een voorstel en open vragen
- 2026-11-17 – open vragen beantwoord door de gebruiker; status uitgewerkt
- 2026-11-17 – gebouwd: tabel `received_requests` (gevuld in de ophaalronde, `portflow_fetch.Fetcher._save_requests`; een mislukte aanroep houdt de vorige lijst), lijst in `dashboard/requests_to_review.py`, kaart op `evaluations.html`, teller in de zijbalk; "Alles verwijderen" telt en wist de tabel. F5: "nog niet opgehaald" volgt een eigen instelling (`requests_last_fetched`), zodat de lijst ook na een eerdere ophaalronde zonder verzoeken eerlijk is. Tests in `tests/test_to_review.py`; in de browser bekeken met echte gegevens na Verversen (21 openstaande verzoeken). Status klaar
