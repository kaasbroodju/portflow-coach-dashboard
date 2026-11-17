# Portflow coach dashboard installeren op Windows (spec 020, I1-I7).
#
#   Installeren of bijwerken (PowerShell):
#     irm https://github.com/petersnoek-hu/portflow-coach-dashboard/releases/latest/download/install-windows.ps1 | iex
#   Verwijderen:
#     & ([scriptblock]::Create((irm https://github.com/petersnoek-hu/portflow-coach-dashboard/releases/latest/download/install-windows.ps1))) --verwijderen
#
# Geen beheerdersrechten nodig. uv zet een eigen Python en de pakketten neer. Voor tests kunnen
# de mappen en het downloadadres worden omgezet met PORTFLOW_INSTALL_ROOT, PORTFLOW_RELEASE_URL,
# PORTFLOW_PORT en PORTFLOW_NO_START.

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"   # Invoke-WebRequest is much faster without the progress bar

$Repo = "petersnoek-hu/portflow-coach-dashboard"
$Base = if ($env:PORTFLOW_RELEASE_URL) { $env:PORTFLOW_RELEASE_URL } else { "https://github.com/$Repo/releases/latest/download" }
$Name = "Portflow coach dashboard"
$Root = if ($env:PORTFLOW_INSTALL_ROOT) { $env:PORTFLOW_INSTALL_ROOT } else { Join-Path $env:LOCALAPPDATA $Name }
$Port = if ($env:PORTFLOW_PORT) { $env:PORTFLOW_PORT } else { "5050" }
$Zip = "portflow-coach-dashboard.zip"
$PythonVersion = "3.13"
$StartMenu = Join-Path ([Environment]::GetFolderPath("Programs")) "$Name.lnk"
$Desktop = Join-Path ([Environment]::GetFolderPath("Desktop")) "$Name.lnk"

function Say($text) { Write-Host $text }
function Step($text) { Write-Host ""; Write-Host "-> $text" -ForegroundColor Cyan }
function Fail($text) { Write-Host ""; Write-Host "X $text" -ForegroundColor Red; throw "Installatie gestopt." }
function Interactive { return -not [Console]::IsInputRedirected -and [Environment]::UserInteractive }
function Ask($question) {
    if (-not (Interactive)) { return $false }
    $answer = Read-Host "$question [j/n]"
    return $answer -match '^(j|ja|y|yes)$'
}

# Een draaiend dashboard netjes stoppen (I5), zodat de bestanden vrij zijn.
function Stop-Dashboard {
    try {
        $answer = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/versie" -TimeoutSec 2
        if ($answer.app -eq "portflow-coach-dashboard") {
            Say "  Het dashboard draait nog; het wordt gestopt."
            try { Invoke-WebRequest -Uri "http://127.0.0.1:$Port/afsluiten" -Method Post -TimeoutSec 2 -UseBasicParsing | Out-Null } catch { }
            Start-Sleep -Seconds 2
        }
    } catch { }
}

# I7 - verwijderen -------------------------------------------------------------------------------
if ($args -contains "--verwijderen") {
    Say "Portflow coach dashboard verwijderen"
    Stop-Dashboard
    foreach ($path in @("$Root\app", "$Root\app-oud", "$Root\app-nieuw", "$Root\venv", $StartMenu, $Desktop)) {
        if (Test-Path $path) { Remove-Item -Recurse -Force $path }
    }
    Say "Het programma en de snelkoppelingen zijn verwijderd."
    if (Test-Path "$Root\data") {
        if (Ask "Ook je gegevens verwijderen (studenten, instellingen, Portflow-verbinding)?") {
            Remove-Item -Recurse -Force $Root
            Say "Je gegevens zijn verwijderd."
        } else {
            Say "Je gegevens blijven staan in: $Root\data"
        }
    }
    return
}

Say "Portflow coach dashboard installeren"

# I2.1 - Chrome ------------------------------------------------------------------------------------
Step "Google Chrome controleren"
$chrome = @(
    "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
    "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
    "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe"
) | Where-Object { $_ -and (Test-Path $_) }
if (-not $chrome) {
    Fail "Google Chrome is niet gevonden. Het dashboard gebruikt Chrome om in te loggen bij Portflow.`n  Installeer Chrome via https://www.google.com/chrome/ en voer deze regel daarna opnieuw uit."
}

$Tmp = Join-Path ([IO.Path]::GetTempPath()) ("portflow-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $Tmp | Out-Null
$Fresh = -not (Test-Path "$Root\app")
$Done = $false

try {
    # I2.2 - uv -------------------------------------------------------------------------------------
    Step "Hulpprogramma uv controleren"
    $uvCommand = Get-Command uv -ErrorAction SilentlyContinue
    $Uv = if ($uvCommand) { $uvCommand.Source } else { Join-Path $env:USERPROFILE ".local\bin\uv.exe" }
    if (-not (Test-Path $Uv)) {
        Say "  uv wordt geinstalleerd (in je eigen gebruikersmap)."
        $env:UV_NO_MODIFY_PATH = "1"
        try {
            powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex" | Out-Null
        } catch {
            Fail "uv kon niet worden geinstalleerd. Controleer je internetverbinding en probeer het opnieuw."
        }
        if (-not (Test-Path $Uv)) { Fail "uv is geinstalleerd, maar niet gevonden in $env:USERPROFILE\.local\bin." }
    }

    # I2.3 - nieuwste versie downloaden en controleren ------------------------------------------------
    Step "Nieuwste versie downloaden"
    try {
        Invoke-WebRequest -Uri "$Base/$Zip" -OutFile "$Tmp\$Zip" -UseBasicParsing
        Invoke-WebRequest -Uri "$Base/$Zip.sha256" -OutFile "$Tmp\$Zip.sha256" -UseBasicParsing
    } catch {
        Fail "Downloaden is niet gelukt. Controleer je internetverbinding en probeer het opnieuw."
    }
    $expected = ((Get-Content "$Tmp\$Zip.sha256" -Raw).Trim() -split '\s+')[0].ToLower()
    $actual = (Get-FileHash -Algorithm SHA256 "$Tmp\$Zip").Hash.ToLower()
    if ($expected -ne $actual) { Fail "De download is beschadigd (de controlesom klopt niet). Probeer het opnieuw." }
    Expand-Archive -Path "$Tmp\$Zip" -DestinationPath "$Tmp\app"
    if (-not (Test-Path "$Tmp\app\app.py")) { Fail "De download bevat geen dashboard." }
    @{ uv = $Uv } | ConvertTo-Json | Set-Content -Path "$Tmp\app\.installed" -Encoding UTF8

    # I2.4 - Python en pakketten (in <root>\venv, los van de code) -----------------------------------
    Step "Python en pakketten installeren (de eerste keer ongeveer 100 MB)"
    New-Item -ItemType Directory -Force -Path "$Root\data" | Out-Null
    $env:UV_PROJECT_ENVIRONMENT = "$Root\venv"
    & $Uv sync --frozen --no-dev --python $PythonVersion --python-preference only-managed --project "$Tmp\app" --quiet
    if ($LASTEXITCODE -ne 0) {
        Fail "Python of de pakketten konden niet worden geinstalleerd. Controleer je internetverbinding en probeer het opnieuw."
    }

    # I3 - bestaande gegevens uit een git-checkout overnemen (een kopie) -------------------------------
    if (-not (Test-Path "$Root\data\dashboard.sqlite3")) {
        $source = $null
        $here = (Get-Location).Path
        if ((Test-Path "$here\data\dashboard.sqlite3") -and (Ask "Gegevens gevonden in $here\data. Overnemen (een kopie; het origineel blijft staan)?")) {
            $source = "$here\data"
        } elseif (Interactive) {
            $folder = Read-Host "`nHeb je het dashboard al eerder vanuit een map gebruikt? Typ of plak het pad van die map en druk op Enter. Alleen Enter slaat dit over"
            $folder = $folder.Trim().Trim('"')
            if ($folder) {
                if (Test-Path "$folder\data\dashboard.sqlite3") { $source = "$folder\data" }
                elseif (Test-Path "$folder\dashboard.sqlite3") { $source = $folder }
                else { Say "  Daar staan geen gegevens van het dashboard; je begint met een lege database." }
            }
        }
        if ($source) {
            Copy-Item -Recurse -Force -Path "$source\*" -Destination "$Root\data"
            Say "  Gegevens overgenomen uit $source."
        }
    }

    # Nieuwe code op zijn plek; de vorige versie blijft als app-oud staan.
    Stop-Dashboard
    if (Test-Path "$Root\app") {
        if (Test-Path "$Root\app-oud") { Remove-Item -Recurse -Force "$Root\app-oud" }
        Move-Item "$Root\app" "$Root\app-oud"
    }
    Move-Item "$Tmp\app" "$Root\app"

    # I4 - snelkoppelingen in het Startmenu en op het bureaublad, zonder terminalvenster ----------------
    Step "Snelkoppelingen maken"
    $shell = New-Object -ComObject WScript.Shell
    foreach ($path in @($StartMenu, $Desktop)) {
        $link = $shell.CreateShortcut($path)
        $link.TargetPath = "$Root\venv\Scripts\pythonw.exe"
        $link.Arguments = "`"$Root\app\app.py`""
        $link.WorkingDirectory = "$Root\app"
        $link.IconLocation = "$Root\app\install\icon.ico"
        $link.Description = $Name
        $link.Save()
    }
    $Done = $true

    # I2.6 - starten ------------------------------------------------------------------------------------
    Step "Dashboard starten"
    if (-not $env:PORTFLOW_NO_START) {
        Start-Process -FilePath "$Root\venv\Scripts\pythonw.exe" -ArgumentList "`"$Root\app\app.py`"" -WorkingDirectory "$Root\app"
    }
    Say ""
    Say "Klaar. Het dashboard opent in je browser."
    Say "Je vindt het voortaan als `"$Name`" in het Startmenu en op je bureaublad."
} finally {
    Remove-Item -Recurse -Force $Tmp -ErrorAction SilentlyContinue
    Remove-Item Env:UV_PROJECT_ENVIRONMENT -ErrorAction SilentlyContinue
    # Geen halve eerste installatie achterlaten (I2); bij bijwerken blijft de oude versie staan.
    if (-not $Done -and $Fresh -and (Test-Path "$Root\venv")) { Remove-Item -Recurse -Force "$Root\venv" }
}
