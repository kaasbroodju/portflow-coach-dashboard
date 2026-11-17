#!/bin/sh
# Portflow coach dashboard installeren op macOS (spec 020, I1-I7).
#
#   Installeren of bijwerken:
#     curl -fsSL https://github.com/petersnoek-hu/portflow-coach-dashboard/releases/latest/download/install-macos.sh | sh
#   Verwijderen:
#     curl -fsSL https://github.com/petersnoek-hu/portflow-coach-dashboard/releases/latest/download/install-macos.sh | sh -s -- --verwijderen
#
# Geen beheerdersrechten nodig. uv zet een eigen Python en de pakketten neer; het script
# downloadt geen programma dat macOS moet vertrouwen. Voor tests kunnen de mappen en het
# downloadadres worden omgezet met PORTFLOW_INSTALL_ROOT, PORTFLOW_APPLICATIONS en
# PORTFLOW_RELEASE_URL.
set -eu

REPO="petersnoek-hu/portflow-coach-dashboard"
BASE="${PORTFLOW_RELEASE_URL:-https://github.com/$REPO/releases/latest/download}"
NAME="Portflow coach dashboard"
ROOT="${PORTFLOW_INSTALL_ROOT:-$HOME/Library/Application Support/$NAME}"
APPS="${PORTFLOW_APPLICATIONS:-$HOME/Applications}"
LAUNCHER="$APPS/$NAME.app"
PORT="${PORTFLOW_PORT:-5050}"
ZIP="portflow-coach-dashboard.zip"
PYTHON_VERSION="3.13"

say() { printf '%s\n' "$*"; }
step() { printf '\n→ %s\n' "$*"; }
fail() { printf '\n✗ %s\n' "$*" >&2; exit 1; }

# ask "vraag": 0 bij ja. Werkt ook als het script via een pijp (curl | sh) binnenkomt.
ask() {
    answer=""
    if [ -t 1 ] && [ -r /dev/tty ]; then
        printf '%s [j/n] ' "$1" > /dev/tty
        read -r answer < /dev/tty || answer=""
    fi
    case "$answer" in j|J|ja|Ja|JA|y|Y|yes) return 0 ;; *) return 1 ;; esac
}

# Een draaiend dashboard netjes stoppen (I5), zodat de bestanden vrij zijn.
stop_running() {
    if curl -fsS --max-time 2 "http://127.0.0.1:$PORT/versie" 2>/dev/null | grep -q '"portflow-coach-dashboard"'; then
        say "  Het dashboard draait nog; het wordt gestopt."
        curl -fsS --max-time 2 -X POST "http://127.0.0.1:$PORT/afsluiten" > /dev/null 2>&1 || true
        sleep 2
    fi
}

# I7 – verwijderen ---------------------------------------------------------------------
if [ "${1:-}" = "--verwijderen" ]; then
    say "Portflow coach dashboard verwijderen"
    stop_running
    rm -rf "$ROOT/app" "$ROOT/app-oud" "$ROOT/app-nieuw" "$ROOT/venv" "$LAUNCHER"
    say "Het programma en de snelkoppeling zijn verwijderd."
    if [ -d "$ROOT/data" ] && ask "Ook je gegevens verwijderen (studenten, instellingen, Portflow-verbinding)?"; then
        rm -rf "$ROOT"
        say "Je gegevens zijn verwijderd."
    elif [ -d "$ROOT/data" ]; then
        say "Je gegevens blijven staan in: $ROOT/data"
    fi
    exit 0
fi

say "Portflow coach dashboard installeren"

# I2.1 – Chrome ---------------------------------------------------------------------------
step "Google Chrome controleren"
if [ ! -d "/Applications/Google Chrome.app" ] && [ ! -d "$HOME/Applications/Google Chrome.app" ]; then
    fail "Google Chrome is niet gevonden. Het dashboard gebruikt Chrome om in te loggen bij Portflow.
  Installeer Chrome via https://www.google.com/chrome/ en voer deze regel daarna opnieuw uit."
fi

TMP="$(mktemp -d)"
FRESH=0
[ -d "$ROOT/app" ] || FRESH=1
cleanup() {
    rm -rf "$TMP"
    # Geen halve eerste installatie achterlaten (I2); bij bijwerken blijft de oude versie staan.
    if [ "${DONE:-0}" != 1 ] && [ "$FRESH" = 1 ]; then rm -rf "$ROOT/venv"; fi
}
trap cleanup EXIT

# I2.2 – uv ---------------------------------------------------------------------------------
step "Hulpprogramma uv controleren"
UV="$(command -v uv || true)"
if [ -z "$UV" ] && [ -x "$HOME/.local/bin/uv" ]; then UV="$HOME/.local/bin/uv"; fi
if [ -z "$UV" ]; then
    say "  uv wordt geïnstalleerd (in je eigen gebruikersmap)."
    curl -fsSL https://astral.sh/uv/install.sh | env UV_NO_MODIFY_PATH=1 sh > /dev/null 2>&1 \
        || fail "uv kon niet worden geïnstalleerd. Controleer je internetverbinding en probeer het opnieuw."
    UV="$HOME/.local/bin/uv"
    [ -x "$UV" ] || fail "uv is geïnstalleerd, maar niet gevonden in $HOME/.local/bin."
fi

# I2.3 – nieuwste versie downloaden en controleren -------------------------------------------
step "Nieuwste versie downloaden"
curl -fsSL "$BASE/$ZIP" -o "$TMP/$ZIP" && curl -fsSL "$BASE/$ZIP.sha256" -o "$TMP/$ZIP.sha256" \
    || fail "Downloaden is niet gelukt. Controleer je internetverbinding en probeer het opnieuw."
EXPECTED="$(cut -d ' ' -f 1 < "$TMP/$ZIP.sha256")"
ACTUAL="$(shasum -a 256 "$TMP/$ZIP" | cut -d ' ' -f 1)"
[ "$EXPECTED" = "$ACTUAL" ] || fail "De download is beschadigd (de controlesom klopt niet). Probeer het opnieuw."
mkdir "$TMP/app"
unzip -q "$TMP/$ZIP" -d "$TMP/app" || fail "Uitpakken is niet gelukt."
[ -f "$TMP/app/app.py" ] || fail "De download bevat geen dashboard."
printf '{"uv": "%s"}\n' "$UV" > "$TMP/app/.installed"

# I2.4 – Python en pakketten (in <root>/venv, los van de code) ---------------------------------
step "Python en pakketten installeren (de eerste keer ongeveer 100 MB)"
mkdir -p "$ROOT/data"
UV_PROJECT_ENVIRONMENT="$ROOT/venv" "$UV" sync --frozen --no-dev --python "$PYTHON_VERSION" \
    --python-preference only-managed --project "$TMP/app" --quiet \
    || fail "Python of de pakketten konden niet worden geïnstalleerd. Controleer je internetverbinding en probeer het opnieuw."

# I3 – bestaande gegevens uit een git-checkout overnemen (een kopie) ----------------------------
if [ ! -f "$ROOT/data/dashboard.sqlite3" ]; then
    SOURCE=""
    if [ -f "$PWD/data/dashboard.sqlite3" ] && ask "Gegevens gevonden in $PWD/data. Overnemen (een kopie; het origineel blijft staan)?"; then
        SOURCE="$PWD/data"
    elif [ -t 1 ] && [ -r /dev/tty ]; then
        printf '\nHeb je het dashboard al eerder vanuit een map gebruikt? Sleep die map hierheen (of typ het pad)\nen druk op Enter. Alleen Enter slaat dit over: ' > /dev/tty
        read -r FOLDER < /dev/tty || FOLDER=""
        FOLDER="$(printf '%s' "$FOLDER" | sed -e "s/^[\"']//" -e "s/[\"'] *$//" -e 's/ *$//' -e 's/\\ / /g')"
        if [ -n "$FOLDER" ]; then
            if [ -f "$FOLDER/data/dashboard.sqlite3" ]; then SOURCE="$FOLDER/data"
            elif [ -f "$FOLDER/dashboard.sqlite3" ]; then SOURCE="$FOLDER"
            else say "  Daar staan geen gegevens van het dashboard; je begint met een lege database."
            fi
        fi
    fi
    if [ -n "$SOURCE" ]; then
        cp -R "$SOURCE/." "$ROOT/data/"
        say "  Gegevens overgenomen uit $SOURCE."
    fi
fi

# Nieuwe code op zijn plek; de vorige versie blijft als app-oud staan.
stop_running
if [ -d "$ROOT/app" ]; then
    rm -rf "$ROOT/app-oud"
    mv "$ROOT/app" "$ROOT/app-oud"
fi
mv "$TMP/app" "$ROOT/app"

# I4 – snelkoppeling: een kleine app in ~/Applications --------------------------------------------
step "Snelkoppeling maken"
rm -rf "$LAUNCHER"
mkdir -p "$LAUNCHER/Contents/MacOS" "$LAUNCHER/Contents/Resources"
cp "$ROOT/app/install/icon.icns" "$LAUNCHER/Contents/Resources/icon.icns"
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
chmod +x "$LAUNCHER/Contents/MacOS/start"
touch "$LAUNCHER"

DONE=1

# I2.6 – starten ------------------------------------------------------------------------------------
step "Dashboard starten"
if [ -z "${PORTFLOW_NO_START:-}" ]; then
    open "$LAUNCHER"
fi
say ""
say "Klaar. Het dashboard opent in je browser."
say "Je vindt het voortaan als \"$NAME\" in de map Apps in je thuismap ($APPS)."
say "Sleep het naar het Dock om het vast te zetten."
