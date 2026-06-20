import os
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, PhotoSize, FSInputFile
from aiogram.fsm.context import FSMContext

from bot.states import ArchiveStates
from bot.i18n import t
from bot.keyboards.inline import optional_fullbody_keyboard, optional_data_keyboard, skip_keyboard

router = Router()


async def _get_lang(state: FSMContext) -> str:
    data = await state.get_data()
    return data.get("lang", "ru")


async def _download_largest_photo(bot: Bot, photos: list[PhotoSize]) -> bytes:
    largest = max(photos, key=lambda p: p.file_size or 0)
    file = await bot.get_file(largest.file_id)
    buf = await bot.download_file(file.file_path)
    return buf.read()


# ── Фото анфас ───────────────────────────────────────────────────────────────

@router.message(ArchiveStates.collecting_front_photo, F.photo)
async def receive_front_photo(message: Message, state: FSMContext, bot: Bot):
    lang = await _get_lang(state)
    photo_bytes = await _download_largest_photo(bot, message.photo)
    await state.update_data(front_photo=photo_bytes)
    profile_example = "assets/example_profile.jpg"
    caption = t("profile_photo_request", lang) + t("data_privacy", lang)
    if os.path.exists(profile_example):
        await message.answer_photo(
            FSInputFile(profile_example),
            caption=caption,
            parse_mode="HTML",
        )
    else:
        await message.answer(caption, parse_mode="HTML")
    await state.set_state(ArchiveStates.collecting_profile_photo)


@router.message(ArchiveStates.collecting_front_photo)
async def front_photo_wrong(message: Message, state: FSMContext):
    lang = await _get_lang(state)
    await message.answer(t("no_photo", lang), parse_mode="HTML")


# ── Фото профиль ─────────────────────────────────────────────────────────────

@router.message(ArchiveStates.collecting_profile_photo, F.photo)
async def receive_profile_photo(message: Message, state: FSMContext, bot: Bot):
    lang = await _get_lang(state)
    photo_bytes = await _download_largest_photo(bot, message.photo)
    await state.update_data(profile_photo=photo_bytes)
    img = "assets/front_request.jpg"
    caption = t("optional_data_request", lang)
    if os.path.exists(img):
        await message.answer_photo(
            FSInputFile(img),
            caption=caption,
            parse_mode="HTML",
            reply_markup=optional_fullbody_keyboard(lang),
        )
    else:
        await message.answer(caption, parse_mode="HTML", reply_markup=optional_fullbody_keyboard(lang))
    await state.set_state(ArchiveStates.asking_optional)


@router.message(ArchiveStates.collecting_profile_photo)
async def profile_photo_wrong(message: Message, state: FSMContext):
    lang = await _get_lang(state)
    await message.answer(t("no_photo", lang), parse_mode="HTML")


# ── Фото в рост ──────────────────────────────────────────────────────────────

@router.callback_query(F.data == "add_fullbody", ArchiveStates.asking_optional)
async def ask_fullbody(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    lang = await _get_lang(state)
    await callback.message.answer(t("fullbody_photo_request", lang), parse_mode="HTML")
    await state.set_state(ArchiveStates.collecting_fullbody)


@router.message(ArchiveStates.collecting_fullbody, F.photo)
async def receive_fullbody_photo(message: Message, state: FSMContext, bot: Bot):
    photo_bytes = await _download_largest_photo(bot, message.photo)
    await state.update_data(fullbody_photo=photo_bytes)
    await _ask_optional_data(message, state)


@router.message(ArchiveStates.collecting_fullbody)
async def fullbody_wrong(message: Message, state: FSMContext):
    lang = await _get_lang(state)
    await message.answer(t("no_photo", lang), parse_mode="HTML")


@router.callback_query(F.data == "skip_fullbody", ArchiveStates.asking_optional)
async def skip_fullbody(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await _ask_optional_data(callback.message, state)


async def _ask_optional_data(message: Message, state: FSMContext):
    lang = await _get_lang(state)
    img = "assets/profile_request.jpg"
    caption = t("ask_optional_data", lang)
    if os.path.exists(img):
        await message.answer_photo(
            FSInputFile(img),
            caption=caption,
            parse_mode="HTML",
            reply_markup=optional_data_keyboard(lang),
        )
    else:
        await message.answer(caption, parse_mode="HTML", reply_markup=optional_data_keyboard(lang))


# ── Опциональные данные ───────────────────────────────────────────────────────

@router.callback_query(F.data == "add_optional_data")
async def add_optional_data(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    lang = await _get_lang(state)
    await callback.message.answer(t("age_request", lang), parse_mode="HTML", reply_markup=skip_keyboard("age", lang))
    await state.set_state(ArchiveStates.asking_age)


@router.callback_query(F.data == "start_analysis")
async def go_to_analysis(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    from bot.handlers.analysis import start_analysis
    await start_analysis(callback.message, state, callback.bot)


# ── Возраст ───────────────────────────────────────────────────────────────────

@router.message(ArchiveStates.asking_age)
async def receive_age(message: Message, state: FSMContext):
    lang = await _get_lang(state)
    if message.text and message.text.strip():
        await state.update_data(age=message.text.strip()[:20])
    await message.answer(t("nationality_request", lang), parse_mode="HTML", reply_markup=skip_keyboard("nationality", lang))
    await state.set_state(ArchiveStates.asking_nationality)


@router.callback_query(F.data == "skip_age", ArchiveStates.asking_age)
async def skip_age(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    lang = await _get_lang(state)
    await callback.message.answer(t("nationality_request", lang), parse_mode="HTML", reply_markup=skip_keyboard("nationality", lang))
    await state.set_state(ArchiveStates.asking_nationality)


# ── Национальность ────────────────────────────────────────────────────────────

@router.message(ArchiveStates.asking_nationality)
async def receive_nationality(message: Message, state: FSMContext):
    lang = await _get_lang(state)
    if message.text and message.text.strip():
        await state.update_data(nationality=message.text.strip()[:50])
    await message.answer(t("origin_request", lang), parse_mode="HTML", reply_markup=skip_keyboard("origin", lang))
    await state.set_state(ArchiveStates.asking_origin)


@router.callback_query(F.data == "skip_nationality", ArchiveStates.asking_nationality)
async def skip_nationality(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    lang = await _get_lang(state)
    await callback.message.answer(t("origin_request", lang), parse_mode="HTML", reply_markup=skip_keyboard("origin", lang))
    await state.set_state(ArchiveStates.asking_origin)


# ── Происхождение ─────────────────────────────────────────────────────────────

@router.message(ArchiveStates.asking_origin)
async def receive_origin(message: Message, state: FSMContext):
    lang = await _get_lang(state)
    if message.text and message.text.strip():
        await state.update_data(origin=message.text.strip()[:100])
    await message.answer(t("anthropometry_request", lang), parse_mode="HTML", reply_markup=skip_keyboard("anthropometry", lang))
    await state.set_state(ArchiveStates.asking_anthropometry)


@router.callback_query(F.data == "skip_origin", ArchiveStates.asking_origin)
async def skip_origin(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    lang = await _get_lang(state)
    await callback.message.answer(t("anthropometry_request", lang), parse_mode="HTML", reply_markup=skip_keyboard("anthropometry", lang))
    await state.set_state(ArchiveStates.asking_anthropometry)


# ── Антропометрия → анализ ────────────────────────────────────────────────────

@router.message(ArchiveStates.asking_anthropometry)
async def receive_anthropometry(message: Message, state: FSMContext, bot: Bot):
    if message.text and message.text.strip():
        await state.update_data(anthropometry=message.text.strip()[:50])
    from bot.handlers.analysis import start_analysis
    await start_analysis(message, state, bot)


@router.callback_query(F.data == "skip_anthropometry", ArchiveStates.asking_anthropometry)
async def skip_anthropometry(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    from bot.handlers.analysis import start_analysis
    await start_analysis(callback.message, state, callback.bot)
