# 033 – Namen verbergen

**Status:** klaar <!-- idee | uitgewerkt | in bouw | klaar -->
**Laatst bijgewerkt:** 2026-11-18

## Doel

Als **coach** of **gildemeester** wil ik met één schakelaar alle studentnamen in het dashboard vervangen door "Student 1", "Student 2", …, zodat ik het dashboard kan demonstreren en screenshots kan delen (bijvoorbeeld via Discord) zonder namen van echte studenten te laten zien.

## Gebruikers

- [x] Coach
- [x] Gildemeester
- Geen verschil.

## Betrokken begrippen

- Privacy: geen echte studentgegevens in screenshots ([architectuur.md](../../docs/architectuur.md))

## Functionele eisen

- [x] **F1 – Schakelaar.** In het gebruikersmenu linksonder (waar ook "Dashboard afsluiten" staat, [spec 020](../020-installatie/spec.md), I5) staat een schakelaar **"Namen verbergen"**. Aan of uit gaat met één klik; de pagina laadt opnieuw.
- [x] **F2 – Vervanging.** Staat hij aan, dan staat op elke plek waar de volledige naam van een student zou staan **"Student N"**: een vast nummer per student (in de volgorde waarin de studenten zijn toegevoegd), zodat je in een demo nog ziet dat het verschillende studenten zijn. Dat geldt voor de zichtbare tekst, tooltips, de titel van de pagina en de zoekfunctie. Ook in de **titels van evaluatieverzoeken** wordt de naam vervangen (studenten zetten hun naam soms in de titel, bijvoorbeeld "Samenwerken - Anna Appel - 3-11-2026").
  - *Acceptatie:* met de schakelaar aan staat de naam van geen enkele gevolgde student meer in de HTML van Overzicht, Evaluaties, Studenten, de studentpagina en Te beoordelen.
- [x] **F3 – Initialen.** De rondjes met initialen van studenten tonen in plaats van de initialen het nummer ("12").
- [x] **F4 – Pagina's.** Het werkt in elk geval op **Overzicht**, **Evaluaties** (tabel, tijdlijn, Te beoordelen), **Beheer › Studenten** en de **studentpagina** ([spec 032](../032-studentpagina/spec.md)); omdat de vervanging op één plek gebeurt, ook op de andere pagina's van het dashboard (Projecten, Semesters, Student bewerken, …).
- [x] **F5 – Zichtbaar dat het aan staat.** Zolang de namen verborgen zijn, staat bovenaan elke pagina een smalle balk **"Namen zijn verborgen"** met **"Namen tonen"**.
- [x] **F6 – Niet onthouden.** De schakelaar geldt tot het dashboard opnieuw start; daarna zijn de namen weer zichtbaar.
- [x] **F7 – Alleen weergave.** Verbergen verandert niets aan de gegevens: niets in de database, niets in Portflow. Bewerken en invullen blijven werken.

### Buiten scope

- Namen van coaches, gildemeesters en de gebruiker zelf (geen voorkeur van de gebruiker; het gaat om de privacy van studenten). Staat een gevolgde student ook in de lijst met coaches of gildemeesters (bijvoorbeeld als beoordelaar), dan wordt zijn naam wel verborgen; de eigen naam van de gebruiker nooit.
- Delen van namen (alleen een voornaam) in vrije tekst, zoals een titel van een verzoek met alleen de voornaam; de vervanging zoekt op de volledige naam zoals die in het dashboard staat.
- Namen in een Excel-bestand dat je aan het importeren bent ([spec 013](../013-excel-importeren/spec.md)): die staan nog niet in het dashboard.

## Schermen

Geen eigen ontwerp. De schakelaar in het gebruikersmenu; de balk zoals de demobanner ([design-system.md](../../docs/design-system.md)).

## Data

- **Bron:** de studenten in de lokale database (voor de nummers en de namen die vervangen worden).
- **Privacy:** dit is een privacyfunctie; de namen verlaten de computer niet.

## Technische eisen

- De vervanging gebeurt op één plek (bij het versturen van elke pagina), niet per template, zodat nieuwe pagina's vanzelf meedoen.
- De stand staat in het geheugen van de app, niet in de database (F6).
- Tests voor F2, F3, F5 en F6.

## Open vragen

- [x] Vervanging: "Student 1", "Student 2", … met een vast nummer per student (F2).
- [x] Andere namen (coaches, gildemeesters, eigen naam): geen voorkeur van de gebruiker; niet verbergen. Studentnamen in titels van verzoeken wel (F2).
- [x] Onthouden: nee, alleen tot het dashboard opnieuw start (F6).

## Logboek

- 2026-11-18 – spec aangemaakt op verzoek van de gebruiker; vragen beantwoord; status uitgewerkt
- 2026-11-18 – gebouwd: `dashboard/hide_names.py` (vervanging na het renderen van elke pagina, alleen hele woorden, ook HTML- en JSON-vormen; nummers in de rondjes), schakelaar in het gebruikersmenu, balk bovenaan; bij opslaan van Student bewerken blijft de echte naam bewaard. Gevonden bij het controleren: de eigen naam van de gebruiker stond als afzender bij een verzoek en werd "Student 140", en een student stond ook bij de coaches; nu opgelost zoals hierboven. Tests in `tests/test_hide_names.py`; in de browser op 10 pagina's met echte gegevens gecontroleerd dat geen studentnaam meer voorkomt. Status klaar
