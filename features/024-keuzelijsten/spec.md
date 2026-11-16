# 024 – Kolommen en keuzelijsten

**Status:** klaar
**Laatst bijgewerkt:** 2026-11-11

## Doel

Als **coach** of **gildemeester** wil ik:

- **eigen kolommen** beheren (toevoegen, wijzigen, volgorde, verwijderen), want de pagina Kolommen is nu alleen een lege pagina;
- de keuzes van **eenvoudige lijstjes** zelf beheren, zodat ik niet afhankelijk ben van vaste waarden in de code;
- een eigen kolom kunnen maken van het type **keuzelijst**.

Een keuzelijst is een geordende lijst items met een **code** en een **omschrijving**. Er zijn drie soorten:

- **Invulling** van een student (nu vast in de code; [gegevensmodel](../../docs/gegevensmodel.md#student));
- **Rol in de squad**, de teamrol (nu vast: PO, SM, 2ePO, 2eSM; [begrippen](../../docs/begrippen.md));
- de lijst van een eigen **keuzelijstkolom**.

## Gebruikers

- [x] Coach
- [x] Gildemeester
- Geen verschil.

## Betrokken begrippen

Invulling, rol in de squad, eigen kolom ([begrippen](../../docs/begrippen.md), [gegevensmodel](../../docs/gegevensmodel.md#kolommen)). De tien vaardigheden (OC … RE) blijven vaste kolommen en zijn hier niet te beheren.

## Functionele eisen

### Kolommen (pagina Kolommen, onder Beheer)

- [x] **K1 – Overzicht.** De pagina Kolommen toont de eigen kolommen in hun volgorde, met code, naam, beschrijving, type en het aantal studenten met een waarde. De tien vaardigheden staan er niet in.
  - *Acceptatie:* met twee eigen kolommen → twee kaarten of regels in de juiste volgorde.
- [x] **K2 – Toevoegen.** Velden: code (kort, verplicht), naam (verplicht), beschrijving, type: **percentage**, **vrije tekst** of **keuzelijst**. Bij een keuzelijst ontstaat een lege lijst met de naam van de kolom (L1). Een nieuwe kolom komt achteraan.
  - *Acceptatie:* voeg een keuzelijstkolom "Werkplek" toe → hij staat op Kolommen, en op Keuzelijsten staat een lege lijst "Werkplek".
- [x] **K3 – Wijzigen.** Code, naam en beschrijving zijn te wijzigen. Het **type niet**: dat ligt vast zodra de kolom bestaat. Wil de gebruiker een ander type, dan maakt hij een nieuwe kolom.
  - *Acceptatie:* het bewerkscherm toont het type, maar niet als keuze.
- [x] **K4 – Volgorde.** De gebruiker kan de volgorde wijzigen. Die bepaalt de volgorde in het Overzicht en de Studentenlijst (na RE).
  - *Acceptatie:* zet kolom B vóór kolom A → in het Overzicht staat B eerst.
- [x] **K5 – Verwijderen.** Na bevestiging, met in de vraag het aantal studenten met een waarde. De waarden gaan mee, en bij een keuzelijstkolom ook zijn lijst.
  - *Acceptatie:* verwijder een kolom met 3 ingevulde waarden → de vraag noemt "3 studenten"; daarna zijn kolom, waarden en lijst weg.

### Keuzelijsten (pagina Keuzelijsten, onder Beheer, na Kolommen)

- [x] **L1 – Overzicht.** De pagina Keuzelijsten toont alle lijsten onder elkaar: Invulling, Rol in de squad, en per keuzelijstkolom een lijst met de naam van die kolom. Per item: code, omschrijving en het aantal studenten met dat item.
  - *Acceptatie:* met één keuzelijstkolom → drie lijsten.
- [x] **L2 – Items beheren.** Per lijst: items toevoegen, de **code en de omschrijving** wijzigen, de volgorde aanpassen en verwijderen. Studenten en cellen verwijzen naar het item, dus een gewijzigde code of omschrijving werkt overal door. Binnen een lijst is elke code uniek (hoofdletters tellen niet mee).
  - *Acceptatie:* wijzig de code "SM" in "Scrum" → alle studenten met SM tonen "Scrum".
- [x] **L3 – Volgorde telt.** De volgorde van de items bepaalt de volgorde in keuzelijstjes, filters en bij groeperen.
  - *Acceptatie:* zet Stage bovenaan → in het filter Invulling en bij "Groeperen: Invulling" komt Stage eerst.
- [x] **L4 – Verwijderen van een item in gebruik.** De bevestiging noemt het aantal studenten met dat item. Na bevestigen is hun waarde leeg.
  - *Acceptatie:* verwijder "Minor" met 2 studenten → de vraag noemt "2 studenten"; daarna is hun invulling leeg.
- [x] **L5 – Open-ICT-standaard.** Bij Invulling en Rol staat een knop die de Open-ICT-waarden toevoegt die nog ontbreken (vergeleken op code). Gewijzigde of eigen items blijven staan. De standaardwaarden komen uit [gegevensmodel.md](../../docs/gegevensmodel.md#student) en [begrippen.md](../../docs/begrippen.md); de code leest ze niet uit de docs, maar neemt ze daaruit over, op één plek.
  - *Acceptatie:* verwijder "Afstuderen", klik de knop → "Afstuderen" is terug; de andere items zijn onveranderd.
- [x] **L6 – Eerste start en bestaande gegevens.** Bij de migratie krijgen Invulling en Rol de huidige vaste waarden als items, en houden studenten hun huidige waarde. Een waarde die niet in de lijst staat, wordt een extra item.
  - *Acceptatie:* een bestaande database met studenten op "Stage" en "SM" → na de migratie dezelfde waarden, nu als items.

### Gebruik in de tabellen

- [x] **G1 – Keuzelijstkolom invullen.** In het Overzicht en de Studentenlijst is een cel van een keuzelijstkolom een keuzelijstje (zoals het semester, [spec 019](../019-eenvoudige-start/spec.md), F7) met "–" en de items. Eén waarde per student. Opslaan gebeurt meteen.
  - *Acceptatie:* kies een item → na herladen staat het er nog; kies "–" → leeg.
- [x] **G2 – Filter.** Elke keuzelijstkolom krijgt een filter in de filterbalk van Overzicht en Studenten ("Alle {naam}" en de items). Het filter wordt onthouden ([spec 023](../023-filters-onthouden/spec.md)).
  - *Acceptatie:* filter op een item → alleen studenten met dat item.
- [x] **G3 – Groeperen.** Elke keuzelijstkolom is een keuze bij Groeperen ("Groeperen: {naam}"), in de volgorde van de items, met "Niet ingevuld" als laatste groep.
  - *Acceptatie:* groepeer op een keuzelijstkolom → een groep per item in de volgorde van de lijst.
- [x] **G4 – Pennetjes.** In de Studentenlijst krijgen Invulling en Rol een pennetje naar hun lijst op de pagina Keuzelijsten ([spec 022](../022-studentenlijst-inline/spec.md), F2).
  - *Acceptatie:* klik het pennetje bij Rol → de pagina Keuzelijsten, bij de lijst Rol in de squad.

### Excel-import

- [x] **E1 – Waarden zoeken in de lijst.** De import ([spec 013](../013-excel-importeren/spec.md)) zoekt invulling en rol op in de lijsten, op code (hoofdletters tellen niet mee). Komt "Stage" of "Minor" in de coachkolom voor (spec 013, F7) en staat dat item niet (meer) in de lijst Invulling, dan **voegt de import het item toe**.
  - *Acceptatie:* verwijder "Minor", importeer een rij met "Minor" in de coachkolom → het item "Minor" bestaat weer en de student heeft die invulling.

### Buiten scope

- Semesters, projecten, gildes, coaches en gildemeesters: die hebben eigen velden en gedrag en houden hun eigen beheerpagina.
- Meer dan één waarde per student in een keuzelijstkolom.
- Kleuren voor items.
- Een lijst delen tussen kolommen: elke keuzelijstkolom heeft zijn eigen lijst.

## Schermen

Geen eigen ontwerp. De pagina's Kolommen en Keuzelijsten volgen de bestaande beheerpagina's (Projecten, Gildes) en de ontwerpen `screenshots/*-CRUD-*.png` ([design-system](../../docs/design-system.md)). Bevestigingen zoals bij Projecten.

## Data

- **Bron:** eigen opslag; geen Portflow-aanroepen.
- **Opzet:** een tabel met lijsten (soort: invulling, rol of kolom; bij een kolom de verwijzing naar die kolom) en een tabel met items (lijst, code, omschrijving, volgorde). `students.track` en `students.squad_role` worden verwijzingen naar items; een waarde van een keuzelijstkolom verwijst naar een item. De migratie zet de bestaande tekstwaarden om (L6).
- **Alles verwijderen** ([spec 014](../014-alles-verwijderen/spec.md)) wist de eigen kolommen en hun lijsten. Invulling en Rol worden daarna weer met de Open-ICT-waarden gevuld, zoals na een eerste start.

## Technische eisen

- Eén beheeronderdeel (template en code) voor alle lijsten; geen kopie per lijst.
- De code hangt niet af van een omschrijving die de gebruiker kan wijzigen. Waar de code een vaste waarde nodig heeft (de Excel-import, E1), zoekt hij op code en maakt het item zo nodig aan.
- Na deze spec bevatten `TRACKS`, `TRACK_LABELS` en `SQUAD_ROLES` alleen nog de Open-ICT-standaardwaarden voor L5 en L6.
- Tests: K1-K5, L1-L6, G1-G4, E1, en de migratie van een bestaande database.

## Keuzes bij het bouwen, ter controle

- **Code van een kolom:** hooguit 12 tekens, uniek (hoofdletters tellen niet mee), en niet gelijk aan een vaardigheidscode (OC … RE).
- **Code van een keuze:** hooguit 40 tekens.
- **Studentenlijst:** de eigen kolommen staan achteraan (na Portflow), met de naam als kolomtitel. Ze zijn aan en uit te zetten met het tandwiel, zoals de andere kolommen. Ze krijgen ook een pennetje: een keuzelijstkolom naar zijn lijst, een andere kolom naar Kolommen.
- **Volgorde wijzigen** gaat met pijltjes (↑ ↓), zonder slepen; dat werkt ook zonder JavaScript.
- **Na Alles verwijderen** zijn Invulling en Rol weer gevuld met de Open-ICT-keuzes.
- **Opgeslagen filters** op een invulling (van vóór deze spec, met de tekst als waarde) vervallen één keer; spec 023, F5.

## Open vragen

- [x] **Plek:** een pagina Keuzelijsten onder Beheer, na Kolommen.
- [x] **Kolommen-pagina:** hoort bij deze spec (K1-K5).
- [x] **Verwijderen van een item in gebruik:** vragen met het aantal studenten, daarna leegmaken (L4).
- [x] **Code wijzigen:** ja, code en omschrijving (L2).
- [x] **Excel-import:** zoeken op code; ontbreekt "Stage" of "Minor", dan maakt de import het item aan (E1).
- [x] **Standaardwaarden:** de docs blijven de bron; een knop voegt ontbrekende Open-ICT-items toe (L5).
- [x] **Meerdere waarden:** nee, één waarde per student.
- [x] **Filters en groeperen:** ja, allebei (G2, G3).
- [x] **Kleur:** nee.
- [x] **Type wijzigen:** niet toegestaan (K3).
- [x] **Lijst delen:** nee, eigen lijst per kolom.

## Logboek

- 2026-11-11 – spec aangemaakt op verzoek van de gebruiker, na advies over een generieke beheerpagina voor eenvoudige lijsten
- 2026-11-11 – open vragen beantwoord; het beheer van eigen kolommen (pagina Kolommen) is aan deze spec toegevoegd; titel "Kolommen en keuzelijsten"; status uitgewerkt
- 2026-11-11 – gebouwd: `choices.py` (lijsten en keuzes), `columns.py` (eigen kolommen), pagina's Kolommen en Keuzelijsten, migratie van `students.track` en `squad_role` naar `track_id` en `squad_role_id`. 18 nieuwe tests; alle tests slagen. Migratie eerst op een kopie van de echte database gecontroleerd (alle 137 studenten houden hun invulling en rol); reservekopie in `data/reservekopieen/`. In de browser bekeken: Keuzelijsten (met de juiste aantallen), Kolommen, Nieuwe kolom, Studenten en Overzicht. Een keuzelijstkolom aanmaken en invullen is alleen met tests gecontroleerd, om je gegevens niet te wijzigen. Status klaar
- 2026-11-11 – aangepast door [spec 027](../027-beheerbalk/spec.md): bovenaan staat de beheerbalk met de aantallen uit die spec en de knop erin
