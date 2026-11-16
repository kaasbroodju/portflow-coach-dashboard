# 020 – Installatie en releases

**Status:** idee
**Laatst bijgewerkt:** 2026-11-11

## Doel

Als **coach** of **gildemeester** wil ik het dashboard met zo min mogelijk technische stappen installeren en starten, zodat ik geen Python-kennis nodig heb om overzicht te krijgen ([soorten gebruik](../../docs/begrippen.md#soorten-gebruik)).

Het stappenplan dat de gebruiker voor ogen heeft:

1. Installeren: een opdracht, een programma of een download.
2. De app voor de eerste keer starten.
3. Chrome opent, de gebruiker logt in bij Portflow en het Chrome-venster sluit weer.
4. De app opent met de gedeelde studenten ([spec 019](../019-eenvoudige-start/spec.md)).

## Gebruikers

- [x] Coach
- [x] Gildemeester
- Ook gebruikers zonder Python-kennis.

## Manieren van installeren

De gebruiker wil op termijn **vier manieren** aanbieden, allemaal zichtbaar op de **GitHub-pagina bij Releases**:

| Manier | Kort | Voorlopige opmerkingen |
|---|---|---|
| **1. Eén opdracht in de terminal** | Eén regel kopiëren en plakken, die de app downloadt, installeert en start | Een goede optie die later wordt uitgewerkt. Een kandidaat is een script dat **uv** gebruikt; uv brengt zelf Python mee, zodat de gebruiker Python niet apart hoeft te installeren. Eén regel voor macOS en Linux, één voor Windows (PowerShell) |
| **2. PyInstaller** | Een kant-en-klaar programma per besturingssysteem, zonder Python | macOS (Gatekeeper) en Windows (SmartScreen) waarschuwen bij een niet-ondertekend programma; op beheerde HU-laptops kan dat blokkeren. Playwright en Chrome moeten meekomen of gevonden worden. Per besturingssysteem een eigen build |
| **3. Repository clonen** | `git clone`, dan de bestaande stappen met venv en `requirements.txt` | Dit is nu de enige manier ([architectuur.md](../../docs/architectuur.md#techstack)); bedoeld voor wie aan de app wil werken |
| **4. Zip downloaden** | De broncode als zip van de release downloaden, uitpakken en starten | Nog uitzoeken hoe "starten" eruitziet zonder terminal, bijvoorbeeld met een startbestand per besturingssysteem (`start.command`, `start.bat`) |

## Functionele eisen

Nog niet uitgewerkt. Eerst de open vragen beantwoorden.

### Buiten scope

- Een gedeelde server of een webversie: het dashboard blijft lokaal ([architectuur.md](../../docs/architectuur.md#beslissingen)).
- Het eenvoudige gebruik van de app zelf: zie [spec 019](../019-eenvoudige-start/spec.md).

## Open vragen

- [ ] Welke manier eerst? Advies: eerst manier 1 (één opdracht) op een paar collega-laptops testen, voordat er tijd in PyInstaller gaat.
- [ ] Welke besturingssystemen moeten werken: macOS, Windows, beide?
- [ ] Mag de app gegevens bewaren in de map waar hij staat (zoals nu `data/`), of in een vaste gebruikersmap? Bij een zip of een programma is "de map van de app" minder voor de hand liggend.
- [ ] Bijwerken: hoe krijgt de gebruiker een nieuwe versie, en blijven zijn gegevens dan behouden?
- [ ] Ondertekenen van het programma (PyInstaller): is daar een Apple-ontwikkelaarsaccount en een Windows-certificaat voor beschikbaar, of accepteren we de waarschuwing met uitleg?
- [ ] Moet Google Chrome geïnstalleerd zijn, of kan Playwright een eigen browser meenemen? Nu gebruikt het inloggen de geïnstalleerde Chrome ([architectuur.md](../../docs/architectuur.md#inloggen)).

## Logboek

- 2026-11-11 – spec aangemaakt als idee. De gebruiker wil vier manieren van installeren, zichtbaar bij Releases op GitHub; installeren met één terminalopdracht is een goede optie die later wordt uitgewerkt.
