# 019 – Eenvoudige start: alle gedeelde studenten zonder instellen

**Status:** klaar
**Laatst bijgewerkt:** 2026-11-19

## Doel

Als **coach** of **gildemeester** die "gewoon even wil kijken" wil ik na het inloggen bij Portflow direct alle studenten zien die hun portfolio met mij hebben gedeeld, met hun behaalde niveaus, zonder eerst iets in te stellen. Zo heb ik met zo weinig mogelijk handelingen overzicht.

De app kent twee soorten gebruik (zie [begrippen.md](../../docs/begrippen.md#soorten-gebruik)):

- **Overzicht krijgen met zo weinig mogelijk handelingen.** Deze spec is voor dit gebruik.
- **Alles goed instellen**, met de beheerpagina's. Dat blijft zoals het is.

Er komen **geen twee standen**. Het is één app die zonder instellingen al bruikbaar is. Het beheer kan daarna worden ingevuld, maar hoeft niet.

## Gebruikers

- [x] Coach, met 1, 2 of 3 squads
- [x] Gildemeester
- Er is geen verschil in wat ze zien. Iemand kan beide rollen hebben.

## Betrokken begrippen

- De tien vaardigheden OC … RE en de weergave van niveaus ([voortgangsregels.md](../../docs/voortgangsregels.md#weergave-per-vaardigheid))
- Welke evaluaties tellen ([voortgangsregels.md](../../docs/voortgangsregels.md#welke-evaluaties-tellen)); voorwaarde 2 verandert (F10–F12)
- Gevolgde en verborgen studenten ([gegevensmodel.md](../../docs/gegevensmodel.md#studenten-toevoegen))

## Functionele eisen

### Alle gedeelde studenten automatisch

- [x] **F1 – Automatisch toevoegen.** Bij elke ophaalronde ([spec 005](../005-gegevens-ophalen/spec.md)), ook de eerste direct na het verbinden, voegt de app **alle** studenten uit de gedeelde portfolio's (`GET /shares/shared-with-me`, gegroepeerd zoals [spec 004](../004-studenten-toevoegen/spec.md), F6) toe die nog niet in het dashboard staan. De gebruiker hoeft niets aan te vinken. Bestaat er al een ongekoppelde student met dezelfde naam, dan koppelt de app die, zoals bij [spec 004](../004-studenten-toevoegen/spec.md), F10.
  - *Acceptatie:* gegeven een leeg dashboard en 12 gedeelde portfolio's van 10 studenten, wanneer de gebruiker verbindt, dan staan er na de ophaalronde 10 studenten op Overzicht met hun niveaus, zonder tussenscherm.
- [x] **F2 – Eerste start.** Na het allereerste verbinden start de ophaalronde vanzelf. Dat is een uitzondering op "verversen alleen met de knop" ([architectuur.md](../../docs/architectuur.md#verversen)); die uitzondering moet in architectuur.md komen. Daarna toont de app Overzicht.
  - *Acceptatie:* op een leeg dashboard opent na het inloggen en het sluiten van Chrome het Overzicht met de opgehaalde studenten; de gebruiker hoeft niet op Verversen te klikken.
- [x] **F3 – Nieuwe shares.** Deelt een student later zijn portfolio, dan verschijnt hij bij de volgende Verversen-ronde vanzelf. Een student die eerder verborgen is (F4), blijft verborgen.
  - *Acceptatie:* een student die na de eerste ronde zijn portfolio deelt, staat na de volgende Verversen-ronde in de lijst; een eerder verborgen student met een nieuwe share blijft verborgen.

### Verbergen

- [x] **F4 – Verbergen per rij.** Elke rij op Overzicht krijgt een icoonknop **"Verbergen"**: een oog met een streep erdoor, met tooltip "Verbergen in dit overzicht". Er staat geen tekst op de knop; het icoon is altijd zichtbaar, aan het eind van de rij. Na een klik verdwijnt de rij uit "Alle studenten die ik niet heb verborgen" (F6). De student wordt **niet verwijderd**: zijn gegevens en indeling blijven bestaan. Het icoon komt in `_icons.html` ([design-system.md](../../docs/design-system.md)).
  - *Acceptatie:* na een klik op het icoon bij een student is de rij weg uit "Alle studenten die ik niet heb verborgen", de teller telt één minder, en bij "Alle studenten van wie ik het portfolio kan zien" staat de student er nog.
- [x] **F5 – Weer tonen.** Bij "Alle studenten van wie ik het portfolio kan zien" (F6) is een verborgen rij gedimd en staat er een icoonknop **"Weer tonen"** (een open oog, tooltip "Weer tonen in dit overzicht"). Een klik maakt de student weer zichtbaar.
  - *Acceptatie:* een verborgen student die weer getoond wordt, staat direct weer in "Alle studenten die ik niet heb verborgen".

### Filter op wie

- [x] **F6 – Filter uitgebreid.** Het filter op wie ([spec 001](../001-studentenoverzicht/spec.md), F14) krijgt de volgende keuzes:

  | Keuze | Toont |
  |---|---|
  | **Alle studenten** (toegevoegd 2026-11-11, bovenaan) | Alle gevolgde studenten, zonder filter: ook de verborgen studenten, als gewone rijen |
  | **Alle studenten die ik niet heb verborgen** (nieuw, standaard) | Alle studenten behalve de verborgen. Hierop werkt de knop Verbergen (F4) |
  | Mijn coachstudenten | Alleen studenten bij wie het veld *coach* gelijk is aan de naam van de gebruiker, of ze nu verborgen zijn of niet |
  | Mijn gildestudenten | Alleen studenten bij wie het veld *gildemeester* (bij een van hun gildes) gelijk is aan de naam van de gebruiker, of ze nu verborgen zijn of niet |
  | **Alle studenten van wie ik het portfolio kan zien** | Nieuwe naam voor "Alle gevolgde studenten". Ook de verborgen studenten, gedimd (F5) |

  - Verbergen speelt alleen bij "Alle studenten die ik niet heb verborgen" en "Alle studenten van wie ik het portfolio kan zien". Bij Alle studenten, Mijn coachstudenten en Mijn gildestudenten zijn alle rijen gewone rijen: niet gedimd, zonder de knoppen Verbergen (F4) en Weer tonen (F5).
  - *Acceptatie:* met 10 studenten, waarvan 2 verborgen, toont "Alle studenten die ik niet heb verborgen" "8 van 10 studenten" en "Alle studenten van wie ik het portfolio kan zien" "10 van 10 studenten". "Alle studenten" toont ook "10 van 10 studenten", zonder gedimde rijen en zonder de knoppen Verbergen en Weer tonen.

### Beoordelaars

- [x] **F10 – Alle beoordelingen tellen mee.** Elke evaluatie door een ander dan de student zelf telt mee, ongeacht of de beoordelaar op de pagina Coaches of Gildemeesters staat. Dit vervangt voorwaarde 2 in [voortgangsregels.md](../../docs/voortgangsregels.md#welke-evaluaties-tellen). De andere voorwaarden (geen zelfevaluatie, binnen de semesterperiode, een van de tien vaardigheden) blijven.
  - *Acceptatie:* op een leeg dashboard telt een evaluatie op OC door een onbekende gildemeester mee en staat die in de cel.
- [x] **F11 – Beoordelaars automatisch toevoegen.** Bij elke ophaalronde voegt de app iedere beoordelaar die in de opgehaalde evaluaties voorkomt en nog niet in de lijst staat, automatisch toe aan de lijst met coaches en gildemeesters. De rol volgt uit wat hij beoordeelde: heeft hij een van de vier productvaardigheden (OC, KO, JKO, KPM) beoordeeld, dan krijgt hij de rollen **gildemeester én coach**; heeft hij alleen een of meer van de zes andere vaardigheden beoordeeld, dan krijgt hij de rol **coach**. Een automatisch toegevoegde gildemeester krijgt geen gildes; die vult de gebruiker zelf in als hij dat wil. Voornaam en achternaam worden gesplitst zoals bij [spec 006](../006-gildemeesters/spec.md) (bij de eerste spatie).
  - *Acceptatie:* na een ophaalronde met evaluaties van 3 onbekende beoordelaars staan die 3 in de lijst; een tweede ronde voegt ze niet nogmaals toe. Een beoordelaar met een evaluatie op KO staat op Coaches én Gildemeesters; een beoordelaar met alleen evaluaties op PL en RE staat alleen op Coaches.
- [x] **F12 – Beoordelaar uitsluiten.** Bij elke beoordelaar (bij het bewerken van een coach of gildemeester) staat een vinkje **"Evaluaties van deze beoordelaar tellen niet mee"**, standaard uit. Staat het aan, dan worden de evaluaties van deze beoordelaar volledig verborgen en tellen ze niet mee, zoals nu met onbekende beoordelaars gebeurt. Bedoeld voor bijvoorbeeld ouderejaars studenten die evaluaties afnamen.
  - *Acceptatie:* nadat het vinkje bij een beoordelaar is aangezet, verdwijnen zijn evaluaties uit de cellen en de details bij hover, en de celkleur past zich aan.
- [x] **F13 – Verwijderde beoordelaar.** Verwijdert de gebruiker een beoordelaar, dan onthoudt de app dat de evaluaties van deze beoordelaar **niet meetellen** (zoals F12). Een volgende ophaalronde voegt hem niet opnieuw toe als meetellende beoordelaar.
  - *Acceptatie:* na het verwijderen van een beoordelaar en een nieuwe ophaalronde tellen zijn evaluaties nog steeds niet mee.

### Verversen

- [x] **F14 – Zichtbare studenten eerst.** *Gewijzigd 2026-11-19 op verzoek van de gebruiker; eerst haalde Verversen alleen de zichtbare studenten op.* Verversen haalt de evaluaties op van **alle studenten die niet verborgen zijn**, en begint met de studenten die **op dat moment zichtbaar** zijn:
  - op **Overzicht** (en **Beheer › Studenten**): de studenten in de lijst na het filter op wie, de andere filters en het zoeken, in de volgorde van de lijst;
  - op **Evaluaties**: de studenten in de tabel bovenaan;
  - op de **pagina van één student**: die student;
  - op andere pagina's: geen voorrang (op naam).

  Een zichtbare student die verborgen is (bijvoorbeeld bij het filter "Alle studenten"), wordt ook opgehaald. Studenten die in deze ronde nieuw zijn toegevoegd (F3), komen na de zichtbare. De lijst met gedeelde portfolio's (F1, F3) haalt de app altijd volledig op. De eerste ophaalronde (F2) haalt alle studenten op.
  - *Acceptatie:* met 10 studenten, waarvan 2 verborgen, en een zoekopdracht die er 3 laat zien, haalt Verversen eerst die 3 op en daarna de andere 5; de 2 verborgen studenten houden hun laatst bewaarde gegevens.

### Semester kiezen in de tabel

- [x] **F7 – Keuzelijst voor het semester.** *Vervallen op 2026-11-18: het semester wijzig je bij Beheer › Studenten ([spec 022](../022-studentenlijst-inline/spec.md)); op Overzicht staat het weer als tekst ("Sem N").* In de cel Student staat nu de subregel "Sem N" ([spec 001](../001-studentenoverzicht/spec.md), F2). Die wordt een klein **keuzelijstje** met "–" (geen semester) en 1 tot en met 8. Kiest de gebruiker een semester, dan slaat de app het direct op, zonder bewerkscherm en zonder opslaan-knop. Het lijstje werkt ook als er onder Beheer geen semesters zijn toegevoegd: het semester van een student is een nummer ([gegevensmodel.md](../../docs/gegevensmodel.md#semester)).
  - *Acceptatie:* bij een student zonder semester staat "–"; na het kiezen van 3 staat er "Sem 3", ook na herladen. De student verhuist uit "Nog in te delen" als hij ook een gilde heeft, of als de lege groepen vervallen (zie F8 en Open vragen).
  - Het lijstje mag het sorteren, zoeken en groeperen niet verstoren: na het kiezen blijft de rij op zijn plek staan tot de pagina opnieuw geladen wordt.

### Weinig instellen

- [x] **F8 – Niet groeperen zolang er niets is ingedeeld.** Zolang geen enkele student een project, semester of gilde heeft, kiest Overzicht standaard **"Niet groeperen"** ([spec 001](../001-studentenoverzicht/spec.md), F16): één platte lijst op naam, zonder groepskoppen en dus zonder "Nog in te delen". Zodra er iets is ingedeeld, is groeperen per project weer de standaard. Heeft de gebruiker zelf een groepering gekozen, dan geldt die.
  - *Acceptatie:* op een dashboard met 10 studenten zonder project, semester of gilde staan de 10 studenten op naam zonder groepskop; nadat één student een semester heeft gekregen, groepeert Overzicht standaard per project.
- [x] **F9 – Lege kolommen verbergen.** Een extra kolom (Coach, Gildemeester, Invulling; [spec 001](../001-studentenoverzicht/spec.md), F3) die bij geen enkele student gevuld is, toont de app niet. Heeft de gebruiker de kolom zelf aan- of uitgezet, dan geldt die keuze.
  - *Acceptatie:* op een dashboard waar bij geen student een gildemeester is ingevuld, staat de kolom Gildemeester niet in de tabel; na het invullen bij één student verschijnt hij weer; zet de gebruiker de kolom zelf aan, dan staat hij er ook als hij leeg is.

### Buiten scope

- Twee standen of een schakelaar "eenvoudig/uitgebreid".
- Het menu Beheer inklappen of verbergen: het menu blijft zoals het is.
- De beheerpagina's (gildes, projecten, semesters, coaches, gildemeesters, kolommen): die blijven zoals ze zijn.
- De installatie: zie [spec 020](../020-installatie/spec.md).
- "Semester behaald": de eenvoudige gebruiker heeft alleen de behaalde niveaus nodig. Bestaande signalen blijven zoals ze zijn.

## Schermen

Er is geen eigen ontwerp; zoals bij [spec 004](../004-studenten-toevoegen/spec.md) is [design-system.md](../../docs/design-system.md) het ontwerp, met het Overzicht uit [`screenshots/kompas-dashboard-ontwerp.png`](../../screenshots/kompas-dashboard-ontwerp.png). Het verberg-icoon (F4) staat aan het eind van de rij en is **altijd zichtbaar**, ook zonder hover.

Gedrag dat niet uit een afbeelding blijkt:

- Verbergen en weer tonen gebeuren zonder het hele overzicht opnieuw te laden.
- Lege toestand: zijn alle studenten verborgen, dan meldt Overzicht "Je hebt alle studenten verborgen", met een link naar "Alle studenten van wie ik het portfolio kan zien".

## Data

- **Bron:** Portflow `GET /shares/shared-with-me` (al gebruikt in [spec 004](../004-studenten-toevoegen/spec.md)) en de evaluaties ([spec 005](../005-gegevens-ophalen/spec.md)).
- **Nieuw veld bij de student:** *verborgen* (ja/nee, standaard nee). Moet in [gegevensmodel.md](../../docs/gegevensmodel.md#student).
- **Verversen:** het toevoegen gebeurt in de gewone ophaalronde; de eerste ronde start vanzelf (F2).
- **Privacy:** de app bewaart nu van **alle** studenten die hun portfolio hebben gedeeld de evaluaties lokaal, ook van studenten die de gebruiker niet volgt. Dat is te verdedigen, want de student heeft het zelf gedeeld, maar het hoort als beslissing in [architectuur.md](../../docs/architectuur.md#privacy).

## Technische eisen

- Migratie: bestaande studenten krijgen *verborgen = nee*; een bestaande database blijft werken.
- Het filter "wie" en het verbergen werken in de browser (zoals het filteren nu), het opslaan via een kleine POST.
- Het semesterlijstje slaat op via een kleine POST en gebruikt dezelfde validatie als Student bewerken ([spec 011](../011-student-bewerken/spec.md)).

## Open vragen

### Beantwoord (2026-11-11)

- [x] **Beoordelaars:** alle beoordelingen tellen mee; beoordelaars uit de evaluaties worden automatisch toegevoegd; per beoordelaar is in te stellen dat zijn evaluaties niet meetellen (F10–F12).
- [x] **Naam van het filter:** "Alle gevolgde studenten" heet voortaan "Alle studenten van wie ik het portfolio kan zien"; de nieuwe keuze "Alle studenten die ik niet heb verborgen" is waar Verbergen op werkt (F6).
- [x] **Oude shares:** die verdwijnen vanzelf, want een share in Portflow eindigt standaard aan het einde van het schooljaar. Wat er toch tussen zit, verbergt de gebruiker zelf (F4).
- [x] **Evaluaties van verborgen studenten:** Verversen haalt ze niet op, tenzij ze zichtbaar zijn in de lijst (F14).
- [x] **"Uit Portflow kiezen"** blijft, voor wie later extra studenten wil volgen ([spec 004](../004-studenten-toevoegen/spec.md)).
- [x] **Bestaande dashboards:** nieuw toegevoegde studenten komen ook op een bestaand dashboard gewoon zichtbaar binnen; de gebruiker verbergt zelf wat hij niet wil zien (F1, F4).
- [x] **Verwijderde beoordelaar:** de app onthoudt dat zijn evaluaties niet meetellen (F13).
- [x] **Verversen bij een filter:** alle niet-verborgen studenten, de zichtbare eerst (F14, gewijzigd 2026-11-19).
- [x] **Filternaam:** "Alle studenten van wie ik het portfolio kan zien" (F6).
- [x] **Coach- en gildefilter:** tonen alleen studenten bij wie het veld *coach*, of *gildemeester*, gelijk is aan de naam van de gebruiker, los van verbergen (F6).
- [x] **Verborgen in het coach- en gildefilter:** verbergen speelt alleen bij de twee filters "Alle studenten van wie ik het portfolio kan zien" en "Alle studenten die ik niet heb verborgen". In het coach- en gildefilter zijn verborgen studenten gewone rijen, zonder dimmen en zonder de knoppen Verbergen en Weer tonen (F4, F5).
- [x] **Rol van een gevonden beoordelaar:** productvaardigheden → gildemeester en coach; alleen andere vaardigheden → coach (F11).
- [x] **Studenten die niet meer delen:** de grijze rij "portfolio niet gedeeld" blijft staan zoals nu ([spec 001](../001-studentenoverzicht/spec.md), F11); de gebruiker kan zo'n student zelf verbergen (F4).
- [x] **Niet groeperen (F8):** zolang er niets is ingedeeld, kiest Overzicht standaard "Niet groeperen": één platte lijst op naam, zonder groepskoppen.
- [x] **Lege kolommen (F9):** een extra kolom die bij niemand gevuld is, toont de app niet, tenzij de gebruiker hem zelf aanzet.
- [x] **Menu Beheer:** blijft zoals het is.
- [x] **Verberg-icoon:** altijd zichtbaar (F4).

### Keuzes bij het bouwen, ter controle

- [ ] **Een student die je niet meer volgt, komt terug.** "Student niet meer volgen" ([spec 011](../011-student-bewerken/spec.md)) verwijdert een student. Deelt die student zijn portfolio nog, dan voegt de volgende Verversen-ronde hem weer toe (F3). Gebruik daarom liever Verbergen. Moet "niet meer volgen" voortaan verbergen, of de app onthouden dat je die student niet wilt?
- [x] Je eigen naam verwijderen (Coaches) sluit je eigen evaluaties niet uit; je naam wordt ook niet automatisch teruggezet ([spec 007](../007-coaches/spec.md), F2a).
- [x] Iemand die je zelf weer toevoegt (namen typen of uit Portflow kiezen), telt weer mee.
- [x] Verversen op een pagina zonder studentenlijst (bijvoorbeeld Instellingen) haalt alle studenten op die niet verborgen zijn. Studenten die in een ronde nieuw zijn toegevoegd, worden in die ronde ook opgehaald.
- [x] Een naam die nog niet te koppelen is omdat meer gedeelde studenten zo heten ([spec 015](../015-koppelen-aan-portflow/spec.md), F4), voegt de app niet automatisch toe; de gebruiker koppelt die bij Student bewerken.
- [x] Automatisch toegevoegde studenten krijgen geen coach.
- [x] De eerste ronde start ook bij het opstarten van de app, als er een geldig token is maar nog nooit is opgehaald.


## Logboek

- 2026-11-11 – spec aangemaakt na een gesprek over de twee soorten gebruik. Keuzes van de gebruiker: de eenvoudige gebruiker ziet alleen behaalde niveaus; standaard alle gedeelde studenten met per rij een icoon om te verbergen; het filter krijgt "Mijn gevolgde studenten"; het semester is in de tabel te kiezen met een keuzelijstje; geen twee standen. De doelgroep omvat coaches met 1 tot 3 squads en gildemeesters.
- 2026-11-11 – antwoorden verwerkt: beoordelaars (F10–F13), filternamen (F6), verversen alleen zichtbare studenten (F14), oude shares en "Uit Portflow kiezen" beantwoord; nieuwe open vragen over de rol van automatisch toegevoegde beoordelaars, bestaande dashboards en verversen bij een filter
- 2026-11-11 – beantwoord: op een bestaand dashboard komen nieuwe studenten gewoon zichtbaar binnen
- 2026-11-11 – beantwoord: een verwijderde beoordelaar telt niet meer mee (F13); verversen bij een filter alleen de zichtbare studenten (F14); filternaam met "van wie"; coach- en gildefilter alleen op de velden coach en gildemeester, los van verbergen (F6)
- 2026-11-11 – beantwoord: in het coach- en gildefilter speelt verbergen geen rol (gewone rijen, geen knoppen)
- 2026-11-11 – beantwoord: rol van een automatisch toegevoegde beoordelaar (F11)
- 2026-11-11 – beantwoord: een student die niet meer deelt, blijft als grijze rij staan
- 2026-11-11 – F8 bevestigd: niet groeperen zolang er niets is ingedeeld
- 2026-11-11 – F9 bevestigd: lege extra kolommen verbergen
- 2026-11-11 – beantwoord: het menu Beheer blijft zoals het is
- 2026-11-11 – beantwoord: het verberg-icoon is altijd zichtbaar. Acceptatiecriterium bij F3 aangevuld en het ontwerp vastgelegd (design-system.md); geen open vragen meer. Status uitgewerkt
- 2026-11-11 – gebouwd en gecontroleerd. Code: `progress.py` (alle beoordelaars tellen, behalve uitgesloten), `staff.py` (uitsluiten, automatisch toevoegen, onthouden bij verwijderen), `portflow_fetch.py` (gedeelde studenten toevoegen, eerste ronde, alleen zichtbare studenten), `overview.py` en `routes.py` (filter, verbergen, semester, standaard niet groeperen, lege kolommen), `_student_table.html`, `staff_edit.html`, `app.js`, `app.css`; database: kolom `students.is_hidden` en tabel `excluded_assessors`. 250 tests slagen, waarvan 18 nieuw in `tests/test_simple_start.py`. In de browser gecontroleerd met de echte database (na een reservekopie): filter, verbergen en weer tonen zonder herladen, gedimde rij, semester kiezen en terugzetten, Verversen stuurt alleen de zichtbare studenten mee, vinkje bij de beoordelaar; geen consolefouten. De eerste ronde na het allereerste verbinden is alleen met een nep-Portflow getest. Eén keuze ter controle staat hierboven. Status klaar
- 2026-11-11 – op verzoek van de gebruiker: het filter op wie heeft bovenaan een vijfde keuze "Alle studenten", die niets filtert; verborgen studenten zijn daar gewone rijen (F6). Gebouwd en getest.
- 2026-11-18 – F7 vervallen op verzoek van de gebruiker: geen keuzelijst voor het semester meer op Overzicht, alleen de tekst "Sem N"; wijzigen gaat bij Beheer › Studenten
- 2026-11-19 – F14 gewijzigd op verzoek van de gebruiker: Verversen haalt weer alle niet-verborgen studenten op, maar de zichtbare eerst (Overzicht: de lijst; Evaluaties: de tabel; studentpagina: die student)
