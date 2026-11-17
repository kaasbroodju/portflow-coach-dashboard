# Portflow coach dashboard installeren op Windows (spec 020, I1-I8).
#
#   Installeren of bijwerken (PowerShell):
#     irm https://github.com/petersnoek-hu/portflow-coach-dashboard/releases/latest/download/install-windows.ps1 | iex
#   Verwijderen:
#     & ([scriptblock]::Create((irm https://github.com/petersnoek-hu/portflow-coach-dashboard/releases/latest/download/install-windows.ps1))) --verwijderen
#
# Geen beheerdersrechten nodig. uv zet een eigen Python en de pakketten neer. Alles wat het
# script doet, komt in install.log in de map waar je het commando gaf (I8). Voor tests kunnen
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

# I8 - logboek -----------------------------------------------------------------------------------
# install.log in de map van het commando; mag dat niet, dan in de thuismap. Aanvullen.
$Log = Join-Path (Get-Location -PSProvider FileSystem).ProviderPath "install.log"
try { [IO.File]::AppendAllText($Log, "") } catch { $Log = Join-Path $env:USERPROFILE "install.log" }

function Log($text) {
    $stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $here = (Get-Location -PSProvider FileSystem).ProviderPath
    $lines = "$text" -split "`r?`n" | ForEach-Object { "$stamp [$here] $_" }
    try { [IO.File]::AppendAllLines($Log, [string[]]$lines) } catch { }
}
function Say($text) { Write-Host $text; if ($text) { Log "MELDING: $text" } }
function Step($text) { Write-Host ""; Write-Host "-> $text" -ForegroundColor Cyan; Log "STAP: $text" }
function Check($what, $result) { Log "CONTROLE: ${what}: $result" }
function Fail($text) {
    Write-Host ""; Write-Host "X $text" -ForegroundColor Red
    Write-Host "  Wat er gebeurde, staat in $Log"
    Log "FOUT: $text"
    throw "Installatie gestopt."
}
# Een programma uitvoeren; de opdracht, de uitvoer en de exitcode gaan in het logboek.
function Run($exe, [string[]]$arguments) {
    Log "OPDRACHT: $exe $($arguments -join ' ')"
    $previous = $ErrorActionPreference
    $ErrorActionPreference = "Continue"   # stderr of a native program is no error by itself
    $global:LASTEXITCODE = 0
    try { $output = & $exe @arguments 2>&1 | ForEach-Object { "$_" }; $code = $LASTEXITCODE } catch { $output = "$_"; $code = -1 }
    $ErrorActionPreference = $previous
    if ($output) { Log (($output | ForEach-Object { "  | $_" }) -join "`n") }
    Log "AFLOOP: exitcode $code"
    return ($code -eq 0)
}
# Een PowerShell-opdracht (zoals downloaden) uitvoeren en de afloop in het logboek zetten.
function Try-Log($description, [scriptblock]$action) {
    Log "OPDRACHT: $description"
    try {
        $output = & $action
        if ($output) { Log (($output | ForEach-Object { "  | $_" }) -join "`n") }
        Log "AFLOOP: gelukt"
        return $true
    } catch {
        Log "  | $($_.Exception.Message)"
        Log "AFLOOP: mislukt"
        return $false
    }
}
function Interactive { return -not [Console]::IsInputRedirected -and [Environment]::UserInteractive }
function Ask($question) {
    $answer = ""
    if (Interactive) { $answer = Read-Host "$question [j/n]" }
    Log "VRAAG: $question ANTWOORD: $(if ($answer) { $answer } else { '(geen)' })"
    return $answer -match '^(j|ja|y|yes)$'
}

Log "=================================================================="
Log "Portflow coach dashboard - installatiescript Windows, gestart met: $(if ($args) { $args -join ' ' } else { '(geen opties)' })"
Log "Systeem: $([Environment]::OSVersion.VersionString), PowerShell $($PSVersionTable.PSVersion), gebruiker $env:USERNAME"
Log "Programma en gegevens: $Root; snelkoppelingen: $StartMenu en $Desktop; downloads: $Base; poort: $Port"

# Een draaiend dashboard netjes stoppen (I5), zodat de bestanden vrij zijn.
# I11: de processen van het geïnstalleerde dashboard (dus niet een versie uit de broncode).
function Installed-Processes {
    $app = "$Root\app\app.py"
    try {
        return @(Get-CimInstance Win32_Process -Filter "Name LIKE 'python%'" -ErrorAction Stop |
                 Where-Object { $_.CommandLine -and $_.CommandLine.Contains($app) })
    } catch { return @() }
}
# Het geïnstalleerde dashboard netjes stoppen (I5), zodat de bestanden vrij zijn. Een ander
# dashboard (bijvoorbeeld de ontwikkelversie uit een git-checkout) blijft draaien.
function Stop-Dashboard {
    $running = (Installed-Processes).Count -gt 0
    Check "geinstalleerd dashboard draait" $(if ($running) { "ja" } else { "nee" })
    if ($running) {
        Say "  Het dashboard draait nog; het wordt gestopt."
        Try-Log "POST http://127.0.0.1:$Port/afsluiten" { Invoke-WebRequest -Uri "http://127.0.0.1:$Port/afsluiten" -Method Post -TimeoutSec 2 -UseBasicParsing | Out-Null } | Out-Null
        Start-Sleep -Seconds 2
        foreach ($process in Installed-Processes) {
            Try-Log "stoppen: proces $($process.ProcessId)" { Stop-Process -Id $process.ProcessId -Force } | Out-Null
        }
    }
}
# Draait er op de poort een ander dashboard dan het geïnstalleerde?
function Other-On-Port {
    $answer = $false
    try { $answer = (Invoke-RestMethod -Uri "http://127.0.0.1:$Port/versie" -TimeoutSec 2).app -eq "portflow-coach-dashboard" } catch { }
    return $answer -and (Installed-Processes).Count -eq 0
}
# I10: het aantal studenten in de database van de installatie ("geen" zonder database).
function Student-Count {
    if (-not (Test-Path "$Root\data\dashboard.sqlite3")) { return "geen" }
    try {
        $count = & "$Root\venv\Scripts\python.exe" -c "import sqlite3, sys; print(sqlite3.connect(sys.argv[1]).execute('SELECT COUNT(*) FROM students').fetchone()[0])" "$Root\data\dashboard.sqlite3" 2>$null
        if ($LASTEXITCODE -eq 0 -and $count) { return "$count".Trim() }
    } catch { }
    return "onbekend"
}
function Remove-Logged($path) {
    if (Test-Path $path) { Try-Log "verwijderen: $path" { Remove-Item -Recurse -Force $path } | Out-Null }
}

# I7 - verwijderen -------------------------------------------------------------------------------
if ($args -contains "--verwijderen") {
    Say "Portflow coach dashboard verwijderen"
    Stop-Dashboard
    foreach ($path in @("$Root\app", "$Root\app-oud", "$Root\app-nieuw", "$Root\venv", $StartMenu, $Desktop)) { Remove-Logged $path }
    Say "Het programma en de snelkoppelingen zijn verwijderd."
    if (Test-Path "$Root\data") {
        if (Ask "Ook je gegevens verwijderen (studenten, instellingen, Portflow-verbinding)?") {
            Remove-Logged $Root
            Say "Je gegevens zijn verwijderd."
        } else {
            Say "Je gegevens blijven staan in: $Root\data"
        }
    }
    Say "Het logboek staat in $Log"
    Log "EINDE: gelukt"
    Log "=================================================================="
    return
}

Say "Portflow coach dashboard installeren"

$Tmp = Join-Path ([IO.Path]::GetTempPath()) ("portflow-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $Tmp | Out-Null
$Fresh = -not (Test-Path "$Root\app")
Check "eerdere installatie" $(if ($Fresh) { "nee" } else { "ja, in $Root\app" })
$Done = $false

try {
    # I2.1 - Chrome ------------------------------------------------------------------------------------
    Step "Google Chrome controleren"
    $chrome = @(
        "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
        "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
        "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe"
    ) | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
    Check "Google Chrome" $(if ($chrome) { $chrome } else { "niet gevonden" })
    if (-not $chrome) {
        Fail "Google Chrome is niet gevonden. Het dashboard gebruikt Chrome om in te loggen bij Portflow.`n  Installeer Chrome via https://www.google.com/chrome/ en voer deze regel daarna opnieuw uit."
    }

    # I2.2 - uv -------------------------------------------------------------------------------------
    Step "Hulpprogramma uv controleren"
    $uvCommand = Get-Command uv -ErrorAction SilentlyContinue
    $Uv = if ($uvCommand) { $uvCommand.Source } else { Join-Path $env:USERPROFILE ".local\bin\uv.exe" }
    Check "uv" $(if (Test-Path $Uv) { $Uv } else { "niet gevonden" })
    if (-not (Test-Path $Uv)) {
        Say "  uv wordt geinstalleerd (in je eigen gebruikersmap)."
        $env:UV_NO_MODIFY_PATH = "1"
        if (-not (Run "powershell" @("-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", "irm https://astral.sh/uv/install.ps1 | iex"))) {
            Fail "uv kon niet worden geinstalleerd. Controleer je internetverbinding en probeer het opnieuw."
        }
        if (-not (Test-Path $Uv)) { Fail "uv is geinstalleerd, maar niet gevonden in $env:USERPROFILE\.local\bin." }
    }
    Run $Uv @("--version") | Out-Null

    # I2.3 - nieuwste versie downloaden en controleren ------------------------------------------------
    Step "Nieuwste versie downloaden"
    $downloaded = (Try-Log "download $Base/$Zip" { Invoke-WebRequest -Uri "$Base/$Zip" -OutFile "$Tmp\$Zip" -UseBasicParsing }) -and
                  (Try-Log "download $Base/$Zip.sha256" { Invoke-WebRequest -Uri "$Base/$Zip.sha256" -OutFile "$Tmp\$Zip.sha256" -UseBasicParsing })
    if (-not $downloaded) { Fail "Downloaden is niet gelukt. Controleer je internetverbinding en probeer het opnieuw." }
    $expected = ((Get-Content "$Tmp\$Zip.sha256" -Raw).Trim() -split '\s+')[0].ToLower()
    $actual = (Get-FileHash -Algorithm SHA256 "$Tmp\$Zip").Hash.ToLower()
    Check "controlesom" "verwacht $expected, gevonden $actual"
    if ($expected -ne $actual) { Fail "De download is beschadigd (de controlesom klopt niet). Probeer het opnieuw." }
    if (-not (Try-Log "uitpakken naar $Tmp\app" { Expand-Archive -Path "$Tmp\$Zip" -DestinationPath "$Tmp\app" })) { Fail "Uitpakken is niet gelukt." }
    if (-not (Test-Path "$Tmp\app\app.py")) { Fail "De download bevat geen dashboard." }
    $Version = (Select-String -Path "$Tmp\app\dashboard\version.py" -Pattern '^VERSION = "(.*)"').Matches.Groups[1].Value
    Check "versie in de download" $(if ($Version) { $Version } else { "onbekend" })
    @{ uv = $Uv } | ConvertTo-Json | Set-Content -Path "$Tmp\app\.installed" -Encoding UTF8

    # I2.4 - Python en pakketten (in <root>\venv, los van de code) -----------------------------------
    Step "Python en pakketten installeren (de eerste keer ongeveer 100 MB)"
    New-Item -ItemType Directory -Force -Path "$Root\data" | Out-Null
    $env:UV_PROJECT_ENVIRONMENT = "$Root\venv"
    Log "OMGEVING: UV_PROJECT_ENVIRONMENT=$Root\venv"
    if (-not (Run $Uv @("sync", "--frozen", "--no-dev", "--python", $PythonVersion, "--python-preference", "only-managed", "--project", "$Tmp\app"))) {
        Fail "Python of de pakketten konden niet worden geinstalleerd. Controleer je internetverbinding en probeer het opnieuw."
    }

    # I3, I10 - bestaande gegevens uit een git-checkout overnemen (een kopie) ------------------------
    # Ook als de installatie al een database heeft zonder studenten (bijvoorbeeld van een eerste start).
    $students = Student-Count
    Check "studenten in $Root\data" $students
    if ($students -ne "geen" -and $students -ne "0") {
        Check "gegevens overnemen" "niet nodig, de gegevens van de installatie blijven staan"
    } else {
        $source = $null
        $here = (Get-Location -PSProvider FileSystem).ProviderPath
        if (Test-Path "$here\data\dashboard.sqlite3") {
            Check "gegevens in $here\data" "ja"
            if (Ask "Gegevens gevonden in $here\data. Overnemen (een kopie; het origineel blijft staan)?") { $source = "$here\data" }
        } elseif (Interactive) {
            $folder = Read-Host "`nHeb je het dashboard al eerder vanuit een map gebruikt? Typ of plak het pad van die map en druk op Enter. Alleen Enter slaat dit over"
            $folder = $folder.Trim().Trim('"')
            Log "VRAAG: map met eerdere gegevens ANTWOORD: $(if ($folder) { $folder } else { '(overgeslagen)' })"
            if ($folder) {
                if (Test-Path "$folder\data\dashboard.sqlite3") { $source = "$folder\data" }
                elseif (Test-Path "$folder\dashboard.sqlite3") { $source = $folder }
                else { Say "  Daar staan geen gegevens van het dashboard; je begint met een lege database." }
            }
        }
        if ($source) {
            Stop-Dashboard   # de database moet vrij zijn
            if (Test-Path "$Root\data\dashboard.sqlite3") {
                $aside = "$Root\data-voor-overnemen-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
                if (-not (Try-Log "verplaatsen: $Root\data -> $aside" { Move-Item "$Root\data" $aside })) {
                    Fail "De lege gegevensmap kon niet opzij worden gezet."
                }
                Say "  De lege gegevens van de installatie staan apart in $aside."
                New-Item -ItemType Directory -Force -Path "$Root\data" | Out-Null
            }
            if (-not (Try-Log "kopieren: $source -> $Root\data" { Copy-Item -Recurse -Force -Path "$source\*" -Destination "$Root\data" })) {
                Fail "Je gegevens konden niet worden gekopieerd."
            }
            foreach ($lock in @("SingletonLock", "SingletonSocket", "SingletonCookie", "lockfile")) {
                Remove-Item -Force "$Root\data\browser-profile\$lock" -ErrorAction SilentlyContinue
            }
            Say "  Gegevens overgenomen uit $source."
        }
    }

    # Nieuwe code op zijn plek; de vorige versie blijft als app-oud staan.
    Stop-Dashboard
    if (Test-Path "$Root\app") {
        Remove-Logged "$Root\app-oud"
        if (-not (Try-Log "verplaatsen: $Root\app -> $Root\app-oud" { Move-Item "$Root\app" "$Root\app-oud" })) {
            Fail "De vorige versie kon niet worden vervangen. Sluit het dashboard en probeer het opnieuw."
        }
    }
    if (-not (Try-Log "verplaatsen: $Tmp\app -> $Root\app" { Move-Item "$Tmp\app" "$Root\app" })) { Fail "De nieuwe versie kon niet worden neergezet." }

    # I4 - snelkoppelingen in het Startmenu en op het bureaublad, zonder terminalvenster ----------------
    Step "Snelkoppelingen maken"
    $shell = New-Object -ComObject WScript.Shell
    foreach ($path in @($StartMenu, $Desktop)) {
        $made = Try-Log "snelkoppeling: $path -> $Root\venv\Scripts\pythonw.exe `"$Root\app\app.py`"" {
            $link = $shell.CreateShortcut($path)
            $link.TargetPath = "$Root\venv\Scripts\pythonw.exe"
            $link.Arguments = "`"$Root\app\app.py`""
            $link.WorkingDirectory = "$Root\app"
            $link.IconLocation = "$Root\app\install\icon.ico"
            $link.Description = $Name
            $link.Save()
        }
        if (-not $made) { Fail "De snelkoppeling $path kon niet worden gemaakt." }
    }
    $Done = $true

    # I2.6 - starten ------------------------------------------------------------------------------------
    Step "Dashboard starten"
    $started = $false
    if ($env:PORTFLOW_NO_START) {
        Log "OVERGESLAGEN: starten (PORTFLOW_NO_START)"
    } elseif (Other-On-Port) {
        Check "ander dashboard op poort $Port" "ja"   # I11
        Say "  Op poort $Port draait al een ander dashboard (bijvoorbeeld de ontwikkelversie)."
        Say "  Stop dat eerst; open daarna het geinstalleerde dashboard met de snelkoppeling."
    } else {
        $started = Try-Log "starten: $Root\venv\Scripts\pythonw.exe `"$Root\app\app.py`"" {
            Start-Process -FilePath "$Root\venv\Scripts\pythonw.exe" -ArgumentList "`"$Root\app\app.py`"" -WorkingDirectory "$Root\app"
        }
    }
    Say ""
    if ($started) { Say "Klaar. Versie $Version is geinstalleerd en het dashboard opent in je browser." }
    else { Say "Klaar. Versie $Version is geinstalleerd." }
    Say "Je vindt het voortaan als `"$Name`" in het Startmenu en op je bureaublad."
    Say "Het logboek van deze installatie staat in $Log"
    Log "EINDE: gelukt"
} catch {
    if ("$_" -ne "Installatie gestopt.") { Log "FOUT: $($_.Exception.Message)"; Write-Host "  Wat er gebeurde, staat in $Log" }
    Log "EINDE: mislukt"
    $global:LASTEXITCODE = 1   # no red error for the user (the message is already shown); a test can still see it failed
} finally {
    Remove-Item -Recurse -Force $Tmp -ErrorAction SilentlyContinue
    Remove-Item Env:UV_PROJECT_ENVIRONMENT -ErrorAction SilentlyContinue
    # Geen halve eerste installatie achterlaten (I2); bij bijwerken blijft de oude versie staan.
    if (-not $Done -and $Fresh -and (Test-Path "$Root\venv")) {
        Remove-Item -Recurse -Force "$Root\venv" -ErrorAction SilentlyContinue
        Log "OPGERUIMD: $Root\venv"
    }
    Log "=================================================================="
}
