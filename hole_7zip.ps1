# Laedt 7-Zip (x64) von den offiziellen GitHub-Releases (github.com/ip7z/7zip) und legt
# 7z.exe, 7z.dll und License.txt in den Zielordner (Standard: tools\7zip neben diesem Skript).
# Wird von build_exe.bat automatisch aufgerufen, wenn tools\7zip fehlt.
#
# Weg 1: MSI-Paket herunterladen, Pruefsumme pruefen, per "msiexec /a" (Admin-Install = nur entpacken,
#        es wird NICHTS installiert) in einen Hilfsordner auspacken.
# Weg 2 (falls Weg 1 scheitert): 7zr.exe + Installer-exe herunterladen und die drei Dateien damit auspacken.
# Neue 7-Zip-Version: $Version, $Nr und die drei SHA-256-Werte unten anpassen.
param([string]$Ziel = (Join-Path $PSScriptRoot 'tools\7zip'))

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'          # macht Invoke-WebRequest unter Windows PowerShell 5.1 viel schneller

$Version = '26.05'
$Nr = '2605'
$Basis = "https://github.com/ip7z/7zip/releases/download/$Version"
$Pruefsummen = @{
    "7z$Nr-x64.msi" = '3fe4ab99fa15629c652944309a2b2bc6e41fc933fc6b63f5df1ebcf3aea68263'
    "7z$Nr-x64.exe" = 'fd99e86f57d8f429ef5ed045bf98315af962e2309b0f1ba87a147a44c71647d0'
    '7zr.exe'       = '9bf582b894dfa665f852d7e9112b02290a1c303c2d95a21fcdc41ffcb03143b7'
}
$Benoetigt = @('7z.exe', '7z.dll', 'License.txt')

try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
} catch { }

function Lade([string]$Name, [string]$Ordner) {
    $Datei = Join-Path $Ordner $Name
    $Url = "$Basis/$Name"
    Write-Host "  Lade $Url"
    try {
        Invoke-WebRequest -UseBasicParsing -Uri $Url -OutFile $Datei
    } catch {
        Write-Host "  Invoke-WebRequest fehlgeschlagen ($($_.Exception.Message)) - versuche curl.exe ..."
        & curl.exe -fsSL --retry 2 -o $Datei $Url
        if ($LASTEXITCODE -ne 0) { throw "Download fehlgeschlagen: $Url" }
    }
    $Ist = (Get-FileHash -Algorithm SHA256 -Path $Datei).Hash.ToLower()
    if ($Ist -ne $Pruefsummen[$Name]) {
        throw "Pruefsumme von $Name stimmt nicht (Download beschaedigt oder veraendert)."
    }
    return $Datei
}

function Finde([string]$Ordner) {
    $Treffer = Get-ChildItem -Path $Ordner -Recurse -Filter '7z.exe' -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($Treffer) {
        $Q = $Treffer.DirectoryName
        foreach ($F in $Benoetigt) { if (-not (Test-Path (Join-Path $Q $F))) { return $null } }
        return $Q
    }
    return $null
}

$Tmp = Join-Path ([IO.Path]::GetTempPath()) ('kk_7zip_' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $Tmp | Out-Null
$Ergebnis = 1
try {
    $Quelle = $null
    try {
        Write-Host "Weg 1: MSI-Paket von 7-Zip $Version"
        $Msi = Lade "7z$Nr-x64.msi" $Tmp
        $Aus = Join-Path $Tmp 'msi'
        $Argumente = '/a "' + $Msi + '" /qn TARGETDIR="' + $Aus + '"'
        $P = Start-Process -FilePath 'msiexec.exe' -ArgumentList $Argumente -Wait -PassThru
        if ($P.ExitCode -ne 0) { throw "msiexec meldet Fehlercode $($P.ExitCode)" }
        $Quelle = Finde $Aus
        if (-not $Quelle) { throw '7z.exe/7z.dll nicht im MSI gefunden' }
    } catch {
        Write-Host "  Weg 1 fehlgeschlagen: $($_.Exception.Message)"
        Write-Host "Weg 2: 7zr.exe + Installer von 7-Zip $Version"
        $Zr = Lade '7zr.exe' $Tmp
        $Inst = Lade "7z$Nr-x64.exe" $Tmp
        $Aus = Join-Path $Tmp 'exe'
        & $Zr x -y "-o$Aus" $Inst @Benoetigt | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "7zr.exe konnte den Installer nicht auspacken (Code $LASTEXITCODE)" }
        $Quelle = Finde $Aus
        if (-not $Quelle) { throw '7z.exe/7z.dll nicht im Installer gefunden' }
    }
    New-Item -ItemType Directory -Force -Path $Ziel | Out-Null
    foreach ($F in $Benoetigt) { Copy-Item -Force -Path (Join-Path $Quelle $F) -Destination (Join-Path $Ziel $F) }
    Write-Host "7-Zip $Version liegt jetzt in: $Ziel"
    $Ergebnis = 0
} catch {
    Write-Host ""
    Write-Host "FEHLER beim Laden von 7-Zip: $($_.Exception.Message)"
} finally {
    Remove-Item -Recurse -Force -Path $Tmp -ErrorAction SilentlyContinue
}
exit $Ergebnis
