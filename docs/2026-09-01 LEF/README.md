# Snapshot van lef.hu.nl (2026-09-01)

Naslagkopie van de volledige website [lef.hu.nl](https://lef.hu.nl), bedoeld om later te zien wat er veranderd is. Deze map is geen bron voor het dashboard; daarvoor blijft [vaardigheden-niveaus-LEF.md](../vaardigheden-niveaus-LEF.md) gelden.

- Naam van de map: 2026-09-01 (gekozen door de gebruiker).
- Opgehaald op: 2026-11-22.
- Volgens de sitemap van de site zijn alle pagina's laatst gewijzigd op 2026-08-26.
- Teksten zijn letterlijk overgenomen. Alleen de opmaak is omgezet naar Markdown: vet, cursief, onderstreept (`<u>`), links en lijsten.

## Bestanden

| Bestand | Pagina op de site |
|---|---|
| [01-vaardigheden.md](01-vaardigheden.md) | Vaardigheden: https://lef.hu.nl/ |
| [02-beroepsrollen.md](02-beroepsrollen.md) | Beroepsrollen: https://lef.hu.nl/beroepsrollen |
| [03-beroepstaken-hboi.md](03-beroepstaken-hboi.md) | Beroepstaken / HBO-i: https://lef.hu.nl/beroepstaken |
| [04-beroepsproducten.md](04-beroepsproducten.md) | Beroepsproducten: https://lef.hu.nl/beroepsproducten |
| [05-zo-gebruik-je-lef.md](05-zo-gebruik-je-lef.md) | Zo gebruik je LEF: https://lef.hu.nl/leeswijzer |
| [ophalen.py](ophalen.py) | Script dat deze bestanden maakt (alleen standaard-Python) |

## Opbouw

- Elke alinea en elk lijstitem staat op één eigen regel. Zo laat een diff precies de gewijzigde zin zien.
- **Vaardigheden:** per vaardigheid `## CODE – Naam` in de volgorde OC, KO, JKO, KPM, PL, BD, SW, FO, PH, RE. Daarna de inleiding en per niveau `### Niveau N`, met de niveautitel vet. Een openklap-item staat direct onder het niveau waar het bij hoort, als `#### Extra context Niveau N`. Op de site staan de openklap-items onder alle vier de niveaus.
- **Beroepsrollen:** per rol `## Rol` met de gildecode eronder (`gilde: …`). De HBO-i-architectuurlagen geeft de site alleen met kleur aan; hier staan ze als lijst met *hoofdlaag*, *extra laag* of *geen*.
- **Beroepstaken en beroepsproducten:** per beroepstaak `## Architectuurlaag Activiteit`, in de volgorde van de site. De pop-ups met extra toelichting staan als `####` onder het niveau van hun knop.
- Filterknoppen, zoekvenster en de keuze voor de niveauweergave zijn bedieningsonderdelen en staan er niet in. De indeling die alleen in die knoppen staat, is wel overgenomen: de vaardigheidscategorieën en Bachelor/Master bij de beroepsrollen.

## Controle op volledigheid

Alle inhoud staat in de HTML die de server stuurt, ook de dichtgeklapte openklap-items en de pop-ups. De woordentelling van `<main>` in de browser was gelijk aan die van de opgehaalde HTML. Een vergelijking per woord tussen de HTML en de Markdown liet alleen de toegevoegde koppen en labels zien.

| Code | Niveaus | Openklap-items | Bij niveau |
|---|---|---|---|
| OC | 4 | 4 | 1, 2, 3, 4 |
| KO | 4 | 3 | 2, 3, 4 |
| JKO | 4 | 3 | 1, 2, 3 |
| KPM | 4 | 4 | 1, 2, 3, 4 |
| PL | 4 | 3 | 1, 2, 3 |
| BD | 4 | 2 | 1, 2 |
| SW | 4 | 2 | 1, 2 |
| FO | 4 | 3 | 1, 2, 4 |
| PH | 4 | 1 | 1 |
| RE | 4 | 2 | 1, 2 |
| **Totaal** | **40** | **27** | |

Overige pagina's:

- 10 beroepsrollen: 9 bachelor en HCAI (master).
- 25 beroepstaken met elk 4 niveaus, plus 2 pop-ups met extra toelichting: Software Realiseren niveau 1 en Software Manage & Control niveau 1.
- 25 beroepstaken met voorbeelden van beroepsproducten.
- De leeswijzer "Zo gebruik je LEF".

## Later vergelijken

1. Haal de site opnieuw op in dezelfde opmaak, in een nieuwe map met de datum van dat moment:

   ```bash
   python3 "docs/2026-09-01 LEF/ophalen.py" "docs/JJJJ-MM-DD LEF"
   ```

   Het script meldt de tellingen per vaardigheid en stopt met een foutmelding als het een onbekende vaardigheid, een openklap-item zonder niveau of een pop-up zonder knop vindt. Kopieer `ophalen.py` naar de nieuwe map.

2. Vergelijk de twee mappen:

   ```bash
   git diff --no-index --word-diff "docs/2026-09-01 LEF" "docs/JJJJ-MM-DD LEF"
   ```

   `--word-diff` laat binnen een gewijzigde regel zien welke woorden veranderd zijn. Zonder die optie zie je hele regels. `diff -ru` werkt ook.

Verschillen in de regels `Opgehaald:` zijn normaal. Verandert de opbouw van de site, dan moet het script misschien worden aangepast. Het stopt in de bekende gevallen met een melding, maar controleer bij twijfel de tellingen.
