# 020 – Installatie, releases en bijwerken

**Status:** in bouw <!-- idee | uitgewerkt | in bouw | klaar -->
**Laatst bijgewerkt:** 2026-11-23

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

- [x] **I1 – Eén regel.** De README en elke releasepagina tonen per besturingssysteem één regel om te kopiëren, met een korte uitleg in gewone taal ("Open Terminal, plak deze regel en druk op Enter"):
  - macOS (Terminal): `curl -fsSL https://github.com/petersnoek-hu/portflow-coach-dashboard/releases/latest/download/install-macos.sh | sh`
  - Windows (PowerShell): `irm https://github.com/petersnoek-hu/portflow-coach-dashboard/releases/latest/download/install-windows.ps1 | iex`
  - *Acceptatie:* op een schone Mac en een schone Windows-laptop zonder Python is het dashboard na het plakken van die ene regel geïnstalleerd en geopend.
- [x] **I2 – Wat het script doet.** Zonder beheerdersrechten, en met een korte Nederlandse melding per stap:
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
- [x] **I4 – Snelkoppeling.** macOS: een app **"Portflow coach dashboard"** in `~/Applications`, met het `>_`-icoon, vast te zetten in het Dock. Windows: een snelkoppeling met dat icoon in het **Startmenu** en op het **bureaublad**. Een klik start de app **zonder terminalvenster** en opent het dashboard in de standaardbrowser. Draait de app al, dan opent alleen het dashboard.
  - *Acceptatie:* twee keer klikken geeft twee browsertabbladen en één draaiende app, geen foutmelding over een bezette poort.
- [x] **I5 – Afsluiten.** In het gebruikersmenu (onderin de zijbalk) staat **"Dashboard afsluiten"**; dat stopt de app en toont "Het dashboard is gestopt. Open het weer met de snelkoppeling."
- [x] **I6 – Nog een keer installeren.** Het script opnieuw uitvoeren werkt de installatie bij (zoals U3) en raakt de gegevens niet.
- [x] **I7 – Verwijderen.** Het script met `--verwijderen` (macOS: `… | sh -s -- --verwijderen`; Windows: `& ([scriptblock]::Create((irm …))) --verwijderen`, omdat `irm | iex` geen argumenten doorgeeft) haalt het programma en de snelkoppeling weg. De gegevens blijven staan, tenzij de gebruiker op de vraag "Ook je gegevens verwijderen?" ja antwoordt.
- [x] **I8 – Logboek.** Elk installatiescript (ook bij bijwerken en `--verwijderen`) schrijft een logboek **`install.log`** in de map waar de gebruiker het commando gaf. Kan het daar niet schrijven, dan in de thuismap (`~/install.log`, `%USERPROFILE%\install.log`). Bestaat het bestand al, dan komen de nieuwe regels onderaan, met een kop per keer dat het script draait. Elke regel heeft de **datum, tijd en het huidige pad**. Het logboek bevat:
  - de kop: datum, besturingssysteem en versie, het script en de gebruikte mappen;
  - elke uitgevoerde opdracht met zijn volledige uitvoer en de afloop (exitcode);
  - elke controle (Chrome, uv, controlesom, gevonden gegevens, draaiend dashboard) met de uitkomst;
  - elke melding aan de gebruiker, elke vraag en het antwoord;
  - aan het eind of het gelukt is, en bij een fout welke stap faalde.
  
  Het script meldt aan het eind waar het logboek staat. Er staan geen wachtwoorden of tokens in (het script komt niet aan de Portflow-verbinding).
  - *Acceptatie:* na een geslaagde en een mislukte installatie in dezelfde map staan beide pogingen in `install.log`, met de opdrachten, hun uitvoer en bij de mislukte poging de stap die faalde.

#### Verbeteringen na de eerste echte installatie (voor versie 0.9.1)

Gevonden bij de installatie van v0.9.0 op een Mac met een ontwikkelomgeving (zie Logboek, 2026-11-17).

- [x] **I9 – Snelkoppeling bij Programma's (macOS).** Het script zet de app in `/Applications` (in de Finder: *Programma's*) als de gebruiker daar mag schrijven, en anders in `~/Applications`. De melding aan het eind noemt de map die echt is gebruikt, in de woorden van de Finder ("Programma's" of "Apps in je thuismap"). Bij bijwerken en verwijderen vindt het script de app in beide mappen.
  - *Acceptatie:* op een Mac waar de gebruiker beheerder is, staat "Portflow coach dashboard" na de installatie bij Programma's in de Finder.
- [x] **I10 – Gegevens later alsnog overnemen.** De vraag om gegevens uit een eerdere map over te nemen (I3) komt ook als de installatie al een database heeft waarin nog **geen studenten** staan (bijvoorbeeld omdat de eerste start een lege database maakte). Overnemen zet de bestaande gegevensmap eerst apart (`data-voor-overnemen-<datum>`), zodat er niets verloren gaat.
  - *Acceptatie:* installeren, de vraag overslaan, het dashboard starten en het script opnieuw draaien: de vraag komt terug, en na het antwoord staan de studenten erin.
- [x] **I11 – Alleen een geïnstalleerd dashboard stoppen.** Het script stopt een draaiend dashboard alleen als dat uit de installatiemap komt. Een dashboard uit een git-checkout (ontwikkelversie) blijft draaien; het script meldt dan dat de poort bezet is en dat het geïnstalleerde dashboard pas start nadat de andere versie is gestopt. Het script herkent het geïnstalleerde dashboard aan zijn proces (het pad `<root>/app/app.py`), zodat ook een dashboard van versie 0.9.0 wordt herkend; `/versie` meldt daarnaast `installed`.
  - *Acceptatie:* met de ontwikkelversie op poort 5050 draait het script zonder die te stoppen.
- [x] **I12 – Eigen poort voor de ontwikkelversie.** De preview in Claude Code (`.claude/launch.json`) gebruikt poort **5051**, zodat de ontwikkelversie en een geïnstalleerd dashboard (5050) naast elkaar kunnen draaien.
- [ ] **I13 – Inloggen bij de eerste start.** Uitzoeken waarom het inloggen bij de eerste echte installatie na 5 minuten afliep (komt het door de melding van *Appbeheer*, of was het venster niet gezien?), en de oorzaak oplossen of in de melding uitleggen. *Open vraag; eerst onderzoeken.* *Ook op de HU-laptop (2026-11-19) lukte verbinden pas bij de tweede poging; wat er bij de eerste misging, weet de gebruiker niet meer. Geen melding van Appbeheer op Windows, dus die verklaring geldt daar niet.*

### Bijwerken

- [x] **U1 – Controleren op een nieuwe versie.** Bij het starten en daarna eens per dag vraagt de app de nieuwste release op bij GitHub (`GET https://api.github.com/repos/petersnoek-hu/portflow-coach-dashboard/releases/latest`). Er gaan geen gegevens mee, behalve het verzoek zelf. Lukt het niet (geen internet), dan gebeurt er niets.
- [x] **U2 – Melding.** Is de versie op GitHub nieuwer, dan staat op elke pagina een smalle balk (zoals de demobanner): **"Versie 1.3.0 is beschikbaar (je hebt 1.2.0)."** met **"Wat is er nieuw"** (een pagina in de app met de releasenote, R6, en een link naar GitHub), **"Nu bijwerken"** en **"Later"**. "Later" verbergt de balk tot de volgende versie.
  - *Acceptatie:* met versie 1.2.0 geïnstalleerd en 1.3.0 op GitHub verschijnt de balk; na "Later" niet meer, tot 1.4.0 verschijnt.
- [x] **U3 – Nu bijwerken.** De app maakt eerst een reservekopie van de database (zonder token, zoals [spec 014](../014-alles-verwijderen/spec.md), zie B8), downloadt de zip, controleert de controlesom, zet de nieuwe code in de programmamap, laat uv de pakketten bijwerken en start zichzelf opnieuw. De pagina toont "Bijwerken…" en herlaadt vanzelf. Lukt het niet, dan blijft de oude versie werken en staat er een melding.
  - *Acceptatie:* na "Nu bijwerken" staat in Instellingen de nieuwe versie, en de studenten, instellingen en Portflow-verbinding zijn er nog.
  - Het hulpscript dat de mappen wisselt (`update_swap.py`) stopt eerst alle processen van de installatie (zoals de Chrome van het inloggen), probeert hernoemen een paar keer (een virusscanner kan nieuwe bestanden even vasthouden), houdt een logboek bij in `<gegevens>/bijwerken/bijwerken.log` en start **altijd** weer een dashboard: de nieuwe versie, of bij elke fout de oude.
  - Blijft het dashboard langer dan 3 minuten weg, dan toont de pagina "Bijwerken…" wat de gebruiker kan doen (opnieuw openen met de snelkoppeling, het logboek, `app-oud` terugzetten).
- [x] **U4 – Uitzetten.** In Instellingen staat **"Controleren op nieuwe versies"** (standaard aan).
- [x] **U5 – Git-checkout.** Draait de app vanuit een git-checkout, dan toont de balk alleen de melding met "Wat is er nieuw", zonder "Nu bijwerken".

- [x] **U6 – Nu bijwerken in Instellingen.** In de kaart **Versie** in Instellingen staat een knop **"Nu bijwerken"**. Die vraagt meteen bij GitHub de nieuwste release op (ook als "Controleren op nieuwe versies" uit staat of de balk met "Later" is weggeklikt) en toont de uitkomst in dezelfde kaart:
  - **nieuwere versie:** "Versie 0.9.3 is beschikbaar (je hebt 0.9.2)." met **"Wat is er nieuw"** en de knop **"Versie 0.9.3 installeren"**, die bijwerkt zoals U3. Vanuit een git-checkout staat er in plaats van de knop dat bijwerken met `git pull` gaat (U5);
  - **geen nieuwere versie:** "Je hebt de nieuwste versie (0.9.2).";
  - **controleren lukt niet:** "Controleren is niet gelukt. Controleer je internetverbinding en probeer het opnieuw."
  - *Acceptatie:* met 0.9.2 geïnstalleerd en 0.9.3 op GitHub toont een klik op "Nu bijwerken" de knop "Versie 0.9.3 installeren"; met 0.9.3 op GitHub en 0.9.3 geïnstalleerd staat er "Je hebt de nieuwste versie (0.9.3)."

- [x] **U7 – Resten van eerdere pogingen opruimen.** Bijwerken (U3, U6) en het installatiescript (I6) ruimen eerst op wat eerdere, mislukte pogingen achterlieten, en zetten dat in het logboek:
  - een half uitgepakte nieuwe versie (`app-nieuw`), een nieuwe versie waarvan de pakketten faalden (`app-mislukt`) en een oude download (`portflow-coach-dashboard.zip` in `<gegevens>/bijwerken`);
  - ontbreekt `app` maar staat `app-oud` er wel (een vastgelopen update), dan zet het installatiescript `app-oud` eerst terug als `app`;
  - na een geslaagde update wordt de download verwijderd.
  
  `app-oud` blijft als reserve staan (hoogstens één). Kopieën van gegevens (`data-leeg-…`, `data-voor-overnemen-…`) en reservekopieën worden nooit automatisch verwijderd. Verwijderen (I7) haalt ook `app-mislukt` weg.
  - *Acceptatie:* met alleen `app-oud` en een achtergebleven `app-nieuw` in de installatiemap staat na het installatiescript weer een werkende `app`, en `app-nieuw` is weg.

### Beta-versie installeren

Voor wie een wijziging wil proberen die nog geen release is (bijvoorbeeld een coach die een fout heeft gemeld, of een tester). De commits zijn niet getest door de workflow van R2; daarom staat er een waarschuwing en een reservekopie.

- [x] **B1 – Keuzelijst "Versie".** In de kaart **Versie** in Instellingen staat een keuzelijst **"Versie"** met twee keuzes:
  - **Nieuwste release** (standaard): het gedrag van U6 (knop "Nu bijwerken", uitkomst in dezelfde kaart);
  - **Beta (commit kiezen)**: toont de lijst met recente commits (B2) en een tweede keuzelijst **"Branch"** (B3).
  - Vanuit een git-checkout is de keuze Beta niet beschikbaar; er staat dat bijwerken met `git pull` en `git checkout` gaat (zoals U5).
  - *Acceptatie:* in een installatie toont de keuzelijst twee keuzes; kiezen van Beta toont de branch-keuzelijst en de commits, zonder de pagina te herladen.
- [x] **B2 – Lijst met recente commits.** Na het kiezen van Beta haalt de app de **10 nieuwste commits** van de gekozen branch op bij GitHub (`GET https://api.github.com/repos/petersnoek-hu/portflow-coach-dashboard/commits?sha=<branch>&per_page=10`) en toont per commit: de korte code (7 tekens), de eerste regel van de commitbericht, de datum en tijd, en een keuzerondje. De eerste commit is niet vooraf gekozen. De huidige beta-commit (B7) is gemarkeerd "geïnstalleerd". Er is geen paginering.
  - *Acceptatie:* de lijst toont precies de 10 nieuwste commits van de branch, nieuwste bovenaan.
- [x] **B3 – Branch kiezen.** De keuzelijst **"Branch"** bevat de branches van de repository (`GET …/branches?per_page=100`), met `main` vooraan en als standaard. Na het veranderen van de branch worden meteen de commits van die branch getoond (B2) en vervalt een eerder gekozen commit.
  - *Acceptatie:* een andere branch kiezen toont de commits van die branch; er is geen "Installeer" zolang er geen commit gekozen is.
- [x] **B4 – Fouten bij ophalen.** Lukt ophalen van de branches of commits niet (geen internet, of de GitHub-limiet voor verzoeken zonder inloggen is bereikt), dan staat er: "Ophalen is niet gelukt. Controleer je internetverbinding en probeer het over een poosje opnieuw." De rest van Instellingen blijft werken.
- [x] **B5 – Installeren met waarschuwing.** Is een commit gekozen, dan staat er een knop **"Installeer"**. Die vraagt eerst een bevestiging met de waarschuwing: **"Dit is een beta-versie die niet is getest en misschien niet goed werkt. Er wordt eerst een reservekopie van je gegevens gemaakt."**, met de knoppen **"Installeer beta-versie"** en **"Annuleren"**. Pas na bevestigen volgt B6.
  - *Acceptatie:* "Annuleren" verandert niets (geen reservekopie, geen download); de waarschuwing komt bij elke keer installeren.
- [x] **B6 – Beta ophalen en installeren.** Na de bevestiging doet de app hetzelfde als U3, maar met de code van die commit: reservekopie (B8), de zip van die commit downloaden (`https://github.com/petersnoek-hu/portflow-coach-dashboard/archive/<volledige commitcode>.zip`), controleren, uitpakken in de programmamap, pakketten bijwerken met uv en opnieuw starten, met dezelfde bescherming als U3 en U7 (bij elke fout blijft de oude versie werken, met een melding). Een commit heeft geen controlesom van de workflow; daarom controleert de app dat de zip uit precies die commit komt (de naam van de bovenste map in de zip eindigt op de volledige commitcode) en dat hij `dashboard/version.py` en `uv.lock` bevat.
  - *Acceptatie:* na "Installeer beta-versie" draait het dashboard met de code van de gekozen commit, en de studenten, instellingen en Portflow-verbinding zijn er nog.
- [x] **B7 – Beta herkenbaar.** Na het installeren van een beta staat in Instellingen › Versie **"Beta: commit a1b2c3d, na versie 0.13.0 (branch main)"**, en onderaan de zijbalk (op elke pagina) **"Versie 0.13.0 + beta a1b2c3d"**. Het versienummer is dat uit de code van de commit: de laatste release vóór die commit, want het nummer verandert alleen bij een release. "Na versie" is dus ook van toepassing op de commit van de release zelf; de app zoekt dat niet apart uit. De app bewaart de commit en branch in `app/.beta`; een gewone update of het installatiescript verwijdert dat bestand. Installeren van de nieuwste release (U3, U6) of van een andere commit zet de gebruiker dus weer terug naar een release of een andere beta. Zie ook de open vraag over de updatebalk.
- [x] **B8 – Reservekopie vóór elke installatie.** Vóór elke installatie van een andere versie maakt de app een reservekopie van de **database**, en pas als die gelukt is begint het downloaden. Dat geldt voor het installeren van een **beta** (B6) én van de **nieuwste release** (U3, U6, de knop in de updatebalk). De reservekopie is die van [spec 014](../014-alles-verwijderen/spec.md) (`reset.backup`): een consistente kopie in `<gegevens>/reservekopieen/`, zonder Portflow-token en zonder API-sleutel.
  - De map `bestanden/` ([spec 038](../038-bestanden-bekijken/spec.md)) en het Chrome-profiel (`browser-profile/`) horen er niet bij: de bestanden zijn altijd opnieuw uit Portflow te halen en het profiel bevat de inlog van Portflow.
  - Mislukt de reservekopie, dan wordt er niets gedownload of vervangen en staat er: "De reservekopie is niet gelukt; er is niets veranderd." De reservekopieën worden nooit automatisch verwijderd (U7).
  - *Acceptatie:* na het installeren van een beta en na het installeren van de nieuwste release staat in `reservekopieen/` telkens een nieuwe database-kopie (zonder token); mislukt de reservekopie (bijvoorbeeld een volle schijf), dan blijft de oude versie ongewijzigd.

### Buiten scope

- Een ondertekend programma (aanpak B), Linux, Homebrew of de Microsoft Store.
- Chrome automatisch installeren.
- Een gedeelde server of webversie: het dashboard blijft lokaal ([architectuur.md](../../docs/architectuur.md#beslissingen)).
- Teruggaan naar een oudere **release** vanuit de app (kan met het script en een versienummer, later). Een oudere commit kiezen als beta (B1) kan wel.
- Pull requests of tags kiezen in plaats van een branch en commit; meer dan 10 commits tonen.

## Schermen

Geen eigen ontwerp. De updatebalk lijkt op de demobanner ([design-system.md](../../docs/design-system.md#componenten)); de knop "Dashboard afsluiten" staat in het gebruikersmenu.

## Data

- **Bron:** GitHub (releases); geen Portflow-gegevens.
- **Verzonden gegevens:** alleen het verzoek aan GitHub (IP-adres en de versie in de User-Agent); geen namen, geen token. Ook de verzoeken voor branches, commits en de zip van een beta (B2, B3, B6) bevatten niets anders. Commitberichten en datums komen van GitHub en worden alleen getoond.
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
- [x] **HU-laptops:** getest door de gebruiker op een beheerde Windows-laptop van de HU (2026-11-19): de installatieregel werkt daar; PowerShell is niet beperkt (zie Logboek).
- [x] **Eerste versienummer:** 1.0.0.
- [x] **Updatebalk bij een beta (B7).** Akkoord (2026-11-22): draait er een beta, dan vergelijkt de balk (U2) zoals altijd het versienummer met de nieuwste release; is er geen nieuwere release, dan blijft de balk weg en blijft de beta staan. Een beta op een hoger versienummer dan de nieuwste release geeft dus geen melding.
- [x] **Reservekopie en `bestanden/` (B8).** De map `bestanden/` komt niet in de reservekopie (2026-11-22): de bestanden zijn altijd opnieuw uit Portflow te halen. Daarmee vervalt ook de vraag over de grootte en de naam van een kopie van die map.

## Logboek

- 2026-11-11 – spec aangemaakt als idee. De gebruiker wil vier manieren van installeren, zichtbaar bij Releases op GitHub; installeren met één terminalopdracht is een goede optie die later wordt uitgewerkt.
- 2026-11-17 – uitgewerkt op verzoek van de gebruiker: installatiescripts voor Windows en macOS zonder zelf Python of pakketten te installeren, een snelkoppeling, en een melding met bijwerken bij een nieuwe release op GitHub. Voorstel: aanpak A (uv); de vier manieren uit de eerste versie zijn teruggebracht tot A, met B en C als afgewogen alternatieven. Open vragen voorgelegd.
- 2026-11-17 – de gebruiker kiest voor dubbelklikken in plaats van een terminalregel; de vorm (installatiebestand of kant-en-klaar programma) en ondertekenen zijn nog open
- 2026-11-17 – aanpak A gekozen: installeren via de console geeft geen waarschuwing van macOS of Windows; het script installeert uv en Python zelf
- 2026-11-17 – open vragen beantwoord: bijwerken met één klik, knop Afsluiten, gegevens in de gebruikersmap met aanbod om bestaande over te nemen, releases automatisch bij een tag met een Claude Code-skill `/release` die de releasenote schrijft (R4–R6), eerste versie 1.0.0. Status uitgewerkt
- 2026-11-17 – gebouwd: versie in `dashboard/version.py` (Instellingen en het gebruikersmenu), gegevensmap in `dashboard/paths.py`, `pyproject.toml` en `uv.lock`, installatiescripts en iconen in `install/`, updatecontrole, updatebalk, pagina "Wat is er nieuw" en bijwerken in `dashboard/updates.py`, `update_routes.py` en `update_swap.py`, "Dashboard afsluiten" in het gebruikersmenu, een tweede klik opent alleen de browser (`app.py`), workflow `.github/workflows/release.yml` (tests op macOS en Windows, zip met controlesom, de installatiescripts proberen op een schone Mac en Windows-machine, release met de releasenote uit `releases/vX.Y.Z.md`), `docs/releases.md` en de skill `.claude/skills/release/`. Tests in `tests/test_install.py`. Op deze Mac in een testmap gecontroleerd: installeren met een nagebouwde release, starten met een eigen gegevensmap, tweede start, afsluiten, verwijderen met behoud van gegevens, en bijwerken met één klik van 1.0.0 naar 1.0.1 (reservekopie, controlesom, wisselen, pakketten, herstart). Nog niet gecontroleerd: het Windows-script (alleen syntaxis; de workflow test het bij de eerste release), de snelkoppelingen via Finder en het Startmenu, de tests op Windows, de skill `/release` en de eerste echte release. Status blijft in bouw tot de eerste release en de test op echte laptops
- 2026-11-17 – eerste release **v0.9.0** (proefversie, gekozen door de gebruiker) met `/release` gemaakt. De eerste run faalde op 3 tests op Windows (Unix-bestandsrechten, en een ophaalronde die de database openhield bij het opruimen); de tests zijn aangepast en de tag is na akkoord verplaatst. De tweede run is geheel geslaagd: tests op macOS en Windows, en installeren, starten, afsluiten en verwijderen op een schone Mac en Windows-machine van GitHub. Een nieuwe workflow start niet altijd bij een tag die in dezelfde push zit; dan helpt de tag opnieuw pushen. `uv.lock` bevat ook het versienummer; toegevoegd aan `docs/releases.md`, de skill en de test. Nog open: installeren met de echte regel op een gewone Mac, een Windows-laptop en een beheerde HU-laptop, de snelkoppelingen, en bijwerken vanuit een echte release
- 2026-11-17 – op verzoek van de gebruiker (I1): de releasepagina toont de installatieregels voor macOS en Windows. De workflow zet `install/release-installatie.md` onder de releasenote; de app laat dat deel weg bij "Wat is er nieuw". De bestaande release v0.9.0 is bijgewerkt
- 2026-11-17 – I8 toegevoegd op verzoek van de gebruiker: een logboek `install.log` in de map van het commando (anders de thuismap), aanvullen bij elke run; status in bouw
- 2026-11-17 – I8 gebouwd: beide scripts schrijven `install.log` (opdrachten met uitvoer en exitcode, controles, meldingen, vragen met antwoord, begin en einde), met datum, tijd en huidig pad op elke regel. macOS getest met een geslaagde en een mislukte run in dezelfde map; Windows met PowerShell op macOS tot aan de Chrome-controle en met `--verwijderen`. De workflow controleert het logboek op beide systemen. Het Windows-script toont bij een fout geen rode PowerShell-fout meer, alleen de melding en waar het logboek staat
- 2026-11-17 – waargenomen bij de eerste echte installatie op macOS: *Privacy en beveiliging › Appbeheer* meldt dat python3.13 een andere app probeert te wijzigen. Dat is Google Chrome dat zichzelf wil bijwerken terwijl het voor het inloggen door het dashboard (Python) is gestart; macOS rekent dat aan Python toe. Waarschijnlijk is weigeren onschuldig (Chrome werkt zich bij als je het zelf opent); nog na te gaan of het inloggen daarna lukt
- 2026-11-17 – eerste echte installatie (v0.9.0) op de Mac van de gebruiker, naast de ontwikkelomgeving: programma, eigen Python 3.13 en de snelkoppeling in `~/Applications` gelukt; de snelkoppeling start het dashboard. Gevonden: (1) de snelkoppeling staat niet bij Programma's in de Finder (`/Applications`); (2) het inloggen liep af na 5 minuten; (3) de vraag over eerdere gegevens werd overgeslagen en komt bij een volgende run niet terug, omdat de eerste start al een lege database maakt; (4) het script stopte het dashboard uit de git-checkout op dezelfde poort. Brew, pyenv, pip en `python3` van de gebruiker zijn niet geraakt. Op verzoek van de gebruiker de gegevens uit de git-checkout met de hand overgenomen (de lege map bewaard als `data-leeg-…`); daarna verbonden met Portflow
- 2026-11-17 – I9–I13 toegevoegd voor versie 0.9.1, op verzoek van de gebruiker, naar de bevindingen van de eerste echte installatie
- 2026-11-17 – I12 gebouwd: `.claude/launch.json` gebruikt poort 5051
- 2026-11-17 – I9–I11 gebouwd voor 0.9.1. macOS in een testmap gecontroleerd: de vraag over eerdere gegevens komt terug bij een lege database en neemt de gegevens over (de lege map apart als `data-voor-overnemen-…`); een ander dashboard op de poort blijft draaien en krijgt een melding, het geïnstalleerde dashboard wordt gestopt; de melding noemt de map van de app. `/Applications` zelf is niet geprobeerd (om de echte map niet aan te raken). Windows alleen op syntaxis; de workflow probeert het bij de release. Ook: opdrachten in het macOS-script lezen niet meer van het toetsenbord, zodat ze geen antwoorden wegnemen. I13 (inloggen) staat nog open
- 2026-11-17 – release **v0.9.1** gemaakt met `/release` (I8–I12 en spec 031). De eerste run faalde op een test van het macOS-script die ook op Windows draaide (daar is ook `sh`); de test draait nu alleen op macOS en de tag is na akkoord verplaatst. De tweede run is geheel geslaagd, met de installatieregels op de releasepagina
- 2026-11-17 – workflow bijgewerkt naar bouwstenen op Node 24 (checkout v7, setup-python v7, upload-artifact v7, download-artifact v8), naar aanleiding van de waarschuwing "Node.js 20 is deprecated"; wordt bij de volgende release getest
- 2026-11-17 – bij de release van v0.9.2 bleef bij verwijderen op Windows de programmamap staan, terwijl het script meldde dat het gelukt was. Hersteld: beide scripts stoppen vóór verwijderen of vervangen alle processen van de installatie (het dashboard, Playwright en de Chrome met het profiel uit de installatie; je eigen Chrome niet), Windows probeert verwijderen twee keer, en lukt het niet, dan noemt het script wat er nog staat (exitcode 1). De workflow toont het logboek van het verwijderen
- 2026-11-17 – release **v0.9.2** gepubliceerd (tweede run geheel geslaagd). In die run vond het Windows-script bij het verwijderen geen andere processen en lukte verwijderen in één keer; de oorzaak van de eerdere mislukking is dus niet zeker (mogelijk een proces dat nog aan het stoppen was). De nieuwe maatregelen en de eerlijke melding blijven staan
- 2026-11-17 – U6 toegevoegd op verzoek van de gebruiker: knop "Nu bijwerken" in de kaart Versie van Instellingen, die meteen controleert en zo nodig aanbiedt te installeren
- 2026-11-17 – U6 gebouwd: route `POST /instellingen/versie-controleren` (`update_routes.check_now`), uitkomst in de kaart Versie; tests in `tests/test_install.py`. In de browser gecontroleerd tegen GitHub: "Je hebt de nieuwste versie (0.9.2)." Het aanbod om te installeren alleen met tests (er is nog geen nieuwere release)
- 2026-11-17 – gemeld door de gebruiker: op Windows bleef bijwerken naar 0.9.2 hangen op "Opnieuw starten"; er werd daarna geen dashboard meer gestart. Waarschijnlijke oorzaak: hernoemen van de programmamap lukte niet, en een fout bij het terugzetten werd niet opgevangen. Hersteld in `update_swap.py` (processen stoppen, opnieuw proberen, logboek, altijd herstarten) en op de pagina Bijwerken (melding na 3 minuten). Op macOS van begin tot eind getest in een testmap; Windows alleen met tests. Let op: bij bijwerken draait het hulpscript van de *geïnstalleerde* versie, dus deze verbetering werkt pas bij het bijwerken vanaf de versie die haar bevat
- 2026-11-17 – U7 toegevoegd op verzoek van de gebruiker: resten van eerdere, mislukte pogingen automatisch opruimen; een vastgelopen update (alleen `app-oud`) herstelt het installatiescript
- 2026-11-17 – U7 gebouwd: `Updater.clean_leftovers` vóór het downloaden, het hulpscript verwijdert de download na een geslaagde update, en beide installatiescripts herstellen een vastgelopen update en ruimen resten op (in het logboek). Tests in `tests/test_install.py`, waaronder het macOS-script met een nagebootste vastgelopen installatie; Windows alleen op syntaxis
- 2026-11-17 – R6: "Wat is er nieuw" toont nu ook codeblokken (zoals de installatieregel in de releasenote van 0.9.3), `code` en *cursief*; gecontroleerd met de echte releasenote van GitHub
- 2026-11-19 – getest door de gebruiker op een beheerde Windows-laptop van de HU. Gelukt: installeren met de regel `irm … | iex` in PowerShell zonder fouten, waarna het dashboard openging (I1, I2); de snelkoppelingen in het Startmenu en op het bureaublad starten het dashboard zonder terminalvenster, en een tweede klik opent alleen een extra tabblad (I4); het script nog eens draaien werkt de installatie bij (I6); bijwerken met de knop in de app, waarna het dashboard vanzelf herstart (U3); Dashboard afsluiten via het gebruikersmenu (I5). Studenten en instellingen bleven staan na opnieuw installeren en na bijwerken. Verbinden met Portflow lukte pas bij de tweede poging; de oorzaak van de eerste mislukking is niet bekend (I13 blijft open). Verwijderen (I7) is op de HU-laptop niet geprobeerd; de workflow controleert het bij elke release op een schone Mac en Windows-machine. I1, I2, I4, I6 en I7 afgevinkt; status blijft in bouw tot I13 is uitgezocht
- 2026-11-22 – B1–B8 toegevoegd op verzoek van de gebruiker: een beta-versie installeren via de keuzelijst Versie in Instellingen (tweede keuzelijst voor de branch, de 10 nieuwste commits, waarschuwing, dan de code van die commit ophalen), en een reservekopie van de database vóór elke installatie, ook van de nieuwste release (U3 aangepast). Keuzes van de gebruiker: keuzelijst met 'Nieuwste release' en 'Beta (commit kiezen)', niet vanuit een git-checkout, 10 commits. Nog niet gebouwd; open vragen volgen in het volgende item
- 2026-11-22 – open vragen beantwoord door de gebruiker: de updatebalk vergelijkt bij een beta zoals altijd (B7), en `bestanden/` hoort niet in de reservekopie, omdat die uit Portflow opnieuw te halen is (B8 en U3 aangepast). De reservekopie is dus de database zonder token (spec 014). Status uitgewerkt voor B1–B8; nog niet gebouwd
- 2026-11-22 – B1–B8 gebouwd: keuzelijst Versie in Instellingen met Beta, branch-keuzelijst en de 10 nieuwste commits (`update_routes.py`, `settings.html`, `app.js`), `Updater.branches/commits/start_beta` in `updates.py` (download van de zip van de commit, controle dat de map in de zip de commitcode draagt, `app/.beta`), en de reservekopie (database zonder token) vóór elke installatie, ook van de nieuwste release; mislukt die, dan wordt er niets gedownload. De pagina Bijwerken herlaadt ook als het versienummer gelijk blijft (een beta). Tests in `tests/test_install.py`; in de browser tegen GitHub gecontroleerd tot en met de waarschuwing (niet daadwerkelijk een beta geïnstalleerd, om de eigen installatie niet te raken). Nog niet geprobeerd: een echte beta-installatie op een geïnstalleerd dashboard, en op Windows
- 2026-11-22 – B7 aangepast op verzoek van de gebruiker: bij een beta staat in Instellingen "Beta: commit …, na versie X (branch …)" en in de zijbalk "Versie X + beta …"; de eenvoudige variant, zonder extra verzoek aan GitHub (de uitgebreide variant met "N commits na versie X" via de compare-API is niet gebouwd)
- 2026-11-23 – fout in `remove_launchers` (macOS) hersteld, gevonden toen de snelkoppeling van de gebruiker in `/Applications` verdween. De functie verwijderde bij het opnieuw aanmaken van de snelkoppeling altijd zowel `/Applications/…app` als `~/Applications/…app`, ook bij een test-/beta-installatie die met `PORTFLOW_APPLICATIONS` naar een andere map wijst; zo'n testrun wiste dus de echte snelkoppeling. Nu haalt een omgezette (test)installatie alleen die ene weg; een gewone installatie ruimt beide standaardlocaties nog op (I9). Windows heeft deze fout niet (het overschrijft de snelkoppelingen in het echte Startmenu en op het bureaublad, zonder omleiding). Regressietest in `tests/test_install.py`. De snelkoppeling van de gebruiker met de hand teruggezet; de fix werkt pas mee vanaf de volgende release
