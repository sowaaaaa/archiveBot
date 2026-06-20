import os
from aiogram import Router, F
from aiogram.types import CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext

from bot.config import AI_PRICE, EXPERT_PRICE, TRIBUTE_LINK_AI, TRIBUTE_LINK_EXPERT
from bot.states import ArchiveStates
from bot.i18n import t
from bot.keyboards.inline import tribute_payment_keyboard, start_after_payment_keyboard
from bot.database.db import get_balance, deduct_balance

router = Router()

SERVICE_PRICES = {"ai": AI_PRICE, "expert": EXPERT_PRICE}
SERVICE_LINKS = {"ai": TRIBUTE_LINK_AI, "expert": TRIBUTE_LINK_EXPERT}
SERVICE_PRICES_EUR = {"ai": 7, "expert": 25}


async def _get_lang(state: FSMContext) -> str:
    data = await state.get_data()
    return data.get("lang", "ru")


@router.callback_query(F.data == "choose_ai", ArchiveStates.welcome)
async def choose_ai(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(analysis_type="ai")
    await _handle_service_choice(callback, state, "ai")


@router.callback_query(F.data == "choose_expert", ArchiveStates.welcome)
async def choose_expert(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(analysis_type="expert")
    await _handle_service_choice(callback, state, "expert")


async def _handle_service_choice(callback: CallbackQuery, state: FSMContext, service_type: str):
    lang = await _get_lang(state)
    balance = await get_balance(callback.from_user.id)
    required = SERVICE_PRICES[service_type]
    label = t(f"service_{service_type}", lang)

    if balance >= required:
        await callback.message.answer(
            t("balance_ok", lang, label=label),
            parse_mode="HTML",
            reply_markup=start_after_payment_keyboard(service_type, lang),
        )
    else:
        await callback.message.answer(
            t("payment_text", lang, label=label, amount=SERVICE_PRICES_EUR[service_type]),
            parse_mode="HTML",
            reply_markup=tribute_payment_keyboard(SERVICE_LINKS[service_type], lang),
        )


@router.callback_query(F.data.startswith("start_paid_"))
async def start_paid_analysis(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    lang = await _get_lang(state)
    service_type = callback.data.replace("start_paid_", "")
    required = SERVICE_PRICES.get(service_type, 0)
    balance = await get_balance(callback.from_user.id)

    if balance < required:
        label = t(f"service_{service_type}", lang)
        await callback.message.answer(
            t("insufficient_balance", lang, balance=balance // 100, required=required // 100),
            parse_mode="HTML",
        )
        await callback.message.answer(
            t("payment_text", lang, label=label, amount=SERVICE_PRICES_EUR.get(service_type, 0)),
            parse_mode="HTML",
            reply_markup=tribute_payment_keyboard(SERVICE_LINKS.get(service_type, TRIBUTE_LINK_AI), lang),
        )
        return

    await deduct_balance(callback.from_user.id, required)
    await state.update_data(analysis_type=service_type)

    if service_type == "expert":
        await callback.message.answer(t("expert_path_intro", lang), parse_mode="HTML")

    front_example = "assets/example_front.jpg"
    if os.path.exists(front_example):
        await callback.message.answer_photo(
            FSInputFile(front_example),
            caption=t("front_photo_request", lang),
            parse_mode="HTML",
        )
    else:
        await callback.message.answer(t("front_photo_request", lang), parse_mode="HTML")
    await state.set_state(ArchiveStates.collecting_front_photo)
