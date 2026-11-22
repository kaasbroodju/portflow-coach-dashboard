# 014 – Alles verwijderen (terug naar de begintoestand)

**Status:** klaar <!-- idee | uitgewerkt | in bouw | klaar -->
**Laatst bijgewerkt:** 2026-11-09

## Doel

Als **coach** of **gildemeester** wil ik met één functie alle gegevens uit het dashboard verwijderen en de app terugzetten in de begintoestand (zoals bij de eerste start), bijvoorbeeld aan het eind van een semester of om opnieuw te beginnen. Omdat dit niet terug te draaien is, vraagt de app twee keer om bevestiging en maakt hij eerst een reservekopie.

## Gebruikers

- [x] Coach
- [x] Gildemeester
- Geen verschil.

## Betrokken begrippen

- De gegevens van het dashboard ([gegevensmodel.md](../../docs/gegevensmodel.md)), de Portflow-koppeling ([spec 003](../003-portflow-verbinden/spec.md)), demodata ([spec 002](../002-app-schil/spec.md))

## Functionele eisen

- [x] **F1 – Plek.** Onderaan **Instellingen**, onder Demodata, staat een blok **"Alles verwijderen"** met de uitleg "Zet het dashboard terug in de begintoestand: alle gegevens worden verwijderd. De Portflow-koppeling blijft, zodat je direct opnieuw kunt ophalen. Er wordt eerst een reservekopie gemaakt." en een rode knop **"Alles verwijderen…"**.
  - *Acceptatie:* Instellingen toont het blok onderaan met de knop.
- [x] **F2 – Eerste bevestiging.** De knop toont eerst de vraag **"Alle gegevens verwijderen?"** met een opsomming van wat verdwijnt (met aantallen: studenten, evaluaties, projecten, semesters, beroepsrollen, gildes, coaches en gildemeesters, eigen kolommen en instellingen), met daaronder "De Portflow-koppeling blijft staan.", en de knoppen **Annuleren** en **Doorgaan**.
  - *Acceptatie:* na "Alles verwijderen…" staat de vraag met de aantallen; Annuleren laat alles staan.
- [x] **F3 – Tweede bevestiging.** "Doorgaan" toont een tweede stap: **"Weet je het zeker? Dit kun je in de app niet ongedaan maken."** met een veld waarin de gebruiker **VERWIJDEREN** typt. Pas dan werkt de knop **"Definitief verwijderen"** (ook de server controleert het woord; hoofd- of kleine letters maken niet uit).
  - *Acceptatie:* zonder het woord, of met een ander woord, wordt niets verwijderd en blijft de tweede stap staan met de uitleg "Typ VERWIJDEREN om te bevestigen."
- [x] **F4 – Reservekopie.** Vóór het verwijderen maakt de app een kopie van de database in `data/reservekopieen/` met datum en tijd in de naam (bijvoorbeeld `dashboard-2026-11-09-2215.sqlite3`). Mislukt de kopie, dan wordt er niets verwijderd en meldt de app dat. Het token en het browserprofiel komen niet in de kopie.
  - *Acceptatie:* na het verwijderen staat er een kopie met de oude gegevens in de map; terugzetten gaat door de app te stoppen en het bestand over `data/dashboard.sqlite3` te zetten.
- [x] **F5 – Wat er verdwijnt.** Alle gegevens in de database (ook demodata, uitgesloten beoordelaars en alle instellingen, zoals de semesterperiode, de kolomkeuze en het tijdstip van ophalen). Ook een lopende, niet afgeronde Excel-import wordt vergeten, en de bewaarde bestanden van bewijsstukken in `bestanden/` worden gewist ([spec 038](../038-bestanden-bekijken/spec.md), toegevoegd 2026-11-22). De AI-adviezen verdwijnen ook; de instellingen van AI-advies (adres van Ollama, model) blijven, net als de Portflow-koppeling ([spec 040](../040-ai-advies-niveau/spec.md)). De structuur van de database blijft, zodat de app meteen verder kan. **De Portflow-koppeling blijft** (gewijzigd 2026-11-11): het token, het browserprofiel (`data/browser-profile`, met de HU-login) en de instellingen van de koppeling (eigen portfolio-id, naam van de gebruiker, Canvas-adres, "Zichtbaar verversen", laatst ververst). Zoals bij het eerste verbinden staat de gebruiker daarna op Coaches.
  - *Acceptatie:* na het verwijderen zijn alle tabellen leeg, behalve de instellingen van de koppeling en de gebruiker op Coaches; het token staat nog in de database en het browserprofiel bestaat nog.
- [x] **F6 – Begintoestand.** Na het verwijderen gaat de gebruiker naar **Overzicht** met de melding "Alle gegevens zijn verwijderd. De reservekopie staat in data/reservekopieen/…". Het dashboard is zoals direct na het eerste verbinden: 0 studenten (de lege staat van [spec 004](../004-studenten-toevoegen/spec.md)), Portflow nog verbonden, geen semesters, projecten, gildes of gildemeesters, en alleen de gebruiker op Coaches. De ophaalronde start niet vanzelf; omdat er nog nooit is opgehaald, werkt de eerstvolgende Verversen als eerste ronde ([spec 019](../019-eenvoudige-start/spec.md), F1, F2): alle gedeelde studenten en beoordelaars komen erbij.
  - *Acceptatie:* Overzicht toont "Nog geen studenten" en de bovenbalk "Verbonden"; Verversen voegt daarna alle gedeelde studenten toe en haalt ze allemaal op.
- [x] **F7 – Niet tijdens inloggen of ophalen.** Loopt er een inlogpoging of een ophaalronde, dan is de knop uitgeschakeld met de uitleg "Wacht tot het inloggen of ophalen klaar is."
  - *Acceptatie:* tijdens een ophaalronde wordt er niets verwijderd.

### Buiten scope

- Een reservekopie terugzetten vanuit de app (kan handmatig, zie F4)
- Alleen een deel verwijderen (bijvoorbeeld alleen studenten); demodata verwijderen heeft al een eigen knop

## Schermen

Geen eigen ontwerp. Volgt de bevestigingen in Instellingen (Demodata verwijderen, Verbinding verbreken); de rode knop is de knop "gevaar" uit het design system.

## Data

- **Bron:** eigen opslag; het token (in de tabel `settings`) en `data/browser-profile` blijven ongemoeid.
- **Privacy:** de reservekopie bevat **geen token** (het wordt uit de kopie gehaald), wel studentgegevens; hij staat in `data/` (niet in de repository) en blijft lokaal.

## Technische eisen

- Eén functie die alles verwijdert, los van de pagina's; de tabellen worden in één transactie leeggemaakt.
- De kopie via de backup-functie van SQLite (een consistente kopie, ook als de app draait).
- Tests: de twee bevestigingen (zonder en met het woord), de kopie, lege tabellen, token en browserprofiel blijven, de begintoestand van Overzicht, en geblokkeerd tijdens ophalen.

## Open vragen

- [x] **Omvang:** alle gegevens; de Portflow-verbinding (token, browserprofiel en instellingen van de koppeling) blijft. *(Gewijzigd 2026-11-11; eerder ging ook de verbinding weg.)*
- [x] **Reservekopie:** ja, automatisch, in `data/reservekopieen/`.
- [x] **Tweede bevestiging:** het woord VERWIJDEREN intypen.
- [x] **Plek:** onderaan Instellingen.

## Logboek

- 2026-11-09 – spec aangemaakt op verzoek van de gebruiker; antwoorden verwerkt; status in bouw
- 2026-11-09 – gebouwd en getest met unit tests (tijdelijke database en browserprofiel); status klaar. Nog niet in de browser bekeken: de server was door de gebruiker gestopt
- 2026-11-11 – gewijzigd op verzoek van de gebruiker: de Portflow-koppeling blijft bij Alles verwijderen (F1, F2, F5, F6), zodat je na het verwijderen meteen "voor het eerst" kunt ophalen om spec 019 te testen. De ronde start niet vanzelf; Verversen werkt als eerste ronde
- 2026-11-11 – het token staat nu in de database (zie spec 003); het blijft staan bij Alles verwijderen en wordt uit de reservekopie gehaald
- 2026-11-11 – aangepast door [spec 024](../024-keuzelijsten/spec.md): eigen kolommen en hun keuzelijsten verdwijnen mee; Invulling en Rol worden daarna weer met de Open-ICT-keuzes gevuld
