# 021 – Mezelf als coach of gildemeester instellen

**Status:** klaar
**Laatst bijgewerkt:** 2026-11-11

## Doel

Als **coach** of **gildemeester** wil ik in het Overzicht met één klik mezelf als coach of gildemeester van een student instellen, zodat ik na de eenvoudige start ([spec 019](../019-eenvoudige-start/spec.md)) snel mijn eigen studenten kan aanwijzen zonder elke student te openen.

Het werkt net als het semesterkeuzelijstje in de tabel (spec 019): wijzigen zonder het bewerkscherm.

## Gebruikers

- [x] Coach: de kolom Coach
- [x] Gildemeester: de kolom Gildemeester
- "Jezelf" is de gebruiker: de naam uit Portflow ([gegevensmodel](../../docs/gegevensmodel.md#gebruiker)).

## Betrokken begrippen

- Coach, gildemeester, gilde: [begrippen](../../docs/begrippen.md).
- De gildemeester hoort bij een gilde van de student; een student heeft nul of meer gildes, elk met een eigen gildemeester ([spec 016](../016-gildes-van-een-student/spec.md), [spec 018](../018-beroepsrol-in-gilde/spec.md)).

## Functionele eisen

- [x] **F1 – Knop bij een lege coach.** In het Overzicht staat in de kolommen Coach en Coach (volledig), als de student geen coach heeft, altijd een klein icoontje in plaats van "–". Klikken maakt de gebruiker coach van deze student. De tabel toont daarna je naam, op dezelfde plek in de pagina.
  - *Acceptatie:* student zonder coach → icoontje; klik → de cel toont je naam, ook na herladen. Student met een coach → geen icoontje.
- [x] **F2 – Knop bij een lege gildemeester.** Idem in de kolommen Gildemeester (voornaam en volledige naam), als geen enkel gilde van de student een gildemeester heeft. Een klik:
  - **Student met gildes:** je wordt gildemeester van de gildes van de student die bij jou horen (jouw gildes in de lijst Gildemeesters, [spec 006](../006-gildemeesters/spec.md)). Hoort geen van die gildes bij jou, dan van al zijn gildes.
  - **Student zonder gilde:** heb je precies één gilde, dan krijgt de student dat gilde, met jou als gildemeester. Heb je geen of meer gildes, dan is er geen icoontje (kies dan eerst een gilde via Student bewerken).
  - *Acceptatie:* student met gildes AI en BE, jij hebt BE → alleen bij BE ben jij gildemeester. Student met gilde AI, jij hebt BE → bij AI ben jij gildemeester. Student zonder gilde, jij hebt alleen BE → de student krijgt BE met jou. Student zonder gilde, jij hebt geen of twee gildes → geen icoontje.
- [x] **F3 – Alleen met een bekende gebruiker.** Is de naam van de gebruiker niet bekend (nooit verbonden met Portflow), dan verschijnt het icoontje niet.
  - *Acceptatie:* zonder naam geen icoontje; een POST geeft een melding en wijzigt niets.
- [x] **F4 – Rol vanzelf erbij.** Sta je nog niet als coach (F1) of gildemeester (F2) in de lijst Coaches/Gildemeesters, dan zet de klik die rol bij je naam aan, of voegt je toe.
  - *Acceptatie:* gebruiker zonder rol gildemeester → na de klik staat hij op Gildemeesters.
- [x] **F5 – Alleen in het Overzicht.** De Studentenlijst krijgt het icoontje niet.
  - *Acceptatie:* de Studentenlijst toont bij een lege coach nog steeds "–".

### Buiten scope

- Een ingevulde coach of gildemeester vervangen of weghalen; dat blijft via Student bewerken ([spec 011](../011-student-bewerken/spec.md)).
- Meerdere studenten tegelijk.

## Schermen

Geen eigen ontwerp. Volgt het Overzicht ([spec 001](../001-studentenoverzicht/spec.md)) en het semesterkeuzelijstje uit spec 019. Icoontje in de stijl van `_icons.html`, met een tooltip als "Maak mij coach" / "Maak mij gildemeester".

## Data

- **Bron:** eigen opslag; `students.coach_id` en `student_guilds.guild_master_id`. Geen Portflow-aanroepen.
- **Privacy:** niets nieuws.

## Technische eisen

- Een POST-route per actie, zoals `/studenten/<id>/semester`. Met JavaScript via `fetch`, daarna herlaadt de pagina op dezelfde scrollpositie (er kunnen meer cellen veranderen, zoals de kolom Gilde en het filter op jouw studenten). Zonder JavaScript een gewone redirect.
- Tests: de gevallen uit F1-F5.

## Open vragen

- [x] **Waar:** alleen in het Overzicht (F5).
- [x] **Gildemeester bij geen gilde:** jouw gilde erbij, als je precies één gilde hebt (F2).
- [x] **Gildemeester bij meerdere gildes:** alleen jouw gildes; hoort geen ervan bij jou, dan alle (F2).
- [x] **Rol:** de rol komt vanzelf bij je naam (F4).
- [x] **Zichtbaarheid:** altijd zichtbaar (F1).

## Logboek

- 2026-11-11 – spec aangemaakt op verzoek van de gebruiker
- 2026-11-11 – open vragen beantwoord; status uitgewerkt
- 2026-11-11 – gebouwd: routes `/studenten/<id>/mij-als-coach` en `/mij-als-gildemeester`, icoontje `user-plus`, 9 tests (259 in totaal slagen). In de browser gecontroleerd met de echte gegevens: icoontjes in lege cellen, na een klik de naam en dezelfde scrollpositie; de testwijziging is teruggezet. Het gildemeester-icoontje alleen met tests gecontroleerd. Status klaar
