import asyncio
import base64
import json
import re
from pathlib import Path
import chromadb
import anthropic
from bot.config import ANTHROPIC_API_KEY, CLAUDE_MODEL, AI_ENABLED
from bot.services.face_metrics import compute_metrics
from bot.i18n import t

KNOWLEDGE_DIR = Path("data/knowledge")


def _parse_json_safe(raw: str) -> dict:
    # Попытка 1: как есть
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Попытка 2: убрать trailing commas перед } и ]
    cleaned = re.sub(r",\s*([}\]])", r"\1", raw)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Попытка 3: вырезать только первый валидный JSON-объект посимвольно
    depth = 0
    start = raw.find("{")
    if start == -1:
        raise ValueError("No JSON object found in response")
    for i, ch in enumerate(raw[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(raw[start:i + 1])
                except json.JSONDecodeError:
                    break

    raise ValueError(f"Failed to parse JSON from model response: {raw[:200]}")

client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)


async def _create_with_retry(*, model, max_tokens, messages, system: str = "", retries: int = 2):
    """Повторяет запрос к Claude при временных ошибках 500/529."""
    kwargs: dict = {"model": model, "max_tokens": max_tokens, "messages": messages}
    if system:
        kwargs["system"] = system
    last_exc = None
    for attempt in range(retries + 1):
        try:
            return await client.messages.create(**kwargs)
        except anthropic.APIStatusError as e:
            last_exc = e
            if e.status_code in (500, 529) and attempt < retries:
                wait = 4 * (attempt + 1)
                print(f"Anthropic {e.status_code} — повтор {attempt+1}/{retries} через {wait}s")
                await asyncio.sleep(wait)
            else:
                raise
    raise last_exc


# ChromaDB — загружается один раз при старте
_chroma: chromadb.Collection | None = None

def _get_collection() -> chromadb.Collection | None:
    global _chroma
    if _chroma is not None:
        return _chroma
    try:
        db = chromadb.PersistentClient(path="data/chroma_db")
        _chroma = db.get_collection("archive_knowledge")
        print(f"RAG: ChromaDB загружена, {_chroma.count()} записей")
    except Exception as e:
        print(f"RAG: ChromaDB недоступна — {e}")
        _chroma = None
    return _chroma


def _encode(photo_bytes: bytes) -> str:
    return base64.standard_b64encode(photo_bytes).decode()


def _image_block(b64: str) -> dict:
    return {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": b64}}


# ── Шаг 1: описание внешности для поиска ─────────────────────────────────────

DESCRIBE_PROMPT = """Ты физический антрополог. Опиши СТРОГО по следующим 15 критериям экспертной типологии:

1. ЛИЦЕВОЙ ИНДЕКС: форма лица — ширина скул vs высота лица (узкое/среднее/широкое)
3. ФОРМА ГЛАЗНИЦ + РАЗРЕЗ: горизонтальный / внутренние уголки ниже внешних / выше внешних; наличие эпикантуса
   ГЛУБИНА ПОСАДКИ ГЛАЗ: слабая (поверхностно) / средняя / сильная — смотри на профиль и 3/4, оцени насколько глазное яблоко углублено в орбиту
4. НОСОВОЙ ИНДЕКС: ширина крыльев vs длина носа (узкий/средний/широкий)
5. ФОРМА СПИНКИ НОСА: прямая / выпуклая (горбатая) / вогнутая (курносая) / волнистая (S-изгиб)
6. ШИРИНА ЧЕЛЮСТЕЙ: ширина нижней челюсти относительно скул — узкая/средняя/широкая
7. ГОРИЗОНТАЛЬНАЯ ПРОФИЛИРОВКА: уплощённость/выступание средней части лица в горизонтальной плоскости (сильная/средняя/слабая)
8. ВЕРТИКАЛЬНАЯ ПРОФИЛИРОВКА: угол наклона лица в вертикальной плоскости (прогнатизм/ортогнатизм/опистогнатизм)
9. ВЫСОТА ПОДБОРОДКА: высота подбородка от нижней губы до нижней точки (низкий/средний/высокий)
10. СТЕПЕНЬ ВЫСТУПА ПОДБОРОДКА: выступающий/нормальный/скошенный
11. ПИГМЕНТАЦИЯ: цвет кожи (шкала Фитцпатрика), волос (шкала Фишера-Заллера), глаз (шкала Бунака)
12. СТРУКТУРА ВОЛОС: прямые/волнистые/вьющиеся; тонкие/средние/грубые
13. ЛОБ: высота, наклон назад, выраженность надбровных дуг
14. СКУЛЫ: выраженность и ширина скуловых дуг
15. ОБЩИЙ МОРФОТИП: общее описание черт лица

Только объективное описание. Никаких выводов о типе."""


async def _describe_appearance(images_content: list[dict]) -> str:
    content = images_content + [{"type": "text", "text": DESCRIBE_PROMPT}]
    response = await _create_with_retry(
        model="claude-sonnet-4-6",
        max_tokens=800,
        messages=[{"role": "user", "content": content}],
    )
    return response.content[0].text


# ── Поиск в ChromaDB ──────────────────────────────────────────────────────────

def _search_knowledge(query: str, n: int = 10) -> tuple[str, list[str]]:
    """Возвращает (текст контекста, список уникальных источников по релевантности)."""
    collection = _get_collection()
    if not collection or collection.count() == 0:
        return "", []
    try:
        results = collection.query(query_texts=[query], n_results=min(n, collection.count()))
        chunks = results["documents"][0]
        sources = [m.get("source", "?") for m in results["metadatas"][0]]
        parts = []
        for chunk, src in zip(chunks, sources):
            parts.append(f"[{src}]\n{chunk}")
        # Уникальные источники в порядке релевантности
        unique_sources = list(dict.fromkeys(sources))
        return "\n\n---\n\n".join(parts), unique_sources
    except Exception as e:
        print(f"RAG search error: {e}")
        return "", []


def _load_reference_images(sources: list[str], max_total: int = 4) -> list[dict]:
    """Загружает эталонные изображения из папок knowledge для топ источников RAG."""
    ref_images = []
    for source in sources:
        if len(ref_images) >= max_total:
            break
        folder = KNOWLEDGE_DIR / Path(source)
        if not folder.is_dir():
            continue
        img_files = sorted(folder.glob("*.jpg"))[:2]  # макс 2 фото на источник
        for img_path in img_files:
            if len(ref_images) >= max_total:
                break
            try:
                b64 = base64.standard_b64encode(img_path.read_bytes()).decode()
                ref_images.append({"source": source, "block": _image_block(b64)})
            except Exception:
                pass
    return ref_images


# ── Шаг 2: финальный анализ с базой знаний ───────────────────────────────────

SYSTEM_PROMPT = """Ты — учёный-архивариус Архива Происхождения. Проводишь строгий морфологический анализ по полному протоколу экспертной типологии.

ПРАВИЛА:
1. Анализируй ТОЛЬКО физические/морфологические характеристики
2. НИКОГДА не делай политических, социальных или интеллектуальных выводов
3. Числовые индексы MediaPipe — ВСПОМОГАТЕЛЬНЫЕ данные. Если они явно противоречат фотографии — ДОВЕРЯЙ ФОТО, а не числам. Числа могут быть погрешностью ракурса.
4. Заполни ВСЕ поля criteria — используй "—" только если реально невозможно определить
5. СТРОГО не более 3 расовых типов: 1 основной + максимум 2 дополнительных. Больше трёх — запрещено.
6. ЛИЦЕВОЙ ИНДЕКС: два источника ошибки — (а) Claude склонен ЗАНИЖАТЬ ЛИ визуально; (б) MediaPipe систематически занижает ЛИ на 3-6% из-за 2D-погрешности (если MediaPipe показывает ~80% = Юрипросопия, реальное значение скорее всего 84-86% = Мезопросопия). ПРАВИЛО: если MediaPipe даёт Юрипросопию НО другие измерения у него с ошибками (носовой > 95%, орбитальный < 55%) — ЛИ тоже ненадёжен, доверяй только визуальному анализу. Нордические, Динарские, Понтийские, Альпийские типы редко имеют настоящую Юрипросопию.
7. ЦЕФАЛЬНЫЙ ИНДЕКС: определяй ОБЯЗАТЕЛЬНО по профильному фото. Признаки долихоцефалии: затылок сильно выступает назад за ушную раковину, череп вытянутый спереди-назад. Признаки брахицефалии: затылок плоский/округлый, череп широкий и короткий. Мезоцефалия: промежуточное. Всегда добавляй «(визуальная оценка по профилю; точный замер — только штангенциркулем)».
8. НОСОВОЙ УКАЗАТЕЛЬ — приоритет источников данных:
   а) Если в ДОПОЛНИТЕЛЬНЫХ ДАННЫХ есть реальные замеры носа (ширина и высота в мм) — ВЫЧИСЛЯЙ НИ из них: НИ = (ширина_носа / высота_носа) × 100. Это точнее любых других методов.
   б) Если MediaPipe НУ < 40% или > 95% — данные НЕДОСТОВЕРНЫ (артефакт 2D). Пиши: «MediaPipe недостоверен; визуальная оценка: [категория]» и опирайся только на фото.
   в) Визуальная оценка НУ ненадёжна у уплощённых типов (монголоиды, азиаты): низкая переносица делает нос визуально шире — НЕ завышай НУ только из-за этого.
9. ОРБИТАЛЬНЫЙ УКАЗАТЕЛЬ — приоритет источников:
   а) Если в ДОПОЛНИТЕЛЬНЫХ ДАННЫХ есть замеры орбиты (высота и ширина) — ВЫЧИСЛЯЙ ОИ из них.
   б) Если MediaPipe ОУ < 30% или > 110% — данные НЕДОСТОВЕРНЫ. Пиши: «MediaPipe недостоверен; визуальная оценка: [категория]» и оценивай по фото.
   в) При уплощённой орбите у монголоидных типов — не путай узкую глазную щель (эпикантус) с низкой орбитой: орбита может быть мезоконхной или гипсиконхной даже при узком разрезе глаз.

ДОПУСТИМЫЕ ТИПЫ (используй КОНКРЕТНЫЕ подтипы, а не обобщённые):
— Европейские: Нордический, Халльштатт-Нордический, Кельто-Нордический, Тевтонордид, Феннонордид, Далланордид, Протонордид, Норик, Трённелагский, Средиземноморский, Атланто-Средиземноморский, Понтийский, Малый Средиземноморский, Иранид, Арабид, Западно-Азиатский Средиземноморский, Эфиопид, Далоне-Средиземноморский, Альпийский, Динарский, Западно-Азиатский Динарид, Арабо-Центральноазиатский Динарид, Арменоидный, Европейский Динарид, Борребю, Брюнн, Афалу, Балтийский, Атлантический, Восточно-Балтийский, Ладожский, Остъевропид, Лапоноидный
— Азиатские: Синидный, Северный Синид, Центральный Синид, Южный Синид, Тунгид, Эскимид, Палео-Монголоид, Туранидный, Кавказидный
— Индийские: Индидный, Индо-Брахид, Гондид, Малид
— Негроидные: Судaнид, Кафрид, Нилотид, Палеонегрид, Бамбутид, Хойдид, Санид
— Прочие: Австралоид, Неомеланезид, Палеомеланезид, Полинезийский, Андид, Бразилид, Лагид, Пампид, Централид, Сильвид, Пасифид, Маргид
ЕСЛИ ни один конкретный подтип не подходит — используй обобщённый (Монголоидный, Негридный и т.д.), но только как последний вариант.
ЗАПРЕЩЕНО: указывать обобщённый тип как дополнительный к его же подтипу. Примеры ошибок: «Синидный + Монголоидный», «Тунгид + Монголоидный», «Нордический + Европейский». Основной и дополнительные типы должны быть РАЗНЫМИ ветвями, не родитель+ребёнок.

ФОРМАТ ОТВЕТА — строго JSON без markdown:
{
  "ethnicity_note": "известные этнические корни (если указаны пользователем, иначе пустая строка)",
  "race_type": "основной расовый тип + влияния, например: Нордический с примесью Восточно-Балтийского и локальной динаризацией",

  "criteria": {
    "facial_index": "Юрипросопия (до 84%) / Мезопросопия (84-87.9%) / Лептопросопия (88%+) + значение",
    "cephalic_index": "Брахицефалия / Мезоцефалия / Долихоцефалия (только визуальная оценка, для точного значения нужен штангенциркуль)",
    "orbital_index": "Гипсиконхия / Мезоконхия / Хамеконхия + источник (реальный замер / визуальная оценка / MediaPipe недостоверен)",
    "nasal_index": "Лепториния (до 70%) / Мезориния (70-84.9%) / Хамэриния (85-99.9%) + источник (реальный замер / визуальная оценка / MediaPipe недостоверен)",
    "forehead_height": "Большая / Средняя / Малая",
    "chin_height": "Большая / Средняя / Малая",
    "cheekbone_height": "Высокие / Средние / Низкие",
    "jaw_width": "Широкая / Средняя / Узкая",
    "forehead_form": "Прямой / Наклонный / Выпуклый",
    "nose_bridge_form": "Прямая / Выпуклая / Вогнутая / Волнистая (S-образная)",
    "lip_form": "Тонкие / Средние / Толстые",
    "chin_form": "Тип V / Тип U / Квадратный / Округлый",
    "eyelid_fold": "Слабая / Средняя / Сильная степень нависания верхнего века",
    "eye_fissure": "Горизонтальный / Внутренние уголки ниже внешних / Выше внешних",
    "horizontal_profiling": "Сильная / Средняя / Слабая",
    "brow_development": "Слабое / Среднее / Сильное развитие надбровий",
    "nasal_base": "Горизонтальное / Приподнятое / Опущенное",
    "vertical_profiling": "Ортогнатная / Прогнатная / Опистогнатная",
    "interocular": "Узкое / Среднее / Широкое межглазное расстояние",
    "eye_depth": "Слабая (поверхностная) / Средняя / Сильная (глубоко посажены) — оценивай по профилю и 3/4",
    "eye_position": "Низко посаженные / Средние / Высоко посаженные — вертикальное положение глаз на лице: расстояние от линии бровей до зрачка относительно высоты лица",
    "pigmentation": "пигментация кожи/волос/глаз по шкалам Фитцпатрика, Фишера-Заллера, Бунака",
    "hair_structure": "Прямые / Волнистые / Вьющиеся; тонкие/средние/грубые",
    "build_type": "Астенический / Нормостенический / Гиперстенический (если известен рост/вес)",
    "special_features": "выдающиеся специфические черты через запятую"
  },

  "primary_type": {"name": "расовый тип", "similarity": <число>},
  "secondary_types": [{"name": "тип", "similarity": <число>}],
  "gothic_description": "поэтическое описание в готическом стиле, 2-3 предложения",
  "chronicle_number": "номер в римских цифрах, например MCMXCIX-VII",
  "confidence": <60-95>
}
Сумма similarity ВСЕХ типов (primary + все secondary) = 100. secondary_types максимум 2 элемента."""


def _build_analysis_message(
    images_content: list[dict],
    appearance: str,
    knowledge: str,
    extra: dict,
    metrics_text: str = "",
    ref_images: list[dict] | None = None,
    lang: str = "ru",
) -> list[dict]:
    extra_lines = []
    for key, label in [("age", "Возраст"), ("nationality", "Национальность"),
                       ("origin", "Происхождение"), ("anthropometry", "Антропометрия")]:
        if extra.get(key):
            extra_lines.append(f"{label}: {extra[key]}")

    lang_instruction = (
        "LANGUAGE: Respond with all text values (gothic_description, race_type, type names, "
        "all criteria values) in English."
        if lang == "en"
        else "LANGUAGE: Отвечай на русском языке (gothic_description, race_type, названия типов, все значения критериев)."
    )

    text_parts = [
        "Проведи антропологический анализ по фотографиям.",
        lang_instruction,
    ]
    if metrics_text:
        text_parts.append(metrics_text)
    text_parts.append(f"ОПИСАНИЕ ВНЕШНОСТИ (предварительный визуальный анализ):\n{appearance}")
    if extra_lines:
        text_parts.append("ДОПОЛНИТЕЛЬНЫЕ ДАННЫЕ:\n" + "\n".join(extra_lines))
    if knowledge:
        text_parts.append(
            "ФРАГМЕНТЫ ИЗ НАУЧНЫХ ИСТОЧНИКОВ (используй как основу для классификации):\n\n"
            + knowledge[:5000]
        )
    text_parts.append(
        "Если фото нечёткое — снизь confidence до 60-65 и упомяни это в gothic_description.\n"
        "Ответь строго в формате JSON."
    )

    content = images_content + [{"type": "text", "text": "\n\n".join(text_parts)}]

    if ref_images:
        current_source = None
        for item in ref_images:
            if item["source"] != current_source:
                current_source = item["source"]
                content.append({"type": "text", "text": f"[Эталонный образец: {current_source}]"})
            content.append(item["block"])

    return content


# ── Форматирование результата ─────────────────────────────────────────────────

def _confidence_bar(value: int, total: int = 10) -> str:
    filled = round(value / 100 * total)
    return "█" * filled + "░" * (total - filled)


def format_result_message(data: dict, lang: str = "ru") -> str:
    primary = data.get("primary_type", {})
    secondary = data.get("secondary_types", [])
    confidence = data.get("confidence", 75)
    chronicle = data.get("chronicle_number", "I-I")
    criteria = data.get("criteria", {})
    race_type = data.get("race_type", "")
    ethnicity = data.get("ethnicity_note", "")

    sec_lines = "\n".join(f"  ✧ {s['name']} — {s['similarity']}%" for s in secondary[:2]) \
                or t("result_secondary_none", lang)

    def _c(key: str) -> str:
        v = criteria.get(key, "")
        return v if v and v not in ("—", "неизвестно", "не указано", "unknown", "not specified") else ""

    crit_rows = [
        (t("crit_facial_index", lang),        _c("facial_index")),
        (t("crit_cephalic_index", lang),       _c("cephalic_index")),
        (t("crit_orbital_index", lang),        _c("orbital_index")),
        (t("crit_nasal_index", lang),          _c("nasal_index")),
        (t("crit_forehead_height", lang),      _c("forehead_height")),
        (t("crit_chin_height", lang),          _c("chin_height")),
        (t("crit_cheekbone_height", lang),     _c("cheekbone_height")),
        (t("crit_jaw_width", lang),            _c("jaw_width")),
        (t("crit_forehead_form", lang),        _c("forehead_form")),
        (t("crit_nose_bridge_form", lang),     _c("nose_bridge_form")),
        (t("crit_lip_form", lang),             _c("lip_form")),
        (t("crit_chin_form", lang),            _c("chin_form")),
        (t("crit_eyelid_fold", lang),          _c("eyelid_fold")),
        (t("crit_eye_fissure", lang),          _c("eye_fissure")),
        (t("crit_horizontal_profiling", lang), _c("horizontal_profiling")),
        (t("crit_brow_development", lang),     _c("brow_development")),
        (t("crit_nasal_base", lang),           _c("nasal_base")),
        (t("crit_vertical_profiling", lang),   _c("vertical_profiling")),
        (t("crit_interocular", lang),          _c("interocular")),
        (t("crit_eye_depth", lang),            _c("eye_depth")),
        (t("crit_eye_position", lang),         _c("eye_position")),
        (t("crit_pigmentation", lang),         _c("pigmentation")),
        (t("crit_hair_structure", lang),       _c("hair_structure")),
        (t("crit_build_type", lang),           _c("build_type")),
        (t("crit_special_features", lang),     _c("special_features")),
    ]
    crit_lines = "\n".join(f"  • <b>{k}:</b> {v}" for k, v in crit_rows if v)

    chronicle_label = "CHRONICLE" if lang == "en" else "ХРОНИКА"
    result = (
        t("result_disclaimer", lang)
        + f"╔══════════════════════════════════╗\n"
        f"║  📜  {chronicle_label} #{chronicle}\n"
        f"╚══════════════════════════════════╝\n\n"
    )
    if ethnicity:
        result += t("result_ethnicity", lang, value=ethnicity) + "\n"
    if race_type:
        result += t("result_race_type", lang, value=race_type) + "\n"
    result += t("result_morphology_header", lang)
    if crit_lines:
        result += crit_lines + "\n\n"
    result += (
        t("result_origin_header", lang)
        + t("result_primary", lang, name=primary.get("name", "—"), pct=primary.get("similarity", 0))
        + t("result_secondary_header", lang) + sec_lines + "\n\n"
        + "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        + f"🕯️ <i>{data.get('gothic_description', '')}</i>\n\n"
        + t("result_confidence", lang, bar=_confidence_bar(confidence), pct=confidence)
    )
    return result


# ── Основная функция ──────────────────────────────────────────────────────────

async def analyze_photos(
    front_bytes: bytes,
    profile_bytes: bytes | None,
    fullbody_bytes: bytes | None,
    extra: dict,
    lang: str = "ru",
) -> tuple[str, dict, bytes | None]:
    if not AI_ENABLED:
        data = _mock_result()
        return format_result_message(data, lang), data, None

    # Собираем блоки изображений
    images_content = [_image_block(_encode(front_bytes))]
    if profile_bytes:
        images_content.append(_image_block(_encode(profile_bytes)))
    if fullbody_bytes:
        images_content.append(_image_block(_encode(fullbody_bytes)))

    loop = asyncio.get_event_loop()

    # Шаг 1: описание внешности (Claude Vision) + вычисление метрик (MediaPipe) — параллельно
    appearance, metrics = await asyncio.gather(
        _describe_appearance(images_content),
        loop.run_in_executor(None, compute_metrics, front_bytes),
    )

    metrics_text = metrics.to_prompt_text()
    if metrics.detected:
        print(f"Метрики лица: ЛУ={metrics.facial_index}, НУ={metrics.nasal_index}, ОУ={metrics.orbital_index}")
    else:
        print(f"Метрики лица: {metrics.error}")

    # Поиск в ChromaDB + загрузка эталонных изображений
    knowledge, ref_sources = await loop.run_in_executor(None, _search_knowledge, appearance)
    ref_images = await loop.run_in_executor(None, _load_reference_images, ref_sources)
    if ref_images:
        print(f"RAG: загружено {len(ref_images)} эталонных изображений из {len(ref_sources)} источников")

    # Шаг 2: финальный анализ с числовыми индексами + знаниями + фото + эталоны
    content = _build_analysis_message(images_content, appearance, knowledge, extra, metrics_text, ref_images, lang)
    response = await _create_with_retry(
        model=CLAUDE_MODEL,
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": content}],
    )

    raw = response.content[0].text
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    json_str = match.group() if match else raw
    data = _parse_json_safe(json_str)
    return format_result_message(data, lang), data, metrics.landmark_image


def _mock_result() -> dict:
    return {
        "face_shape": "Овальная",
        "main_features": [
            "Высокие скулы",
            "Прямой нос с тонкой переносицей",
            "Глубоко посаженные глаза",
            "Чёткий контур нижней челюсти",
        ],
        "special_features": "Характерная симметрия черт лица, мягкий переход от лба к вискам.",
        "primary_type": {"name": "Нордический", "similarity": 68},
        "secondary_types": [
            {"name": "Атлантический", "similarity": 20},
            {"name": "Балтийский", "similarity": 12},
        ],
        "gothic_description": (
            "Облик несёт в себе отпечаток северных хроник — холодная ясность черт, "
            "словно высеченных в камне древней крепости."
        ),
        "chronicle_number": "MCMXCIX-VII",
        "confidence": 72,
    }
