import asyncio
import logging
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiohttp import web

from bot.config import BOT_TOKEN, WEBHOOK_PORT
from bot.database.db import init_db
from bot.handlers import start, collection, analysis, admin, payment
from bot.webhook_server import make_app, set_bot

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN не задан в .env")

    logger.info("Инициализация базы данных...")
    await init_db()

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(admin.router)
    dp.include_router(payment.router)
    dp.include_router(start.router)
    dp.include_router(collection.router)
    dp.include_router(analysis.router)

    runner = web.AppRunner(make_app())
    try:
        # Запуск веб-сервера для вебхуков Tribute
        set_bot(bot)
        await runner.setup()
        await web.TCPSite(runner, "0.0.0.0", WEBHOOK_PORT).start()
        logger.info(f"Tribute webhook сервер запущен на порту {WEBHOOK_PORT}")

        logger.info("Запуск бота «Архив Происхождения»...")
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await runner.cleanup()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
