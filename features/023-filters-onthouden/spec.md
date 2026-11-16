# 023 – Filters onthouden

**Status:** klaar
**Laatst bijgewerkt:** 2026-11-11

## Doel

Als **coach** of **gildemeester** wil ik dat de filters in Overzicht ([spec 001](../001-studentenoverzicht/spec.md)) en Studenten ([spec 010](../010-studentenlijst/spec.md)) blijven staan als ik terugkom, zodat ik ze niet steeds opnieuw hoef te kiezen.

## Gebruikers

- [x] Coach
- [x] Gildemeester
- Geen verschil.

## Betrokken begrippen

De filterbalk: wie, semester, invulling, project, gilde, groeperen en "Aan te sporen".

## Functionele eisen

- [x] **F1 – Onthouden bij wijzigen.** Wijzigt de gebruiker een keuze in de filterbalk, dan bewaart de app alle keuzes van die pagina. Opent de gebruiker de pagina later zonder filters in het adres (via het menu, na een herstart van de app), dan staan de bewaarde keuzes er weer.
  - *Acceptatie:* kies in Overzicht "Semester 3" en "Groeperen: Gilde", ga naar Instellingen en terug via het menu → beide keuzes staan er nog, ook na een herstart.
- [x] **F2 – Per pagina.** Overzicht en Studenten onthouden elk hun eigen keuzes.
  - *Acceptatie:* filter in Studenten op een project → het Overzicht is niet gefilterd.
- [x] **F3 – Niet het zoekveld.** Het zoekveld begint altijd leeg.
- [x] **F4 – Filters wissen.** In de filterbalk staat een link **"Filters wissen"**, alleen als een keuze afwijkt van de standaard. Klikken zet alle keuzes van die pagina terug naar de standaard en onthoudt dat.
  - *Acceptatie:* met een filter → de link staat er; klik → standaardfilters, de link is weg, ook na terugkomen.
- [x] **F5 – Verdwenen keuzes.** Bestaat een bewaarde keuze niet meer (bijvoorbeeld een verwijderd project of gilde), dan vervalt alleen die keuze.
  - *Acceptatie:* bewaar een filter op een project, verwijder het project → de pagina toont "Alle projecten".
- [x] **F6 – Standaard blijft meebewegen.** Wie en Groeperen worden alleen bewaard als ze afwijken van de standaard; zo blijft de standaardgroepering uit [spec 019](../019-eenvoudige-start/spec.md) (F8) werken tot de gebruiker zelf iets kiest.

### Buiten scope

- Sortering en de kolomkeuze (die worden al apart bewaard).

## Schermen

Geen eigen ontwerp. "Filters wissen" als tekstlink in de filterbalk.

## Data

- **Bron:** eigen opslag; per pagina een instelling (`filters_overview`, `filters_students`) met de keuzes als JSON. "Alles verwijderen" ([spec 014](../014-alles-verwijderen/spec.md)) wist ze mee.

## Technische eisen

- De filterbalk is een GET-formulier; het formulier stuurt een verborgen veld mee zodat de app ook "alles op standaard" als bewuste keuze herkent.
- Tests: F1-F6.

## Open vragen

- [x] **Per pagina of samen:** per pagina (F2).
- [x] **Zoekveld:** niet onthouden (F3).
- [x] **Wissen:** ja, "Filters wissen" (F4).

## Logboek

- 2026-11-11 – spec aangemaakt op verzoek van de gebruiker; vragen beantwoord; status in bouw
- 2026-11-11 – gebouwd: `saved_filters`, `save_filters` en `valid_filters` in `overview.py`; verborgen veld `f` in de filterbalk. 6 nieuwe tests; 273 tests slagen. In de browser gecontroleerd: semester 3 gekozen, via het menu terug → blijft staan; Filters wissen → alles terug op standaard. Status klaar
