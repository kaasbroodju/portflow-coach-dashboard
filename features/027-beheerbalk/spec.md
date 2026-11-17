# 027 – Beheerbalk met aantallen

**Status:** klaar <!-- idee | uitgewerkt | in bouw | klaar -->
**Laatst bijgewerkt:** 2026-11-11

## Doel

Als **coach** of **gildemeester** wil ik bovenaan elke beheerpagina in één oogopslag zien hoeveel er is, wie erbij hoort en wat nog geregeld moet worden, zodat ik weet waar werk zit. De pagina's onder Beheer zijn nu niet gelijk: de helft heeft een samenvattingsbalk, elk met een eigen opbouw, en de knop "+ … toevoegen" staat op een eigen regel.

## Gebruikers

- [x] Coach
- [x] Gildemeester
- Geen verschil.

## Betrokken begrippen

- De pagina's in de menugroep Beheer ([spec 002](../002-app-schil/spec.md), F17)
- Verborgen studenten ([spec 019](../019-eenvoudige-start/spec.md), F4); studenten zonder project ([spec 012](../012-projecten/spec.md), F4)

## Functionele eisen

- [x] **F1 – Eén balk op elke Beheer-pagina.** Bovenaan de inhoud van Studenten, Semesters, Gildes, Gildemeesters, Coaches, Projecten, Kolommen en Keuzelijsten staat één kaart, de **beheerbalk**: links de aantallen, rechts de primaire knop van de pagina. De aparte regel met de knop boven de inhoud ([spec 002](../002-app-schil/spec.md), F8) vervalt op deze pagina's. Op Studenten staat "+ Student toevoegen" daardoor in de balk, niet meer in de filterbalk.
  - *Acceptatie:* op elke genoemde pagina staat precies één beheerbalk, met de knop rechts erin; boven de balk staat geen losse knop.
- [x] **F2 – Vaste opbouw.** Elk aantal is een vet getal met daarachter een kort label, bijvoorbeeld "**12** actieve projecten". Er zijn hoogstens drie aantallen, altijd in deze volgorde: (1) hoeveel er van het onderwerp van de pagina zijn, (2) hoeveel studenten (of evaluaties) daarbij horen, (3) wat nog aandacht vraagt. Het getal van (3) is oranje als het groter is dan 0. Er staat geen uitlegzin in de balk.
  - *Acceptatie:* met 3 studenten zonder project is "3" bij Projecten oranje; met 0 is het gewoon donker.
- [x] **F3 – De aantallen per pagina.** Enkelvoud en meervoud volgen het getal ("1 gilde", "2 gildes").

  | Pagina | 1 | 2 | 3 (aandacht) |
  |---|---|---|---|
  | Studenten | **N** studenten (alle gevolgde) | **N** verborgen | **N** zonder project |
  | Semesters | **N** semesters, waarvan **M** actief (minstens één student) | **N** studenten met een semester | **N** zonder semester |
  | Gildes | **N** gildes | **N** studenten met minstens één gilde | **N** zonder gilde |
  | Gildemeesters | **N** gildemeesters | **N** evaluaties tellen mee | **N** gildes zonder gildemeester (geen gildemeester heeft dat gilde) |
  | Coaches | **N** coaches | **N** evaluaties tellen mee | **N** studenten zonder coach |
  | Projecten | **N** actieve projecten (minstens één student) | **N** studenten in een project | **N** zonder project |
  | Kolommen | **N** eigen kolommen | – | – |
  | Keuzelijsten | **N** keuzelijsten | **N** keuzes | – |

  - *Acceptatie:* met 5 studenten, waarvan 1 verborgen, 2 zonder project en 1 zonder coach, toont Studenten "5 studenten · 1 verborgen · 2 zonder project" en Coaches bij (3) "1 student zonder coach".
- [x] **F4 – Lege pagina.** Toont een pagina haar lege toestand ("Nog geen gildes." met een knop), dan staat er geen beheerbalk; de knop staat zoals nu boven de inhoud of in de lege toestand.
  - *Acceptatie:* zonder gildes staat op Gildes geen beheerbalk en wel de lege toestand met "+ Gilde toevoegen".

### Buiten scope

- Klikken op een aantal om te filteren (kan later).
- Onderliggende pagina's (bewerken, toevoegen): die houden de knop boven de inhoud, als ze er een hebben.

## Schermen

Geen eigen ontwerp. De samenvattingsbalk uit de CRUD-ontwerpen in [`screenshots/`](../../screenshots/) is het uitgangspunt ([design-system.md](../../docs/design-system.md#componenten)), met de opbouw van F2.

## Data

- **Bron:** alleen de lokale database; geen Portflow-verzoeken.
- **Privacy:** alleen aantallen, geen namen.

## Technische eisen

- De tellingen staan op één plek in de code; de balk is één gedeeld template.
- Tests voor de tellingen van F3 en voor F1 en F4.

## Open vragen

- [x] Welke aantallen per pagina? Voorstel van 2026-11-11 aangenomen ("Ja, zo bouwen"), met de tabel van F3.
- [x] Studenten: een eigen balk (zoals voorgesteld), niet de getallen in de filterbalk.
- [x] Uitlegzinnen in de balk vervallen, net als de uitleg bij de paginakop.

## Logboek

- 2026-11-11 – spec aangemaakt naar het voorstel om de Beheer-pagina's gelijk te trekken; door de gebruiker goedgekeurd; status in bouw
- 2026-11-11 – gebouwd: gedeeld template `_management_bar.html`, tellingen in `dashboard/summary.py`, tests in `tests/test_management_bar.py`; alle tests slagen en in de browser bekeken. Status klaar
- 2026-11-17 – aangepast door [spec 028](../028-filters-inklappen/spec.md): op Studenten staat de beheerbalk in de werkbalk van de tabel, onder de regel met het zoekveld, en klapt hij mee in
