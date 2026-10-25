# -*- mode: python ; coding: utf-8 -*-
# Ergebnis: EINE einzelne, vollständig eigenständige Datei  dist\KreisKonverter.exe
# Eingebaut sind: ffmpeg (Audio/Video), 7-Zip (7z/RAR), Lizenztexte (inkl. LICENSE = AGPL-3.0), PDF-Engine, PDF-Tabellen (pdfplumber), Word/Excel/PowerPoint-Konverter, Windows-Texterkennung (OCR),
# HEIC, QR-Code, Tray, JAI-Sprachansagen (falls Ordner jai vorhanden). Auf dem Zielrechner muss NICHTS installiert werden.
#
# Schnellerer Start: unten bei "EXE" den Block auf ONEDIR umstellen (siehe Kommentar) - dann entsteht
# der Ordner dist\KreisKonverter\ (ideal zusammen mit einem Inno-Setup-Installer).
import lzma
import os
import shutil
from PyInstaller.utils.hooks import collect_all

BASIS = os.path.abspath(SPECPATH)
datas, binaries = [], []
hiddenimports = [
    'PIL._tkinter_finder', 'PIL.ImageTk', 'PIL.ImageDraw', 'PIL.ImageFilter', 'PIL.ImageChops',   # sonst bleibt die Oberfläche leer
    'win32com.client', 'pythoncom', 'pywintypes',            # Office (optional, nur wenn Office vorhanden ist)
    'openpyxl', 'pdfplumber', 'pdfminer', 'pypdfium2', 'pypdfium2_raw', 'pypdf', 'qrcode', 'xlrd', 'olefile', 'striprtf', 'striprtf.striprtf',
    'lxml', 'lxml.etree', 'lxml._elementpath',
    # Windows-eigene Texterkennung
    'winrt.runtime', 'winrt.windows.foundation', 'winrt.windows.foundation.collections',
    'winrt.windows.globalization', 'winrt.windows.graphics.imaging',
    'winrt.windows.media.ocr', 'winrt.windows.storage.streams',
]


def sammle(paket):
    """Fehlt ein Paket, wird es übersprungen (die zugehörige Funktion fehlt dann in der exe)."""
    try:
        d, b, h = collect_all(paket)
    except Exception:
        print(f"WARNUNG: Paket {paket} nicht gefunden - zugehörige Funktion fehlt in der exe")
        return
    datas.extend(d)
    binaries.extend(b)
    hiddenimports.extend(h)


for paket in ('tkinterdnd2', 'openpyxl', 'pypdf', 'pillow_heif', 'pymupdf', 'pystray',
              'docx', 'pptx', 'xlrd', 'olefile', 'striprtf', 'qrcode',
              # PDF-Tabellen lesen: pdfplumber mit pdfminer (inkl. CMap-Daten) und pypdfium2 (inkl. pdfium.dll)
              'pdfplumber', 'pdfminer', 'pypdfium2', 'pypdfium2_raw'):
    sammle(paket)
for paket in ('winrt.runtime', 'winrt.windows.foundation', 'winrt.windows.foundation.collections',
              'winrt.windows.globalization', 'winrt.windows.graphics.imaging',
              'winrt.windows.media.ocr', 'winrt.windows.storage.streams'):
    sammle(paket)


def ffmpeg_einbetten():
    """Packt das ffmpeg aus dem Paket imageio-ffmpeg als ffmpeg.xz in die exe.
    (Die exe entpackt es beim ersten Audio/Video-Auftrag einmalig - so startet sie schnell.)"""
    import imageio_ffmpeg
    quelle = imageio_ffmpeg.get_ffmpeg_exe()
    ordner = os.path.join(BASIS, '_ffmpeg_cache')
    os.makedirs(ordner, exist_ok=True)
    ziel = os.path.join(ordner, 'ffmpeg.xz')
    if not (os.path.isfile(ziel) and os.path.getmtime(ziel) >= os.path.getmtime(quelle)):
        print('Komprimiere ffmpeg (einmalig, dauert etwa eine halbe Minute) ...')
        with open(quelle, 'rb') as f_in, lzma.open(ziel + '.tmp', 'wb', preset=5) as f_out:
            shutil.copyfileobj(f_in, f_out, 1024 * 1024)
        os.replace(ziel + '.tmp', ziel)
    return ziel


def siebenzip_einbetten():
    r"""7z.exe + 7z.dll (x64, offizielles Paket) aus tools\7zip -> Ordner '7zip' in der exe.
    (Die exe kopiert sie beim ersten 7z/RAR-Auftrag nach %LOCALAPPDATA%\KreisKonverter\7zip.)
    build_exe.bat lädt die Dateien automatisch herunter, wenn tools\7zip fehlt."""
    ordner = os.path.join(BASIS, 'tools', '7zip')
    fehlt = [f for f in ('7z.exe', '7z.dll', 'License.txt') if not os.path.isfile(os.path.join(ordner, f))]
    if fehlt:
        raise SystemExit('FEHLER: 7-Zip fehlt in tools\\7zip (' + ', '.join(fehlt) + '). '
                         'Bitte mit build_exe.bat bauen - es lädt 7-Zip automatisch herunter.')
    return [(os.path.join(ordner, f), '7zip') for f in ('7z.exe', '7z.dll', 'License.txt')]


def lizenzen_einbetten():
    """Ordner 'lizenzen' (Übersicht + Lizenztexte, u. a. GPL für ffmpeg, LGPL/unRAR für 7-Zip)
    und die eigene Lizenz LICENSE (AGPL-3.0)."""
    ordner = os.path.join(BASIS, 'lizenzen')
    if not os.path.isfile(os.path.join(ordner, 'LIZENZEN.txt')):
        raise SystemExit('FEHLER: Ordner "lizenzen" fehlt neben KreisKonverter.spec')
    if not os.path.isfile(os.path.join(BASIS, 'LICENSE')):
        raise SystemExit('FEHLER: Datei LICENSE fehlt neben KreisKonverter.spec')
    return ([(os.path.join(ordner, f), 'lizenzen') for f in sorted(os.listdir(ordner)) if f.lower().endswith('.txt')]
            + [(os.path.join(BASIS, 'LICENSE'), '.')])


# PyMuPDF bringt Layout-Modelle (.onnx, ca. 25 MB) mit, die hier nicht gebraucht werden
datas[:] = [d for d in datas if not str(d[0]).lower().endswith('.onnx')]
datas.append((ffmpeg_einbetten(), '.'))
datas.extend(siebenzip_einbetten())
datas.extend(lizenzen_einbetten())


def jai_einbetten():
    """Sprachansagen der JAI-Stimme (Ordner 'jai', *.mp3) – nur wenn der Ordner existiert.
    Ohne den Ordner läuft das Programm normal, die Ansagen entfallen dann still."""
    ordner = os.path.join(BASIS, 'jai')
    if not os.path.isdir(ordner):
        return []
    return [(os.path.join(ordner, f), 'jai') for f in sorted(os.listdir(ordner)) if f.lower().endswith('.mp3')]


datas.extend(jai_einbetten())

symbol = os.path.join(BASIS, 'kreis.ico')

a = Analysis(
    ['kreis_konverter.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # imageio_ffmpeg: ffmpeg steckt bereits als ffmpeg.xz in der exe (sonst wäre es doppelt enthalten)
    # erweiterungen: optionale private Zusatzmodule gehören nie in die öffentliche exe
    excludes=['numpy', 'matplotlib', 'scipy', 'pandas', 'IPython', 'pytest', 'imageio_ffmpeg',
              'cv2', 'onnxruntime', 'rapidocr_onnxruntime', 'erweiterungen'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='KreisKonverter',
    icon=symbol if os.path.exists(symbol) else None,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,                    # UPX verlangsamt den Start und löst oft Virenscanner-Fehlalarme aus
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# --- ONEDIR-Variante (schnellerer Start): obigen EXE-Block durch diesen ersetzen
# exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='KreisKonverter',
#           icon=symbol, upx=False, console=False)
# coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='KreisKonverter')
