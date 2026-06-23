import asyncio
import os
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext

from bot.states import ArchiveStates
from bot.i18n import t, get_loading_messages
from bot.keyboards.inline import expert_keyboard, restart_keyboard
from bot.services.ai_service import analyze_photos
from bot.database.db import increment_analysis, create_expert_request
from bot.config import ADMIN_IDS, ADMIN_CHAT_ID, EXPERT_PRICE

EXPERT_PRICE_EUR = EXPERT_PRICE // 100

router = Router()



async def _animate_loading(chat_id: int, bot: Bot, stop_event: asyncio.Event, lang: str = "ru"):
    from aiogram.types import InputMediaPhoto

    msgs = get_loading_messages(lang)
    current_msg = None
    i = 0

    while not stop_event.is_set():
        idx = i % len(msgs)
        img_path = f"assets/loading_{idx + 1}.jpg"
        caption = msgs[idx]
        try:
            if current_msg is None:
                if os.path.exists(img_path):
                    current_msg = await bot.send_photo(
                        chat_id, FSInputFile(img_path), caption=caption, parse_mode="HTML"
                    )
                else:
                    current_msg = await bot.send_message(chat_id, caption, parse_mode="HTML")
            else:
                if os.path.exists(img_path):
                    await bot.edit_message_media(
                        chat_id=chat_id,
                        message_id=current_msg.message_id,
                        media=InputMediaPhoto(
                            media=FSInputFile(img_path),
                            caption=caption,
                            parse_mode="HTML",
                        ),
                    )
                else:
                    await bot.edit_message_caption(
                        chat_id=chat_id,
                        message_id=current_msg.message_id,
                        caption=caption,
                        parse_mode="HTML",
                    )
        except Exception:
            pass
        i += 1
        try:
            await asyncio.wait_for(asyncio.shield(stop_event.wait()), timeout=4.0)
        except asyncio.TimeoutError:
            pass

    if current_msg:
        try:
            await current_msg.delete()
        except Exception:
            pass


async def start_analysis(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    lang = data.get("lang", "ru")

    front_bytes: bytes | None = data.get("front_photo")
    if not front_bytes:
        await message.answer(t("analysis_error", lang), parse_mode="HTML")
        await state.clear()
        return

    # Эксперт-путь: пропускаем ИИ, сразу создаём заявку
    if data.get("analysis_type") == "expert":
        await _handle_expert_path(message, state, bot, data)
        return

    await state.set_state(ArchiveStates.analyzing)

    stop_event = asyncio.Event()
    anim_task = asyncio.create_task(_animate_loading(message.chat.id, bot, stop_event, lang))

    user = message.from_user
    uname = f"@{user.username}" if user.username else f"tg://user?id={user.id}"
    notify_targets = list(ADMIN_IDS)
    if ADMIN_CHAT_ID and ADMIN_CHAT_ID not in notify_targets:
        notify_targets.append(ADMIN_CHAT_ID)
    for admin_id in notify_targets:
        try:
            await bot.send_message(
                admin_id,
                f"🤖 <b>Новый ИИ-разбор</b>\n"
                f"👤 {user.first_name} ({uname})\n"
                f"🆔 <code>{user.id}</code>",
                parse_mode="HTML",
            )
        except Exception:
            pass

    try:
        profile_bytes: bytes | None = data.get("profile_photo")
        fullbody_bytes: bytes | None = data.get("fullbody_photo")
        extra = {
            "age": data.get("age"),
            "nationality": data.get("nationality"),
            "origin": data.get("origin"),
            "anthropometry": data.get("anthropometry"),
        }

        _, result_data, _ = await analyze_photos(
            front_bytes, profile_bytes, fullbody_bytes, extra, lang=lang
        )

        stop_event.set()
        await anim_task

        await increment_analysis(message.chat.id)

        try:
            from bot.services.pdf_service import generate_result_pdf
            from aiogram.types import BufferedInputFile
            pdf_bytes = await asyncio.get_event_loop().run_in_executor(
                None, generate_result_pdf, result_data, lang
            )
            user = message.from_user
            username = user.first_name or user.username or "пользователь"
            pdf_caption = f"📄 Хроника — {username}" if lang == "ru" else f"📄 Chronicle — {username}"
            await message.answer_document(
                BufferedInputFile(pdf_bytes, filename="chronicle.pdf"),
                caption=pdf_caption,
            )
        except Exception as e:
            print(f"PDF generation error: {e}")

        _expert_img = "assets/archivirus.jpg"
        _expert_text = _build_expert_offer_text(lang)
        _expert_kb = expert_keyboard(lang)
        if os.path.exists(_expert_img):
            await message.answer_photo(
                FSInputFile(_expert_img),
                caption=_expert_text,
                parse_mode="HTML",
                reply_markup=_expert_kb,
            )
        else:
            await message.answer(_expert_text, parse_mode="HTML", reply_markup=_expert_kb)

        await state.update_data(result_data=result_data)
        await state.set_state(ArchiveStates.showing_results)

    except Exception as e:
        stop_event.set()
        await anim_task
        print(f"Analysis error: {e}")
        await message.answer(t("analysis_error", lang), parse_mode="HTML")
        await state.clear()


def _build_expert_offer_text(lang: str = "ru") -> str:
    return t("expert_offer", lang, price=EXPERT_PRICE_EUR)


@router.callback_query(F.data == "request_expert", ArchiveStates.showing_results)
async def request_expert(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await callback.answer()
    data = await state.get_data()
    lang = data.get("lang", "ru")

    request_id = await create_expert_request(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
        age=data.get("age"),
        nationality=data.get("nationality"),
        origin=data.get("origin"),
        anthropometry=data.get("anthropometry"),
    )

    _img = "assets/envelope.jpg"
    _text = t("expert_requested", lang)
    _kb = restart_keyboard(lang)
    if os.path.exists(_img):
        await callback.message.answer_photo(FSInputFile(_img), caption=_text, parse_mode="HTML", reply_markup=_kb)
    else:
        await callback.message.answer(_text, parse_mode="HTML", reply_markup=_kb)

    admin_notification = _build_admin_notification(callback.from_user, data, request_id, source="ai_upsell")

    notify_targets = list(ADMIN_IDS)
    if ADMIN_CHAT_ID and ADMIN_CHAT_ID not in notify_targets:
        notify_targets.append(ADMIN_CHAT_ID)

    for admin_id in notify_targets:
        try:
            await bot.send_message(admin_id, admin_notification, parse_mode="HTML")
        except Exception as e:
            print(f"Не удалось уведомить администратора {admin_id}: {e}")

    await state.set_state(ArchiveStates.expert_upsell)


async def _handle_expert_path(message: Message, state: FSMContext, bot: Bot, data: dict):
    lang = data.get("lang", "ru")
    user = message.from_user
    request_id = await create_expert_request(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
        age=data.get("age"),
        nationality=data.get("nationality"),
        origin=data.get("origin"),
        anthropometry=data.get("anthropometry"),
    )

    _img = "assets/envelope.jpg"
    _text = t("expert_direct_confirmed", lang)
    _kb = restart_keyboard(lang)
    if os.path.exists(_img):
        await message.answer_photo(FSInputFile(_img), caption=_text, parse_mode="HTML", reply_markup=_kb)
    else:
        await message.answer(_text, parse_mode="HTML", reply_markup=_kb)

    notification = _build_admin_notification(user, data, request_id, source="expert_direct")
    notify_targets = list(ADMIN_IDS)
    if ADMIN_CHAT_ID and ADMIN_CHAT_ID not in notify_targets:
        notify_targets.append(ADMIN_CHAT_ID)

    for admin_id in notify_targets:
        try:
            await bot.send_message(admin_id, notification, parse_mode="HTML")
            # Пересылаем фото эксперту
            for label, key in [("анфас", "front_photo"), ("профиль", "profile_photo"), ("в рост", "fullbody_photo")]:
                photo_bytes: bytes | None = data.get(key)
                if photo_bytes:
                    from aiogram.types import BufferedInputFile
                    await bot.send_photo(
                        admin_id,
                        BufferedInputFile(photo_bytes, filename=f"{key}.jpg"),
                        caption=f"📸 Фото {label} — заявка #{request_id}",
                    )
        except Exception as e:
            print(f"Не удалось уведомить администратора {admin_id}: {e}")

    await state.clear()


def _build_admin_notification(user, data: dict, request_id: int, source: str = "ai_upsell") -> str:
    username = f"@{user.username}" if user.username else "нет"
    source_label = "🧠 Прямой заказ эксперта" if source == "expert_direct" else "🤖 После ИИ-анализа"
    lines = [
        f"📋 <b>Новая заявка на экспертный разбор #{request_id}</b>",
        f"📌 Источник: {source_label}\n",
        f"👤 {user.first_name} ({username})",
        f"🆔 <code>{user.id}</code>",
    ]
    if data.get("age"):
        lines.append(f"🎂 Возраст: {data['age']}")
    if data.get("nationality"):
        lines.append(f"🌍 Национальность: {data['nationality']}")
    if data.get("origin"):
        lines.append(f"🏰 Происхождение: {data['origin']}")
    if data.get("anthropometry"):
        lines.append(f"📏 Антропометрия: {data['anthropometry']}")

    if user.username:
        lines.append(f"\n💬 <a href='https://t.me/{user.username}'>Написать @{user.username}</a>")
    else:
        lines.append(f"\n💬 Написать пользователю: tg://user?id={user.id}")
    return "\n".join(lines)
