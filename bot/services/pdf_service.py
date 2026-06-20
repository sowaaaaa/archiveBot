import io
import os
from PIL import Image, ImageDraw, ImageFont
import fitz

BG_PATH = "assets/result_bg.jpg"


def _load_font(size: int):
    candidates = [
        "assets/fonts/Cormorant-VariableFont_wght.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _fsize(font) -> int:
    return getattr(font, "size", 20)


OVERLAY_ALPHA = 165
SCALE = 2             # коэффициент масштабирования фона
TOP_PAD = 130 * SCALE
SIDE_PAD = 90 * SCALE
BOT_PAD = 120 * SCALE


class _Renderer:
    LINE_SPACING = 1.55

    C_GOLD = (220, 175, 75)
    C_TEXT = (240, 228, 210)
    C_DIM = (170, 158, 138)
    C_HEADER = (220, 190, 110)

    def __init__(self):
        bg_raw = Image.open(BG_PATH).convert("RGBA")
        # Масштабируем до 2x для высокого качества текста
        self.bg = bg_raw.resize((bg_raw.width * 2, bg_raw.height * 2), Image.LANCZOS)
        self.W, self.H = self.bg.size
        self.TW = self.W - SIDE_PAD * 2

        self.f_title = _load_font(76)
        self.f_header = _load_font(52)
        self.f_body = _load_font(42)
        self.f_small = _load_font(34)

        self.pages: list[Image.Image] = []
        self._new_page()

    def _new_page(self):
        self.img = self.bg.copy().convert("RGB")
        self.draw = ImageDraw.Draw(self.img)
        self.y = TOP_PAD

    def _commit(self):
        self.pages.append(self.img)
        self._new_page()

    def _overflow(self, h: int) -> bool:
        return self.y + h > self.H - BOT_PAD

    def _draw(self, x: int, y: int, text: str, font, color):
        self.draw.text((x, y), text, font=font, fill=color)

    # ── Public primitives ─────────────────────────────────────────────────────

    def header(self, text: str, font=None, color=None):
        font = font or self.f_header
        color = color or self.C_HEADER
        lh = int(_fsize(font) * self.LINE_SPACING)
        if self._overflow(lh + 24):
            self._commit()
        # Линия сверху
        self.draw.line([(SIDE_PAD, self.y), (self.W - SIDE_PAD, self.y)],
                       fill=self.C_GOLD, width=1)
        self.y += 10
        self._draw(SIDE_PAD, self.y, text, font, color)
        self.y += lh
        # Линия снизу
        self.draw.line([(SIDE_PAD, self.y), (self.W - SIDE_PAD, self.y)],
                       fill=self.C_GOLD, width=1)
        self.y += 12

    def space(self, px: int = 14):
        self.y += px
        if self._overflow(0):
            self._commit()

    def divider(self):
        if self._overflow(30):
            self._commit()
        self.y += 8
        self.draw.line(
            [(SIDE_PAD, self.y), (self.W - SIDE_PAD, self.y)],
            fill=self.C_DIM, width=1,
        )
        self.y += 18

    def line(self, text: str, font, color, indent: int = 0):
        if not text.strip():
            self.y += int(_fsize(font) * self.LINE_SPACING * 0.5)
            if self._overflow(0):
                self._commit()
            return

        lh = int(_fsize(font) * self.LINE_SPACING)
        max_w = self.TW - indent
        words = text.split()
        buf = ""

        for word in words:
            candidate = (buf + " " + word).strip()
            bx = self.draw.textbbox((0, 0), candidate, font=font)
            if bx[2] - bx[0] <= max_w:
                buf = candidate
            else:
                if buf:
                    if self._overflow(lh):
                        self._commit()
                    self._draw(SIDE_PAD + indent, self.y, buf, font, color)
                    self.y += lh
                buf = word

        if buf:
            if self._overflow(lh):
                self._commit()
            self._draw(SIDE_PAD + indent, self.y, buf, font, color)
            self.y += lh

    def criterion(self, label: str, value: str, font=None):
        """Метка золотом, значение на следующей строке с отступом."""
        font = font or self.f_body
        lh = int(_fsize(font) * self.LINE_SPACING)
        indent = 30

        # Метка
        if self._overflow(lh):
            self._commit()
        self._draw(SIDE_PAD, self.y, label, font, self.C_GOLD)
        self.y += lh

        # Значение с переносом
        self.line(value, font, self.C_TEXT, indent=indent)

    def finish(self) -> list[Image.Image]:
        self.pages.append(self.img)
        return self.pages


def generate_result_pdf(data: dict, lang: str = "ru") -> bytes:
    from bot.i18n import t

    if not os.path.exists(BG_PATH):
        raise FileNotFoundError(f"Background not found: {BG_PATH}")

    r = _Renderer()

    primary = data.get("primary_type", {})
    secondary = data.get("secondary_types", [])
    confidence = data.get("confidence", 75)
    chronicle = data.get("chronicle_number", "I-I")
    criteria = data.get("criteria", {})
    race_type = data.get("race_type", "")
    ethnicity = data.get("ethnicity_note", "")
    gothic_desc = data.get("gothic_description", "")

    def _c(key: str) -> str:
        v = criteria.get(key, "")
        return v if v and v not in ("—", "неизвестно", "не указано", "unknown", "not specified") else ""

    ru = lang == "ru"
    chronicle_label = "ХРОНИКА" if ru else "CHRONICLE"

    # ── Заголовок ─────────────────────────────────────────────────────────────
    r.header(f"{chronicle_label}  #{chronicle}", font=r.f_title, color=r.C_GOLD)
    r.space(8)
    r.divider()

    disclaimer = (
        "Расовый тип определяется визуально — возможны погрешности. "
        "Разница между типами составляет всего 1–3 мм."
        if ru else
        "Racial type is determined visually — errors possible. "
        "The difference between types is only 1–3 mm."
    )
    r.line(disclaimer, r.f_small, r.C_DIM)
    r.space(8)
    r.divider()

    if ethnicity:
        r.line(f"{'Этничность' if ru else 'Ethnicity'}:  {ethnicity}", r.f_body, r.C_TEXT)
    if race_type:
        r.line(f"{'Расовый тип' if ru else 'Racial type'}:  {race_type}", r.f_body, r.C_TEXT)

    r.space(10)

    if gothic_desc:
        r.line(gothic_desc, r.f_body, r.C_TEXT)
        r.space(10)

    r.divider()

    # ── Происхождение ─────────────────────────────────────────────────────────
    r.header(f"[ {'ПРОИСХОЖДЕНИЕ' if ru else 'ORIGIN'} ]")
    r.space(8)

    pn = primary.get("name", "—")
    ps = primary.get("similarity", 0)
    sim_lbl = "Сходство" if ru else "Similarity"
    r.line(f"{'Основной тип' if ru else 'Primary type'}:  {pn}   {sim_lbl}: {ps}%",
           r.f_body, r.C_TEXT)

    if secondary:
        sec_lbl = "Дополнительные примеси" if ru else "Secondary admixtures"
        r.line(f"{sec_lbl}:", r.f_body, r.C_TEXT)
        for s in secondary[:2]:
            r.line(f"  •  {s['name']} — {s['similarity']}%", r.f_body, r.C_TEXT, indent=20)

    r.space(10)
    filled = round(confidence / 100 * 10)
    bar = "█" * filled + "░" * (10 - filled)
    conf_lbl = "Уверенность" if ru else "Confidence"
    r.line(f"{conf_lbl}:  {bar}  {confidence}%", r.f_body, r.C_GOLD)
    r.space(14)
    r.divider()

    # ── Морфологический разбор ────────────────────────────────────────────────
    morph_lbl = "МОРФОЛОГИЧЕСКИЙ РАЗБОР" if ru else "MORPHOLOGICAL BREAKDOWN"
    r.header(f"[ {morph_lbl} ]")
    r.space(8)

    crit_keys = [
        ("crit_facial_index",        "facial_index"),
        ("crit_cephalic_index",      "cephalic_index"),
        ("crit_orbital_index",       "orbital_index"),
        ("crit_nasal_index",         "nasal_index"),
        ("crit_forehead_height",     "forehead_height"),
        ("crit_chin_height",         "chin_height"),
        ("crit_cheekbone_height",    "cheekbone_height"),
        ("crit_jaw_width",           "jaw_width"),
        ("crit_forehead_form",       "forehead_form"),
        ("crit_nose_bridge_form",    "nose_bridge_form"),
        ("crit_lip_form",            "lip_form"),
        ("crit_chin_form",           "chin_form"),
        ("crit_eyelid_fold",         "eyelid_fold"),
        ("crit_eye_fissure",         "eye_fissure"),
        ("crit_horizontal_profiling","horizontal_profiling"),
        ("crit_brow_development",    "brow_development"),
        ("crit_nasal_base",          "nasal_base"),
        ("crit_vertical_profiling",  "vertical_profiling"),
        ("crit_interocular",         "interocular"),
        ("crit_eye_depth",           "eye_depth"),
        ("crit_eye_position",        "eye_position"),
        ("crit_pigmentation",        "pigmentation"),
        ("crit_hair_structure",      "hair_structure"),
        ("crit_build_type",          "build_type"),
        ("crit_special_features",    "special_features"),
    ]
    for key_i18n, key_data in crit_keys:
        val = _c(key_data)
        if val:
            r.criterion(f"• {t(key_i18n, lang)}:", val)

    # ── Сборка PDF ────────────────────────────────────────────────────────────
    pages = r.finish()
    pdf = fitz.open()
    dpi = 300
    for img in pages:
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        w_pt = img.width * 72 / dpi
        h_pt = img.height * 72 / dpi
        page = pdf.new_page(width=w_pt, height=h_pt)
        page.insert_image(page.rect, stream=buf.read())

    return pdf.tobytes()
