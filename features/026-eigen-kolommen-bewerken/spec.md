# 026 – Eigen kolommen in Student bewerken

**Status:** klaar
**Laatst bijgewerkt:** 2026-11-11

## Doel

Als **coach** of **gildemeester** wil ik de waarden van de eigen kolommen ([spec 024](../024-keuzelijsten/spec.md)) van een student ook in **Student bewerken** ([spec 011](../011-student-bewerken/spec.md)) kunnen aanpassen. Dan staan alle gegevens van die student op één plek, en hoef ik niet in de tabel te zoeken.

## Gebruikers

- [x] Coach
- [x] Gildemeester
- Geen verschil.

## Betrokken begrippen

Eigen kolom, keuzelijst ([gegevensmodel](../../docs/gegevensmodel.md#kolommen)).

## Functionele eisen

- [x] **F1 – Blok Eigen kolommen.** In Student bewerken staat boven Notities een blok **"Eigen kolommen"**. Daarin staat per eigen kolom een veld, in de volgorde van de pagina Kolommen, met de naam van de kolom als label en de beschrijving als uitleg. Zijn er geen eigen kolommen, dan is het blok er niet.
  - *Acceptatie:* met twee eigen kolommen → twee velden in de juiste volgorde; zonder eigen kolommen → geen blok.
- [x] **F2 – Veld per type.** Een percentage is een getalveld met "%", vrije tekst een tekstveld, en een keuzelijst een keuzelijstje met "–" en de keuzes van de kolom. De huidige waarde staat ingevuld.
  - *Acceptatie:* een student met 75 bij een percentagekolom → het veld toont 75.
- [x] **F3 – Opslaan.** Opslaan bewaart de eigen kolommen samen met de andere velden. Een leeg veld maakt de waarde leeg. De controles zijn dezelfde als in de tabel ([spec 001](../001-studentenoverzicht/spec.md), F8): een percentage is een heel getal van 0 tot en met 100, en een keuze moet uit de lijst van de kolom komen.
  - *Acceptatie:* vul 80 in → in het Overzicht staat 80%; maak het veld leeg → de cel is leeg.
- [x] **F4 – Ongeldige waarde.** Is een waarde ongeldig, dan wordt **niets** opgeslagen. Het formulier blijft staan met de ingevulde waarden en een melding, net als bij de andere velden.
  - *Acceptatie:* vul 120 in bij een percentage en wijzig ook de naam → melding; naam en percentage zijn onveranderd.
- [x] **F5 – Ook bij handmatig toevoegen.** Het formulier Student handmatig toevoegen ([spec 017](../017-student-handmatig-toevoegen/spec.md)) heeft hetzelfde blok.
  - *Acceptatie:* voeg een student toe met een waarde in een eigen kolom → de waarde staat in het Overzicht.

### Buiten scope

- Eigen kolommen beheren (toevoegen, verwijderen): dat blijft op de pagina Kolommen.

## Schermen

Geen eigen ontwerp. Volgt het formulier Student bewerken.

## Data

- **Bron:** eigen opslag (`custom_values`). Geen Portflow-aanroepen.

## Technische eisen

- De controle van een waarde staat op één plek, voor de tabel en het formulier samen.
- Tests: F1-F5.

## Keuzes bij het bouwen, ter controle

- Staat een kolom niet in het verstuurde formulier (bijvoorbeeld omdat hij intussen is toegevoegd), dan blijft de waarde van die kolom onveranderd.

## Open vragen

- [x] **Handmatig toevoegen:** ja, hetzelfde blok (F5).
- [x] **Plek:** een eigen blok boven Notities (F1).
- [x] **Ongeldige waarde:** niets opslaan, melding tonen (F4).

## Logboek

- 2026-11-11 – spec aangemaakt op verzoek van de gebruiker; vragen beantwoord; status in bouw
- 2026-11-11 – gebouwd: één controle `check_custom_value` voor tabel en formulier; de waarden worden in dezelfde transactie bewaard als de andere velden. 6 nieuwe tests; alle tests slagen. In de app bekeken: het blok Eigen kolommen staat boven Notities, met je kolom Signaal. Status klaar
