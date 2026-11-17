# 020 – Installatie, releases en bijwerken

**Status:** in bouw <!-- idee | uitgewerkt | in bouw | klaar -->
**Laatst bijgewerkt:** 2026-11-17

## Doel

Als **coach** of **gildemeester** zonder technische kennis wil ik het dashboard op Windows of macOS installeren en openen zoals elk ander programma, zodat ik overzicht krijg zonder zelf Python, een pad of pakketten te hoeven installeren ([soorten gebruik](../../docs/begrippen.md#soorten-gebruik)). Als er een nieuwe versie op GitHub staat, wil ik dat horen en hem met één klik kunnen installeren.

Het stappenplan van de gebruiker:

1. Op de GitHub-pagina bij **Releases** de installatie-instructie voor zijn besturingssysteem volgen.
2. Het dashboard openen met een **snelkoppeling** (Startmenu en bureaublad op Windows, Programma's en Dock op macOS).
3. Chrome opent, de gebruiker logt in bij Portflow en het Chrome-venster sluit weer ([spec 003](../003-portflow-verbinden/spec.md)).
4. De app opent met de gedeelde studenten ([spec 019](../019-eenvoudige-start/spec.md)).
5. Later: de app meldt een nieuwe versie; één klik werkt hem bij, de gegevens blijven staan.

## Gebruikers

- [x] Coach
- [x] Gildemeester
- Vooral gebruikers zonder Python-kennis; ontwikkelaars blijven de repository clonen.

## Keuze van de aanpak

Gekozen: **A** (zie [Open vragen](#open-vragen)).

| Aanpak | Voordelen | Nadelen |
|---|---|---|
| **A. Installatiescript met uv** (gekozen) | Geen Python of pakketten nodig: [uv](https://docs.astral.sh/uv/) zet zelf een eigen Python en de pakketten neer, in de gebruikersmap, zonder beheerdersrechten. Het script is leesbaar en klein. Bijwerken is eenvoudig: nieuwe code neerzetten en de pakketten bijwerken. Geen probleem met ondertekenen, want er wordt geen programma gedownload dat macOS of Windows moet vertrouwen | De installatie begint met één regel in Terminal of PowerShell (kopiëren en plakken). Het eerste installeren downloadt ±100 MB (Python, Flask, Playwright) |
| B. Kant-en-klaar programma (PyInstaller, `.dmg` en `.exe`) | Dubbelklikken, geen terminal | Zonder Apple-ontwikkelaarsaccount (€99/jaar) en Windows-certificaat blokkeren Gatekeeper en SmartScreen het programma of tonen ze een angstige waarschuwing; op beheerde HU-laptops soms helemaal niet te openen. Per besturingssysteem een eigen build. Bijwerken vervangt het hele programma |
| C. Zip met startbestand (`start.command`, `start.bat`) | Geen terminal nodig om te downloaden | De gebruiker moet nog steeds Python en de pakketten installeren, of het startbestand doet dat alsnog (= aanpak A, maar met waarschuwingen bij het eerste openen) |

Clonen met git, venv en `requirements.txt` blijft bestaan voor ontwikkelaars ([architectuur.md](../../docs/architectuur.md#techstack)).

## Functionele eisen

### Releases (voor de beheerder van de repository)

- [x] **R1 – Versienummer.** De app heeft één versienummer (`MAJOR.MINOR.PATCH`, bijvoorbeeld `1.2.0`) op één plek in de code. De release op GitHub heeft de tag `v1.2.0` en Nederlandse release-notes ("Wat is er nieuw"). De app toont zijn versie onderaan Instellingen.
  - *Acceptatie:* na het installeren van release `v1.2.0` staat in Instellingen "Versie 1.2.0".
- [x] **R2 – Release maken.** Een tag `vX.Y.Z` pushen start een GitHub Actions-workflow die de tests draait op macOS en Windows en de release aanmaakt met als bijlagen: de code als zip, `install-macos.sh`, `install-windows.ps1` en een bestand met de SHA-256-controlesom van de zip. Faalt een test, dan komt er geen release.
  - *Acceptatie:* `git tag v1.2.0 && git push --tags` levert binnen enkele minuten een release met de vier bijlagen op.
- [x] **R3 – Vaste adressen.** De installatiescripts zijn altijd te vinden op `https://github.com/petersnoek-hu/portflow-coach-dashboard/releases/latest/download/<bestand>`, zodat de instructie in de README en op de releasepagina niet per versie verandert.
- [x] **R4 – Release met Claude Code.** In de repository staat een Claude Code-skill **`/release`** die een release voor de beheerder voorbereidt en, na zijn akkoord, publiceert. De skill:
  1. controleert dat de werkmap schoon is, op `main` staat en dat alle tests slagen;
  2. toont wat er sinds de vorige release veranderd is (commits en de logboekregels van de specs) en vraagt of het een **patch**, **minor** of **major** versie wordt, met een voorstel;
  3. schrijft een **releasenote** in het Nederlands, voor gebruikers zonder technische kennis: wat is nieuw, wat is verbeterd, wat is opgelost, en of de gebruiker iets moet doen. Geen code- of bestandsnamen, geen studentgegevens; ontwikkelingsgericht geformuleerd zoals de interface ([design-system.md](../../docs/design-system.md));
  4. legt de releasenote voor en verwerkt aanpassingen tot de beheerder akkoord is;
  5. zet het versienummer, maakt de commit en de tag, en pusht pas na een uitdrukkelijk "ja";
  6. volgt de GitHub Actions-run en meldt het adres van de release, of de fout als het misgaat.
  - *Acceptatie:* `/release` in Claude Code levert, na de vragen en het akkoord, een gepubliceerde release met een Nederlandse releasenote; zonder akkoord wordt er niets gepusht.
- [x] **R5 – Instructie.** `docs/releases.md` beschrijft hetzelfde stappenplan voor wie het zonder Claude Code doet, met een sjabloon voor de releasenote. De skill volgt dat document.
- [x] **R6 – Releasenote in de app.** "Wat is er nieuw" in de updatebalk (U2) toont de releasenote van GitHub, zodat de gebruiker ziet wat de nieuwe versie brengt.

### Installeren (voor de gebruiker)

- [ ] **I1 – Eén regel.** De README en elke releasepagina tonen per besturingssysteem één regel om te kopiëren, met een korte uitleg in gewone taal ("Open Terminal, plak deze regel en druk op Enter"):
  - macOS (Terminal): `curl -fsSL https://github.com/petersnoek-hu/portflow-coach-dashboard/releases/latest/download/install-macos.sh | sh`
  - Windows (PowerShell): `irm https://github.com/petersnoek-hu/portflow-coach-dashboard/releases/latest/download/install-windows.ps1 | iex`
  - *Acceptatie:* op een schone Mac en een schone Windows-laptop zonder Python is het dashboard na het plakken van die ene regel geïnstalleerd en geopend.
- [ ] **I2 – Wat het script doet.** Zonder beheerdersrechten, en met een korte Nederlandse melding per stap:
  1. Controleert of Google Chrome geïnstalleerd is; zo niet, dan stopt het met een link naar de downloadpagina van Chrome.
  2. Installeert uv in de gebruikersmap, als dat er nog niet is.
  3. Downloadt de nieuwste release (zip), controleert de controlesom en pakt hem uit in de programmamap (I3).
  4. Laat uv een eigen Python en de pakketten uit de lockfile installeren.
  5. Maakt de snelkoppeling (I4).
  6. Start de app.
  - *Acceptatie:* zonder internet of zonder Chrome stopt het script met een begrijpelijke melding en blijft er geen halve installatie achter.
- [x] **I3 – Vaste mappen.** Programma en gegevens staan gescheiden, zodat bijwerken de gegevens niet raakt:

  | | macOS | Windows |
  |---|---|---|
  | Programma | `~/Library/Application Support/Portflow coach dashboard/app/` | `%LOCALAPPDATA%\Portflow coach dashboard\app\` |
  | Gegevens (database, browserprofiel, reservekopieën) | `~/Library/Application Support/Portflow coach dashboard/data/` | `%LOCALAPPDATA%\Portflow coach dashboard\data\` |

  Vanuit een git-checkout blijft de app `data/` naast de code gebruiken. Vindt het script bij de eerste installatie een git-checkout met gegevens, of geeft de gebruiker er een op, dan biedt het aan die `data/` over te nemen (een kopie; het origineel blijft staan).
- [ ] **I4 – Snelkoppeling.** macOS: een app **"Portflow coach dashboard"** in `~/Applications`, met het `>_`-icoon, vast te zetten in het Dock. Windows: een snelkoppeling met dat icoon in het **Startmenu** en op het **bureaublad**. Een klik start de app **zonder terminalvenster** en opent het dashboard in de standaardbrowser. Draait de app al, dan opent alleen het dashboard.
  - *Acceptatie:* twee keer klikken geeft twee browsertabbladen en één draaiende app, geen foutmelding over een bezette poort.
- [x] **I5 – Afsluiten.** In het gebruikersmenu (onderin de zijbalk) staat **"Dashboard afsluiten"**; dat stopt de app en toont "Het dashboard is gestopt. Open het weer met de snelkoppeling."
- [ ] **I6 – Nog een keer installeren.** Het script opnieuw uitvoeren werkt de installatie bij (zoals U3) en raakt de gegevens niet.
- [ ] **I7 – Verwijderen.** Het script met `--verwijderen` (macOS: `… | sh -s -- --verwijderen`; Windows: `& ([scriptblock]::Create((irm …))) --verwijderen`, omdat `irm | iex` geen argumenten doorgeeft) haalt het programma en de snelkoppeling weg. De gegevens blijven staan, tenzij de gebruiker op de vraag "Ook je gegevens verwijderen?" ja antwoordt.

### Bijwerken

- [x] **U1 – Controleren op een nieuwe versie.** Bij het starten en daarna eens per dag vraagt de app de nieuwste release op bij GitHub (`GET https://api.github.com/repos/petersnoek-hu/portflow-coach-dashboard/releases/latest`). Er gaan geen gegevens mee, behalve het verzoek zelf. Lukt het niet (geen internet), dan gebeurt er niets.
- [x] **U2 – Melding.** Is de versie op GitHub nieuwer, dan staat op elke pagina een smalle balk (zoals de demobanner): **"Versie 1.3.0 is beschikbaar (je hebt 1.2.0)."** met **"Wat is er nieuw"** (een pagina in de app met de releasenote, R6, en een link naar GitHub), **"Nu bijwerken"** en **"Later"**. "Later" verbergt de balk tot de volgende versie.
  - *Acceptatie:* met versie 1.2.0 geïnstalleerd en 1.3.0 op GitHub verschijnt de balk; na "Later" niet meer, tot 1.4.0 verschijnt.
- [x] **U3 – Nu bijwerken.** De app maakt eerst een reservekopie van de database (zonder token, zoals [spec 014](../014-alles-verwijderen/spec.md)), downloadt de zip, controleert de controlesom, zet de nieuwe code in de programmamap, laat uv de pakketten bijwerken en start zichzelf opnieuw. De pagina toont "Bijwerken…" en herlaadt vanzelf. Lukt het niet, dan blijft de oude versie werken en staat er een melding.
  - *Acceptatie:* na "Nu bijwerken" staat in Instellingen de nieuwe versie, en de studenten, instellingen en Portflow-verbinding zijn er nog.
- [x] **U4 – Uitzetten.** In Instellingen staat **"Controleren op nieuwe versies"** (standaard aan).
- [x] **U5 – Git-checkout.** Draait de app vanuit een git-checkout, dan toont de balk alleen de melding met "Wat is er nieuw", zonder "Nu bijwerken".

### Buiten scope

- Een ondertekend programma (aanpak B), Linux, Homebrew of de Microsoft Store.
- Chrome automatisch installeren.
- Een gedeelde server of webversie: het dashboard blijft lokaal ([architectuur.md](../../docs/architectuur.md#beslissingen)).
- Teruggaan naar een oudere versie vanuit de app (kan met het script en een versienummer, later).

## Schermen

Geen eigen ontwerp. De updatebalk lijkt op de demobanner ([design-system.md](../../docs/design-system.md#componenten)); de knop "Dashboard afsluiten" staat in het gebruikersmenu.

## Data

- **Bron:** GitHub (releases); geen Portflow-gegevens.
- **Verzonden gegevens:** alleen het verzoek aan GitHub (IP-adres en de versie in de User-Agent); geen namen, geen token.
- **Privacy:** de database, het token en het browserprofiel blijven in de gegevensmap op de laptop (I3) en gaan nooit mee in een update of een release.

## Technische eisen

- Dependencies blijven Flask en Playwright ([architectuur.md](../../docs/architectuur.md#techstack)); `requests` is niet nodig (de app gebruikt `urllib`). uv is alleen een installatiehulpmiddel, geen dependency van de app. Voor uv komt een `pyproject.toml` met lockfile (`uv.lock`) naast `requirements.txt`.
- Playwright gebruikt de geïnstalleerde Chrome (`channel="chrome"`), dus het script hoeft geen browser te downloaden (`playwright install` is niet nodig).
- De app herkent een installatie aan het bestand `app/.installed` dat het script schrijft (met het pad van uv), en gebruikt dan `<root>/data`; zonder dat bestand blijft het `data/` naast de code. `PORTFLOW_DASHBOARD_DATA` kan de gegevensmap omzetten. Python en de pakketten staan in `<root>/venv`, los van de code, zodat bijwerken alleen `app/` vervangt.
- Starten zonder terminalvenster: op Windows met `pythonw.exe`, op macOS via de kleine app uit I4.
- De scripts staan in de repository (bijvoorbeeld `install/`) en hebben tests waar dat kan (bijvoorbeeld een droge run).
- Testen op echte laptops: een schone Mac, een schone Windows-laptop en een beheerde HU-laptop.

## Open vragen

- [x] **Aanpak:** A, installatiescript via de console (2026-11-17). De gebruiker wilde eerst liever dubbelklikken, maar kiest voor de console omdat die geen waarschuwing geeft:
  - macOS (Gatekeeper) en Windows (SmartScreen) waarschuwen alleen bij bestanden met een downloadlabel (macOS: `com.apple.quarantine`, Windows: *Mark of the Web*). Browsers zetten dat label; `curl` en `irm` in de console niet. Ook wat het script en uv daarna neerzetten (uv, Python, pakketten, de snelkoppeling) heeft geen label.
  - Wel een aandachtspunt: op beheerde Windows-laptops kan beleid (AppLocker, *Constrained Language Mode*) PowerShell-scripts beperken; dat is iets anders dan de SmartScreen-waarschuwing en moet getest worden.
  - De gebruiker installeert **uv niet zelf**: het script installeert uv (met het officiële installatiescript van uv) als het er nog niet is.
  - De gebruiker installeert **Python niet zelf**: uv zet een eigen Python neer. (Python zelf installeren zou voor de gebruiker acceptabel zijn, maar is dus niet nodig.) Pakketten installeren doet het script; dat vond de gebruiker te complex om zelf te doen.
- [x] **Bijwerken:** met één klik in de app (U3).
- [x] **Afsluiten:** een knop "Dashboard afsluiten" in het gebruikersmenu (I5).
- [x] **Gegevensmap:** een vaste gebruikersmap (I3); het script biedt aan bestaande gegevens uit een git-checkout over te nemen.
- [x] **Releases maken:** automatisch bij een tag (R2), met een Claude Code-skill `/release` die de vragen stelt en vooral een goede releasenote schrijft (R4), en een instructie op papier (R5).
- [ ] **HU-laptops** (blokkeert het bouwen niet, wel het afronden): is er een beheerde Windows-laptop van de HU om op te testen? PowerShell-scripts kunnen daar beperkt zijn.
- [x] **Eerste versienummer:** 1.0.0.

## Logboek

- 2026-11-11 – spec aangemaakt als idee. De gebruiker wil vier manieren van installeren, zichtbaar bij Releases op GitHub; installeren met één terminalopdracht is een goede optie die later wordt uitgewerkt.
- 2026-11-17 – uitgewerkt op verzoek van de gebruiker: installatiescripts voor Windows en macOS zonder zelf Python of pakketten te installeren, een snelkoppeling, en een melding met bijwerken bij een nieuwe release op GitHub. Voorstel: aanpak A (uv); de vier manieren uit de eerste versie zijn teruggebracht tot A, met B en C als afgewogen alternatieven. Open vragen voorgelegd.
- 2026-11-17 – de gebruiker kiest voor dubbelklikken in plaats van een terminalregel; de vorm (installatiebestand of kant-en-klaar programma) en ondertekenen zijn nog open
- 2026-11-17 – aanpak A gekozen: installeren via de console geeft geen waarschuwing van macOS of Windows; het script installeert uv en Python zelf
- 2026-11-17 – open vragen beantwoord: bijwerken met één klik, knop Afsluiten, gegevens in de gebruikersmap met aanbod om bestaande over te nemen, releases automatisch bij een tag met een Claude Code-skill `/release` die de releasenote schrijft (R4–R6), eerste versie 1.0.0. Status uitgewerkt
- 2026-11-17 – gebouwd: versie in `dashboard/version.py` (Instellingen en het gebruikersmenu), gegevensmap in `dashboard/paths.py`, `pyproject.toml` en `uv.lock`, installatiescripts en iconen in `install/`, updatecontrole, updatebalk, pagina "Wat is er nieuw" en bijwerken in `dashboard/updates.py`, `update_routes.py` en `update_swap.py`, "Dashboard afsluiten" in het gebruikersmenu, een tweede klik opent alleen de browser (`app.py`), workflow `.github/workflows/release.yml` (tests op macOS en Windows, zip met controlesom, de installatiescripts proberen op een schone Mac en Windows-machine, release met de releasenote uit `releases/vX.Y.Z.md`), `docs/releases.md` en de skill `.claude/skills/release/`. Tests in `tests/test_install.py`. Op deze Mac in een testmap gecontroleerd: installeren met een nagebouwde release, starten met een eigen gegevensmap, tweede start, afsluiten, verwijderen met behoud van gegevens, en bijwerken met één klik van 1.0.0 naar 1.0.1 (reservekopie, controlesom, wisselen, pakketten, herstart). Nog niet gecontroleerd: het Windows-script (alleen syntaxis; de workflow test het bij de eerste release), de snelkoppelingen via Finder en het Startmenu, de tests op Windows, de skill `/release` en de eerste echte release. Status blijft in bouw tot de eerste release en de test op echte laptops
- 2026-11-17 – eerste release **v0.9.0** (proefversie, gekozen door de gebruiker) met `/release` gemaakt. De eerste run faalde op 3 tests op Windows (Unix-bestandsrechten, en een ophaalronde die de database openhield bij het opruimen); de tests zijn aangepast en de tag is na akkoord verplaatst. De tweede run is geheel geslaagd: tests op macOS en Windows, en installeren, starten, afsluiten en verwijderen op een schone Mac en Windows-machine van GitHub. Een nieuwe workflow start niet altijd bij een tag die in dezelfde push zit; dan helpt de tag opnieuw pushen. `uv.lock` bevat ook het versienummer; toegevoegd aan `docs/releases.md`, de skill en de test. Nog open: installeren met de echte regel op een gewone Mac, een Windows-laptop en een beheerde HU-laptop, de snelkoppelingen, en bijwerken vanuit een echte release
