from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.i18n import t


def language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="Русский",
            callback_data="set_lang_ru",
            icon_custom_emoji_id="5449408995691341691",
        ),
        InlineKeyboardButton(
            text="English",
            callback_data="set_lang_en",
            icon_custom_emoji_id="5202196682497859879",
        ),
    ]])


def welcome_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=t("btn_ai", lang),
                callback_data="choose_ai",
                icon_custom_emoji_id="5931614414351372818",
            ),
            InlineKeyboardButton(
                text=t("btn_expert", lang),
                callback_data="choose_expert",
                icon_custom_emoji_id="5886412370347036129",
            ),
        ],
        [InlineKeyboardButton(
            text=t("btn_what_is", lang),
            callback_data="what_is",
            icon_custom_emoji_id="5771695636411847302",
        )],
        [InlineKeyboardButton(
            text=t("btn_language", lang),
            callback_data="change_language",
            icon_custom_emoji_id="5879585266426973039",
        )],
    ])


def back_to_menu_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=t("btn_back", lang), callback_data="back_to_start")
    ]])


def skip_keyboard(callback: str, lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=t("btn_skip", lang), callback_data=f"skip_{callback}")
    ]])


def optional_fullbody_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=t("btn_add_fullbody", lang),
            callback_data="add_fullbody",
            icon_custom_emoji_id="6050592962730005028",
        )],
        [InlineKeyboardButton(text=t("btn_skip", lang), callback_data="skip_fullbody")],
    ])


def optional_data_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=t("btn_add_data", lang),
            callback_data="add_optional_data",
            icon_custom_emoji_id="5879841310902324730",
        )],
        [InlineKeyboardButton(
            text=t("btn_start_analysis", lang),
            callback_data="start_analysis",
            icon_custom_emoji_id="5839200986022812209",
        )],
    ])


def expert_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_request_expert", lang), callback_data="request_expert")],
        [InlineKeyboardButton(text=t("btn_back_archive", lang), callback_data="back_to_start")],
    ])


def restart_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=t("btn_new_analysis", lang), callback_data="back_to_start")
    ]])


def tribute_payment_keyboard(link: str, lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=t("btn_pay_tribute", lang),
            url=link,
            icon_custom_emoji_id="6028338546736107668",
            style="primary",
        )],
    ])


def start_after_payment_keyboard(service_type: str, lang: str = "ru") -> InlineKeyboardMarkup:
    key = "btn_start_ai" if service_type == "ai" else "btn_start_expert"
    emoji_id = "5931614414351372818" if service_type == "ai" else "5886412370347036129"
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text=t(key, lang),
            callback_data=f"start_paid_{service_type}",
            icon_custom_emoji_id=emoji_id,
        )
    ]])


# ── Только для админки (не переводится) ──────────────────────────────────────

def admin_panel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="💳 Платежи на проверке", callback_data="admin_payments")],
        [InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users")],
        [InlineKeyboardButton(text="📋 Заявки на разбор", callback_data="admin_requests")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="✏️ Редактировать тексты", callback_data="admin_texts")],
    ])


def admin_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="◀️ Назад в панель", callback_data="admin_back")
    ]])


def broadcast_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Отправить", callback_data="broadcast_send")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_back")],
    ])


def request_action_keyboard(request_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Принято в работу", callback_data=f"req_accept_{request_id}")],
        [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"req_reject_{request_id}")],
    ])


def payment_check_keyboard(payment_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить оплату", callback_data=f"pay_confirm_{payment_id}")],
        [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"pay_reject_{payment_id}")],
    ])
