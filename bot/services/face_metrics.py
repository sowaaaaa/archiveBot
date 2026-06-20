"""
Вычисление антропологических индексов + генерация маски лица (468 точек).
Покрывает все критерии экспертной типологии из формата разбора.
"""
import os
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
os.environ.setdefault("GLOG_minloglevel", "3")

import urllib.request
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision
from dataclasses import dataclass, field

_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "face_landmarker/face_landmarker/float16/1/face_landmarker.task"
)
_MODEL_PATH = os.path.join("data", "face_landmarker.task")
_landmarker: mp_vision.FaceLandmarker | None = None


def _ensure_model() -> None:
    if not os.path.exists(_MODEL_PATH):
        os.makedirs(os.path.dirname(_MODEL_PATH), exist_ok=True)
        print(f"MediaPipe: скачиваю модель (~29 MB) -> {_MODEL_PATH}")
        urllib.request.urlretrieve(_MODEL_URL, _MODEL_PATH)
        print("MediaPipe: модель загружена")


def _get_landmarker() -> mp_vision.FaceLandmarker:
    global _landmarker
    if _landmarker is None:
        _ensure_model()
        base_options = mp_python.BaseOptions(model_asset_path=_MODEL_PATH)
        options = mp_vision.FaceLandmarkerOptions(
            base_options=base_options,
            num_faces=1,
            min_face_detection_confidence=0.5,
        )
        _landmarker = mp_vision.FaceLandmarker.create_from_options(options)
    return _landmarker


# ── Ключевые лендмарки ────────────────────────────────────────────────────────
LM = {
    "forehead":         10,
    "chin":            152,
    "left_cheek":      234,
    "right_cheek":     454,
    "nasion":            6,
    "glabella":          9,
    "nose_bridge":     168,
    "nose_tip":          1,
    "subnasale":        94,
    "left_alare":      129,
    "right_alare":     358,
    "left_eye_outer":   33,
    "left_eye_inner":  133,
    "left_eye_top":    159,
    "left_eye_bot":    145,
    "right_eye_inner": 362,
    "right_eye_outer": 263,
    "right_eye_top":   386,
    "right_eye_bot":   374,
    "mouth_left":       61,
    "mouth_right":     291,
    "upper_lip_top":    13,
    "lower_lip_bot":    14,
    "left_jaw":        172,
    "right_jaw":       397,
    "left_brow_in":    107,
    "right_brow_in":   336,
}

# ── Контуры для отрисовки маски ───────────────────────────────────────────────
_FACE_OVAL = [10,338,297,332,284,251,389,356,454,323,361,288,
              397,365,379,378,400,377,152,148,176,149,150,136,
              172,58,132,93,234,127,162,21,54,103,67,109,10]
_LEFT_EYE  = [33,7,163,144,145,153,154,155,133,173,157,158,159,160,161,246,33]
_RIGHT_EYE = [263,249,390,373,374,380,381,382,362,398,384,385,386,387,388,466,263]
_LEFT_BROW = [46,53,52,65,55,107,66,105,63,70]
_RIGHT_BROW= [276,283,282,295,285,336,296,334,293,300]
_NOSE      = [168,6,197,195,5,4,1,19,94,2,164,0]
_UPPER_LIP = [61,185,40,39,37,0,267,269,270,409,291]
_LOWER_LIP = [61,146,91,181,84,17,314,405,321,375,291]

_CONTOURS = [_FACE_OVAL, _LEFT_EYE, _RIGHT_EYE, _LEFT_BROW, _RIGHT_BROW,
             _NOSE, _UPPER_LIP, _LOWER_LIP]


def _dist(p1: tuple, p2: tuple) -> float:
    return float(np.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2))


def _classify(value: float, thresholds: list[tuple[float, str]]) -> str:
    for max_val, label in thresholds:
        if value < max_val:
            return label
    return thresholds[-1][1]


@dataclass
class FaceMetrics:
    detected: bool = False
    error: str = ""

    # ── Основные индексы ──────────────────────────────────────────────────────
    facial_index: float | None = None
    nasal_index: float | None = None
    orbital_index: float | None = None
    interocular_ratio: float | None = None
    jaw_index: float | None = None

    facial_type: str = ""
    nasal_type: str = ""
    orbital_type: str = ""
    eye_spacing: str = ""
    jaw_type: str = ""

    # ── Критерии эксперта ─────────────────────────────────────────────────────
    forehead_height_ratio: float | None = None
    forehead_height_type: str = ""     # большая / средняя / малая
    forehead_form: str = ""            # прямой / наклонный / выпуклый

    cheekbone_position: str = ""       # высокие / средние / низкие скулы

    lip_thickness_ratio: float | None = None
    lip_form: str = ""                 # тонкие / средние / толстые

    chin_form: str = ""                # тип V / U / квадратный

    brow_prominence: str = ""          # слабое / среднее / сильное развитие надбровий
    nasal_base: str = ""               # горизонтальное / приподнятое / опущенное
    vertical_profiling: str = ""       # ортогнатная / прогнатная / опистогнатная

    eye_depth: str = ""
    chin_height_ratio: float | None = None
    chin_height_type: str = ""
    chin_protrusion: str = ""
    nose_bridge_form: str = ""
    horizontal_profiling: str = ""
    lip_profile: str = ""
    face_symmetry: str = ""
    eye_fissure_angle: str = ""

    # ── Маска лица (JPEG bytes) ───────────────────────────────────────────────
    landmark_image: bytes | None = field(default=None, repr=False)

    # Диапазоны валидных значений для человеческого лица
    _VALID_RANGES = {
        "facial_index":      (70.0, 105.0),
        "nasal_index":       (55.0,  95.0),
        "orbital_index":     (55.0, 100.0),
        "interocular_ratio": (20.0,  50.0),
        "jaw_index":         (45.0,  95.0),
    }

    def _is_valid(self, key: str, val: float | None) -> bool:
        if val is None:
            return False
        lo, hi = self._VALID_RANGES.get(key, (0, 9999))
        return lo <= val <= hi

    def to_prompt_text(self) -> str:
        if not self.detected:
            return f"[MediaPipe: лицо не обнаружено — {self.error}]"

        lines = [
            "=== ДАННЫЕ MediaPipe (468 точек лица) ===",
            "ВАЖНО: проверь каждое значение визуально. Если число противоречит фото — доверяй фото.\n",
        ]

        # Числовые индексы — только если попадают в валидный анатомический диапазон
        index_pairs = [
            ("facial_index",      self.facial_index,
             f"Лицевой указатель: {self.facial_index:.1f}% -> {self.facial_type}"),
            ("nasal_index",       self.nasal_index,
             f"Носовой указатель: {self.nasal_index:.1f}% -> {self.nasal_type}"),
            ("orbital_index",     self.orbital_index,
             f"Орбитальный указатель: {self.orbital_index:.1f}% -> {self.orbital_type}"),
            ("interocular_ratio", self.interocular_ratio,
             f"Межглазничный: {self.interocular_ratio:.1f}% -> {self.eye_spacing}"),
            ("jaw_index",         self.jaw_index,
             f"Нижнечелюстной: {self.jaw_index:.1f}% -> {self.jaw_type}"),
        ]
        for key, val, text in index_pairs:
            if val is not None:
                if self._is_valid(key, val):
                    lines.append(text)
                else:
                    lines.append(f"[!] {text} — ВОЗМОЖНАЯ ПОГРЕШНОСТЬ, проверь визуально")

        # Пропорции — всегда показываем (они менее критичны)
        prop_pairs = [
            (self.forehead_height_ratio,
             f"Высота лба: {self.forehead_height_ratio:.1f}% -> {self.forehead_height_type}"),
            (self.chin_height_ratio,
             f"Высота подбородка: {self.chin_height_ratio:.1f}% -> {self.chin_height_type}"),
            (self.lip_thickness_ratio,
             f"Толщина губ: {self.lip_thickness_ratio:.1f}% -> {self.lip_form}"),
        ]
        for val, text in prop_pairs:
            if val is not None:
                lines.append(text)

        strs = [
            self.forehead_form, self.cheekbone_position, self.chin_form,
            self.brow_prominence, self.nasal_base, self.vertical_profiling,
            self.eye_depth, self.chin_protrusion, self.nose_bridge_form,
            self.horizontal_profiling, self.lip_profile, self.face_symmetry,
            self.eye_fissure_angle,
        ]
        for s in strs:
            if s:
                lines.append(s)

        lines.append("\nПри расхождении чисел с фото — приоритет у визуального анализа.")
        return "\n".join(lines)


# ── Генерация маски лица ──────────────────────────────────────────────────────

def _draw_face_mask(img_bgr: np.ndarray, lms, w: int, h: int) -> bytes | None:
    try:
        canvas = img_bgr.copy()

        # Лёгкое затемнение
        dark = np.zeros_like(canvas)
        cv2.addWeighted(dark, 0.25, canvas, 0.75, 0, canvas)

        def px(idx: int) -> tuple[int, int]:
            return int(lms[idx].x * w), int(lms[idx].y * h)

        # Все 468 точек — мелкие, зелёные
        for i, lm in enumerate(lms):
            if i >= 468:
                break
            x, y = int(lm.x * w), int(lm.y * h)
            cv2.circle(canvas, (x, y), 1, (0, 220, 50), -1, cv2.LINE_AA)

        # Контурные линии — чуть ярче
        line_color = (0, 255, 80)
        for contour in _CONTOURS:
            valid = [idx for idx in contour if idx < len(lms)]
            pts = [px(idx) for idx in valid]
            for i in range(len(pts) - 1):
                cv2.line(canvas, pts[i], pts[i+1], line_color, 1, cv2.LINE_AA)

        # Подпись
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(canvas, "ARCHIVE SCAN / 468pt", (10, h - 10),
                    font, 0.4, (0, 200, 60), 1, cv2.LINE_AA)

        _, buf = cv2.imencode(".jpg", canvas, [cv2.IMWRITE_JPEG_QUALITY, 88])
        return buf.tobytes()
    except Exception as e:
        print(f"face mask draw error: {e}")
        return None


# ── Вычисление метрик ─────────────────────────────────────────────────────────

def compute_metrics(image_bytes: bytes) -> FaceMetrics:
    result = FaceMetrics()
    try:
        arr = np.frombuffer(image_bytes, np.uint8)
        img_bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img_bgr is None:
            result.error = "не удалось декодировать изображение"
            return result

        h, w = img_bgr.shape[:2]
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)
        detection = _get_landmarker().detect(mp_image)

        if not detection.face_landmarks:
            result.error = "лицо не найдено на фото"
            return result

        lms = detection.face_landmarks[0]
        result.detected = True

        def pt(key: str) -> tuple[float, float]:
            lm = lms[LM[key]]
            return lm.x * w, lm.y * h

        def z(key: str) -> float:
            return lms[LM[key]].z

        # ── Лицевой указатель ─────────────────────────────────────────────────
        # Морфологическая высота = насион -> подбородок (без лба) - стандарт антропологии
        morph_face_h = _dist(pt("nasion"), pt("chin"))
        # Физическая высота = лоб -> подбородок - для пропорций лба/скул
        physical_face_h = _dist(pt("forehead"), pt("chin"))
        face_w = _dist(pt("left_cheek"), pt("right_cheek"))
        if face_w > 0:
            fi = (morph_face_h / face_w) * 100
            result.facial_index = round(fi, 1)
            result.facial_type = _classify(fi, [
                (84.0,  "Юрипросопия (широкое лицо, до 84%)"),
                (88.0,  "Мезопросопия (среднее, 84-87.9%)"),
                (999.0, "Лептопросопия (узкое, 88%+)"),
            ])

        # ── Носовой указатель ─────────────────────────────────────────────────
        nose_w = _dist(pt("left_alare"), pt("right_alare"))
        nose_h = _dist(pt("nasion"), pt("subnasale"))
        if nose_h > 0:
            ni = (nose_w / nose_h) * 100
            result.nasal_index = round(ni, 1)
            result.nasal_type = _classify(ni, [
                (70.0,  "Лепториния (узкий, до 70%)"),
                (85.0,  "Мезориния (средний, 70-84.9%)"),
                (999.0, "Хамэриния (широкий, 85-99.9%)"),
            ])

        # ── Орбитальный указатель ─────────────────────────────────────────────
        l_eye_w = _dist(pt("left_eye_outer"), pt("left_eye_inner"))
        l_eye_h = _dist(pt("left_eye_top"), pt("left_eye_bot"))
        r_eye_w = _dist(pt("right_eye_inner"), pt("right_eye_outer"))
        r_eye_h = _dist(pt("right_eye_top"), pt("right_eye_bot"))
        if l_eye_w > 0 and r_eye_w > 0:
            oi = ((l_eye_h / l_eye_w) + (r_eye_h / r_eye_w)) / 2 * 100
            result.orbital_index = round(oi, 1)
            result.orbital_type = _classify(oi, [
                (75.0,  "Хамеконхия / Микросем (низкая орбита, до 75%)"),
                (85.0,  "Мезоконхия / Мезосем (средняя, 75-84.9%)"),
                (999.0, "Гипсиконхия / Мегасем (высокая орбита, 85%+)"),
            ])

        # ── Межглазничный индекс ──────────────────────────────────────────────
        interocular = _dist(pt("left_eye_inner"), pt("right_eye_inner"))
        biocular = _dist(pt("left_eye_outer"), pt("right_eye_outer"))
        if biocular > 0:
            ir = (interocular / biocular) * 100
            result.interocular_ratio = round(ir, 1)
            result.eye_spacing = _classify(ir, [
                (28.0,  "Узкое межглазное расстояние (до 28%)"),
                (36.0,  "Среднее межглазное расстояние (28-35.9%)"),
                (999.0, "Широкое межглазное расстояние (36%+)"),
            ])

        # ── Нижнечелюстной индекс ─────────────────────────────────────────────
        jaw_w = _dist(pt("left_jaw"), pt("right_jaw"))
        if face_w > 0:
            ji = (jaw_w / face_w) * 100
            result.jaw_index = round(ji, 1)
            result.jaw_type = _classify(ji, [
                (65.0,  "Узкая нижняя челюсть (до 65%)"),
                (80.0,  "Средняя нижняя челюсть (65-79.9%)"),
                (999.0, "Широкая нижняя челюсть (80%+)"),
            ])

        # ── Высота лба ────────────────────────────────────────────────────────
        # от точки лба(10) до насиона(6) — в y-координатах (y растёт вниз)
        forehead_h_px = pt("nasion")[1] - pt("forehead")[1]
        if physical_face_h > 0 and forehead_h_px > 0:
            fhr = (forehead_h_px / physical_face_h) * 100
            result.forehead_height_ratio = round(fhr, 1)
            one_third = physical_face_h / 3
            tolerance = one_third * 0.05
            if forehead_h_px > one_third + tolerance:
                result.forehead_height_type = "Высокий лоб (A-B > 1/3 высоты лица)"
            elif forehead_h_px < one_third - tolerance:
                result.forehead_height_type = "Низкий лоб (A-B < 1/3 высоты лица)"
            else:
                result.forehead_height_type = "Средний лоб (A-B ≈ 1/3 высоты лица, ±5%)"

        # ── Форма лба (наклон) ────────────────────────────────────────────────
        # Если лоб(10) дальше от камеры чем переносица(6) → наклонный
        fz_diff = z("forehead") - z("nasion")
        if fz_diff > 0.025:
            result.forehead_form = "Форма лба: Наклонный (скошен назад)"
        elif fz_diff > -0.01:
            result.forehead_form = "Форма лба: Прямой"
        else:
            result.forehead_form = "Форма лба: Выпуклый"

        # ── Положение скул по высоте ──────────────────────────────────────────
        cheek_y_ratio = ((pt("left_cheek")[1] + pt("right_cheek")[1]) / 2 - pt("forehead")[1]) / physical_face_h * 100
        result.cheekbone_position = _classify(cheek_y_ratio, [
            (38.0, "Скулы: Высокое расположение (до 38% от лба)"),
            (52.0, "Скулы: Среднее расположение (38-51.9%)"),
            (999.0, "Скулы: Низкое расположение (52%+)"),
        ])

        # ── Форма губ (толщина) ───────────────────────────────────────────────
        lip_h_px = _dist(pt("upper_lip_top"), pt("lower_lip_bot"))
        if morph_face_h > 0:
            ltr = (lip_h_px / morph_face_h) * 100
            result.lip_thickness_ratio = round(ltr, 1)
            result.lip_form = _classify(ltr, [
                (3.5, "Форма губ: Тонкие (до 3.5%)"),
                (6.0, "Форма губ: Средние (3.5-5.9%)"),
                (999.0, "Форма губ: Толстые (6%+)"),
            ])

        # ── Форма подбородка (по Эйкштедту) ──────────────────────────────────
        chin_w = _dist(pt("left_jaw"), pt("right_jaw"))
        mouth_w = _dist(pt("mouth_left"), pt("mouth_right"))
        if mouth_w > 0:
            chin_ratio = chin_w / mouth_w
            if chin_ratio < 0.75:
                result.chin_form = "Форма подбородка: Остроугольный тип V (узкий)"
            elif chin_ratio < 0.92:
                result.chin_form = "Форма подбородка: Округлый тип U"
            else:
                result.chin_form = "Форма подбородка: Квадратный тип (широкий)"

        # ── Степень развития надбровий ────────────────────────────────────────
        # Сравниваем Z надпереносья с насионом — выступание надбровной дуги
        brow_z_diff = z("nasion") - z("glabella")
        if brow_z_diff > 0.025:
            result.brow_prominence = "Надбровья: Слабое развитие"
        elif brow_z_diff > 0.005:
            result.brow_prominence = "Надбровья: Среднее развитие"
        else:
            result.brow_prominence = "Надбровья: Сильное развитие"

        # ── Основание носа ────────────────────────────────────────────────────
        sub_y = pt("subnasale")[1]
        alare_avg_y = (pt("left_alare")[1] + pt("right_alare")[1]) / 2
        nose_base_diff = sub_y - alare_avg_y
        if nose_base_diff > 4:
            result.nasal_base = "Основание носа: Опущенное"
        elif nose_base_diff < -4:
            result.nasal_base = "Основание носа: Приподнятое"
        else:
            result.nasal_base = "Основание носа: Горизонтальное"

        # ── Вертикальная профилировка ─────────────────────────────────────────
        # Сравниваем Z нижней части лица vs верхней
        lower_z = (z("subnasale") + z("lower_lip_bot") + z("chin")) / 3
        upper_z = (z("nasion") + z("glabella")) / 2
        vp_diff = upper_z - lower_z
        if vp_diff > 0.035:
            result.vertical_profiling = "Вертикальная профилировка: Прогнатная (нижняя часть выступает)"
        elif vp_diff > -0.015:
            result.vertical_profiling = "Вертикальная профилировка: Ортогнатная"
        else:
            result.vertical_profiling = "Вертикальная профилировка: Опистогнатная (нижняя часть скошена)"

        # ── Глубина посадки глаз ──────────────────────────────────────────────
        eye_z_avg = (z("left_eye_top") + z("right_eye_top")) / 2
        cheek_z_avg = (z("left_cheek") + z("right_cheek")) / 2
        eye_depth_diff = eye_z_avg - cheek_z_avg
        if eye_depth_diff > 0.04:
            result.eye_depth = "Глубина посадки глаз: Сильная"
        elif eye_depth_diff > 0.01:
            result.eye_depth = "Глубина посадки глаз: Средняя"
        else:
            result.eye_depth = "Глубина посадки глаз: Слабая (поверхностная)"

        # ── Высота подбородка ─────────────────────────────────────────────────
        chin_h = _dist(pt("lower_lip_bot"), pt("chin"))
        if morph_face_h > 0:
            chr_ = (chin_h / morph_face_h) * 100
            result.chin_height_ratio = round(chr_, 1)
            result.chin_height_type = _classify(chr_, [
                (14.0, "Высота подбородка: Малая (до 14%)"),
                (20.0, "Высота подбородка: Средняя (14-19.9%)"),
                (999.0, "Высота подбородка: Большая (20%+)"),
            ])

        # ── Степень выступа подбородка ────────────────────────────────────────
        chin_protrusion_diff = z("forehead") - z("chin")
        if chin_protrusion_diff > 0.05:
            result.chin_protrusion = "Выступ подбородка: Выступающий (прогения)"
        elif chin_protrusion_diff > 0.01:
            result.chin_protrusion = "Выступ подбородка: Нормальный"
        else:
            result.chin_protrusion = "Выступ подбородка: Скошенный / слабый"

        # ── Форма спинки носа ─────────────────────────────────────────────────
        z_n   = z("nasion")
        z_tip = z("nose_tip")
        z_expected_mid = (z_n + z_tip) / 2
        bridge_dev = z("nose_bridge") - z_expected_mid
        sub_dev = z("subnasale") - z_expected_mid
        if bridge_dev * sub_dev < -0.0004 and abs(bridge_dev) > 0.01 and abs(sub_dev) > 0.01:
            result.nose_bridge_form = "Форма спинки носа: Волнистая (S-образный изгиб)"
        elif bridge_dev < -0.015:
            result.nose_bridge_form = "Форма спинки носа: Выпуклая (горбатый нос)"
        elif bridge_dev > 0.015:
            result.nose_bridge_form = "Форма спинки носа: Вогнутая (курносая)"
        else:
            result.nose_bridge_form = "Форма спинки носа: Прямая"

        # ── Горизонтальная профилировка ───────────────────────────────────────
        nose_cheek_z_diff = cheek_z_avg - z("nasion")
        if nose_cheek_z_diff < 0.03:
            result.horizontal_profiling = "Горизонтальная профилировка: Слабая (уплощённое лицо)"
        elif nose_cheek_z_diff < 0.08:
            result.horizontal_profiling = "Горизонтальная профилировка: Средняя"
        else:
            result.horizontal_profiling = "Горизонтальная профилировка: Сильная (нос выступает)"

        # ── Профиль губ ───────────────────────────────────────────────────────
        diff = z("nose_tip") - z("upper_lip_top")
        if diff > 0.02:
            result.lip_profile = "Профиль губ: Опистохейлия (губы скошены назад)"
        elif diff < -0.01:
            result.lip_profile = "Профиль губ: Прохейлия (губы выступают)"
        else:
            result.lip_profile = "Профиль губ: Ортохейлия (вертикальный)"

        # ── Разрез глазной щели ──────────────────────────────────────────────────
        # Сравниваем внутренние уголки глаз с горизонталью через внешние уголки
        l_outer_y = pt("left_eye_outer")[1]
        r_outer_y = pt("right_eye_outer")[1]
        outer_avg_y = (l_outer_y + r_outer_y) / 2
        inner_avg_y = (pt("left_eye_inner")[1] + pt("right_eye_inner")[1]) / 2
        biocular_dist = _dist(pt("left_eye_outer"), pt("right_eye_outer"))
        fissure_threshold = biocular_dist * 0.015
        fissure_diff = inner_avg_y - outer_avg_y  # + = внутренние ниже; - = выше
        if abs(fissure_diff) <= fissure_threshold:
            result.eye_fissure_angle = "Разрез глаз: Горизонтальный"
        elif fissure_diff > fissure_threshold:
            result.eye_fissure_angle = "Разрез глаз: Внутренние уголки ниже внешних"
        else:
            result.eye_fissure_angle = "Разрез глаз: Внутренние уголки выше внешних"

        # ── Симметрия ─────────────────────────────────────────────────────────
        center_x = (pt("left_cheek")[0] + pt("right_cheek")[0]) / 2
        asym = abs(pt("nose_tip")[0] - center_x) / (face_w / 2) * 100 if face_w > 0 else 0
        if asym < 3:
            result.face_symmetry = "Симметрия: Высокая"
        elif asym < 7:
            result.face_symmetry = "Симметрия: Умеренная асимметрия"
        else:
            result.face_symmetry = f"Симметрия: Заметная асимметрия ({asym:.0f}%)"

        # ── Маска лица ────────────────────────────────────────────────────────
        result.landmark_image = _draw_face_mask(img_bgr, lms, w, h)

    except Exception as e:
        result.detected = False
        result.error = str(e)

    return result
