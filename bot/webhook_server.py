import hmac
import hashlib
import json
import logging

from aiohttp import web

from bot.config import TRIBUTE_API_KEY, TRIBUTE_PRODUCT_AI_ID, TRIBUTE_PRODUCT_EXPERT_ID, AI_PRICE, EXPERT_PRICE

logger = logging.getLogger(__name__)

_bot = None


def set_bot(bot):
    global _bot
    _bot = bot


async def handle_tribute_webhook(request: web.Request) -> web.Response:
    body = await request.read()

    signature = request.headers.get("trbt-signature", "")
    expected = hmac.new(TRIBUTE_API_KEY.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        logger.warning("Tribute webhook: неверная подпись")
        return web.Response(status=403)

    try:
        data = json.loads(body)
    except Exception:
        return web.Response(status=400)

    logger.info(f"Tribute webhook event: {data.get('type')} payload={json.dumps(data.get('payload', {}))}")

    payload = data.get("payload", {})

    # Достаём product_id и telegram_id из разных возможных структур payload
    product_id = (
        payload.get("product", {}).get("id")
        or payload.get("product_id")
    )
    telegram_id = (
        payload.get("buyer", {}).get("telegram_id")
        or payload.get("subscriber", {}).get("telegram_id")
        or payload.get("telegram_id")
    )

    if not telegram_id or not product_id:
        logger.warning(f"Tribute webhook: не найден telegram_id или product_id, payload={payload}")
        return web.Response(status=200)

    if product_id == TRIBUTE_PRODUCT_AI_ID:
        amount, service_type, label = AI_PRICE, "ai", "Типирование ИИ"
    elif product_id == TRIBUTE_PRODUCT_EXPERT_ID:
        amount, service_type, label = EXPERT_PRICE, "expert", "Экспертный разбор"
    else:
        logger.info(f"Tribute webhook: неизвестный product_id={product_id}, игнорируем")
        return web.Response(status=200)

    from bot.database.db import add_balance
    await add_balance(telegram_id, amount)
    logger.info(f"Начислено {amount} центов EUR пользователю {telegram_id} за {label}")

    if _bot:
        import os
        from aiogram.types import FSInputFile
        from bot.keyboards.inline import start_after_payment_keyboard
        from bot.i18n import t
        from bot.database.db import get_user_lang
        try:
            lang = await get_user_lang(telegram_id)
        except Exception:
            lang = "ru"
        text = t("payment_confirmed", lang)
        keyboard = start_after_payment_keyboard(service_type, lang)
        img = "assets/payment.jpg"
        try:
            if os.path.exists(img):
                await _bot.send_photo(
                    telegram_id,
                    FSInputFile(img),
                    caption=text,
                    parse_mode="HTML",
                    reply_markup=keyboard,
                )
            else:
                await _bot.send_message(
                    telegram_id, text, parse_mode="HTML", reply_markup=keyboard,
                )
        except Exception as e:
            logger.error(f"Не удалось уведомить пользователя {telegram_id}: {e}")

    return web.Response(status=200)


def make_app() -> web.Application:
    app = web.Application()
    app.router.add_post("/tribute/webhook", handle_tribute_webhook)
    return app
