#!/bin/sh
# Portflow coach dashboard installeren op macOS (spec 020, I1-I8).
#
#   Installeren of bijwerken:
#     curl -fsSL https://github.com/petersnoek-hu/portflow-coach-dashboard/releases/latest/download/install-macos.sh | sh
#   Verwijderen:
#     curl -fsSL https://github.com/petersnoek-hu/portflow-coach-dashboard/releases/latest/download/install-macos.sh | sh -s -- --verwijderen
#
# Geen beheerdersrechten nodig. uv zet een eigen Python en de pakketten neer; het script
# downloadt geen programma dat macOS moet vertrouwen. Alles wat het script doet, komt in
# install.log in de map waar je het commando gaf (I8). Voor tests kunnen de mappen en het
# downloadadres worden omgezet met PORTFLOW_INSTALL_ROOT, PORTFLOW_APPLICATIONS,
# PORTFLOW_RELEASE_URL, PORTFLOW_PORT en PORTFLOW_NO_START.
set -eu

REPO="petersnoek-hu/portflow-coach-dashboard"
BASE="${PORTFLOW_RELEASE_URL:-https://github.com/$REPO/releases/latest/download}"
NAME="Portflow coach dashboard"
ROOT="${PORTFLOW_INSTALL_ROOT:-$HOME/Library/Application Support/$NAME}"
# I9: de app bij Programma's (/Applications) als dat mag, anders in Apps in de thuismap.
if [ -n "${PORTFLOW_APPLICATIONS:-}" ]; then APPS="$PORTFLOW_APPLICATIONS"; APPS_NAME="de map $APPS"
elif [ -w /Applications ]; then APPS="/Applications"; APPS_NAME="Programma's"
else APPS="$HOME/Applications"; APPS_NAME="Apps in je thuismap ($HOME/Applications)"
fi
LAUNCHER="$APPS/$NAME.app"
PORT="${PORTFLOW_PORT:-5050}"
ZIP="portflow-coach-dashboard.zip"
PYTHON_VERSION="3.13"

# I8 – logboek ----------------------------------------------------------------------------
# install.log in de map van het commando; mag dat niet, dan in de thuismap. Aanvullen.
LOG="$PWD/install.log"
if ! { : >> "$LOG"; } 2> /dev/null; then LOG="$HOME/install.log"; fi

log() {
    stamp="$(date '+%Y-%m-%d %H:%M:%S')"
    printf '%s\n' "$*" | while IFS= read -r line; do
        printf '%s [%s] %s\n' "$stamp" "$PWD" "$line"
    done >> "$LOG" 2> /dev/null || true
}

say() { printf '%s\n' "$*"; if [ -n "$*" ]; then log "MELDING: $*"; fi; }
step() { printf '\n→ %s\n' "$*"; log "STAP: $*"; }
check() { log "CONTROLE: $1: $2"; }
fail() {
    printf '\n✗ %s\n' "$*" >&2
    log "FOUT: $*"
    printf '  Wat er gebeurde, staat in %s\n' "$LOG" >&2
    exit 1
}

# run <opdracht…>: voer een opdracht uit en schrijf hem met zijn uitvoer en exitcode in het logboek.
# De uitvoer gaat niet naar het scherm; de gebruiker ziet alleen de meldingen.
run() {
    log "OPDRACHT: $*"
    status=0
    output="$("$@" 2>&1 < /dev/null)" || status=$?   # opdrachten lezen nooit de antwoorden van de gebruiker weg
    if [ -n "$output" ]; then log "$(printf '%s\n' "$output" | sed 's/^/  | /')"; fi
    log "AFLOOP: exitcode $status"
    return $status
}

# ask "vraag": 0 bij ja. Werkt ook als het script via een pijp (curl | sh) binnenkomt.
ask() {
    answer=""
    if [ -t 1 ] && [ -r /dev/tty ]; then
        printf '%s [j/n] ' "$1" > /dev/tty
        read -r answer < /dev/tty || answer=""
    fi
    log "VRAAG: $1 ANTWOORD: ${answer:-(geen)}"
    case "$answer" in j|J|ja|Ja|JA|y|Y|yes) return 0 ;; *) return 1 ;; esac
}

finish() {
    code=$?
    rm -rf "${TMP:-}"
    # Geen halve eerste installatie achterlaten (I2); bij bijwerken blijft de oude versie staan.
    if [ "${DONE:-0}" != 1 ] && [ "${FRESH:-0}" = 1 ]; then rm -rf "$ROOT/venv"; log "OPGERUIMD: $ROOT/venv"; fi
    if [ "$code" = 0 ]; then log "EINDE: gelukt"; else log "EINDE: mislukt (exitcode $code)"; fi
    log "=================================================================="
}
trap finish EXIT

log "=================================================================="
log "Portflow coach dashboard – installatiescript macOS, gestart met: ${*:-(geen opties)}"
log "Systeem: $(sw_vers -productName 2> /dev/null) $(sw_vers -productVersion 2> /dev/null) ($(uname -m)), gebruiker $(id -un)"
log "Programma en gegevens: $ROOT; snelkoppeling: $LAUNCHER ($APPS_NAME); downloads: $BASE; poort: $PORT"

# I11: draait het geïnstalleerde dashboard (dus niet een versie uit de broncode)?
installed_running() { ps -axo command= | grep -F "$ROOT/app/app.py" | grep -vq grep; }

# Het geïnstalleerde dashboard netjes stoppen (I5), zodat de bestanden vrij zijn. Een ander
# dashboard (bijvoorbeeld de ontwikkelversie uit een git-checkout) blijft draaien.
stop_running() {
    if installed_running; then
        check "geïnstalleerd dashboard draait" "ja"
        say "  Het dashboard draait nog; het wordt gestopt."
        run curl -fsS --max-time 2 -X POST "http://127.0.0.1:$PORT/afsluiten" || true
        sleep 2
        if installed_running; then run pkill -f "$ROOT/app/app.py" || true; sleep 1; fi
    else
        check "geïnstalleerd dashboard draait" "nee"
    fi
    # Ook Playwright en de Chrome die het dashboard voor het inloggen startte (met het profiel uit
    # de installatie); je eigen Chrome hoort er niet bij.
    if pgrep -f "$ROOT/" > /dev/null 2>&1; then
        check "andere processen van de installatie" "$(pgrep -fl "$ROOT/" | cut -c1-120 | tr '\n' ';')"
        run pkill -f "$ROOT/" || true
        sleep 1
    else
        check "andere processen van de installatie" "geen"
    fi
}

# Draait er op de poort een ander dashboard dan het geïnstalleerde?
other_on_port() {
    curl -fsS --max-time 2 "http://127.0.0.1:$PORT/versie" 2> /dev/null | grep -q '"portflow-coach-dashboard"' && ! installed_running
}

# I10: het aantal studenten in de database van de installatie ("geen" zonder database).
student_count() {
    if [ ! -f "$ROOT/data/dashboard.sqlite3" ]; then echo geen; return; fi
    "$ROOT/venv/bin/python" -c 'import sqlite3, sys; print(sqlite3.connect(sys.argv[1]).execute("SELECT COUNT(*) FROM students").fetchone()[0])' \
        "$ROOT/data/dashboard.sqlite3" 2> /dev/null || echo onbekend
}

# I9: de app staat in /Applications of in ~/Applications (versie 0.9.0); haal ze bij een gewone
# installatie allebei weg. Is de map omgezet (PORTFLOW_APPLICATIONS, voor tests), haal dan alleen
# die ene weg, zodat een test de echte snelkoppeling van de gebruiker niet wist.
remove_launchers() {
    if [ -n "${PORTFLOW_APPLICATIONS:-}" ]; then set -- "$LAUNCHER"
    else set -- "/Applications/$NAME.app" "$HOME/Applications/$NAME.app"; fi
    for old in "$@"; do
        if [ -d "$old" ]; then run rm -rf "$old" || say "  $old kon niet worden verwijderd; sleep het zelf naar de prullenmand."; fi
    done
}

# I7 – verwijderen ---------------------------------------------------------------------
if [ "${1:-}" = "--verwijderen" ]; then
    say "Portflow coach dashboard verwijderen"
    stop_running
    run rm -rf "$ROOT/app" "$ROOT/app-oud" "$ROOT/app-nieuw" "$ROOT/app-mislukt" "$ROOT/venv" || true
    remove_launchers
    KEPT=""
    for path in "$ROOT/app" "$ROOT/app-oud" "$ROOT/app-nieuw" "$ROOT/app-mislukt" "$ROOT/venv" "/Applications/$NAME.app" "$HOME/Applications/$NAME.app"; do
        if [ -e "$path" ]; then KEPT="$KEPT
  $path"; fi
    done
    if [ -n "$KEPT" ]; then
        say "Niet alles kon worden verwijderd; dit staat er nog:$KEPT"
        say "Sluit het dashboard en voer dit daarna nog een keer uit."
    else
        say "Het programma en de snelkoppeling zijn verwijderd."
    fi
    if [ -d "$ROOT/data" ] && ask "Ook je gegevens verwijderen (studenten, instellingen, Portflow-verbinding)?"; then
        run rm -rf "$ROOT"
        say "Je gegevens zijn verwijderd."
    elif [ -d "$ROOT/data" ]; then
        say "Je gegevens blijven staan in: $ROOT/data"
    fi
    say "Het logboek staat in $LOG"
    if [ -n "$KEPT" ]; then exit 1; fi
    exit 0
fi

say "Portflow coach dashboard installeren"

# I2.1 – Chrome ---------------------------------------------------------------------------
step "Google Chrome controleren"
CHROME=""
for candidate in "/Applications/Google Chrome.app" "$HOME/Applications/Google Chrome.app"; do
    if [ -d "$candidate" ]; then CHROME="$candidate"; fi
done
check "Google Chrome" "${CHROME:-niet gevonden}"
if [ -z "$CHROME" ]; then
    fail "Google Chrome is niet gevonden. Het dashboard gebruikt Chrome om in te loggen bij Portflow.
  Installeer Chrome via https://www.google.com/chrome/ en voer deze regel daarna opnieuw uit."
fi

# U7 – resten van eerdere, mislukte pogingen opruimen; een vastgelopen update herstellen.
# app-oud blijft als reserve staan; kopieën van gegevens worden nooit verwijderd.
if [ ! -d "$ROOT/app" ] && [ -d "$ROOT/app-oud" ]; then
    check "app ontbreekt, app-oud staat er wel" "vastgelopen update; app-oud wordt teruggezet"
    run mv "$ROOT/app-oud" "$ROOT/app" || true
fi
CLEANED=""
for left in "$ROOT/app-nieuw" "$ROOT/app-mislukt" "$ROOT/data/bijwerken/$ZIP"; do
    if [ -e "$left" ]; then run rm -rf "$left" && CLEANED="$CLEANED ${left##*/}" || true; fi
done
check "resten van eerdere pogingen opgeruimd" "${CLEANED:- geen}"

TMP="$(mktemp -d)"
FRESH=0
[ -d "$ROOT/app" ] || FRESH=1
check "eerdere installatie" "$([ "$FRESH" = 1 ] && echo nee || echo "ja, in $ROOT/app")"

# I2.2 – uv ---------------------------------------------------------------------------------
step "Hulpprogramma uv controleren"
UV="$(command -v uv || true)"
if [ -z "$UV" ] && [ -x "$HOME/.local/bin/uv" ]; then UV="$HOME/.local/bin/uv"; fi
check "uv" "${UV:-niet gevonden}"
if [ -z "$UV" ]; then
    say "  uv wordt geïnstalleerd (in je eigen gebruikersmap)."
    run sh -c 'curl -fsSL https://astral.sh/uv/install.sh | env UV_NO_MODIFY_PATH=1 sh' \
        || fail "uv kon niet worden geïnstalleerd. Controleer je internetverbinding en probeer het opnieuw."
    UV="$HOME/.local/bin/uv"
    [ -x "$UV" ] || fail "uv is geïnstalleerd, maar niet gevonden in $HOME/.local/bin."
fi
run "$UV" --version || true

# I2.3 – nieuwste versie downloaden en controleren -------------------------------------------
step "Nieuwste versie downloaden"
run curl -fsSL "$BASE/$ZIP" -o "$TMP/$ZIP" && run curl -fsSL "$BASE/$ZIP.sha256" -o "$TMP/$ZIP.sha256" \
    || fail "Downloaden is niet gelukt. Controleer je internetverbinding en probeer het opnieuw."
EXPECTED="$(cut -d ' ' -f 1 < "$TMP/$ZIP.sha256")"
ACTUAL="$(shasum -a 256 "$TMP/$ZIP" | cut -d ' ' -f 1)"
check "controlesom" "verwacht $EXPECTED, gevonden $ACTUAL"
[ "$EXPECTED" = "$ACTUAL" ] || fail "De download is beschadigd (de controlesom klopt niet). Probeer het opnieuw."
mkdir "$TMP/app"
run unzip -q "$TMP/$ZIP" -d "$TMP/app" || fail "Uitpakken is niet gelukt."
[ -f "$TMP/app/app.py" ] || fail "De download bevat geen dashboard."
VERSION="$(sed -n 's/^VERSION = "\(.*\)"/\1/p' "$TMP/app/dashboard/version.py")"
check "versie in de download" "${VERSION:-onbekend}"
printf '{"uv": "%s"}\n' "$UV" > "$TMP/app/.installed"

# I2.4 – Python en pakketten (in <root>/venv, los van de code) ---------------------------------
step "Python en pakketten installeren (de eerste keer ongeveer 100 MB)"
mkdir -p "$ROOT/data"
run env UV_PROJECT_ENVIRONMENT="$ROOT/venv" "$UV" sync --frozen --no-dev --python "$PYTHON_VERSION" \
    --python-preference only-managed --project "$TMP/app" \
    || fail "Python of de pakketten konden niet worden geïnstalleerd. Controleer je internetverbinding en probeer het opnieuw."

# I3, I10 – bestaande gegevens uit een git-checkout overnemen (een kopie) ---------------------
# Ook als de installatie al een database heeft zonder studenten (bijvoorbeeld van een eerste start).
STUDENTS="$(student_count)"
check "studenten in $ROOT/data" "$STUDENTS"
if [ "$STUDENTS" != geen ] && [ "$STUDENTS" != 0 ]; then
    check "gegevens overnemen" "niet nodig, de gegevens van de installatie blijven staan"
else
    SOURCE=""
    if [ -f "$PWD/data/dashboard.sqlite3" ]; then
        check "gegevens in $PWD/data" "ja"
        if ask "Gegevens gevonden in $PWD/data. Overnemen (een kopie; het origineel blijft staan)?"; then SOURCE="$PWD/data"; fi
    elif [ -t 1 ] && [ -r /dev/tty ]; then
        printf '\nHeb je het dashboard al eerder vanuit een map gebruikt? Sleep die map hierheen (of typ het pad)\nen druk op Enter. Alleen Enter slaat dit over: ' > /dev/tty
        read -r FOLDER < /dev/tty || FOLDER=""
        FOLDER="$(printf '%s' "$FOLDER" | sed -e "s/^[\"']//" -e "s/[\"'] *$//" -e 's/ *$//' -e 's/\\ / /g')"
        log "VRAAG: map met eerdere gegevens ANTWOORD: ${FOLDER:-(overgeslagen)}"
        if [ -n "$FOLDER" ]; then
            if [ -f "$FOLDER/data/dashboard.sqlite3" ]; then SOURCE="$FOLDER/data"
            elif [ -f "$FOLDER/dashboard.sqlite3" ]; then SOURCE="$FOLDER"
            else say "  Daar staan geen gegevens van het dashboard; je begint met een lege database."
            fi
        fi
    fi
    if [ -n "$SOURCE" ]; then
        stop_running   # de database moet vrij zijn
        if [ -f "$ROOT/data/dashboard.sqlite3" ]; then
            ASIDE="$ROOT/data-voor-overnemen-$(date '+%Y%m%d-%H%M%S')"
            run mv "$ROOT/data" "$ASIDE" || fail "De lege gegevensmap kon niet opzij worden gezet."
            say "  De lege gegevens van de installatie staan apart in $ASIDE."
            mkdir -p "$ROOT/data"
        fi
        run cp -R "$SOURCE/." "$ROOT/data/" || fail "Je gegevens konden niet worden gekopieerd."
        run rm -f "$ROOT/data/browser-profile/SingletonLock" "$ROOT/data/browser-profile/SingletonSocket" "$ROOT/data/browser-profile/SingletonCookie"
        say "  Gegevens overgenomen uit $SOURCE."
    fi
fi

# Nieuwe code op zijn plek; de vorige versie blijft als app-oud staan.
stop_running
if [ -d "$ROOT/app" ]; then
    run rm -rf "$ROOT/app-oud"
    run mv "$ROOT/app" "$ROOT/app-oud"
fi
run mv "$TMP/app" "$ROOT/app"

# I4 – snelkoppeling: een kleine app in ~/Applications --------------------------------------------
step "Snelkoppeling maken"
remove_launchers
run mkdir -p "$LAUNCHER/Contents/MacOS" "$LAUNCHER/Contents/Resources"
run cp "$ROOT/app/install/icon.icns" "$LAUNCHER/Contents/Resources/icon.icns"
cat > "$LAUNCHER/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleName</key><string>$NAME</string>
  <key>CFBundleDisplayName</key><string>$NAME</string>
  <key>CFBundleIdentifier</key><string>nl.openict.portflow-coach-dashboard</string>
  <key>CFBundleExecutable</key><string>start</string>
  <key>CFBundleIconFile</key><string>icon</string>
  <key>CFBundlePackageType</key><string>APPL</string>
</dict>
</plist>
PLIST
# Start het dashboard op de achtergrond, zonder Terminal; app.py opent de browser
# (of alleen de browser, als het dashboard al draait).
cat > "$LAUNCHER/Contents/MacOS/start" <<LAUNCH
#!/bin/sh
ROOT='$ROOT'
nohup "\$ROOT/venv/bin/python" "\$ROOT/app/app.py" >> "\$ROOT/data/dashboard.log" 2>&1 &
LAUNCH
run chmod +x "$LAUNCHER/Contents/MacOS/start"
run touch "$LAUNCHER"
log "GESCHREVEN: $LAUNCHER/Contents/Info.plist en $LAUNCHER/Contents/MacOS/start"

DONE=1

# I2.6 – starten ------------------------------------------------------------------------------------
step "Dashboard starten"
STARTED=0
if [ -n "${PORTFLOW_NO_START:-}" ]; then
    log "OVERGESLAGEN: starten (PORTFLOW_NO_START)"
elif other_on_port; then
    check "ander dashboard op poort $PORT" "ja"   # I11
    say "  Op poort $PORT draait al een ander dashboard (bijvoorbeeld de ontwikkelversie)."
    say "  Stop dat eerst; open daarna het geïnstalleerde dashboard met de snelkoppeling."
else
    run open "$LAUNCHER" && STARTED=1 || say "  Het dashboard kon niet automatisch worden geopend; open het met de snelkoppeling."
fi
say ""
if [ "$STARTED" = 1 ]; then
    say "Klaar. Versie ${VERSION:-?} is geïnstalleerd en het dashboard opent in je browser."
else
    say "Klaar. Versie ${VERSION:-?} is geïnstalleerd."
fi
say "Je vindt het voortaan als \"$NAME\" bij $APPS_NAME."
say "Sleep het naar het Dock om het vast te zetten."
say "Het logboek van deze installatie staat in $LOG"
