# 031 – Gegevensbestand tonen en kiezen

**Status:** klaar <!-- idee | uitgewerkt | in bouw | klaar -->
**Laatst bijgewerkt:** 2026-11-17

## Doel

Als **beheerder of ontwikkelaar** wil ik zien welk databestand het dashboard gebruikt, en het dashboard kunnen starten met een ander databestand, zodat ik weet waar mijn gegevens staan en bijvoorbeeld een testkopie kan gebruiken naast mijn echte gegevens. Sinds [spec 020](../020-installatie/spec.md) kan dat op meerdere plekken zijn (naast de code, in de installatiemap).

## Gebruikers

- [x] Coach
- [x] Gildemeester
- Geen verschil. De opdrachtregeloptie is vooral voor wie de app zelf start (ontwikkelaar, beheerder).

## Betrokken begrippen

- De gegevensmap ([architectuur.md](../../docs/architectuur.md), *Gegevensmap*; [spec 020](../020-installatie/spec.md), I3)

## Functionele eisen

- [x] **F1 – Kopje "Data" in Instellingen.** Instellingen krijgt een kaart **"Data"** met de volledige paden van:
  - de **database** (het SQLite-bestand dat nu in gebruik is);
  - het **Chrome-profiel** (de Portflow-login);
  - de map met **reservekopieën**;
  - het **logbestand** (`dashboard.log`), of "nog niet aangemaakt".
  
  De paden zijn te selecteren en te kopiëren.
  - *Acceptatie:* in Instellingen staat bij Database exact het pad van het bestand dat de app gebruikt.
- [x] **F2 – Herkomst.** Bij de database staat waar de keuze vandaan komt: **standaard** (de map `data/` naast de code), **installatie** (de gegevensmap van een geïnstalleerd dashboard), **opdrachtregel** (`--database`) of **omgevingsvariabele** (`PORTFLOW_DASHBOARD_DATA`).
- [x] **F3 – Map openen.** Een knop **"Map openen"** opent de map van de database in de Finder (macOS) of de Verkenner (Windows).
- [x] **F4 – Opdrachtregeloptie.** `python app.py --database <pad>` start het dashboard met dat databestand. Een relatief pad geldt vanaf de map waar je de opdracht geeft; `~` werkt. Het Chrome-profiel, de reservekopieën en het logbestand komen in **dezelfde map** als dat bestand, zodat één bestand met zijn map één volledig dashboard is (met een eigen Portflow-login).
  - *Acceptatie:* met `--database ~/test/dashboard.sqlite3` toont Instellingen dat pad met herkomst "opdrachtregel", en het Chrome-profiel staat in `~/test/browser-profile`.
- [x] **F5 – Bestand bestaat niet.** Bestaat het opgegeven bestand niet, dan start de app niet en meldt hij: "Het databestand … bestaat niet. Controleer het pad." (geen nieuwe lege database, om een tikfout niet te verwarren met een leeg dashboard).
- [x] **F6 – Draait al.** Draait er al een dashboard op de poort, dan geldt [spec 020](../020-installatie/spec.md), I4 (alleen de browser openen); met `--database` meldt de app daarnaast dat het draaiende dashboard misschien een ander databestand gebruikt.

### Buiten scope

- Een ander databestand kiezen of wisselen vanuit de interface.
- Een nieuwe, lege database maken via de opdrachtregel (zie F5).

## Schermen

Geen eigen ontwerp: een kaart in Instellingen zoals de andere ([design-system.md](../../docs/design-system.md)).

## Data

- **Bron:** alleen de app zelf; geen Portflow-verzoeken.
- **Privacy:** paden kunnen de gebruikersnaam bevatten; ze blijven lokaal. Het token staat in de database en wordt niet getoond.

## Technische eisen

- De gegevensmap wordt op één plek bepaald (`dashboard/paths.py`); `create_app` leidt het Chrome-profiel af van de map van de database.
- Map openen: `open` op macOS, `explorer` op Windows; alleen de map van de database, nooit een pad uit het verzoek.
- Tests voor F1, F2, F4 en F5.

## Open vragen

- [x] Waar komen Chrome-profiel en reservekopieën met `--database`? In dezelfde map als het bestand (F4).
- [x] Wat staat er onder "Data"? Database, Chrome-profiel, reservekopieën, logbestand, herkomst en een knop om de map te openen (F1–F3).
- [x] Bestand bestaat niet: stoppen met een melding (F5).

## Logboek

- 2026-11-17 – spec aangemaakt op verzoek van de gebruiker; vragen beantwoord; status in bouw
- 2026-11-17 – gebouwd: kaart Data in Instellingen (`routes.data_paths`), herkomst in `dashboard/paths.py`, knop Map openen, optie `--database` in `app.py`; het Chrome-profiel staat nu altijd naast de database (`create_app`). Tests in `tests/test_data_paths.py`; in de browser bekeken. Status klaar
