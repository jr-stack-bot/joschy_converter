@echo off
setlocal
cd /d "%~dp0"

set PY=
py --version >nul 2>&1 && set PY=py
if "%PY%"=="" (
    python --version >nul 2>&1 && set PY=python
)
if "%PY%"=="" (
    echo.
    echo FEHLER: Python wurde nicht gefunden.
    echo Bitte Python 3 von https://www.python.org/downloads/ installieren
    echo und beim Installieren "Add python.exe to PATH" anhaken.
    echo Danach diese Datei erneut starten.
    echo.
    pause
    exit /b 1
)

echo Verwende: %PY%
%PY% -m pip install --upgrade pip
echo.
echo Installiere benoetigte Pakete mit festen Versionen aus requirements.txt ...
echo (alles wird in die exe eingebaut)
%PY% -m pip install -r requirements.txt
if not errorlevel 1 goto pakete_pruefen
echo.
echo HINWEIS: Nicht alle Pakete liessen sich auf einmal installieren - versuche sie einzeln ...
for /f "usebackq eol=# tokens=1" %%P in ("requirements.txt") do (
    %PY% -m pip install %%P
    if errorlevel 1 echo HINWEIS: %%P konnte nicht installiert werden - die zugehoerige Funktion fehlt dann in der exe.
)
:pakete_pruefen
rem Pflichtpakete muessen da sein (HEIC, Tray, Office-Anbindung und Texterkennung sind optional)
%PY% -c "import PIL, tkinterdnd2, PyInstaller, openpyxl, pypdf, qrcode, pymupdf, imageio_ffmpeg, docx, pptx, xlrd, olefile, striprtf, pdfplumber"
if errorlevel 1 goto fehler

echo.
echo Pruefe 7-Zip (fuer 7z erstellen sowie 7z/RAR entpacken) ...
if exist "tools\7zip\7z.exe" if exist "tools\7zip\7z.dll" if exist "tools\7zip\License.txt" goto siebenzip_da
echo 7-Zip fehlt in tools\7zip - lade es von den offiziellen GitHub-Releases ...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0hole_7zip.ps1" -Ziel "%~dp0tools\7zip"
if errorlevel 1 goto siebenzip_installiert
if exist "tools\7zip\7z.exe" if exist "tools\7zip\7z.dll" goto siebenzip_da
:siebenzip_installiert
rem Notloesung ohne Internet: ein auf diesem PC installiertes 64-Bit-7-Zip verwenden
set "SZ_PF=%ProgramW6432%"
if "%SZ_PF%"=="" set "SZ_PF=%ProgramFiles%"
if not exist "%SZ_PF%\7-Zip\7z.exe" goto fehler_7zip
if not exist "%SZ_PF%\7-Zip\7z.dll" goto fehler_7zip
if not exist "%SZ_PF%\7-Zip\License.txt" goto fehler_7zip
echo Verwende das installierte 7-Zip aus "%SZ_PF%\7-Zip".
if not exist "tools\7zip" mkdir "tools\7zip"
copy /y "%SZ_PF%\7-Zip\7z.exe" "tools\7zip\" >nul || goto fehler_7zip
copy /y "%SZ_PF%\7-Zip\7z.dll" "tools\7zip\" >nul || goto fehler_7zip
copy /y "%SZ_PF%\7-Zip\License.txt" "tools\7zip\" >nul || goto fehler_7zip
:siebenzip_da
rem Lizenztext immer passend zur eingebauten 7-Zip-Version mitliefern
copy /y "tools\7zip\License.txt" "lizenzen\7-Zip_License.txt" >nul

echo.
echo Erstelle KreisKonverter.exe (das dauert ein paar Minuten) ...
%PY% -m PyInstaller KreisKonverter.spec --noconfirm --clean
if errorlevel 1 goto fehler
if not exist "dist\KreisKonverter.exe" goto fehler

echo.
echo Fertig! Die Datei liegt in: dist\KreisKonverter.exe
echo Diese eine Datei kann einfach weitergegeben werden - es muss nichts installiert werden.
pause
exit /b 0

:fehler_7zip
echo.
echo FEHLER: 7-Zip konnte nicht geladen werden (Internet/Firewall?).
echo Abhilfe: 7-Zip 64-Bit von https://www.7-zip.org installieren und build_exe.bat erneut starten,
echo oder die Dateien 7z.exe, 7z.dll und License.txt aus "C:\Program Files\7-Zip"
echo in den Ordner tools\7zip neben dieser Datei kopieren.
pause
exit /b 1

:fehler
echo.
echo FEHLER: Das hat nicht geklappt. Siehe Meldungen oben.
pause
exit /b 1
