# 028 – Filters inklappen

**Status:** klaar <!-- idee | uitgewerkt | in bouw | klaar -->
**Laatst bijgewerkt:** 2026-11-18

## Doel

Als **coach** of **gildemeester** wil ik de filters boven de tabel op Overzicht en Studenten kunnen inklappen, zodat de tabel meer ruimte krijgt. In de compacte stand blijft alleen het zoekveld zichtbaar.

## Gebruikers

- [x] Coach
- [x] Gildemeester
- Geen verschil.

## Betrokken begrippen

- De werkbalk met filters ([spec 001](../001-studentenoverzicht/spec.md), F13–F17; [spec 010](../010-studentenlijst/spec.md)), onthouden filters ([spec 023](../023-filters-onthouden/spec.md)), de legenda met kleurvinkjes ([spec 001](../001-studentenoverzicht/spec.md), F23), de beheerbalk ([spec 027](../027-beheerbalk/spec.md))

## Functionele eisen

- [x] **F1 – Knop Filters.** **Rechtsboven** in de werkbalk staat een knop **"Filters"** met een filtericoon en een pijltje (▾ open, ▸ dicht), in beide standen op precies dezelfde plek. De bovenste regel van de werkbalk bevat alleen het zoekveld (zo breed als er plaats is) en deze knop; de filters staan in de uitgebreide stand op de regels daaronder. Op Studenten staat de beheerbalk daarom niet meer boven de tabel, maar in de werkbalk, direct onder die bovenste regel. Een klik wisselt tussen de **uitgebreide** en de **compacte** stand.
  - *Acceptatie:* een klik op "Filters" in de uitgebreide stand verbergt de filters; nog een klik toont ze weer. De knop staat in beide standen rechtsboven, op dezelfde plek.
- [x] **F2 – Compacte stand.** Zichtbaar blijven alleen het zoekveld (met ⌘K) en de knop Filters, op één regel (op Overzicht ook de keuzelijst wie, zie F7). Verborgen zijn: de keuzelijsten (wie, behalve op Overzicht, semester, invulling, project, gilde, eigen keuzelijstkolommen, groeperen), "Aan te sporen", "Filters wissen", de knop "+ Student toevoegen", de regel eronder met de legenda-vinkjes (0, 1, 2 evaluaties, openstaand) en de knop Kolommen of het tandwiel, en op Studenten de beheerbalk ([spec 027](../027-beheerbalk/spec.md)) en de pennetjes boven de kolomkoppen ([spec 022](../022-studentenlijst-inline/spec.md), F2).
  - *Acceptatie:* in de compacte stand staat tussen de bovenbalk en de kolomkoppen van de tabel alleen de regel met het zoekveld en de knop Filters, ook op Studenten.
- [x] **F3 – Filters blijven werken.** Inklappen verandert niets aan de gekozen filters, de groepering en de kleuren; het zoekveld blijft live zoeken.
  - *Acceptatie:* met "Mijn coachstudenten" gekozen en de filters ingeklapt toont de tabel nog steeds alleen coachstudenten.
- [x] **F4 – Zichtbaar dat er gefilterd wordt.** Zijn er filters actief (elke keuzelijst die niet op de standaard staat, "Aan te sporen" en een andere groepering dan de standaard; zoals bij "Filters wissen"), dan toont de knop het aantal: **"Filters · 2"**.
  - *Acceptatie:* met een semester en een project gekozen staat op de knop "Filters · 2"; na "Filters wissen" staat er alleen "Filters".
- [x] **F5 – Onthouden.** De stand (compact of uitgebreid) wordt per pagina bewaard, zoals de filters zelf ([spec 023](../023-filters-onthouden/spec.md)), en geldt ook na herstarten. Standaard: **compact**.
  - *Acceptatie:* bij de eerste keer zijn beide pagina's compact; Overzicht uitgeklapt en Studenten compact blijft zo na herladen en na herstart van de app.
- [x] **F6 – Zonder JavaScript.** De knop werkt ook zonder JavaScript (dan via herladen van de pagina).
- [x] **F7 – Wie blijft zichtbaar op Overzicht.** Op Overzicht staat de keuzelijst **wie** ("Alle studenten", "Mijn coachstudenten", "Mijn gildestudenten" …) in de bovenste regel, tussen het zoekveld en de knop Filters, en blijft in de compacte stand zichtbaar. De bovenste regel wordt daar: zoekveld – keuzelijst wie – knop Filters. Op Studenten verandert niets. Een gekozen wie telt nog steeds mee in het aantal op de knop (F4).
  - *Acceptatie:* op Overzicht in de compacte stand staan zoekveld, de keuzelijst wie en de knop Filters op één regel; een andere keuze in de lijst filtert de tabel meteen.

### Buiten scope

- Andere pagina's dan Overzicht en Studenten.

## Schermen

Geen eigen ontwerp. Knop in dezelfde stijl als de bestaande secundaire knoppen ([design-system.md](../../docs/design-system.md#componenten)).

## Data

- **Bron:** alleen de lokale database (instelling per pagina, zoals spec 023).
- **Privacy:** geen studentgegevens.

## Technische eisen

- De stand staat in `settings`, met dezelfde opzet als de onthouden filters.
- Tests voor F2, F4 en F5.

## Open vragen

- [x] De beheerbalk op Studenten klapt mee in (F2).
- [x] Kolommen en het tandwiel zijn in de compacte stand ook verborgen (F2).
- [x] Standaardstand bij de eerste keer: compact (F5).
- [x] Teller op de knop: ja (F4).

## Logboek

- 2026-11-17 – spec aangemaakt op verzoek van de gebruiker, met een voorstel en open vragen
- 2026-11-17 – open vragen beantwoord door de gebruiker: beheerbalk en Kolommen klappen mee in, standaard compact, met teller; status in bouw
- 2026-11-17 – gebouwd: knop Filters in de werkbalk, stand in `settings` (`filters_compact_overview`, `filters_compact_students`), klasse `filters-compact` op de inhoud; tests in `tests/test_filters_fold.py`. In de browser in- en uitgeklapt op Overzicht; Studenten alleen met tests gecontroleerd. Status klaar
- 2026-11-17 – F1 aangepast op verzoek van de gebruiker: de knop staat in beide standen rechtsboven, op dezelfde plek; zoekveld en knop vormen samen de bovenste regel
- 2026-11-17 – op Studenten staat de beheerbalk in de werkbalk onder de regel met het zoekveld, zodat de knop Filters bij uitklappen niet verspringt
- 2026-11-17 – op verzoek van de gebruiker: in de compacte stand zijn op Studenten ook de pennetjes boven de kolomkoppen verborgen (F2)
- 2026-11-18 – F7 toegevoegd en gebouwd op verzoek van de gebruiker: op Overzicht blijft de keuzelijst wie in de compacte stand zichtbaar, tussen zoekveld en knop Filters
