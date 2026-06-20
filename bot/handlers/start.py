import os
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext

from bot.states import ArchiveStates
from bot.i18n import t
from bot.keyboards.inline import welcome_keyboard, back_to_menu_keyboard, language_keyboard
from bot.database.db import upsert_user, get_language, set_language

router = Router()

WELCOME_IMAGE_PATH = "assets/welcome.jpg"


async def _get_lang(user_id: int, state: FSMContext) -> str:
    data = await state.get_data()
    if "lang" in data:
        return data["lang"]
    lang = await get_language(user_id) or "ru"
    await state.update_data(lang=lang)
    return lang


async def _send_welcome(target: Message, state: FSMContext, lang: str):
    text = t("welcome", lang)
    kb = welcome_keyboard(lang)
    if os.path.exists(WELCOME_IMAGE_PATH):
        photo = FSInputFile(WELCOME_IMAGE_PATH)
        await target.answer_photo(photo=photo, caption=text, parse_mode="HTML", reply_markup=kb)
    else:
        await target.answer(text, parse_mode="HTML", reply_markup=kb)
    await state.set_state(ArchiveStates.welcome)


async def _show_language_select(target: Message, state: FSMContext):
    await target.answer(t("choose_language"), parse_mode="HTML", reply_markup=language_keyboard())
    await state.set_state(ArchiveStates.choosing_language)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await upsert_user(message.from_user.id, message.from_user.username, message.from_user.first_name)

    saved_lang = await get_language(message.from_user.id)
    if saved_lang:
        await state.update_data(lang=saved_lang)
        await _send_welcome(message, state, saved_lang)
    else:
        await _show_language_select(message, state)


@router.message(Command("language"))
async def cmd_language(message: Message, state: FSMContext):
    await _show_language_select(message, state)


@router.callback_query(F.data == "change_language")
async def change_language(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await _show_language_select(callback.message, state)


@router.callback_query(F.data.in_({"set_lang_ru", "set_lang_en"}))
async def set_lang(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    lang = "ru" if callback.data == "set_lang_ru" else "en"
    await set_language(callback.from_user.id, lang)
    await state.update_data(lang=lang)
    await _send_welcome(callback.message, state, lang)


@router.callback_query(F.data == "back_to_start")
async def back_to_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    await upsert_user(callback.from_user.id, callback.from_user.username, callback.from_user.first_name)
    saved_lang = await get_language(callback.from_user.id) or "ru"
    await state.update_data(lang=saved_lang)
    await _send_welcome(callback.message, state, saved_lang)


@router.callback_query(F.data == "what_is")
async def what_is(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    lang = await _get_lang(callback.from_user.id, state)
    await callback.message.answer(t("what_is", lang), parse_mode="HTML", reply_markup=back_to_menu_keyboard(lang))
