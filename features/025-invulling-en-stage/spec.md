# 025 – Invulling bij semester, en (Stage) als project

**Status:** klaar
**Laatst bijgewerkt:** 2026-11-11

## Doel

Als **coach** of **gildemeester** wil ik minder hoeven in te vullen. De invulling volgt vaak uit het semester ([gegevensmodel](../../docs/gegevensmodel.md#student)). Ook wil ik in één oogopslag zien dat een student zonder project op stage is.

## Gebruikers

- [x] Coach
- [x] Gildemeester
- Geen verschil.

## Betrokken begrippen

Semester, invulling, project (squad): [begrippen](../../docs/begrippen.md). Invulling is een keuzelijst ([spec 024](../024-keuzelijsten/spec.md)).

## Functionele eisen

- [x] **F1 – Invulling uit het semester.** Kiest de gebruiker semester **3 of 4** en is de invulling van de student nog **leeg**, dan wordt de invulling **Open projecten**. Bij semester **8** wordt dat **Afstuderen**. Een ingevulde invulling verandert nooit.
  - *Acceptatie:* student zonder invulling, kies semester 3 → invulling Open projecten. Student met invulling Stage, kies semester 4 → blijft Stage. Semester 5 → invulling blijft leeg.
- [x] **F2 – Overal waar je het semester kiest.** Dat zijn het keuzelijstje in het Overzicht en in de Studentenlijst, Student bewerken, Student handmatig toevoegen en de Excel-import. Zie je de invulling op dezelfde pagina, dan is die na de keuze zichtbaar.
  - *Acceptatie:* in elk van deze vijf geldt F1. Bij de Excel-import geldt het alleen als de rij zelf geen invulling heeft en de student nog geen invulling heeft.
- [x] **F3 – Keuze ontbreekt.** Staat Open projecten of Afstuderen niet (meer) in de keuzelijst Invulling (vergeleken op code), dan voegt de app die keuze toe aan het eind van de lijst.
  - *Acceptatie:* verwijder Afstuderen, kies semester 8 → Afstuderen staat weer in de lijst en de student heeft die invulling.
- [x] **F4 – (Stage) als project.** Heeft een student de invulling **Stage** (code) en **geen project**, dan staat bij Project **"(Stage)"**. Dat geldt in het Overzicht en in de Studentenlijst. Heeft de student wel een project, dan blijft dat zichtbaar.
  - *Acceptatie:* Studentenlijst: de projectcel toont "(Stage)" zolang er geen project gekozen is.
- [x] **F5 – Eigen groep.** Bij **Groeperen: Project** komen deze studenten in een groep **"(Stage)"**, na de projecten en vóór "Zonder project". Het projectfilter verandert niet.
  - *Acceptatie:* een stagestudent zonder project staat in de groep "(Stage)", niet in "Zonder project".

### Buiten scope

- Andere afleidingen, bijvoorbeeld Minor bij semester 6.
- Een bestaande invulling aanpassen als het semester verandert.

## Schermen

Geen eigen ontwerp. Volgt het Overzicht ([spec 001](../001-studentenoverzicht/spec.md)) en de Studentenlijst ([spec 022](../022-studentenlijst-inline/spec.md)).

## Data

- **Bron:** eigen opslag. De regel (semester → invulling) staat op één plek in de code en in [gegevensmodel.md](../../docs/gegevensmodel.md#student).

## Technische eisen

- Eén functie voor F1 en F3, aangeroepen vanaf alle plekken uit F2.
- Kiest de gebruiker in een tabel een semester en vult de app de invulling in, dan herlaadt de pagina op dezelfde plek (anders blijft de oude invulling staan).
- Tests: F1-F5.

## Open vragen

- [x] **Waar:** overal waar je het semester kiest (F2).
- [x] **Keuze ontbreekt:** toevoegen aan de lijst (F3).
- [x] **(Stage):** alleen als er geen project is (F4).
- [x] **Groeperen:** een eigen groep "(Stage)"; het filter verandert niet (F5).

## Logboek

- 2026-11-11 – spec aangemaakt op verzoek van de gebruiker; vragen beantwoord; status in bouw
- 2026-11-11 – gebouwd: `choices.track_for_semester` en `fill_track` (F1, F3), aangeroepen vanuit het semesterlijstje in Overzicht en Studentenlijst, Student bewerken, handmatig toevoegen en de Excel-import; een gevulde invulling geeft in de tabel een herlaadsignaal (205). Groep "(Stage)" bij Groeperen: Project. 8 nieuwe tests; alle tests slagen. In de browser met je gegevens bekeken: 11 stagestudenten zonder project tonen "(Stage)" en staan in die groep. Status klaar
