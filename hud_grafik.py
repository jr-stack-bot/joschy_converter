"""
HUD-Grafik des Kreis-Konverters: Konstanten, Farben/Themes, Masken und das Zeichnen eines Bildes.
© JOSCHY – Lizenz: AGPL-3.0

Ausgelagert aus dem Hauptprogramm (ohne Verhaltensänderung). Dieses Modul importiert nie das Hauptprogramm.
SKALA und SS ändern sich zur Laufzeit (setze_skalierung) - von außen immer als hud_grafik.SKALA/.SS lesen.
"""
from __future__ import annotations

import math
import random
import threading
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

# Zierringe (B3): (radius, linie_px, deckkraft, periode_grad, bilder, grad_pro_s), alles in logischen Pixeln.
# Jede Symmetrieperiode liegt als Bildfolge mit 0,625° Schritt vor; der Tick-Ring ist der vierte Ring.
RINGE = {"A": (136, 2.0, 110, 15.0, 24, +18.0),     # 24 Bögen à 9°
         "B": (127, 1.5, 80, 10.0, 16, -12.0),      # 36 radiale Striche (r-4 … r+4)
         "C": (118, 3.0, 60, 30.0, 48, +7.0)}       # 12 Bögen à 14°
RING_SCHRITT = 0.625
GLOW_SPARSAM = 10          # feste Glow-Stufe bei "sparsam"

# Partikel (B3): Sprite-Atlas mit 4 Größen (logische px) x 4 Helligkeiten (Alpha)
PARTIKEL_GROESSEN = (3, 5, 8, 12)
PARTIKEL_ALPHA = (64, 128, 192, 255)
UEBERGANG_S = 0.3          # Dauer eines weichen Zustandsübergangs


def ease(t):
    """Smoothstep (ease-in-out), auf [0, 1] begrenzt."""
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


class Partikel:
    """Teilchen, die auf r = 60…150 um die Mitte kreisen (logische px), mit Ein- und Ausblenden."""

    def __init__(self, rng=None):
        self.rng = rng or random.Random()
        self._teile = []            # [winkel_grad, r, omega_grad_s, alter, leben, groesse_i]

    def schritt(self, dt, max_n):
        rest = []
        for p in self._teile:
            p[3] += dt
            if p[3] < p[4]:
                p[0] = (p[0] + p[2] * dt) % 360
                rest.append(p)
        self._teile = rest
        if len(rest) < max_n:                     # höchstens ein neues Teilchen je Schritt
            rng = self.rng
            omega = rng.uniform(4.0, 15.0) * rng.choice((-1, 1))
            rest.append([rng.uniform(0, 360), rng.uniform(60.0, 150.0), omega, 0.0,
                         rng.uniform(2.0, 5.0), rng.randrange(4)])

    @staticmethod
    def _hell(alter, leben):
        f = alter / leben
        h = 3.0 * min(1.0, f / 0.25, (1.0 - f) / 0.25)
        return max(0, min(3, int(round(h))))

    def liste(self):
        aus = []
        for w, r, _, alter, leben, gi in self._teile:
            a = math.radians(w)
            aus.append((170 + r * math.cos(a), 170 + r * math.sin(a), gi, self._hell(alter, leben)))
        return tuple(aus)


STUFEN = ("voll", "sparsam", "aus")
BUDGET_MS = 15.0           # Median-Zeichenzeit, ab der eine Stufe tiefer gezeichnet wird
BUDGET_FENSTER = 30        # Bilder je Messfenster (und Bilder Aufwärmphase, die nicht zählen)
BUDGET_FENSTER_FOLGE = 2   # so viele volle Fenster in Folge müssen über BUDGET_MS liegen


class Zeitbudget:
    """Zeichenzeit-Budget: Median über Fenster von 30 Bildern, interne Abstufung der Effekte.

    - Nach Start und nach jedem leeren() (Ring-/Glow-Neubau, Themen-/Stufenwechsel, Pause) zählen die ersten
      30 Bilder nicht (Aufwärmphase).
    - Liegt der Median zweier aufeinanderfolgender voller Fenster über 15 ms, wird eine Stufe tiefer gezeichnet.
    - Kein automatisches Hochstufen (Sperre gegen Schwingen); erst freigeben() (manuelle Wahl im Menü)
      hebt die Abstufung auf. Die gespeicherte Einstellung bleibt unberührt.
    """

    def __init__(self):
        self.mittel = None          # Median des zuletzt vollen Fensters (ms)
        self.runter = 0             # Stufen unterhalb der gewünschten
        self._wunsch = "voll"       # zuletzt an stufe() übergeben (begrenzt die Abstufung auf "aus")
        self.leeren()

    def leeren(self):
        """Fenster leeren und Aufwärmphase neu beginnen."""
        self._aufwaermen = BUDGET_FENSTER
        self._fenster = []
        self._ueber = 0             # volle Fenster in Folge mit Median > BUDGET_MS

    def freigeben(self):
        """Manuelle Wahl: interne Abstufung aufheben und neu messen."""
        self.runter = 0
        self.mittel = None
        self.leeren()

    def melde(self, ms, jetzt=None):
        """Meldet die Zeichenzeit eines Bildes. True, wenn sich die interne Abstufung geändert hat."""
        if self._aufwaermen > 0:
            self._aufwaermen -= 1
            return False
        self._fenster.append(ms)
        if len(self._fenster) < BUDGET_FENSTER:
            return False
        s = sorted(self._fenster)
        n = len(s)
        self.mittel = s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2
        self._fenster = []
        self._ueber = self._ueber + 1 if self.mittel > BUDGET_MS else 0
        if self._ueber < BUDGET_FENSTER_FOLGE:
            return False
        self._ueber = 0
        if self.runter < len(STUFEN) - 1 - STUFEN.index(self._wunsch):
            self.runter += 1
            self.leeren()           # Stufenwechsel: neu aufwärmen
            return True
        return False

    def stufe(self, gewuenscht):
        """Effektive Stufe: die gewünschte, um die interne Abstufung tiefer (höchstens bis "aus")."""
        if gewuenscht not in STUFEN:
            gewuenscht = "voll"
        self._wunsch = gewuenscht
        i = STUFEN.index(gewuenscht)
        return STUFEN[min(len(STUFEN) - 1, i + self.runter)]


class Messung:
    """Messmodus (--messen): sammelt Zeichenzeiten je Zustand; nach `dauer` Sekunden einmal fällig."""

    def __init__(self, dauer=60.0):
        self.dauer = dauer
        self.start = None           # beim ersten add/faellig gesetzt
        self.werte = {}             # zustand -> [ms]
        self._gemeldet = False

    def add(self, zustand, ms, jetzt):
        if self.start is None:
            self.start = jetzt
        self.werte.setdefault(zustand, []).append(ms)

    def faellig(self, jetzt):
        """Genau einmal True, ab start + dauer."""
        if self.start is None:
            self.start = jetzt
        if self._gemeldet or jetzt < self.start + self.dauer:
            return False
        self._gemeldet = True
        return True

    def bericht(self):
        zeilen = []
        for zustand, liste in self.werte.items():
            s = sorted(liste)
            n = len(s)
            p95 = s[math.ceil(0.95 * n) - 1]
            zeilen.append(f"messen {zustand}: mittel {sum(s) / n:.1f} ms, p95 {p95:.1f} ms, n={n}")
        return "\n".join(zeilen)


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
        # Zierringe und Glow (B3) entstehen erst bei Bedarf im Hintergrund (Effekte != "aus"), bis dahin None.
        # Bei "aus" kosten sie weder Speicher noch Startzeit.
        self.ringe = None           # {"A": [Maske, ...], ...}, zugeschnitten auf b3_box
        self.glow = None            # {("ABC", stufe): Maske, ("AB", GLOW_SPARSAM): Maske}, zugeschnitten auf b3_box
        self.b3_box = None          # gemeinsamer Ausschnitt (links, oben, rechts, unten) in echten Pixeln
        self._ringe_thread = None
        self._ringe_lock = threading.Lock()
        self._ringe_gen = 0         # erhöht bei jeder Freigabe; ein veralteter Bau-Thread verwirft sein Ergebnis
        self._b3_farbe = None       # (farbe, box, Ausschnitt) - Cache für den zugeschnittenen Farbverlauf
        self._atlas = None          # Partikel-Atlas, erst beim ersten Partikel gebaut (bei "aus" nie)
        self._atlas_boxen = None
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
        self.kopf = self._kopf()            # _hex_cache bleibt: die Sechseck-Masken sind farblos
        self.core_ss = self._core(theme_name)
        self.plain = verkleinere(self.core_ss)
        self.idle = _Lazy(lambda k: verkleinere(self._pille(k)))
        self._bogen_cache.clear()
        if self._atlas is not None:                   # Partikel in der neuen Designfarbe
            self._atlas_bauen()

    @property
    def atlas(self):
        """Sprite-Atlas (RGBA) der Partikel: Spalten = Größen, Zeilen = Helligkeiten."""
        if self._atlas is None:
            self._atlas_bauen()
        return self._atlas

    def atlas_box(self, groesse_i, hell_i):
        if self._atlas_boxen is None:
            self._atlas_bauen()
        return self._atlas_boxen[groesse_i][hell_i]

    def _atlas_bauen(self):
        farbe = hexrgb(theme_daten(self.akt_theme)["CYAN"])
        seiten = [max(2, P(s)) for s in PARTIKEL_GROESSEN]
        breite, hoehe = sum(seiten) + len(seiten) - 1, sum([seiten[-1]] * 4) + 3
        alpha = Image.new("L", (breite, hoehe), 0)
        boxen = [[None] * 4 for _ in seiten]
        x = 0
        for gi, w in enumerate(seiten):
            k = 8                                       # weicher Punkt: überabgetastet, geblurt, verkleinert
            m = Image.new("L", (w * k, w * k), 0)
            ImageDraw.Draw(m).ellipse([w * k * 0.22, w * k * 0.22, w * k * 0.78, w * k * 0.78], fill=255)
            m = m.filter(ImageFilter.GaussianBlur(w * k * 0.12)).resize((w, w), Image.LANCZOS)
            hoch = m.getextrema()[1] or 1
            for hi, a in enumerate(PARTIKEL_ALPHA):
                y = hi * (seiten[-1] + 1)
                alpha.paste(m.point(lambda v, f=a / hoch: min(255, int(v * f + 0.5))), (x, y))
                boxen[gi][hi] = (x, y, x + w, y + w)
            x += w + 1
        atlas = Image.new("RGBA", (breite, hoehe), farbe + (0,))
        atlas.putalpha(alpha)
        self._atlas, self._atlas_boxen = atlas, boxen

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

    @staticmethod
    def _ring_bild(name, k):
        """Bild k eines Zierrings (um k·0,625° versetzt), direkt gezeichnet und danach verkleinert."""
        radius, linie, deckkraft, periode, _, _ = RINGE[name]
        N = 340 * SS
        c = N / 2
        m = Image.new("L", (N, N), 0)
        d = ImageDraw.Draw(m)
        versatz = k * RING_SCHRITT - 90
        breite = max(1, int(linie * SS))
        r = radius * SS
        box = [c - r, c - r, c + r, c + r]
        if name == "A":
            for i in range(24):
                a0 = i * 15 + versatz
                d.arc(box, a0, a0 + 9, fill=deckkraft, width=breite)
        elif name == "B":
            for i in range(36):
                a = i * 10 + versatz
                d.line([polar(c, (radius - 4) * SS, a), polar(c, (radius + 4) * SS, a)], fill=deckkraft, width=breite)
        else:
            for i in range(12):
                a0 = i * 30 + versatz
                d.arc(box, a0, a0 + 14, fill=deckkraft, width=breite)
        return verkleinere(m)

    def ringe_bauen(self):
        """Ringe und Glow erzeugen (synchron). Gesetzt wird erst am Ende (glow, b3_box, zuletzt ringe).

        Gehalten werden nur die kombinierten Glow-Masken (16 Stufen A+B+C für "voll", Stufe 10 A+B für
        "sparsam"); die Einzelstufen sind danach frei. Alle Masken werden verlustfrei auf den gemeinsamen
        Ausschnitt b3_box zugeschnitten (außerhalb ist alles 0) - so bleibt B3 unter 25/45 MB bei 150/200 %.
        """
        with self._ringe_lock:
            gen = self._ringe_gen
        einzeln = {name: self._glow(name) for name in RINGE}
        glow = {}
        for i in range(16):
            glow[("ABC", i)] = ImageChops.screen(ImageChops.screen(einzeln["A"][i], einzeln["B"][i]), einzeln["C"][i])
        glow[("AB", GLOW_SPARSAM)] = ImageChops.screen(einzeln["A"][GLOW_SPARSAM], einzeln["B"][GLOW_SPARSAM])
        del einzeln
        box = glow[("ABC", 15)].getbbox()                      # hellste Stufe = größte Ausdehnung
        glow = {k: m.crop(box) for k, m in glow.items()}
        ringe = {}
        for name, werte in RINGE.items():
            folge = []
            for k in range(werte[4]):
                m = self._ring_bild(name, k)
                bb = m.getbbox()
                if bb and not (bb[0] >= box[0] and bb[1] >= box[1] and bb[2] <= box[2] and bb[3] <= box[3]):
                    raise ValueError(f"Ring {name} ragt über den Glow-Ausschnitt hinaus")
                folge.append(m.crop(box))
            ringe[name] = folge
        # Caches füllen, bevor die Ringe erscheinen: das Zeitbudget wärmt mit den Ringen neu auf und misst
        # danach nur noch Bilder ohne Cache-Fehlgriffe (siehe vorwaermen).
        self.vorwaermen(lambda: gen != self._ringe_gen)
        with self._ringe_lock:
            if gen != self._ringe_gen:                          # inzwischen freigegeben: verwerfen
                return
            self.glow, self.b3_box = glow, box
            self.ringe = ringe

    def ringe_starten(self):
        """ringe_bauen in einem Daemon-Thread starten (höchstens einmal, nach ringe_freigeben wieder möglich)."""
        with self._ringe_lock:
            if self._ringe_thread is not None or self.ringe is not None:
                return
            self._ringe_thread = threading.Thread(target=self.ringe_bauen, name="hud-ringe", daemon=True)
            thread = self._ringe_thread
        thread.start()

    def ringe_freigeben(self):
        """Effekte "aus": Ringe und Glow freigeben; ein laufender Bau verwirft sein Ergebnis.
        Nur aus dem Zeichen-Thread aufrufen (zeichne liest die Felder ohne Sperre)."""
        with self._ringe_lock:
            self._ringe_gen += 1
            self.ringe = None
            self.glow = None
            self.b3_box = None
            self._ringe_thread = None
            self._b3_farbe = None
            self._atlas = None
            self._atlas_boxen = None

    def ringe_bytes(self):
        """Speicher aller B3-Daten in Bytes: Ringe, Glow-Masken, Farb-Ausschnitt und Partikel-Atlas.
        Übergänge halten nichts dauerhaft (Mischbilder leben nur während eines Bildes)."""
        bilder = [b for folge in (self.ringe or {}).values() for b in folge] + list((self.glow or {}).values())
        if self._b3_farbe is not None:
            bilder.append(self._b3_farbe[2])
        if self._atlas is not None:
            bilder.append(self._atlas)
        return sum(b.width * b.height * len(b.getbands()) for b in bilder)

    def ring_maske(self, name, winkel):
        _, _, _, periode, bilder, _ = RINGE[name]
        return self.ringe[name][int((winkel % periode) / RING_SCHRITT) % bilder]

    @staticmethod
    def _glow(name):
        """16 Helligkeitsstufen des weichgezeichneten Kreisrings unter einem Zierring (drehungsfrei)."""
        radius, linie, deckkraft = RINGE[name][:3]
        basis = verkleinere(ring_maske(radius - linie / 2, radius + linie / 2)).filter(ImageFilter.GaussianBlur(5 * SKALA))
        return [basis.point(lambda v, k=(0.30 + 0.70 * i / 15) * deckkraft / 255: int(v * k)) for i in range(16)]

    @staticmethod
    def glow_index(puls):
        i = int(round((puls - 0.30) / 0.70 * 15))
        return max(0, min(15, i))

    def glow_kombi(self, namen, i):
        """Glow mehrerer Ringe in Stufe i als eine Maske (screen = wie nacheinander in derselben Farbe eingefügt)."""
        return self.glow[(namen, i)]

    def farbe_b3(self, farbe):
        """Farbverlauf, auf b3_box zugeschnitten (einfacher Cache, wechselt nur mit key/Theme)."""
        c = self._b3_farbe
        if c is None or c[0] is not farbe or c[1] != self.b3_box:
            c = self._b3_farbe = (farbe, self.b3_box, farbe.crop(self.b3_box))
        return c[2]

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

    @staticmethod
    def _hex_formen():
        """Farblose Sechseck-Ringe des Emblems (überabgetastet), für alle keys und Themes gleich."""
        LS = 124 * SS
        c = LS / 2

        def box(r):
            return [c - r * SS, c - r * SS, c + r * SS, c + r * SS]

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
        return hex_a, hex_b

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

        hex_a, hex_b = self._hex_formen()

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
        """Gedrehte Sechseck-Masken in 3°-Schritten (gecacht statt pro Frame neu gedreht).
        hex_a/hex_b sind für alle keys und Themes gleich (farblos): ein gemeinsamer Cache für alle."""
        ka = int((w_hex % 360) // 3) % 120
        kb = int(((w_hex * 1.6) % 360) // 3) % 120
        ma = self._hex_cache.get(("a", ka))
        if ma is None:
            ma = self._hex_cache[("a", ka)] = self._hex_drehen(self.emb[key]["hex_a"], -ka * 3)
        mb = self._hex_cache.get(("b", kb))
        if mb is None:
            mb = self._hex_cache[("b", kb)] = self._hex_drehen(self.emb[key]["hex_b"], kb * 3)
        return ma, mb

    @staticmethod
    def _hex_drehen(maske, grad):
        return verkleinere(maske.rotate(grad, resample=Image.BILINEAR))

    def _radar_drehen(self, k):
        return verkleinere(self.radar.rotate(k * 3, resample=Image.BILINEAR))

    def vorwaermen(self, abbruch=None):
        """Nur bei 100 %: Radar-, Sechseck- und Hover-Wellen-Cache vollständig füllen (im Ringe-Thread).

        Ohne das füllen sich diese Caches erst in den ersten 10-16 s, und jedes fehlende Bild kostet
        1,5-5,6 ms (Drehen/Weichzeichnen in Überabtastung). Genau in diese Zeit fallen die Messfenster
        des Zeitbudgets (B5) nach dem Ringe-Bau: "voll" wurde dadurch zu teuer gemessen. Die Bilder sind
        dieselben, die zeichne() sonst selbst erzeugt hätte (bitgleich); Speicher wie nach 16 s Laufzeit.
        Bei höherer Skalierung (keine Radar-Bildfolge, B3-Speichergrenze) passiert nichts.
        abbruch(): True -> sofort aufhören (Ringe inzwischen freigegeben)."""
        if SKALA != 1.0:
            return
        abbruch = abbruch or (lambda: False)
        hex_a, hex_b = self._hex_formen()        # eigene Masken: kein Zugriff auf emb aus diesem Thread
        for k in range(120):
            if abbruch():
                return
            if k not in self._radar_cache:
                self._radar_cache[k] = self._radar_drehen(k)
            if ("a", k) not in self._hex_cache:
                self._hex_cache[("a", k)] = self._hex_drehen(hex_a, -k * 3)
            if ("b", k) not in self._hex_cache:
                self._hex_cache[("b", k)] = self._hex_drehen(hex_b, k * 3)
        for schluessel in range(20, 76):          # hover_welle: radius 40…150 -> radius // 2
            if abbruch():
                return
            self.hover_welle(schluessel * 2)

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
            m = self._radar_cache[k] = self._radar_drehen(k)
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
    stufe: str = "aus"      # Effekt-Stufe: "voll" | "sparsam" | "aus"
    w_ringe: tuple[float, float, float] = (0.0, 0.0, 0.0)   # Winkel der Zierringe A, B, C
    partikel: tuple = ()                # ((x_log, y_log, groesse_i, hell_i), ...)
    alt_key: str | None = None          # Übergang: vorheriger key ...
    alt_basis: str | None = None        # ... und vorheriges Grundbild (Kategorie oder "plain")
    ueb: float = 1.0                    # Anteil des neuen Bildes (geglättet), 1 = kein Übergang


def _basis_id(zustand, kat):
    return kat if zustand in ("bereit", "wahl") else "plain"


def _basis_bild(g, basis):
    return g.plain if basis == "plain" else g.idle[basis]


def zeichne(g, d):
    """Ein Bild des Kreises (RGB, inklusive Kreismaske bzw. Mini-Skalierung)."""
    farbe = g.conic[d.key]
    basis = _basis_id(d.zustand, d.kat)
    gemischt = False
    if d.stufe != "aus" and d.alt_key is not None and d.ueb < 1.0:
        # weicher Übergang: Farbe (und ggf. Grundbild) aus altem und neuem Zustand mischen
        if d.alt_key != d.key:
            farbe = Image.blend(g.conic[d.alt_key], farbe, d.ueb)
            gemischt = True
        if d.alt_basis is not None and d.alt_basis != basis:
            rahmen = Image.blend(_basis_bild(g, d.alt_basis), _basis_bild(g, basis), d.ueb)
        else:
            rahmen = _basis_bild(g, basis).copy()
    else:
        rahmen = _basis_bild(g, basis).copy()

    puls_faktor = 5.2 if d.zustand == "laeuft" else 2.6
    puls = 0.65 + 0.35 * math.sin(d.t_lauf * puls_faktor)
    rahmen.paste(farbe, (0, 0), g.halo_fuer(puls))

    rahmen.paste(farbe, (0, 0), g.spur)
    rahmen.paste(farbe, (0, 0), g.ticks[int((d.w_ticks % 15) / 0.5) % 30])
    if d.stufe != "aus" and g.ringe is not None:
        # Zierringe und Glow in derselben Farbe: Masken erst vereinen, dann nur einmal einfügen (spart Zeit).
        # Die Ringe überlappen sich nicht (lighter ist exakt); Glow kommt per screen dazu.
        namen = "ABC" if d.stufe == "voll" else "AB"
        maske = g.ring_maske(namen[0], d.w_ringe[0])
        for i in range(1, len(namen)):
            maske = ImageChops.lighter(maske, g.ring_maske(namen[i], d.w_ringe[i]))
        maske = ImageChops.screen(maske, g.glow_kombi(namen, g.glow_index(puls) if d.stufe == "voll" else GLOW_SPARSAM))
        # Während eines Übergangs ist farbe jedes Bild neu: nur zuschneiden, nicht cachen (hält keinen Speicher)
        rahmen.paste(farbe.crop(g.b3_box) if gemischt else g.farbe_b3(farbe), g.b3_box[:2], maske)
    if d.stufe == "voll" and not d.mini and d.partikel:
        atlas = g.atlas
        for x, y, gi, hi in d.partikel:
            box = g.atlas_box(gi, hi)
            w, h = box[2] - box[0], box[3] - box[1]
            rahmen.alpha_composite(atlas, dest=(P(x) - w // 2, P(y) - h // 2), source=box)
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
