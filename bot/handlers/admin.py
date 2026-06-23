import asyncio
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.config import ADMIN_IDS
from bot.states import AdminStates
from bot.texts import ADMIN_PANEL_TEXT, BROADCAST_COMPOSE, BROADCAST_CONFIRM, BROADCAST_DONE
from bot.keyboards.inline import (
    admin_panel_keyboard, admin_back_keyboard, broadcast_confirm_keyboard, request_action_keyboard
)
from bot.database.db import (
    get_stats, get_recent_users, get_expert_requests, get_all_telegram_ids,
    update_expert_status, get_bot_text, set_bot_text, get_pending_payments,
    confirm_payment, reject_payment, add_balance,
)
from bot.config import AI_PRICE, EXPERT_PRICE

router = Router()

EDITABLE_TEXTS = {
    "welcome": "Приветственный текст",
    "expert_offer": "Оффер экспертного разбора",
    "expert_requested": "Подтверждение заявки",
}


def _is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


# ── Вход в панель ─────────────────────────────────────────────────────────────

@router.message(Command("admin"))
async def admin_entry(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        return
    await state.clear()
    await message.answer(ADMIN_PANEL_TEXT, parse_mode="HTML", reply_markup=admin_panel_keyboard())
    await state.set_state(AdminStates.panel)


@router.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(AdminStates.panel)
    await callback.message.answer(
        ADMIN_PANEL_TEXT, parse_mode="HTML", reply_markup=admin_panel_keyboard()
    )


# ── Статистика ────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    if not _is_admin(callback.from_user.id):
        return await callback.answer("Нет доступа", show_alert=True)

    await callback.answer()
    stats = await get_stats()

    text = (
        "📊 <b>СТАТИСТИКА АРХИВА</b>\n\n"
        f"👥 Всего пользователей: <b>{stats['total_users']}</b>\n"
        f"🆕 Новых сегодня: <b>{stats['new_today']}</b>\n"
        f"🔮 Всего анализов: <b>{stats['total_analyses']}</b>\n"
        f"📋 Ожидают разбора: <b>{stats['expert_pending']}</b>"
    )
    await callback.message.answer(text, parse_mode="HTML", reply_markup=admin_back_keyboard())


# ── Пользователи ──────────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin_users")
async def admin_users(callback: CallbackQuery):
    if not _is_admin(callback.from_user.id):
        return await callback.answer("Нет доступа", show_alert=True)

    await callback.answer()
    users = await get_recent_users(limit=10)

    if not users:
        await callback.message.answer(
            "👥 Пользователей пока нет.", reply_markup=admin_back_keyboard()
        )
        return

    lines = ["👥 <b>ПОСЛЕДНИЕ ПОЛЬЗОВАТЕЛИ</b>\n"]
    for u in users:
        username = f"@{u['username']}" if u["username"] else "—"
        lines.append(
            f"• {u['first_name']} ({username})\n"
            f"  🆔 <code>{u['telegram_id']}</code> | "
            f"Анализов: {u['analyses_count']} | {u['created_at'][:10]}"
        )

    await callback.message.answer(
        "\n".join(lines), parse_mode="HTML", reply_markup=admin_back_keyboard()
    )


# ── Платежи на проверке ───────────────────────────────────────────────────────

@router.callback_query(F.data == "admin_payments")
async def admin_payments(callback: CallbackQuery):
    if not _is_admin(callback.from_user.id):
        return await callback.answer("Нет доступа", show_alert=True)

    await callback.answer()
    from bot.keyboards.inline import payment_check_keyboard
    payments = await get_pending_payments(limit=10)

    if not payments:
        await callback.message.answer(
            "💳 Нет платежей на проверке.", reply_markup=admin_back_keyboard()
        )
        return

    await callback.message.answer(
        f"💳 <b>ПЛАТЕЖИ НА ПРОВЕРКЕ</b> ({len(payments)} шт.):",
        parse_mode="HTML",
    )
    for p in payments:
        username = f"@{p['username']}" if p["username"] else "—"
        service_ru = "Типирование ИИ" if p["service_type"] == "ai" else "Экспертный разбор"
        info = (
            f"💳 <b>Платёж #{p['id']}</b>\n"
            f"👤 {p['first_name']} ({username})\n"
            f"🆔 <code>{p['telegram_id']}</code>\n"
            f"📌 {service_ru} — <b>{p['amount']} ₽</b>\n"
            f"📅 {p['created_at'][:16]}"
        )
        await callback.message.answer(info, parse_mode="HTML")
        if p.get("screenshot_file_id"):
            await callback.message.answer_photo(
                p["screenshot_file_id"],
                reply_markup=payment_check_keyboard(p["id"]),
            )


# ── Подтверждение / отклонение платежа ───────────────────────────────────────

@router.callback_query(F.data.startswith("pay_confirm_"))
async def admin_pay_confirm(callback: CallbackQuery, bot: Bot):
    if not _is_admin(callback.from_user.id):
        return await callback.answer("Нет доступа", show_alert=True)

    payment_id = int(callback.data.split("_")[-1])
    payment = await confirm_payment(payment_id)
    if not payment:
        return await callback.answer("Платёж не найден", show_alert=True)

    await callback.answer("✅ Оплата подтверждена")
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(f"✅ Платёж #{payment_id} подтверждён, баланс начислен.")

    import os
    from aiogram.types import FSInputFile
    from bot.i18n import t
    from bot.database.db import get_user_lang

    user_id = payment["telegram_id"]
    try:
        lang = await get_user_lang(user_id)
    except Exception:
        lang = "ru"

    img = "assets/payment.jpg"
    text = t("payment_confirmed", lang)
    try:
        if os.path.exists(img):
            await bot.send_photo(
                user_id,
                FSInputFile(img),
                caption=text,
                parse_mode="HTML",
            )
        else:
            await bot.send_message(user_id, text, parse_mode="HTML")
    except Exception as e:
        print(f"Не удалось уведомить пользователя {user_id}: {e}")


@router.callback_query(F.data.startswith("pay_reject_"))
async def admin_pay_reject(callback: CallbackQuery, bot: Bot):
    if not _is_admin(callback.from_user.id):
        return await callback.answer("Нет доступа", show_alert=True)

    payment_id = int(callback.data.split("_")[-1])
    payment = await reject_payment(payment_id)
    if not payment:
        return await callback.answer("Платёж не найден", show_alert=True)

    await callback.answer("❌ Отклонено")
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(f"❌ Платёж #{payment_id} отклонён.")

    from bot.i18n import t
    from bot.database.db import get_user_lang

    user_id = payment["telegram_id"]
    try:
        lang = await get_user_lang(user_id)
    except Exception:
        lang = "ru"

    try:
        await bot.send_message(user_id, t("payment_rejected", lang), parse_mode="HTML")
    except Exception as e:
        print(f"Не удалось уведомить пользователя {user_id}: {e}")


# ── Заявки на экспертный разбор ───────────────────────────────────────────────

@router.callback_query(F.data == "admin_requests")
async def admin_requests(callback: CallbackQuery):
    if not _is_admin(callback.from_user.id):
        return await callback.answer("Нет доступа", show_alert=True)

    await callback.answer()
    requests = await get_expert_requests(status="pending", limit=10)

    if not requests:
        await callback.message.answer(
            "📋 Новых заявок нет.", reply_markup=admin_back_keyboard()
        )
        return

    await callback.message.answer(
        f"📋 <b>ЗАЯВКИ НА РАЗБОР</b> ({len(requests)} ожидает):",
        parse_mode="HTML",
    )

    for req in requests:
        username = f"@{req['username']}" if req["username"] else "—"
        info_lines = [
            f"📋 <b>Заявка #{req['id']}</b>",
            f"👤 {req['first_name']} ({username})",
            f"🆔 <code>{req['telegram_id']}</code>",
            f"📅 {req['created_at'][:16]}",
        ]
        if req.get("age"):
            info_lines.append(f"🎂 Возраст: {req['age']}")
        if req.get("nationality"):
            info_lines.append(f"🌍 Нац.: {req['nationality']}")
        if req.get("origin"):
            info_lines.append(f"🏰 Происх.: {req['origin']}")
        if req.get("anthropometry"):
            info_lines.append(f"📏 Антропометрия: {req['anthropometry']}")
        if req.get("username"):
            info_lines.append(f"💬 <a href='https://t.me/{req['username']}'>Написать @{req['username']}</a>")
        else:
            info_lines.append(f"💬 <a href='tg://user?id={req['telegram_id']}'>Написать</a>")

        await callback.message.answer(
            "\n".join(info_lines),
            parse_mode="HTML",
            reply_markup=request_action_keyboard(req["id"]),
        )


@router.callback_query(F.data.startswith("req_accept_"))
async def accept_request(callback: CallbackQuery, bot: Bot):
    if not _is_admin(callback.from_user.id):
        return await callback.answer("Нет доступа", show_alert=True)

    request_id = int(callback.data.split("_")[-1])
    await update_expert_status(request_id, "accepted")
    await callback.answer("✅ Принято в работу")
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(f"✅ Заявка #{request_id} принята в работу.")


@router.callback_query(F.data.startswith("req_reject_"))
async def reject_request(callback: CallbackQuery):
    if not _is_admin(callback.from_user.id):
        return await callback.answer("Нет доступа", show_alert=True)

    request_id = int(callback.data.split("_")[-1])
    await update_expert_status(request_id, "rejected")
    await callback.answer("❌ Отклонено")
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(f"❌ Заявка #{request_id} отклонена.")


# ── Выдать бесплатный разбор ─────────────────────────────────────────────────

@router.callback_query(F.data == "admin_grant")
async def admin_grant(callback: CallbackQuery, state: FSMContext):
    if not _is_admin(callback.from_user.id):
        return await callback.answer("Нет доступа", show_alert=True)
    await callback.answer()
    await callback.message.answer(
        "🎁 <b>ВЫДАТЬ БЕСПЛАТНЫЙ РАЗБОР</b>\n\n"
        "Введи Telegram ID пользователя:",
        parse_mode="HTML",
        reply_markup=admin_back_keyboard(),
    )
    await state.set_state(AdminStates.grant_enter_id)


@router.message(AdminStates.grant_enter_id)
async def grant_enter_id(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        return
    if not message.text or not message.text.strip().lstrip("-").isdigit():
        await message.answer("⚠️ Введи числовой Telegram ID.")
        return
    await state.update_data(grant_user_id=int(message.text.strip()))
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🤖 Типирование ИИ", callback_data="grant_ai"),
            InlineKeyboardButton(text="👥 Экспертный разбор", callback_data="grant_expert"),
        ],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back")],
    ])
    await message.answer("Выбери тип разбора:", reply_markup=kb)
    await state.set_state(AdminStates.grant_choose_service)


@router.callback_query(F.data.in_({"grant_ai", "grant_expert"}), AdminStates.grant_choose_service)
async def grant_choose_service(callback: CallbackQuery, state: FSMContext, bot: Bot):
    if not _is_admin(callback.from_user.id):
        return await callback.answer("Нет доступа", show_alert=True)

    data = await state.get_data()
    user_id = data.get("grant_user_id")
    service_type = "ai" if callback.data == "grant_ai" else "expert"
    amount = AI_PRICE if service_type == "ai" else EXPERT_PRICE
    label = "Типирование ИИ" if service_type == "ai" else "Экспертный разбор"

    await add_balance(user_id, amount)
    await callback.answer("✅ Выдано")
    await callback.message.answer(
        f"✅ Пользователю <code>{user_id}</code> выдан бесплатный <b>{label}</b>.",
        parse_mode="HTML",
        reply_markup=admin_back_keyboard(),
    )

    import os
    from aiogram.types import FSInputFile
    from bot.i18n import t
    from bot.database.db import get_user_lang
    from bot.keyboards.inline import start_after_payment_keyboard
    try:
        lang = await get_user_lang(user_id)
    except Exception:
        lang = "ru"
    text = t("payment_confirmed", lang)
    kb = start_after_payment_keyboard(service_type, lang)
    img = "assets/payment.jpg"
    try:
        if os.path.exists(img):
            await bot.send_photo(user_id, FSInputFile(img), caption=text, parse_mode="HTML", reply_markup=kb)
        else:
            await bot.send_message(user_id, text, parse_mode="HTML", reply_markup=kb)
    except Exception as e:
        await callback.message.answer(f"⚠️ Не удалось уведомить пользователя: {e}")

    await state.set_state(AdminStates.panel)


# ── Рассылка ──────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast(callback: CallbackQuery, state: FSMContext):
    if not _is_admin(callback.from_user.id):
        return await callback.answer("Нет доступа", show_alert=True)

    await callback.answer()
    await callback.message.answer(BROADCAST_COMPOSE, parse_mode="HTML")
    await state.set_state(AdminStates.broadcast_compose)


@router.message(AdminStates.broadcast_compose)
async def broadcast_receive_text(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        return

    await state.update_data(broadcast_text=message.html_text)
    await message.answer(message.html_text, parse_mode="HTML")
    await message.answer(BROADCAST_CONFIRM, parse_mode="HTML", reply_markup=broadcast_confirm_keyboard())
    await state.set_state(AdminStates.broadcast_confirm)


@router.callback_query(F.data == "broadcast_send", AdminStates.broadcast_confirm)
async def broadcast_send(callback: CallbackQuery, state: FSMContext, bot: Bot):
    if not _is_admin(callback.from_user.id):
        return await callback.answer("Нет доступа", show_alert=True)

    await callback.answer()
    data = await state.get_data()
    text = data.get("broadcast_text", "")

    user_ids = await get_all_telegram_ids()
    sent = 0
    failed = 0

    status_msg = await callback.message.answer(
        f"⏳ Рассылка... 0 / {len(user_ids)}"
    )

    for uid in user_ids:
        try:
            await bot.send_message(uid, text, parse_mode="HTML")
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)

        if (sent + failed) % 20 == 0:
            try:
                await status_msg.edit_text(f"⏳ Рассылка... {sent + failed} / {len(user_ids)}")
            except Exception:
                pass

    await status_msg.edit_text(BROADCAST_DONE.format(sent=sent, failed=failed))
    await state.set_state(AdminStates.panel)


# ── Редактирование текстов ────────────────────────────────────────────────────

@router.callback_query(F.data == "admin_texts")
async def admin_texts(callback: CallbackQuery, state: FSMContext):
    if not _is_admin(callback.from_user.id):
        return await callback.answer("Нет доступа", show_alert=True)

    await callback.answer()
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    buttons = [
        [InlineKeyboardButton(text=label, callback_data=f"edit_text_{key}")]
        for key, label in EDITABLE_TEXTS.items()
    ]
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back")])

    await callback.message.answer(
        "✏️ <b>РЕДАКТИРОВАНИЕ ТЕКСТОВ</b>\n\nВыбери текст для редактирования:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )
    await state.set_state(AdminStates.edit_text_select)


@router.callback_query(F.data.startswith("edit_text_"), AdminStates.edit_text_select)
async def edit_text_select(callback: CallbackQuery, state: FSMContext):
    if not _is_admin(callback.from_user.id):
        return await callback.answer("Нет доступа", show_alert=True)

    key = callback.data.replace("edit_text_", "")
    await state.update_data(edit_text_key=key)

    current = await get_bot_text(key, "(не задан)")
    await callback.answer()
    await callback.message.answer(
        f"✏️ Текущий текст для <b>{EDITABLE_TEXTS.get(key, key)}</b>:\n\n"
        f"{current}\n\n"
        f"Введи новый текст (HTML поддерживается) или /cancel:",
        parse_mode="HTML",
    )
    await state.set_state(AdminStates.edit_text_input)


@router.message(AdminStates.edit_text_input)
async def edit_text_input(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        return

    data = await state.get_data()
    key = data.get("edit_text_key")
    if not key:
        return

    await set_bot_text(key, message.html_text)
    await message.answer(
        f"✅ Текст <b>{EDITABLE_TEXTS.get(key, key)}</b> обновлён.",
        parse_mode="HTML",
        reply_markup=admin_back_keyboard(),
    )
    await state.set_state(AdminStates.panel)


@router.message(Command("cancel"))
async def cancel_admin(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        return
    current_state = await state.get_state()
    if current_state and current_state.startswith("AdminStates"):
        await state.set_state(AdminStates.panel)
        await message.answer(
            ADMIN_PANEL_TEXT, parse_mode="HTML", reply_markup=admin_panel_keyboard()
        )
