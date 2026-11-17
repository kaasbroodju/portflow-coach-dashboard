# 029 – Tijdlijn van evaluaties en compacte voortgangstabel

**Status:** klaar <!-- idee | uitgewerkt | in bouw | klaar -->
**Laatst bijgewerkt:** 2026-11-17

## Doel

Als **coach** of **gildemeester** wil ik per week van de semesterperiode zien hoeveel evaluaties mijn studenten hebben gekregen en hoeveel er nog op beoordeling wachten, zodat ik zie wanneer er gewerkt wordt, waar het stilvalt en hoeveel beoordelingswerk er klaarstaat.

De console-app heeft deze grafiek al (de "weekgrafiek", [design-system.md](../../docs/design-system.md#schermen)). De webapp krijgt dezelfde grafiek, op de pagina **Evaluaties**, met daarboven, net als in de console-app, een **compacte voortgangstabel** van dezelfde studenten. Die pagina is nu een lege plaatshouder.

## Gebruikers

- [x] Coach
- [x] Gildemeester
- Geen verschil. Wie de grafiek gaat over, kies je met de keuzelijst (F2).

## Betrokken begrippen

- Evaluaties, behaald en openstaand (`?`), met hun regels: [voortgangsregels.md](../../docs/voortgangsregels.md#openstaand)
- De semesterperiode (Instellingen; [gegevensmodel.md](../../docs/gegevensmodel.md#gebruiker))
- De keuzelijst "wie" van Overzicht ([spec 001](../001-studentenoverzicht/spec.md), F13; [spec 019](../019-eenvoudige-start/spec.md))
- Alle tien vaardigheden, OC … RE; geen HBO-i-beroepstaken (die staan nog niet in de lokale gegevens)

## Functionele eisen

- [x] **F1 – Weekgrafiek op Evaluaties.** Op de pagina Evaluaties staat een staafgrafiek met **één staaf per week** van de semesterperiode, van de week van de begindatum tot en met de week van de einddatum (weken beginnen op maandag). Elke staaf is gestapeld:
  - onderaan het aantal **behaalde** evaluaties in die week (groen);
  - erbovenop het aantal **ingediende, nog niet beoordeelde** evaluaties (`?`, blauw).
  
  Boven elke staaf staat het totaal (alleen als het groter is dan 0). Onder de as staan het weeknummer (W1, W2, …) en de maandag van die week (bijvoorbeeld "6/10"). Links staat een verticale as met aantallen. Onder de grafiek staat een legenda: "behaald" en "ingediend (?)".
  - *Acceptatie:* met 3 behaalde evaluaties en 2 openstaande in week 4 staat bij W4 een staaf met 3 groen en 2 blauw, en erboven "5".
- [x] **F2 – Kiezen over welke studenten.** Boven de grafiek staat **alleen** dezelfde keuzelijst "wie" als op Overzicht (geen semester, project, gilde of eigen keuzelijsten) (onder andere "Alle studenten", "Alle studenten die ik niet heb verborgen", "Mijn coachstudenten", "Mijn gildestudenten"), met dezelfde opties en dezelfde betekenis. De grafiek telt alleen de evaluaties van de gekozen studenten. De keuze wordt **onthouden** na herladen en herstarten, als eigen keuze van Evaluaties, los van Overzicht (zoals [spec 023](../023-filters-onthouden/spec.md)).
  - *Acceptatie:* met "Mijn coachstudenten" telt de grafiek alleen evaluaties van studenten met de gebruiker als coach.
- [x] **F3 – Wat telt mee.** Er tellen dezelfde evaluaties als in het overzicht ([voortgangsregels.md](../../docs/voortgangsregels.md)): evaluaties van uitgesloten beoordelaars tellen niet, en een openstaande evaluatie telt alleen zoals daar beschreven (alleen de nieuwste per vaardigheid, binnen de semesterperiode). Een **eindassessment** (alle tien vaardigheden in één verzoek) telt niet als tien openstaande evaluaties. Elke vaardigheid in een evaluatieverzoek telt als één evaluatie, zoals in de console-app. Een beoordeling op startniveau (`0`) telt mee als behaalde evaluatie. Evaluaties buiten de semesterperiode tellen niet.
  - *Acceptatie:* een eindassessment dat nog niet is beoordeeld, voegt geen tien blauwe evaluaties toe aan de grafiek.
- [x] **F3a – Week van indienen.** Een evaluatie telt in de week waarin de student hem **indiende**, ook als hij later beoordeeld is. Dat is de datum van de zelfevaluatie van de student in hetzelfde evaluatieverzoek, voor dezelfde vaardigheid. Is die er niet, dan geldt de datum van de beoordeling.
  - *Acceptatie:* een evaluatie die in week 3 is ingediend en in week 5 beoordeeld, telt in week 3 als behaald.
- [x] **F4 – Getallen bij hover.** Bij hover (of focus) over een staaf staat er: de week met datums ("W4, 22/9 – 28/9"), het aantal behaald en het aantal ingediend.
- [x] **F5 – Lege toestand.** Zijn er voor de gekozen studenten geen evaluaties in de semesterperiode, dan staat er "Nog geen evaluaties in deze semesterperiode." in plaats van de grafiek. Boven de grafiek staat de semesterperiode met een link naar Instellingen; is er geen periode opgeslagen, dan geldt het lopende semester (zoals op Overzicht) en staat er "(het lopende semester)" achter.

### Compacte voortgangstabel

- [x] **F7 – Tabel boven de grafiek.** Boven de grafiek staat een compacte tabel met dezelfde voortgang als op Overzicht ([spec 001](../001-studentenoverzicht/spec.md)), voor dezelfde studenten als de grafiek (de keuzelijst "wie" van F2 geldt voor beide).
  - *Acceptatie:* met "Mijn coachstudenten" staan in de tabel alleen coachstudenten, en telt de grafiek alleen hun evaluaties.
- [x] **F8 – Kolommen.** Student (naam, met het rol-label en "Assessment ingeleverd" zoals op Overzicht), OC … RE, Gilde, Project, Semester, Rol (in de squad), Coach en Gildemeester (voornamen). Geen eigen kolommen en geen kolomkeuze.
- [x] **F9 – Cellen als op Overzicht.** De cellen van OC … RE tonen dezelfde tekst, dezelfde kleuren (ook blauw voor `?` en grijs `n/b`) en dezelfde details bij hover als op Overzicht. De markup van een cel staat op één plek en wordt door beide tabellen gebruikt.
- [x] **F10 – Ordening per project.** De rijen staan per project (in de volgorde van de projecten op Overzicht), met studenten zonder project als laatste; binnen een project op naam. Tussen twee projecten staat alleen een dunne lijn, geen groepskop.
  - *Acceptatie:* twee studenten van project A en één zonder project: eerst A (op naam), dan een lijn, dan de student zonder project.
- [x] **F11 – Compact en alleen lezen.** Kleinere letters en lagere rijen dan op Overzicht, zonder avatar. De tabel is niet sorteerbaar en heeft geen zoekveld, geen knoppen om te verbergen en geen keuzelijst voor het semester. Onder de tabel staat het aantal studenten. Zijn er geen studenten bij de keuze, dan staat er "Geen studenten bij deze keuze."

### Buiten scope

- HBO-i-beroepstaken in de grafiek (de console-app kon ze verbergen; de webapp heeft ze nog niet).
- Klikken op een staaf om de evaluaties van die week te zien (kan later).
- De lijst met openstaande evaluatieverzoeken die op jouw beoordeling wachten (de rest van de pagina Evaluaties; [spec 030](../030-te-beoordelen/spec.md)).
- Een grafiek per student.
- Sorteren, zoeken, eigen kolommen en bewerken in de compacte tabel (dat kan op Overzicht en Studenten).
- De huidige week markeren.

## Schermen

| Scherm | Bestand | Opmerking |
|---|---|---|
| Weekgrafiek in de console-app | — | Getoond door de gebruiker in de chat (2026-11-17), niet opgeslagen: bevat echte namen. |

Kleuren: groen en blauw zoals de niveaulabels ([design-system.md](../../docs/design-system.md#kleuren)): behaald in het groen van "2 of meer evaluaties", ingediend in het blauw van de `?`-cel. Geen grafiekbibliotheek: de staven zijn HTML/CSS of inline SVG ([architectuur.md](../../docs/architectuur.md)).

## Data

- **Bron:** alleen de lokale database (tabel `evaluations`, opgehaald door [spec 005](../005-gegevens-ophalen/spec.md)); geen Portflow-verzoeken.
- **Benodigde velden:** vaardigheid, niveau, datum, status van het evaluatieverzoek, beoordelaar.
- **Verversen:** na "Verversen", zoals het overzicht.
- **Privacy:** alleen aantallen per week; geen namen in de grafiek.

## Technische eisen

- De telling per week staat op één plek in de code, en gebruikt dezelfde regels (uitgesloten beoordelaars, openstaand, eindassessment) als het overzicht; niet opnieuw implementeren.
- De keuzelijst "wie" gebruikt dezelfde code als Overzicht.
- Tests voor F1 (indeling in weken, grenzen van de periode), F2 en F3.

## Open vragen

- [x] Datum: de week van **indienen** (F3a). Let op: de console-app gebruikte de datum van het beoordelingsitem, ondanks de naam `submitted_at`; de webapp neemt de datum van de zelfevaluatie, die lokaal ook al wordt opgeslagen.
- [x] Filters: alleen de keuzelijst "wie" (F2).
- [x] Onthouden: ja, een eigen keuze voor Evaluaties (F2).
- [x] Startniveau telt mee als behaalde evaluatie (F3).
- [x] Huidige week markeren: nee (buiten scope).
- [x] Compacte tabel: boven de grafiek, per project met een dunne lijn, kolommen Gilde, Project, Semester, Rol, Coach en Gildemeester (antwoorden van 2026-11-17).

## Logboek

- 2026-11-17 – spec aangemaakt op verzoek van de gebruiker, naar de weekgrafiek van de console-app; onderdeel van de pagina Evaluaties
- 2026-11-17 – open vragen beantwoord door de gebruiker; status uitgewerkt
- 2026-11-17 – gebouwd: telling in `dashboard/timeline.py` (op basis van `progress.py`, dat nu per evaluatie ook de datum van indienen bijhoudt), pagina `evaluations.html`, keuze "wie" in `settings` (`evaluations_who`); tests in `tests/test_timeline.py`. F5 aangepast: er is altijd een periode (het lopende semester als er niets is opgeslagen), dus een link naar Instellingen in plaats van een lege toestand. In de browser bekeken. Status klaar
- 2026-11-17 – uitgebreid op verzoek van de gebruiker met de compacte voortgangstabel (F7–F11); open vragen beantwoord; status in bouw
- 2026-11-17 – compacte tabel gebouwd: één kaart "Voortgang" met de keuzelijst, de tabel en daaronder "Evaluaties per week"; de cel is een gedeelde macro (`_level_cell.html`) voor Overzicht en Evaluaties; blokken per project in `timeline.project_blocks`; tests in `tests/test_timeline.py`. In de browser bekeken. Status klaar
