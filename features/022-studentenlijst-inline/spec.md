# 022 – Studentenlijst: inline wijzigen en naar beheer

**Status:** klaar
**Laatst bijgewerkt:** 2026-11-11

## Doel

Als **coach** of **gildemeester** wil ik in de Studentenlijst ([spec 010](../010-studentenlijst/spec.md)) de indeling van een student direct in de tabel wijzigen, met keuzelijstjes zoals het semester in het Overzicht ([spec 019](../019-eenvoudige-start/spec.md)), zodat ik niet elke student hoef te openen. Een pennetje boven een kolom brengt me naar de beheerpagina van die kolom, om bijvoorbeeld een project of gilde toe te voegen.

## Gebruikers

- [x] Coach
- [x] Gildemeester
- Geen verschil.

## Betrokken begrippen

Semester, project, invulling, teamrol, gilde, coach, gildemeester: [begrippen](../../docs/begrippen.md), [gegevensmodel](../../docs/gegevensmodel.md).

## Functionele eisen

- [x] **F1 – Keuzelijst per kolom.** In de Studentenlijst wordt elke cel een keuzelijst in dezelfde onopvallende stijl als het semester in het Overzicht. Een keuze wordt meteen bewaard, zonder herladen. De lege keuze is "–".

  | Kolom | Keuzes | Beheerpagina (F2) |
  |---|---|---|
  | Semester | Sem 1 … Sem 8 | Semesters |
  | Project | de projecten (weergavenaam) | Projecten |
  | Invulling | de keuzes van de keuzelijst Invulling | Keuzelijsten (sinds [spec 024](../024-keuzelijsten/spec.md)) |
  | Rol (teamrol) | de keuzes van de keuzelijst Rol in de squad | Keuzelijsten (sinds spec 024) |
  | Gilde | de gildes, alleen bij nul of één gilde (F4) | Gildes |
  | Coach (voornaam / volledige naam) | de coaches | Coaches |
  | Gildemeester (voornaam / volledige naam) | de gildemeesters, per gilde (F5) | Gildemeesters |
  | Portflow | geen keuzelijst: blijft tekst | – |

  - *Acceptatie:* per kolom: kies een waarde → na herladen staat die waarde er nog; kies "–" → leeg.
- [x] **F2 – Pennetje boven de kolom.** Boven de kolomtitel staat een pennetje dat naar de beheerpagina van die kolom gaat (tabel bij F1).
  - *Acceptatie:* klik op het pennetje bij Project → de pagina Projecten.
- [x] **F3 – Sorteren blijft werken** met de nieuwe waarde. De rij blijft in zijn groep staan tot de pagina herlaadt (zoals bij het semester in het Overzicht).
  - *Acceptatie:* wijzig een project en sorteer op Project → de rij staat op de nieuwe plek.
- [x] **F4 – Gilde.** Heeft de student geen of één gilde, dan is de cel een keuzelijst met de gildes. Een ander gilde kiezen vervangt het gilde; de gildemeester van het oude gilde vervalt. "–" haalt het gilde weg. Heeft de student meer gildes, dan blijft de cel tekst; wijzigen gaat via Student bewerken. Na een wijziging herlaadt de pagina op dezelfde plek, omdat de kolom Gildemeester meeverandert.
  - *Acceptatie:* student met AI → kies BE → alleen BE, zonder gildemeester. Student met AI en BE → tekst "AI, BE".
- [x] **F5 – Gildemeester per gilde.** Per gilde van de student staat een keuzelijst met de gildemeesters; bij meer gildes met de gildecode ervoor ("AI:"). Zonder gilde staat er "–", zonder keuzelijst.
  - *Acceptatie:* student met AI en BE → twee keuzelijstjes; kies bij BE een gildemeester → alleen BE verandert.
- [x] **F6 – Voornaam of volledige naam.** In de kolommen Coach en Gildemeester tonen de keuzes de voornaam, in de kolommen "(volledig)" de volledige naam ([spec 006](../006-gildemeesters/spec.md), F21).
- [x] **F7 – Alleen de Studentenlijst.** Het Overzicht krijgt geen pennetjes en geen nieuwe keuzelijsten.

### Buiten scope

- Naam, studentnummer, startdatum en notities: die blijven in Student bewerken ([spec 011](../011-student-bewerken/spec.md)).

## Schermen

Geen eigen ontwerp. Keuzelijst zoals `.semester-pick` in het Overzicht; pennetje in de stijl van `_icons.html`.

## Data

- **Bron:** eigen opslag (`students`, `student_guilds`). Geen Portflow-aanroepen.
- **Keuzes:** dezelfde als in Student bewerken (spec 011). Is de huidige coach of gildemeester niet (meer) coach of gildemeester in de lijst, dan staat die toch als keuze in de lijst, zodat de cel klopt.

## Technische eisen

- Opslaan via één route per veld, zoals `/studenten/<id>/semester`, met de controles van Student bewerken (spec 011) op één plek.
- Tests per kolom: opslaan, leegmaken, ongeldige waarde.

## Open vragen

- [x] **Gilde:** keuzelijst bij nul of één gilde; bij meer gildes tekst (F4).
- [x] **Gildemeester:** een keuzelijst per gilde (F5).
- [x] **Portflow, Invulling, Rol:** geen pennetje; Portflow blijft tekst. *(Invulling en Rol hebben sinds spec 024 wel een pennetje.)*
- [x] **Overzicht:** geen pennetjes (F7).

## Logboek

- 2026-11-11 – spec aangemaakt op verzoek van de gebruiker
- 2026-11-11 – open vragen beantwoord; status in bouw
- 2026-11-11 – gebouwd: routes `/studenten/<id>/veld/<veld>` en `/studenten/<id>/gildemeester/<gilde>`, controles in `student_edit.py`, icoontje `pencil`. De kolommen voornaam en volledige naam houden elkaar bij. 8 nieuwe tests; 267 tests slagen. In de browser gecontroleerd met de echte gegevens (invulling en coach gewijzigd en teruggezet). Status klaar
- 2026-11-11 – aangepast door [spec 024](../024-keuzelijsten/spec.md): Invulling en Rol krijgen een pennetje naar Keuzelijsten; de keuzes komen uit de keuzelijsten
- 2026-11-17 – aangepast door [spec 028](../028-filters-inklappen/spec.md): in de compacte stand van de filters zijn de pennetjes boven de kolommen verborgen
