"""Локализация бота. Поддерживаемые языки: ru, en."""

_T: dict[str, dict[str, str]] = {
    "ru": {
        # ── Выбор языка ──────────────────────────────────────────────────────────
        "choose_language": '<tg-emoji emoji-id="5879585266426973039">🌐</tg-emoji> Выберите язык / Choose language:',
        "btn_lang_ru": "🇷🇺 Русский",
        "btn_lang_en": "🇬🇧 English",

        # ── Главное меню ─────────────────────────────────────────────────────────
        "welcome": (
            '<tg-emoji emoji-id="5316932602051977742">🪄</tg-emoji><b>АРХИВ ПРОИСХОЖДЕНИЯ</b>\n\n'
            "<i>...Скрипит старинная дверь. Тысячелетняя пыль оседает на каменных ступенях..."
            " Где-то в глубине архива мерцает пламя одинокой свечи...</i>\n\n"
            "Ты стоишь у врат <b>Великого Хранилища</b>, где архивариус хранит летописи поколений. "
            "Здесь, в тиши библиотечных сводов, среди запечатанных томов и угасших свечей, "
            "каждый облик обретает свою хронику.\n\n"
            '<tg-emoji emoji-id="5388922215347534633">📜</tg-emoji> <b><i>Выбери путь, и хроники будут открыты.</i></b>'
        ),
        "what_is": (
            "<b>Как работает AntroLore:</b>\n\n"
            " <b>Специфика антропологии:</b>\n"
            "Человеческий лик изменчив. Разница между фенотипами и расами в антропологии составляет "
            "всего от 1 до 3 миллиметров. Достаточно слегка изменить ракурс, поднять подбородок или "
            "включить другой свет — и автоматический алгоритм может выдать другой результат. Именно "
            "поэтому автоматический скан на разных фото может незначительно отличаться.\n\n"
            " <b>Автоматический скан:</b>\n"
            "Система вычисляет индексы лица, пропорции и метрики на основе присланных вами данных, "
            "чтобы дать первое, мгновенное приближение.\n\n"
            "♰ <b>Вердикт Эксперта (Рекомендуется):</b>\n"
            "Чтобы узнать истину, выберите Экспертный разбор. Наш живой эксперт (Архивариус) вручную "
            "нивелирует искажения камеры, сопоставит ваши точные замеры тела, высчитает пропорции черепа "
            "и вынесет окончательный, проверенный человеком вердикт о вашем этно-миксе и происхождении."
        ),

        "btn_ai": "Фенотипирование",
        "btn_expert": "Экспертный разбор",
        "btn_what_is": "Как это работает",
        "btn_language": "Язык",
        "btn_back": "« В главное меню",
        "btn_skip": "Пропустить »",
        "btn_add_fullbody": "Добавить фото в рост",
        "btn_add_data": "Добавить данные",
        "btn_start_analysis": "Начать анализ",
        "btn_request_expert": " Заказать экспертный разбор",
        "btn_back_archive": "« Вернуться в архив",
        "btn_new_analysis": "🔄 Новый анализ",
        "btn_pay_tribute": "Оплатить через Tribute",
        "btn_start_ai": "Начать типирование ИИ",
        "btn_start_expert": "Начать экспертный разбор",

        "analysis_type_select": (
            "📖 <b>ВЫБОР ПУТИ</b>\n\n"
            "<i>Архивариус указывает на два тома, лежащих перед тобой...</i>\n\n"
            "🤖 <b>Типирование ИИ</b> — мгновенный анализ внешности нейросетью. "
            "Архив сам изучит твои черты и составит хронику.\n\n"
            "🧠 <b>Эксперт</b> — живой специалист по типологии лично изучит твой облик "
            "и даст развёрнутый разбор в течение 24 часов.\n\n"
            "<i>Какой путь ты выбираешь?</i>"
        ),

        # ── Оплата ───────────────────────────────────────────────────────────────
        "balance_ok": '<tg-emoji emoji-id="5769403330761593044">👛</tg-emoji>На твоём балансе достаточно средств для услуги <b>{label}</b>.',
        "balance_text": "💰 Твой баланс: <b>{balance} EUR</b>",
        "insufficient_balance": (
            "⚠️ <b>Недостаточно средств</b>\n\n"
            "На твоём балансе <b>{balance} EUR</b>, а требуется <b>{required} EUR</b>.\n\n"
            "Оплати услугу через Tribute — /start → Открыть архив → выбери услугу."
        ),
        "payment_text": (
            '<tg-emoji emoji-id="5904462880941545555">🪙</tg-emoji> <b>ОПЛАТА ДОСТУПА</b>\n\n'
            "<i>Архивариус раскрывает книгу записей и указывает на сумму...</i>\n\n"
            '<tg-emoji emoji-id="5796440171364749940">📌</tg-emoji>Услуга: <b>{label}</b>\n'
            '<tg-emoji emoji-id="6037083366438737901">💎</tg-emoji>К оплате: <b>{amount} EUR</b>\n\n'
            "· · ·\n\n"
            "Нажми кнопку ниже, чтобы перейти к оплате через Tribute.\n\n"
            "<i>После оплаты доступ откроется автоматически — уведомление придёт в этот чат.</i>"
        ),
        "payment_confirmed": (
            '<tg-emoji emoji-id="5278411813468269386">✅</tg-emoji> <b>Оплата подтверждена!</b>\n\n'
            "<i>Ворота архива открываются...</i>\n\n"
            "Баланс пополнен. Нажми кнопку ниже, чтобы начать."
        ),
        "payment_rejected": (
            "❌ <b>Оплата отклонена.</b>\n\n"
            "<i>Архивариус не нашёл записи о твоём взносе...</i>\n\n"
            "Если считаешь, что произошла ошибка — напиши в поддержку: @DerDu9"
        ),
        "service_ai": "Типирование ИИ",
        "service_expert": "Экспертный разбор",

        # ── Путь эксперта ────────────────────────────────────────────────────────
        "expert_path_intro": (
            "🧠 <b>ПУТЬ ЭКСПЕРТА</b>\n\n"
            "<i>Архивариус зажигает отдельную свечу и достаёт особый том...</i>\n\n"
            "Ты выбрал разбор живым экспертом по типологии. "
            "Это глубокий и точный анализ, основанный на многолетнем опыте.\n\n"
            "Передай фотографии — эксперт изучит их лично и свяжется с тобой."
        ),
        "expert_direct_confirmed": (
            "📜 <b>ЗАЯВКА ПРИНЯТА В АРХИВ</b>\n\n"
            "<i>Архивариус запечатал конверт с твоими данными восковой печатью...</i>\n\n"
            "Твои материалы переданы эксперту по типологии. "
            "Он свяжется с тобой в течение <b>24 часов</b>.\n\n"
            "⚔️ <i>Архив всегда помнит тех, кто ступил на его порог.</i>"
        ),
        "expert_offer": (
            '<tg-emoji emoji-id="5886412370347036129">👤</tg-emoji> <b>ЭКСПЕРТНЫЙ РАЗБОР</b>\n\n'
            "Предварительный анализ завершён. Но в хрониках сокрыто намного больше...\n\n"
            "✦ Детальный разбор каждой черты лика\n"
            "✦ Полная генеалогическая карта фенотипа\n"
            "✦ Исторические параллели и архивные источники\n"
            "✦ Личный ответ архивариуса в течение 24 часов\n\n"
            '<tg-emoji emoji-id="5904462880941545555">🪙</tg-emoji><b>Стоимость: {price} EUR</b>\n\n'
            "<i>Желаешь заглянуть глубже?</i>"
        ),
        "expert_requested": (
            "📜 <b>Заявка принята в архив</b>\n\n"
            "<i>Архивариус сделал пометку в журнале записей...</i>\n\n"
            "Твоя заявка на экспертный разбор передана. "
            "Хранитель архива свяжется с тобой в течение 24 часов.\n\n"
            "⚔️ <i>Архив всегда помнит тех, кто ступил на его порог.</i>"
        ),

        # ── Сбор фото ────────────────────────────────────────────────────────────
        "front_photo_request": (
            '<tg-emoji emoji-id="5388922215347534633">📜</tg-emoji> <b>ШАГ I / III — АНФАС</b>\n\n'
            "♰ <b>Архивариус требует точности.</b>\n"
            "Чтобы свести к минимуму погрешности в 1-3 мм, твой лик должен соответствовать "
            "<b>Строгим Правилам:</b>\n\n"
            "1. Строго анфас и профиль. Никаких наклонов головы.\n"
            "2. Нейтральное выражение лица. Без улыбок и прищура.\n"
            "3. Хорошее, ровное освещение без глубоких теней на лице.\n"
            "4. Держи камеру минимум в 1.5 метрах от лица (используй зум), чтобы избежать "
            "искажения линзы смартфона.\n\n"
            "<i>Пришли фотографию анфас, чтобы открыть хроники...</i>"
        ),
        "profile_photo_request": (
            '<tg-emoji emoji-id="5388922215347534633">📜</tg-emoji> <b>ШАГ II / III — ПРОФИЛЬ</b>\n\n'
            "<i>Архивариус перелистывает страницу манускрипта...</i>\n\n"
            "Теперь передай фотографию своего лика <b>в профиль</b> — вид сбоку.\n\n"
            "✦ Поверни <b>голову ровно на 90°</b>\n"
            "✦ <b>Взгляд</b> направлен <b>вперёд</b>\n"
            "✦ Волосы не должны закрывать черты"
        ),
        "optional_data_request": (
            '<tg-emoji emoji-id="5226512880362332956">📖</tg-emoji> <b>ШАГ III / III — ДОПОЛНИТЕЛЬНЫЕ СВЕДЕНИЯ</b>\n\n'
            "<i>Архивариус готовится дополнить хронику...</i>\n\n"
            "Ты можешь предоставить дополнительные сведения для более точного анализа. "
            "Каждый пункт необязателен — пропусти, если не желаешь раскрывать.\n\n"
            "Желаешь предоставить фотографию в <b>полный рост</b>?"
        ),
        "fullbody_photo_request": (
            "📜 <b>ФОТОГРАФИЯ В ПОЛНЫЙ РОСТ</b>\n\n"
            "<i>Архив расширяет свои страницы...</i>\n\n"
            "Передай фотографию в полный рост.\n\n"
            "✦ Стоя прямо, ноги слегка расставлены\n"
            "✦ Руки вдоль тела\n"
            "✦ Нейтральный фон"
        ),
        "ask_optional_data": (
            '<tg-emoji emoji-id="5879841310902324730">✏️</tg-emoji> <b>Хотите добавить текстовые сведения?</b>\n\n'
            "<i>Это повысит точность хроники.</i>"
        ),
        "age_request": (
            "🖋️ <b>ВОЗРАСТ</b>\n\n"
            "<i>Перо касается пергамента...</i>\n\n"
            "Укажи свой возраст (например: <i>27</i>) или нажми «Пропустить»."
        ),
        "nationality_request": (
            "🖋️ <b>НАЦИОНАЛЬНОСТЬ</b>\n\n"
            "<i>Архивариус сверяется с таблицами народов...</i>\n\n"
            "Укажи свою национальность или нажми «Пропустить»."
        ),
        "origin_request": (
            "🖋️ <b>ПРОИСХОЖДЕНИЕ СЕМЬИ</b>\n\n"
            "<i>Открываются генеалогические записи...</i>\n\n"
            "Укажи регион происхождения семьи или нажми «Пропустить»."
        ),
        "anthropometry_request": (
            "🖋️ <b>АНТРОПОМЕТРИЧЕСКИЕ ДАННЫЕ</b>\n\n"
            "<i>Последние строки в записи подготовлены...</i>\n\n"
            "Укажи данные в формате: <code>рост вес</code>\n"
            "Например: <code>182 75</code>\n\n"
            "Или нажми «Пропустить»."
        ),
        "data_privacy": (
            "\n\n"
            '<tg-emoji emoji-id="5951846549288917006">🔒</tg-emoji> '
            "<i>Твои фотографии и данные не хранятся — они удаляются "
            "сразу после обработки архивариусом.</i>"
        ),
        "no_photo": "🖼️ Пожалуйста, отправь именно <b>фотографию</b>, а не файл или текст.",

        # ── Анализ ───────────────────────────────────────────────────────────────
        "analysis_error": (
            "⚠️ <b>Архив временно недоступен</b>\n\n"
            "<i>Что-то потревожило тишину библиотеки...\n"
            "Архивариус не смог завершить запись.</i>\n\n"
            "Попробуй ещё раз — нажми /start"
        ),
        "loading_0": (
            "⚗️ <b>Архивариус изучает хроники...</b>\n\n"
            "<i>🕯️ Пламя свечи колышется над раскрытым манускриптом...\n"
            "Тени скользят по каменным стенам архива...</i>"
        ),
        "loading_1": (
            "🔍 <b>Сопоставляются внешние признаки...</b>\n\n"
            "<i>📖 Перелистываются страницы древних томов...\n"
            "Архивариус сверяется с таблицами летописей...</i>"
        ),
        "loading_2": (
            "📚 <b>Открываются древние тома...</b>\n\n"
            "<i>🗝️ Ключи звенят у пояса архивариуса...\n"
            "Запечатанные хранилища открывают свои тайны...</i>"
        ),
        "loading_3": (
            "🖋️ <b>Архив готовит запись...</b>\n\n"
            "<i>📜 Перо касается пергамента...\n"
            "Чернила ложатся строка за строкой...</i>"
        ),
        "loading_4": (
            "🌑 <b>Анализируются черты лика...</b>\n\n"
            "<i>🔮 Тени танцуют на высоких сводах...\n"
            "Архивариус погружается в размышления...</i>"
        ),
        "loading_5": (
            "⚔️ <b>Составляется хроника...</b>\n\n"
            "<i>🏰 Замок хранит свои секреты...\n"
            "Скоро запись будет завершена...</i>"
        ),
        "face_scan_caption": "🔬 <i>Антропологическая маска — 468 точек лица</i>",
        "result_disclaimer": (
            "⚠️ <i>Расовый тип определяется визуально — возможны погрешности, "
            "искажающие точный расовый состав: разница между типами составляет всего 1–3 мм. "
            "Для точного анализа обратитесь к нашим экспертам мирового уровня.</i>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        ),
        "result_ethnicity": "🌍 <b>Этничность:</b> {value}",
        "result_race_type": "🏛 <b>Расовый тип:</b> {value}",
        "result_morphology_header": "\n━━━━━━ 【 МОРФОЛОГИЧЕСКИЙ РАЗБОР 】 ━━━━━━\n\n",
        "result_origin_header": "━━━━ 【 ПРОИСХОЖДЕНИЕ 】 ━━━━\n\n",
        "result_primary": "⚜️ <b>Основной тип:</b> {name}\n   Сходство: <b>{pct}%</b>\n\n",
        "result_secondary_header": "📊 <b>Дополнительные примеси:</b>\n",
        "result_secondary_none": "  ✧ Не определено",
        "result_confidence": "🔮 <b>Уверенность:</b> {bar} {pct}%",

        # ── Метки критериев ──────────────────────────────────────────────────────
        "crit_facial_index": "Лицевой указатель",
        "crit_cephalic_index": "Головной указатель",
        "crit_orbital_index": "Орбитальный указатель",
        "crit_nasal_index": "Носовой указатель",
        "crit_forehead_height": "Высота лба",
        "crit_chin_height": "Высота подбородка",
        "crit_cheekbone_height": "Высота скул",
        "crit_jaw_width": "Ширина челюсти",
        "crit_forehead_form": "Форма лба",
        "crit_nose_bridge_form": "Форма спинки носа",
        "crit_lip_form": "Форма губ",
        "crit_chin_form": "Форма подбородка",
        "crit_eyelid_fold": "Нависание века",
        "crit_eye_fissure": "Разрез глаз",
        "crit_horizontal_profiling": "Гориз. профилировка",
        "crit_brow_development": "Развитие надбровий",
        "crit_nasal_base": "Основание носа",
        "crit_vertical_profiling": "Верт. профилировка",
        "crit_interocular": "Межглазное расстояние",
        "crit_eye_depth": "Глубина посадки глаз",
        "crit_eye_position": "Позиция глаз на лице",
        "crit_pigmentation": "Тип пигментации",
        "crit_hair_structure": "Структура волос",
        "crit_build_type": "Телосложение",
        "crit_special_features": "Специфические черты",
    },

    "en": {
        # ── Language selection ────────────────────────────────────────────────────
        "choose_language": "🌐 Выберите язык / Choose language:",
        "btn_lang_ru": "🇷🇺 Русский",
        "btn_lang_en": "🇬🇧 English",

        # ── Main menu ────────────────────────────────────────────────────────────
        "welcome": (
            '<tg-emoji emoji-id="5316932602051977742">🪄</tg-emoji><b>ARCHIVE OF ORIGIN</b>\n\n'
            "<i>...An ancient door creaks. A thousand years of dust settles on stone steps..."
            " Somewhere deep in the archive, the flame of a lone candle flickers...</i>\n\n"
            "You stand at the gates of the <b>Great Repository</b>, where the archivist keeps "
            "the chronicles of generations. Here, in the silence of library vaults, among "
            "sealed volumes and extinguished candles, every face finds its chronicle.\n\n"
            '<tg-emoji emoji-id="5388922215347534633">📜</tg-emoji> <b><i>Choose your path, and the chronicles shall be revealed.</i></b>'
        ),
        "what_is": (
            "<b>How AntroLore works:</b>\n\n"
            " <b>The Challenge of Anthropology:</b>\n"
            "Human features are fluid. The physical difference between distinct phenotypes and races "
            "can be as minimal as 1 to 3 millimeters. A slight change in camera angle, lighting, or "
            "head tilt can completely alter how the automated algorithm perceives your bone structure. "
            "This is why automated scanning (PhenoTyping) on different photos may sometimes yield "
            "varying results.\n\n"
            " <b>The Automated Scan:</b>\n"
            "Our system calculates facial indexes, proportions, and metrics based on your uploaded "
            "files to give you an initial, instant approximation of your roots.\n\n"
            "♰ <b>The Expert Verdict (Highly Recommended):</b>\n"
            "To find the absolute truth, choose Expert Review. Our living Archivist will manually "
            "neutralize camera distortions, evaluate your body measurements, calculate exact skull "
            "indices, and deliver a definitive, human-verified report on your ethnic mix and ancestry."
        ),

        # ── Buttons ──────────────────────────────────────────────────────────────
        "btn_ai": "PhenoTyping",
        "btn_expert": "Expert Review",
        "btn_what_is": "How it works",
        "btn_language": "Language",
        "btn_back": "« Back to menu",
        "btn_skip": "Skip »",
        "btn_add_fullbody": "Add full-body photo",
        "btn_add_data": "Add data",
        "btn_start_analysis": "Start analysis",
        "btn_request_expert": " Order expert analysis",
        "btn_back_archive": "« Return to archive",
        "btn_new_analysis": " New analysis",
        "btn_pay_tribute": "Pay via Tribute",
        "btn_start_ai": "Start AI Typing",
        "btn_start_expert": "Start Expert Analysis",

        # ── Analysis type ────────────────────────────────────────────────────────
        "analysis_type_select": (
            "📖 <b>CHOOSE YOUR PATH</b>\n\n"
            "<i>The archivist points to two volumes lying before you...</i>\n\n"
            "🤖 <b>AI Typing</b> — instant facial analysis by neural network. "
            "The archive will study your features and compile a chronicle.\n\n"
            "🧠 <b>Expert</b> — a live typology specialist will personally examine your appearance "
            "and provide a detailed analysis within 24 hours.\n\n"
            "<i>Which path do you choose?</i>"
        ),

        # ── Payment ──────────────────────────────────────────────────────────────
        "balance_ok": '<tg-emoji emoji-id="5769403330761593044">👛</tg-emoji>Your balance is sufficient for the <b>{label}</b> service.',
        "balance_text": "💰 Your balance: <b>{balance} EUR</b>",
        "insufficient_balance": (
            "⚠️ <b>Insufficient funds</b>\n\n"
            "Your balance is <b>{balance} EUR</b>, but <b>{required} EUR</b> is required.\n\n"
            "Pay via Tribute — /start → Open archive → choose a service."
        ),
        "payment_text": (
            '<tg-emoji emoji-id="5904462880941545555">🪙</tg-emoji> <b>ACCESS PAYMENT</b>\n\n'
            "<i>The archivist opens the ledger and points to the amount...</i>\n\n"
            '<tg-emoji emoji-id="5796440171364749940">📌</tg-emoji>Service: <b>{label}</b>\n'
            '<tg-emoji emoji-id="6037083366438737901">💎</tg-emoji>To pay: <b>{amount} EUR</b>\n\n'
            "· · ·\n\n"
            "Press the button below to proceed to payment via Tribute.\n\n"
            "<i>After payment, access will open automatically — a notification will come to this chat.</i>"
        ),
        "payment_confirmed": (
            "✅ <b>Payment confirmed!</b>\n\n"
            "<i>The gates of the archive open...</i>\n\n"
            "Balance topped up. Press the button below to begin."
        ),
        "payment_rejected": (
            "❌ <b>Payment declined.</b>\n\n"
            "<i>The archivist found no record of your contribution...</i>\n\n"
            "If you believe this is an error — contact support: @DerDu9"
        ),
        "service_ai": "AI Typing",
        "service_expert": "Expert Analysis",

        # ── Expert path ──────────────────────────────────────────────────────────
        "expert_path_intro": (
            "🧠 <b>EXPERT PATH</b>\n\n"
            "<i>The archivist lights a separate candle and retrieves a special volume...</i>\n\n"
            "You have chosen analysis by a live typology expert. "
            "This is a deep and precise analysis based on years of experience.\n\n"
            "Send your photos — the expert will study them personally and contact you."
        ),
        "expert_direct_confirmed": (
            "📜 <b>REQUEST ACCEPTED INTO THE ARCHIVE</b>\n\n"
            "<i>The archivist sealed your envelope with a wax seal...</i>\n\n"
            "Your materials have been passed to the typology expert. "
            "They will contact you within <b>24 hours</b>.\n\n"
            "⚔️ <i>The archive always remembers those who crossed its threshold.</i>"
        ),
        "expert_offer": (
            '<tg-emoji emoji-id="5886412370347036129">👤</tg-emoji> <b>EXPERT ANALYSIS</b>\n\n'
            "Preliminary analysis complete. But the chronicles hold much more...\n\n"
            "✦ Detailed breakdown of each facial feature\n"
            "✦ Complete genealogical phenotype map\n"
            "✦ Historical parallels and archival sources\n"
            "✦ Personal response from the archivist within 24 hours\n\n"
            '<tg-emoji emoji-id="5904462880941545555">🪙</tg-emoji><b>Cost: {price} EUR</b>\n\n'
            "<i>Do you wish to look deeper?</i>"
        ),
        "expert_requested": (
            "📜 <b>Request accepted into the archive</b>\n\n"
            "<i>The archivist made a note in the record book...</i>\n\n"
            "Your request for expert analysis has been submitted. "
            "The keeper of the archive will contact you within 24 hours.\n\n"
            "⚔️ <i>The archive always remembers those who crossed its threshold.</i>"
        ),

        # ── Photo collection ─────────────────────────────────────────────────────
        "front_photo_request": (
            '<tg-emoji emoji-id="5388922215347534633">📜</tg-emoji> <b>STEP I / III — EN FACE</b>\n\n'
            "♰ <b>The Archivist demands precision.</b>\n"
            "To minimize errors in the 1-3mm range, your photo must follow the "
            "<b>Sacred Rules:</b>\n\n"
            "1. Strict full-face (en face) and profile. No head tilts.\n"
            "2. Neutral expression. No smiling, no squinting.\n"
            "3. Good, even lighting. No deep shadows on the face.\n"
            "4. Keep the camera at least 1.5 meters away (use zoom) to avoid lens distortion.\n\n"
            "<i>Send your photo to open the chronicles...</i>"
        ),
        "profile_photo_request": (
            '<tg-emoji emoji-id="5388922215347534633">📜</tg-emoji> <b>STEP II / III — PROFILE</b>\n\n'
            "<i>The archivist turns the manuscript page...</i>\n\n"
            "Now send a photograph of your face <b>in profile</b> — side view.\n\n"
            "✦ Turn <b>head exactly 90°</b>\n"
            "✦ <b>Gaze</b> directed <b>forward</b>\n"
            "✦ Hair should not cover facial features"
        ),
        "optional_data_request": (
            '<tg-emoji emoji-id="5226512880362332956">📖</tg-emoji> <b>STEP III / III — ADDITIONAL INFO</b>\n\n'
            "<i>The archivist prepares to add to the chronicle...</i>\n\n"
            "You may provide additional information for more accurate analysis. "
            "Each point is optional — skip if you prefer not to share.\n\n"
            "Would you like to provide a <b>full-body photo</b>?"
        ),
        "fullbody_photo_request": (
            "📜 <b>FULL-BODY PHOTOGRAPH</b>\n\n"
            "<i>The archive expands its pages...</i>\n\n"
            "Send a full-body photograph.\n\n"
            "✦ Standing straight, feet slightly apart\n"
            "✦ Arms at sides\n"
            "✦ Neutral background"
        ),
        "ask_optional_data": (
            "📝 <b>Would you like to add text information?</b>\n\n"
            "<i>This will improve the accuracy of the chronicle.</i>"
        ),
        "age_request": (
            "🖋️ <b>AGE</b>\n\n"
            "<i>The quill touches the parchment...</i>\n\n"
            "Enter your age (e.g., <i>27</i>) or press Skip."
        ),
        "nationality_request": (
            "🖋️ <b>NATIONALITY</b>\n\n"
            "<i>The archivist consults the tables of peoples...</i>\n\n"
            "Enter your nationality or press Skip."
        ),
        "origin_request": (
            "🖋️ <b>FAMILY ORIGIN</b>\n\n"
            "<i>Genealogical records are opened...</i>\n\n"
            "Enter your family's region of origin or press Skip."
        ),
        "anthropometry_request": (
            "🖋️ <b>ANTHROPOMETRIC DATA</b>\n\n"
            "<i>The final lines of the record are prepared...</i>\n\n"
            "Enter data as: <code>height weight</code>\n"
            "Example: <code>182 75</code>\n\n"
            "Or press Skip."
        ),
        "data_privacy": (
            "\n\n"
            '<tg-emoji emoji-id="5951846549288917006">🔒</tg-emoji> '
            "<i>Your photos and data are not stored — they are deleted "
            "immediately after processing by the archivist.</i>"
        ),
        "no_photo": "🖼️ Please send a <b>photo</b>, not a file or text.",

        # ── Analysis ─────────────────────────────────────────────────────────────
        "analysis_error": (
            "⚠️ <b>Archive temporarily unavailable</b>\n\n"
            "<i>Something disturbed the silence of the library...\n"
            "The archivist could not complete the record.</i>\n\n"
            "Try again — press /start"
        ),
        "loading_0": (
            "⚗️ <b>The archivist studies the chronicles...</b>\n\n"
            "<i>🕯️ Candlelight flickers over the open manuscript...\n"
            "Shadows glide along the stone walls of the archive...</i>"
        ),
        "loading_1": (
            "🔍 <b>Comparing external features...</b>\n\n"
            "<i>📖 Pages of ancient volumes are being turned...\n"
            "The archivist consults the chronicle tables...</i>"
        ),
        "loading_2": (
            "📚 <b>Ancient volumes are opening...</b>\n\n"
            "<i>🗝️ Keys jingle at the archivist's belt...\n"
            "Sealed repositories reveal their secrets...</i>"
        ),
        "loading_3": (
            "🖋️ <b>The archive prepares the record...</b>\n\n"
            "<i>📜 The quill touches the parchment...\n"
            "Ink falls line by line...</i>"
        ),
        "loading_4": (
            "🌑 <b>Analyzing facial features...</b>\n\n"
            "<i>🔮 Shadows dance on the high vaults...\n"
            "The archivist descends into contemplation...</i>"
        ),
        "loading_5": (
            "⚔️ <b>Compiling the chronicle...</b>\n\n"
            "<i>🏰 The castle keeps its secrets...\n"
            "The record will be complete soon...</i>"
        ),
        "face_scan_caption": "🔬 <i>Anthropological mask — 468 facial landmarks</i>",
        "result_disclaimer": (
            "⚠️ <i>Racial type is determined visually — errors are possible that may distort "
            "the exact racial composition: the difference between types is only 1–3 mm. "
            "For precise analysis, consult our world-class experts.</i>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        ),
        "result_ethnicity": "🌍 <b>Ethnicity:</b> {value}",
        "result_race_type": "🏛 <b>Racial type:</b> {value}",
        "result_morphology_header": "\n━━━━━━ 【 MORPHOLOGICAL BREAKDOWN 】 ━━━━━━\n\n",
        "result_origin_header": "━━━━ 【 ORIGIN 】 ━━━━\n\n",
        "result_primary": "⚜️ <b>Primary type:</b> {name}\n   Similarity: <b>{pct}%</b>\n\n",
        "result_secondary_header": "📊 <b>Secondary admixtures:</b>\n",
        "result_secondary_none": "  ✧ Not determined",
        "result_confidence": "🔮 <b>Confidence:</b> {bar} {pct}%",

        # ── Criteria labels ──────────────────────────────────────────────────────
        "crit_facial_index": "Facial index",
        "crit_cephalic_index": "Cephalic index",
        "crit_orbital_index": "Orbital index",
        "crit_nasal_index": "Nasal index",
        "crit_forehead_height": "Forehead height",
        "crit_chin_height": "Chin height",
        "crit_cheekbone_height": "Cheekbone height",
        "crit_jaw_width": "Jaw width",
        "crit_forehead_form": "Forehead form",
        "crit_nose_bridge_form": "Nose bridge form",
        "crit_lip_form": "Lip form",
        "crit_chin_form": "Chin form",
        "crit_eyelid_fold": "Eyelid fold",
        "crit_eye_fissure": "Eye fissure",
        "crit_horizontal_profiling": "Horiz. profiling",
        "crit_brow_development": "Brow development",
        "crit_nasal_base": "Nasal base",
        "crit_vertical_profiling": "Vert. profiling",
        "crit_interocular": "Interocular distance",
        "crit_eye_depth": "Eye socket depth",
        "crit_eye_position": "Eye position on face",
        "crit_pigmentation": "Pigmentation",
        "crit_hair_structure": "Hair structure",
        "crit_build_type": "Body type",
        "crit_special_features": "Special features",
    },
}


def t(key: str, lang: str = "ru", **kwargs) -> str:
    """Возвращает переведённую строку. Fallback: ru → key."""
    text = _T.get(lang, _T["ru"]).get(key) or _T["ru"].get(key, key)
    return text.format(**kwargs) if kwargs else text


def get_loading_messages(lang: str) -> list[str]:
    return [t(f"loading_{i}", lang) for i in range(6)]
