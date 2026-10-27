"""
HUD-Grafik des Kreis-Konverters: Konstanten, Farben/Themes, Masken und das Zeichnen eines Bildes.
© JOSCHY – Lizenz: AGPL-3.0

Ausgelagert aus dem Hauptprogramm (ohne Verhaltensänderung). Dieses Modul importiert nie das Hauptprogramm.
SKALA und SS ändern sich zur Laufzeit (setze_skalierung) - von außen immer als hud_grafik.SKALA/.SS lesen.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from PIL import Image, ImageChops, ImageDraw, ImageFilter


# ------------------------------------------------------------------ Design & Themes
TRANS = "#010203"
TRANS_RGBA = (1, 2, 3, 255)
S_NORMAL, S_MINI = 340, 120
SS = 2          # Überabtastung beim Zeichnen (wird bei hoher Bildschirmskalierung erhöht)

# Bildschirmskalierung (1.0 = 100 %, 1.5 = 150 % ...). Alle Maße im Programm sind "logische" Pixel
# eines 340er-Kreises; gezeichnet wird in P(...) echten Pixeln, damit der Kreis bei 150 % scharf UND
# gleich groß wie bisher erscheint. Wird in KreisApp vor dem Aufbau der Grafik gesetzt.
SKALA = 1.0


def P(v):
    """Logische Pixel -> echte Bildschirmpixel."""
    return int(round(v * SKALA))


def setze_skalierung(faktor):
    global SKALA, SS
    SKALA = float(faktor)
    # mindestens 2-fach überabtasten (bei 150 % also 3, bei 200 % 4) - so bleiben Kanten glatt
    SS = 2 if SKALA <= 1.0 else max(2, int(math.ceil(2 * SKALA - 1e-9)))


def verkleinere(img):
    """Überabgetastete Zeichnung (Faktor SS, logische Größe) auf echte Bildschirmpixel bringen."""
    if SKALA == 1.0:
        return img.reduce(SS)                                  # wie bisher
    w, h = P(img.width / SS), P(img.height / SS)
    k = img.width // w
    if k * w == img.width and k * h == img.height:
        return img.reduce(k)
    return img.resize((w, h), Image.LANCZOS)


# HUD / Geometry Constants
R_DISC = 162
BTN_Y, BTN_DX, BTN_R = 90, 74, 17      # Knöpfe Menü/Schließen (gezeichnet in Grafik._core, Treffer im Hauptprogramm)
PILL_Y = 238

STANDARD_THEME = "Reaktor"
THEMES = {
    "Reaktor": {
        "CYAN": "#2ee6d6", "MAGENTA": "#ff3b30", "ROT": "#ff3b30",
        "bg_dark": "#060b0e", "bg_inner": "#0a1317", "border": "#1d3a40",
        "core_c1": "#12262d", "core_c2": "#03070a", "glow_a": (46, 230, 214, 38), "glow_b": (255, 59, 48, 14),
        "FUNKEN": ["#2ee6d6", "#ffffff", "#ff3b30", "#7ff5ea", "#2ee6d6"]
    },
    "Cyan": {
        "CYAN": "#00f0ff", "MAGENTA": "#ff2bd6",
        "ROT": "#ff2bd6", "bg_dark": "#050918", "bg_inner": "#070d24", "border": "#1b2a6c",
        "core_c1": "#0f1a40", "core_c2": "#03060f", "glow_a": (0, 240, 255, 52), "glow_b": (138, 92, 255, 60),
        "FUNKEN": ["#00f0ff", "#ff2bd6", "#00ff9d", "#ffb000", "#ffffff", "#8a5cff"]
    },
    "Matrix": {
        "CYAN": "#00ff66", "MAGENTA": "#008833",
        "ROT": "#ccff00", "bg_dark": "#021206", "bg_inner": "#04200b", "border": "#0a4d1b",
        "core_c1": "#073a14", "core_c2": "#010803", "glow_a": (0, 255, 102, 52), "glow_b": (0, 136, 51, 60),
        "FUNKEN": ["#00ff66", "#33ff99", "#008833", "#aaffcc", "#ffffff"]
    },
    "Iron": {
        "CYAN": "#ff3300", "MAGENTA": "#ffcc00",
        "ROT": "#ffcc00", "bg_dark": "#180505", "bg_inner": "#240707", "border": "#6c1b1b",
        "core_c1": "#401010", "core_c2": "#0c0202", "glow_a": (255, 51, 0, 52), "glow_b": (255, 204, 0, 60),
        "FUNKEN": ["#ff3300", "#ffcc00", "#ff6600", "#ffffff", "#ff9933"]
    },
    "Stealth": {
        "CYAN": "#00ccff", "MAGENTA": "#a2b5cd",
        "ROT": "#ff4d4d", "bg_dark": "#0a0f14", "bg_inner": "#101720", "border": "#283848",
        "core_c1": "#1c2a38", "core_c2": "#05080b", "glow_a": (0, 204, 255, 45), "glow_b": (112, 144, 176, 50),
        "FUNKEN": ["#00ccff", "#a2b5cd", "#ffffff", "#7090b0"]
    }
}

FARBEN = {
    "Bild": ("#00f0ff", "#3d7bff"),
    "Office": ("#2b579a", "#107c41"),
    "PDF": ("#e74c3c", "#c0392b"),
    "Daten": ("#ff9900", "#ff5500"),
    "E-Book": ("#9b59b6", "#8e44ad"),
    "Archiv": ("#2ecc71", "#27ae60"),
    "wahl": ("#ffb000", "#ff8a00"),       # Modus FORMAT WÄHLEN
    "QR": ("#9b59b6", "#8e44ad"),
    "Audio": ("#ff2bd6", "#8a5cff"),
    "Video": ("#ffb000", "#ff3d6b"),
    "hover": ("#00ff9d", "#00f0ff"),
    "run": ("#00f0ff", "#ff2bd6"),
    "ok": ("#00ff9d", "#00c2ff"),
    "err": ("#ff3b6b", "#ff8a00"),
}


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mix(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def farbe_aus(stops, t):
    n = len(stops) - 1
    p = (t % 1.0) * n
    i = min(int(p), n - 1)
    return mix(stops[i], stops[i + 1], p - i)


def verlauf(size, c1, c2):
    w, h = size
    img = Image.new("RGB", size)
    d = ImageDraw.Draw(img)
    for y in range(h):
        d.line([(0, y), (w, y)], fill=mix(c1, c2, y / max(1, h - 1)))
    return img


def kreis_maske(r, size=None):
    size = size or 340 * SS
    m = Image.new("L", (size, size), 0)
    c = size / 2
    ImageDraw.Draw(m).ellipse([c - r * SS, c - r * SS, c + r * SS, c + r * SS], fill=255)
    return m


def ring_maske(r_innen, r_aussen, size=None):
    return ImageChops.subtract(kreis_maske(r_aussen, size), kreis_maske(r_innen, size))


def auf_ebene(img, zeichnen, blur=0):
    ebene = Image.new("RGBA", img.size, (0, 0, 0, 0))
    zeichnen(ImageDraw.Draw(ebene))
    if blur:
        ebene = ebene.filter(ImageFilter.GaussianBlur(blur))
    img.alpha_composite(ebene)


def polar(c, r, grad):
    a = math.radians(grad)
    return (c + r * math.cos(a), c + r * math.sin(a))


class _Lazy(dict):
    """Dict, das fehlende Einträge beim ersten Zugriff erzeugt (beschleunigt den Start)."""
    def __init__(self, fabrik):
        super().__init__()
        self._fabrik = fabrik

    def __missing__(self, key):
        wert = self._fabrik(key)
        self[key] = wert
        return wert


EMB_GLYPH = {"ok": "check", "err": "warn"}


def theme_daten(name):
    return THEMES.get(name, THEMES[STANDARD_THEME])


def hexfarbe(rgb):
    return "#%02x%02x%02x" % tuple(int(v) for v in rgb[:3])


class Grafik:
    def __init__(self, akt_theme=STANDARD_THEME):
        self.akt_theme = akt_theme
        self._radar_cache, self._hex_cache, self._bogen_cache = {}, {}, {}
        self._welle_cache, self._prog_cache = {}, {}
        self.halo = verkleinere(ring_maske(141, 153)).filter(ImageFilter.GaussianBlur(8 * SKALA)) \
            .point(lambda v: int(v * 0.6))
        self.halo_stufen = [self.halo.point(lambda v, k=0.30 + 0.70 * i / 15: int(v * k)) for i in range(16)]
        self.spur = verkleinere(ring_maske(143, 151)).point(lambda v: int(v * 0.20))
        self.prog_ss = ring_maske(143, 151)
        self.prog_glow = verkleinere(ring_maske(139, 155)).filter(ImageFilter.GaussianBlur(6 * SKALA))
        self.ticks = self._ticks()
        self.radar = self._radar()
        self._radar_klein = None
        # Windows macht nur exakt eine Farbe unsichtbar (keine Halbtransparenz). Damit am Rand keine
        # dunklen Mischpixel stehen bleiben, wird jedes Bild mit einer harten Kreismaske beschnitten.
        self.schnitt = self._harte_maske(P(S_NORMAL))
        self.schnitt_mini = self._harte_maske(P(S_MINI))
        self.kante_mini = ImageChops.subtract(self.schnitt_mini, self._harte_maske(P(S_MINI), -1.6 * SKALA))
        self.trans_gross = Image.new("RGB", (P(S_NORMAL), P(S_NORMAL)), TRANS_RGBA[:3])
        self.trans_mini = Image.new("RGB", (P(S_MINI), P(S_MINI)), TRANS_RGBA[:3])
        self.rebuild_theme(akt_theme)

    @staticmethod
    def _harte_maske(groesse, zusatz=0.0):
        m = Image.new("L", (groesse, groesse), 0)
        r = R_DISC * groesse / 340.0 + zusatz
        c = groesse / 2.0
        ImageDraw.Draw(m).ellipse([c - r, c - r, c + r - 1, c + r - 1], fill=255)
        return m

    def rebuild_theme(self, theme_name):
        self.akt_theme = theme_name
        td = theme_daten(theme_name)
        self.farben = {k: self._farbe_fuer(k, td) for k in FARBEN}
        self.conic = {k: self._conic(k) for k in FARBEN}
        self.emb = _Lazy(lambda k: self._emblem(k, EMB_GLYPH.get(k, "pfeil")))
        self._hex_cache.clear()
        self.kopf = self._kopf()
        self.core_ss = self._core(theme_name)
        self.plain = verkleinere(self.core_ss)
        self.idle = _Lazy(lambda k: verkleinere(self._pille(k)))
        self._bogen_cache.clear()

    @staticmethod
    def _farbe_fuer(key, td):
        """Alle Leuchtelemente in der Designfarbe; nur Erfolg/Fehler weichen ab."""
        a, rot, w = hexrgb(td["CYAN"]), hexrgb(td["ROT"]), (255, 255, 255)
        if key == "ok":
            return mix(a, (0, 255, 157), 0.55), a
        if key == "err":
            return rot, mix(rot, (255, 170, 0), 0.6)
        if key == "run":
            return a, mix(a, w, 0.55)
        if key == "hover":
            return mix(a, w, 0.35), a
        if key == "wahl":                    # FORMAT WÄHLEN: Bernstein als "bitte entscheiden"
            return mix(a, (255, 176, 0), 0.75), mix(a, (255, 120, 0), 0.6)
        return a, mix(a, w, 0.30)

    def _conic(self, key):
        c1, c2 = self.farben[key]
        stops = [c1, c2, c1]
        n = P(340)
        img = Image.new("RGB", (n, n))
        d = ImageDraw.Draw(img)
        for i in range(360):
            d.pieslice([0, 0, n - 1, n - 1], i - 90, i - 88, fill=farbe_aus(stops, i / 360))
        return img

    def _ticks(self):
        frames = []
        c = (340 * SS) / 2
        for f in range(30):
            m = Image.new("L", (340 * SS, 340 * SS), 0)
            d = ImageDraw.Draw(m)
            for i in range(72):
                lang = i % 3 == 0
                r0, r1 = (153, 166) if lang else (160, 166)
                a = i * 5 + f * 0.5 - 90
                d.line([polar(c, r0 * SS, a), polar(c, r1 * SS, a)],
                       fill=165 if lang else 85, width=int((2.2 if lang else 1.6) * SS))
            frames.append(verkleinere(m))
        return frames

    def _radar(self):
        N = 340 * SS
        m = Image.new("L", (N, N), 0)
        d = ImageDraw.Draw(m)
        c = N / 2
        R = 132 * SS
        for i in range(85):
            d.pieslice([c - R, c - R, c + R, c + R], -90 + i - 1.2, -90 + i,
                       fill=int(70 * (1 - i / 85) ** 2))
        for k in range(4):
            a0 = k * 90 + 8
            d.arc([c - 140 * SS, c - 140 * SS, c + 140 * SS, c + 140 * SS], a0, a0 + 52,
                  fill=255, width=int(4 * SS))
        for k in range(3):
            a0 = k * 120 + 30
            d.arc([c - 131 * SS, c - 131 * SS, c + 131 * SS, c + 131 * SS], a0, a0 + 34,
                  fill=170, width=int(2 * SS))
        return m

    def _core(self, theme_name):
        """Statischer Hintergrund im Stil einer Reaktor-Konsole (Metallgehäuse, Leuchtbögen, Module)."""
        N = 340 * SS
        c = N / 2
        td = theme_daten(theme_name)
        A, ROT = hexrgb(td["CYAN"]), hexrgb(td["ROT"])
        hell, dunkel = hexrgb(td["core_c1"]), hexrgb(td["core_c2"])
        W = (255, 255, 255)

        def S(v):
            return v * SS

        def Wd(v):
            return max(1, int(round(v * SS)))

        def box(r):
            return [c - S(r), c - S(r), c + S(r), c + S(r)]

        def eckig(x0, y0, x1, y1, k):
            x0, y0, x1, y1, k = S(x0), S(y0), S(x1), S(y1), S(k)
            return [(x0 + k, y0), (x1 - k, y0), (x1, y0 + k), (x1, y1 - k),
                    (x1 - k, y1), (x0 + k, y1), (x0, y1 - k), (x0, y0 + k)]

        core = Image.new("RGBA", (N, N), TRANS_RGBA)

        # 1. Metallgehäuse (Lichteinfall von oben)
        metall = verlauf((N, N), mix(hell, (190, 210, 215), 0.22), mix(dunkel, (0, 0, 0), 0.4)).convert("RGBA")
        core.paste(metall, (0, 0), kreis_maske(R_DISC))
        auf_ebene(core, lambda d: d.arc(box(158), 200, 340, fill=W + (38,), width=Wd(5)), blur=S(3))

        # 2. Zifferblatt: radialer Verlauf, dunkel am Rand
        R_F = 146
        flaeche = Image.new("RGBA", (N, N), (0, 0, 0, 0))
        d = ImageDraw.Draw(flaeche)
        for i in range(60):
            t = i / 59
            d.ellipse(box(R_F * (1 - t * 0.98)), fill=mix(dunkel, hell, t ** 0.9) + (255,))
        core.alpha_composite(flaeche)
        glow_a = td.get("glow_a", A + (40,))
        glow_b = td.get("glow_b", ROT + (14,))
        auf_ebene(core, lambda d: (d.ellipse(box(76), fill=glow_a),
                                   d.ellipse([c - S(120), c + S(40), c + S(120), c + S(150)], fill=glow_b)), blur=S(28))

        def zifferblatt(d):
            for y in range(0, N, 3 * SS):                                     # Bildschirm-Zeilen
                d.line([(0, y), (N, y)], fill=(0, 0, 0, 34), width=SS)
            d.ellipse(box(R_F + 1), outline=(0, 0, 0, 220), width=Wd(3))      # Fuge zum Gehäuse
            d.ellipse(box(R_F + 3), outline=W + (34,), width=SS)
            d.ellipse(box(R_DISC - 1), outline=(150, 170, 175, 255), width=Wd(1.6))   # helle Außenkante
            d.ellipse(box(R_DISC - 3), outline=(0, 0, 0, 150), width=SS)
            d.ellipse(box(128), outline=A + (55,), width=SS)
            d.ellipse(box(98), outline=W + (13,), width=SS)
            for i in range(0, 360, 6):                                          # gestrichelter Innenring
                d.arc(box(62), i, i + 3, fill=A + (48,), width=SS)
            for i in range(0, 360, 10):                                         # Skala
                lang = i % 30 == 0
                d.line([polar(c, S(128 - (6 if lang else 3)), i), polar(c, S(128), i)],
                       fill=A + (90,) if lang else W + (26,), width=SS)
            for a in (0, 90, 180, 270):                                         # Fadenkreuz
                d.line([polar(c, S(102), a), polar(c, S(124), a)], fill=A + (60,), width=SS)
        auf_ebene(core, zifferblatt)

        # 3. Leuchtbögen und Markierungen auf dem Gehäuse
        bogen_segmente = ((200, 246), (294, 340), (22, 66), (114, 158))
        auf_ebene(core, lambda d: [d.arc(box(155.5), a0, a1, fill=A + (210,), width=Wd(3)) for a0, a1 in bogen_segmente],
                  blur=S(4))

        def gehaeuse(d):
            for a0, a1 in bogen_segmente:
                d.arc(box(155.5), a0, a1, fill=A + (235,), width=Wd(2.2))
                d.arc(box(155.5), a0 + 2, a0 + 7, fill=W + (255,), width=Wd(3.2))
                d.arc(box(155.5), a1 - 7, a1 - 2, fill=W + (255,), width=Wd(3.2))
            for a0 in (252, 280, 72, 102):                                     # rote Akzente
                d.arc(box(149.5), a0, a0 + 8, fill=ROT + (230,), width=Wd(1.6))
            for a in range(0, 360, 4):                                          # feine Rasterung
                d.line([polar(c, S(160), a), polar(c, S(162), a)], fill=(0, 0, 0, 120), width=SS)
            for a in (45, 135, 225, 315):                                       # Schrauben
                x, y = polar(c, S(155), a)
                r = S(4.6)
                d.ellipse([x - r, y - r, x + r, y + r], fill=(10, 16, 19, 255), outline=(110, 128, 132, 255), width=SS)
                d.line([x - r * 0.6, y, x + r * 0.6, y], fill=(150, 165, 170, 200), width=SS)
        auf_ebene(core, gehaeuse)

        # 4. Lichtleisten (wie die leuchtenden Balken im Vorbild)
        def leiste(d, a, laenge, breite, farbe):
            px, py = polar(c, S(132), a)
            t = math.radians(a + 90)
            n = math.radians(a)
            tx, ty = math.cos(t) * S(laenge) / 2, math.sin(t) * S(laenge) / 2
            nx, ny = math.cos(n) * S(breite) / 2, math.sin(n) * S(breite) / 2
            d.polygon([(px - tx - nx, py - ty - ny), (px + tx - nx, py + ty - ny),
                       (px + tx + nx, py + ty + ny), (px - tx + nx, py - ty + ny)], fill=farbe)
        winkel = (-32, 32, 148, 212)
        auf_ebene(core, lambda d: [leiste(d, a, 34, 9, A + (200,)) for a in winkel], blur=S(5))

        def leisten(d):
            for a in winkel:
                leiste(d, a, 34, 7, (8, 18, 22, 255))
                leiste(d, a, 30, 3.4, mix(A, W, 0.7) + (255,))
                ex, ey = polar(c, S(124), a - 8)                     # rote Halteklammer
                ix, iy = polar(c, S(119), a - 8)
                d.line([(ex, ey), (ix, iy)], fill=ROT + (230,), width=Wd(1.5))
        auf_ebene(core, leisten)

        # 5. Module: Statusplatte oben, Datenmodule links/rechts, Platte unten
        def module(d):
            d.polygon(eckig(112, 50, 228, 74, 6), fill=(5, 12, 15, 225), outline=A + (150,))
            d.line([(S(150), S(50)), (S(190), S(50))], fill=mix(A, W, 0.6) + (255,), width=Wd(2))
            d.line([(S(112), S(68)), (S(112), S(56))], fill=ROT + (220,), width=Wd(1.5))
            d.line([(S(228), S(68)), (S(228), S(56))], fill=ROT + (220,), width=Wd(1.5))
            for sx in (1, -1):                                                  # seitliche Datenmodule
                x0, x1 = (24, 52) if sx == 1 else (288, 316)
                d.polygon(eckig(x0, 124, x1, 152, 4), fill=(5, 12, 15, 235), outline=A + (140,))
                for i, l in enumerate((18, 12, 15, 8)):
                    yy = S(130 + i * 5)
                    xa = S(x0 + 5) if sx == 1 else S(x1 - 5 - l)
                    d.line([(xa, yy), (xa + S(l), yy)], fill=(mix(A, W, 0.5) if i == 0 else A) + (170 if i == 0 else 90,),
                           width=SS)
                rx = S(x1 - 7) if sx == 1 else S(x0 + 3)
                d.rectangle([rx, S(145), rx + S(4), S(148)], fill=ROT + (230,))
                ax = S(x1) if sx == 1 else S(x0)                                # Leiterbahn ins Zifferblatt
                bx = S(x1 + 14) if sx == 1 else S(x0 - 14)
                d.line([(ax, S(124)), (bx, S(124)), (bx + (S(8) if sx == 1 else -S(8)), S(116))],
                       fill=ROT + (150,), width=SS)
            d.polygon(eckig(100, 266, 240, 305, 8), fill=(5, 12, 15, 170), outline=A + (80,))
            d.line([(S(150), S(305)), (S(190), S(305))], fill=A + (200,), width=Wd(2))
        auf_ebene(core, module)

        # 6. Knöpfe (Menü / Schließen) als eingelassene Metallschalter
        def knoepfe(d):
            M = 170
            for sx, art in ((-BTN_DX, "menu"), (BTN_DX, "close")):
                cx, cy = S(M + sx), S(BTN_Y)
                d.ellipse([cx - S(BTN_R + 2), cy - S(BTN_R + 2), cx + S(BTN_R + 2), cy + S(BTN_R + 2)], fill=(2, 5, 7, 255))
                d.ellipse([cx - S(BTN_R), cy - S(BTN_R), cx + S(BTN_R), cy + S(BTN_R)], fill=(13, 25, 29, 255),
                          outline=A + (180,), width=int(1.4 * SS))
                d.ellipse([cx - S(BTN_R - 4), cy - S(BTN_R - 4), cx + S(BTN_R - 4), cy + S(BTN_R - 4)],
                          outline=W + (22,), width=SS)
                d.ellipse([cx - S(1.6), cy - S(BTN_R - 1.5), cx + S(1.6), cy - S(BTN_R - 4.7)], fill=ROT + (255,))
                w = int(2.4 * SS)
                if art == "menu":
                    for dy in (-5, 0, 5):
                        d.line([cx - S(7), cy + S(dy), cx + S(7), cy + S(dy)], fill=W + (235,), width=w)
                else:
                    d.line([cx - S(5.5), cy - S(5.5), cx + S(5.5), cy + S(5.5)], fill=W + (235,), width=w)
                    d.line([cx - S(5.5), cy + S(5.5), cx + S(5.5), cy - S(5.5)], fill=W + (235,), width=w)
        auf_ebene(core, knoepfe)
        return core

    def _pille(self, kat):
        """Formatanzeige als beleuchtete Bildschirmplatte."""
        img = self.core_ss.copy()
        A = self.farben[kat][0]
        K = hexrgb(FARBEN[kat][0])                                  # Kategoriefarbe als kleine Kennung
        ROT = hexrgb(theme_daten(self.akt_theme)["ROT"])
        W = (255, 255, 255)
        M = 170
        x0, x1 = (M - 82) * SS, (M + 82) * SS
        y0, y1 = (PILL_Y - 21) * SS, (PILL_Y + 21) * SS
        ch = 9 * SS
        pts = [(x0 + ch, y0), (x1 - ch, y0), (x1, y0 + ch), (x1, y1 - ch),
               (x1 - ch, y1), (x0 + ch, y1), (x0, y1 - ch), (x0, y0 + ch)]
        auf_ebene(img, lambda d: d.polygon(pts, fill=A + (90,)), blur=10 * SS)
        auf_ebene(img, lambda d: d.polygon(pts, fill=(4, 13, 16, 238)))
        linien = Image.new("RGBA", img.size, (0, 0, 0, 0))
        dl = ImageDraw.Draw(linien)
        for y in range(y0, y1, 3 * SS):
            dl.line([(x0, y), (x1, y)], fill=A + (22,), width=SS)
        maske = Image.new("L", img.size, 0)
        ImageDraw.Draw(maske).polygon(pts, fill=255)
        linien.putalpha(ImageChops.multiply(linien.getchannel("A"), maske))
        img.alpha_composite(linien)

        def umriss(d):
            d.line(pts + [pts[0]], fill=A + (255,), width=int(1.6 * SS), joint="curve")
            inn = 4 * SS
            d.rectangle([x0 + ch, y0 + inn, x1 - ch, y1 - inn], outline=A + (45,), width=SS)
            d.line([(x0 + ch, y0), (x0 + ch + 18 * SS, y0)], fill=W + (255,), width=int(2.6 * SS))
            d.line([(x1 - ch, y1), (x1 - ch - 18 * SS, y1)], fill=W + (255,), width=int(2.6 * SS))
            d.rectangle([x0 + 5 * SS, (PILL_Y - 7) * SS, x0 + 8 * SS, (PILL_Y + 7) * SS], fill=K + (255,))
            for sx in (-1, 1):
                d.line([((M + sx * 22) * SS, y1 + 4 * SS), ((M + sx * 34) * SS, y1 + 4 * SS)],
                       fill=ROT + (220,), width=int(1.5 * SS))
            cy = PILL_Y * SS
            for sx, r in ((-62, -1), (62, 1)):
                cx = (M + sx) * SS
                d.line([(cx - r * 3 * SS, cy - 8 * SS), (cx + r * 4 * SS, cy), (cx - r * 3 * SS, cy + 8 * SS)],
                       fill=A + (255,), width=int(2.8 * SS), joint="curve")
        auf_ebene(img, umriss)
        return img

    def _emblem(self, key, glyph):
        """Reaktorkern: konzentrische, gegenläufig drehende Ringe mit Symbol in der Mitte."""
        c1, c2 = self.farben[key]
        L = 124
        LS = L * SS
        c = LS / 2

        def box(r):
            return [c - r * SS, c - r * SS, c + r * SS, c + r * SS]

        glow = Image.new("RGBA", (LS, LS), (0, 0, 0, 0))
        auf_ebene(glow, lambda d: d.ellipse(box(40), fill=c1 + (100,)), blur=7.5 * SS)
        auf_ebene(glow, lambda d: (d.ellipse(box(25), fill=(2, 8, 10, 200)),
                                   d.ellipse(box(25), outline=c1 + (70,), width=SS)))
        LP = P(L)                                                  # Größe in echten Pixeln
        glow = glow.resize((LP, LP), Image.LANCZOS)

        hex_a = Image.new("L", (LS, LS), 0)                        # äußerer Ring: drei breite Segmente
        d = ImageDraw.Draw(hex_a)
        for i in range(3):
            a0 = i * 120
            d.arc(box(35), a0, a0 + 74, fill=255, width=int(3 * SS))
            d.arc(box(35), a0 + 82, a0 + 100, fill=150, width=int(1.6 * SS))
            d.arc(box(39.5), a0 + 30, a0 + 44, fill=200, width=int(1.4 * SS))
        hex_b = Image.new("L", (LS, LS), 0)                        # innerer Ring: Strichkranz
        d = ImageDraw.Draw(hex_b)
        for i in range(0, 360, 15):
            d.arc(box(29), i, i + 9, fill=210, width=int(2 * SS))
        d.ellipse(box(22), outline=110, width=SS)

        gl = Image.new("L", (LS, LS), 0)
        d = ImageDraw.Draw(gl)
        if glyph == "pfeil":
            d.rounded_rectangle([c - 3.2 * SS, c - 15 * SS, c + 3.2 * SS, c + 3 * SS], radius=3 * SS, fill=255)
            d.polygon([(c - 11 * SS, c - 3 * SS), (c + 11 * SS, c - 3 * SS), (c, c + 11 * SS)], fill=255)
            d.rounded_rectangle([c - 13 * SS, c + 14 * SS, c + 13 * SS, c + 17 * SS], radius=1.5 * SS, fill=255)
        elif glyph == "check":
            d.line([(c - 12 * SS, c + 1 * SS), (c - 3 * SS, c + 10 * SS), (c + 13 * SS, c - 9 * SS)],
                   fill=255, width=int(5.5 * SS), joint="curve")
        else:
            d.rounded_rectangle([c - 3.2 * SS, c - 15 * SS, c + 3.2 * SS, c + 3 * SS], radius=3 * SS, fill=255)
            d.ellipse([c - 4 * SS, c + 8 * SS, c + 4 * SS, c + 16 * SS], fill=255)
        return {"glow": glow, "hex_a": hex_a, "hex_b": hex_b, "glyph": verkleinere(gl),
                "ca": Image.new("RGBA", (LP, LP), c1 + (255,)),
                "cb": Image.new("RGBA", (LP, LP), c2 + (255,)),
                "cg": Image.new("RGBA", (LP, LP), (255, 255, 255, 255)), "L": LP}

    def _kopf(self):
        L = 48
        LS = L * SS
        a = self.farben["run"][0]
        img = Image.new("RGBA", (LS, LS), (0, 0, 0, 0))
        auf_ebene(img, lambda d: d.ellipse([LS / 2 - 15 * SS, LS / 2 - 15 * SS, LS / 2 + 15 * SS, LS / 2 + 15 * SS],
                                           fill=a + (190,)), blur=4 * SS)
        auf_ebene(img, lambda d: d.ellipse([LS / 2 - 5 * SS, LS / 2 - 5 * SS, LS / 2 + 5 * SS, LS / 2 + 5 * SS],
                                           fill=(255, 255, 255, 255)))
        return img.resize((P(L), P(L)), Image.LANCZOS)

    def halo_fuer(self, puls):
        i = int(round((puls - 0.30) / 0.70 * 15))
        return self.halo_stufen[max(0, min(15, i))]

    def hex_masken(self, key, w_hex):
        """Gedrehte Sechseck-Masken in 3°-Schritten (gecacht statt pro Frame neu gedreht)."""
        emb = self.emb[key]
        ka = int((w_hex % 360) // 3) % 120
        kb = int(((w_hex * 1.6) % 360) // 3) % 120
        ma = self._hex_cache.get((key, "a", ka))
        if ma is None:
            ma = self._hex_cache[(key, "a", ka)] = verkleinere(emb["hex_a"].rotate(-ka * 3, resample=Image.BILINEAR))
        mb = self._hex_cache.get((key, "b", kb))
        if mb is None:
            mb = self._hex_cache[(key, "b", kb)] = verkleinere(emb["hex_b"].rotate(kb * 3, resample=Image.BILINEAR))
        return ma, mb

    def fortschritt(self, frac):
        schluessel = int(min(frac, 0.9999) * 240)
        if schluessel in self._prog_cache:
            return self._prog_cache[schluessel]
        if len(self._prog_cache) > 120:
            self._prog_cache.clear()
        frac = schluessel / 240.0
        N = 340 * SS
        pie = Image.new("L", (N, N), 0)
        ImageDraw.Draw(pie).pieslice([0, 0, N - 1, N - 1], -90, -90 + 360 * min(frac, 0.9999), fill=255)
        maske = verkleinere(ImageChops.multiply(self.prog_ss, pie))
        glow = ImageChops.multiply(self.prog_glow,
                                   verkleinere(pie).filter(ImageFilter.GaussianBlur(5 * SKALA))).point(lambda v: int(v * 0.8))
        self._prog_cache[schluessel] = (maske, glow)
        return maske, glow

    def radar_maske(self, winkel):
        k = int(winkel // 3) % 120
        if SKALA != 1.0:
            # bei hoher Skalierung das fertig verkleinerte Bild drehen: schnell und ohne großen Zwischenspeicher
            if self._radar_klein is None:
                self._radar_klein = verkleinere(self.radar)
            return self._radar_klein.rotate(k * 3, resample=Image.BILINEAR)
        m = self._radar_cache.get(k)
        if m is None:
            m = self._radar_cache[k] = verkleinere(self.radar.rotate(k * 3, resample=Image.BILINEAR))
        return m

    def kategorien_bogen(self, index, gesamt):
        if (index, gesamt) in self._bogen_cache:
            return self._bogen_cache[(index, gesamt)]
        N = 340 * SS
        m = Image.new("L", (N, N), 0)
        d = ImageDraw.Draw(m)
        winkel_pro_segment = 360 / max(1, gesamt)
        start_w = index * winkel_pro_segment - 90
        end_w = start_w + winkel_pro_segment - 2
        c = N / 2
        R = 157 * SS
        d.arc([c - R, c - R, c + R, c + R], start_w, end_w, fill=255, width=int(3 * SS))
        self._bogen_cache[(index, gesamt)] = verkleinere(m)
        return self._bogen_cache[(index, gesamt)]

    def hover_welle(self, radius):
        schluessel = int(radius // 2)
        if schluessel in self._welle_cache:
            return self._welle_cache[schluessel]
        radius = schluessel * 2
        N = 340 * SS
        m = Image.new("L", (N, N), 0)
        d = ImageDraw.Draw(m)
        c = N / 2
        r = radius * SS
        d.ellipse([c - r, c - r, c + r, c + r], outline=255, width=int(4 * SS))
        self._welle_cache[schluessel] = verkleinere(m).filter(ImageFilter.GaussianBlur(4 * SKALA))
        return self._welle_cache[schluessel]


@dataclass
class BildDaten:
    """Alles, was zeichne() für ein Bild braucht (Zeit- und Winkelwerte berechnet KreisApp._tick)."""
    zustand: str
    hover: bool
    mini: bool
    key: str
    kat: str
    ekey: str
    bogen_i: int | None
    bogen_n: int
    w_ticks: float
    w_radar: float
    w_hex: float
    welle_radius: float
    prog: float
    t_fertig: float         # Sekunden seit "fertig"
    t_lauf: float           # Sekunden seit Programmstart (jetzt - t0)


def zeichne(g, d):
    """Ein Bild des Kreises (RGB, inklusive Kreismaske bzw. Mini-Skalierung)."""
    farbe = g.conic[d.key]
    rahmen = (g.idle[d.kat] if d.zustand in ("bereit", "wahl") else g.plain).copy()

    puls_faktor = 5.2 if d.zustand == "laeuft" else 2.6
    puls = 0.65 + 0.35 * math.sin(d.t_lauf * puls_faktor)
    rahmen.paste(farbe, (0, 0), g.halo_fuer(puls))

    rahmen.paste(farbe, (0, 0), g.spur)
    rahmen.paste(farbe, (0, 0), g.ticks[int((d.w_ticks % 15) / 0.5) % 30])
    rahmen.paste(farbe, (0, 0), g.radar_maske(d.w_radar))

    if d.hover:
        welle_maske = g.hover_welle(d.welle_radius)
        rahmen.paste(farbe, (0, 0), welle_maske)

    if d.bogen_i is not None:
        try:
            bogen_maske = g.kategorien_bogen(d.bogen_i, d.bogen_n)
            rahmen.paste(farbe, (0, 0), bogen_maske)
        except Exception:
            pass

    M = 170
    if d.zustand == "laeuft" and d.prog > 0.002:
        maske, glow = g.fortschritt(d.prog)
        rahmen.paste(farbe, (0, 0), glow)
        rahmen.paste(farbe, (0, 0), maske)
        a = math.radians(-90 + 360 * min(d.prog, 0.9999))
        kx, ky = M + 147 * math.cos(a), M + 147 * math.sin(a)
        rahmen.alpha_composite(g.kopf, dest=(int(kx * SKALA - g.kopf.width / 2), int(ky * SKALA - g.kopf.height / 2)))

    if d.zustand == "fertig":
        t = d.t_fertig
        if t < 1.2:
            rad = 20 + t / 1.2 * 150
            m = Image.new("L", (340 * SS, 340 * SS), 0)
            ImageDraw.Draw(m).ellipse([(340 * SS) / 2 - rad * SS, (340 * SS) / 2 - rad * SS, (340 * SS) / 2 + rad * SS, (340 * SS) / 2 + rad * SS],
                                      outline=int(230 * (1 - t / 1.2)), width=int(3 * SS))
            rahmen.paste(farbe, (0, 0), verkleinere(m))

    emb = g.emb[d.ekey]
    cy = (104 if d.zustand == "fertig" else 118) if d.zustand not in ("bereit", "wahl") else 118 + math.sin(d.t_lauf * (7 if d.hover else 2.2)) * (6 if d.hover else 2.5)
    L = emb["L"]
    ex, ey = int(M * SKALA - L / 2), int(cy * SKALA - L / 2)
    if d.zustand != "laeuft":
        rahmen.alpha_composite(emb["glow"], dest=(ex, ey))
        ma, mb = g.hex_masken(d.ekey, d.w_hex)
        rahmen.paste(emb["ca"], (ex, ey), ma)
        rahmen.paste(emb["cb"], (ex, ey), mb)
        rahmen.paste(emb["cg"], (ex, ey), emb["glyph"])

    out_img = rahmen.convert("RGB")
    if d.mini:
        out_img = out_img.resize((P(S_MINI), P(S_MINI)), Image.LANCZOS)
        out_img = Image.composite(out_img, g.trans_mini, g.schnitt_mini)
        out_img.paste((150, 170, 175), (0, 0), g.kante_mini)        # helle Metallkante
    else:
        out_img = Image.composite(out_img, g.trans_gross, g.schnitt)
    return out_img
