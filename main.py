"""Botni ishga tushirish."""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand
from aiogram.fsm.storage.memory import MemoryStorage
import channel_events
import handlers
from config import BOT_TOKEN
from database import init_db
from middleware import ThrottlingMiddleware
from scheduler import setup_scheduler

# Loglarni yoqamiz
logging.basicConfig(level=logging.INFO)


async def set_bot_commands(bot: Bot):
    """Telegram menyusidagi komandalar ro'yxatini o'rnatamiz."""
    commands = [
        BotCommand(command="start", description="Shaxsiy linkni olish"),
        BotCommand(command="help", description="Yordam / qo'llanma"),
        BotCommand(command="top", description="TOP-10 reyting"),
    ]
    await bot.set_my_commands(commands)


async def main():
    # Botni yaratamiz — barcha xabarlar uchun HTML formatni yoqamiz
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Spamdan himoya: har bir foydalanuvchidan 1 soniyada 1 xabar
    dp.message.middleware(ThrottlingMiddleware(rate_limit=1.0))

    # Handlerlarni ulaymiz
    dp.include_router(handlers.router)
    dp.include_router(channel_events.router)

    # Database jadvallarini yaratamiz
    await init_db()

    # Menyu komandalarini o'rnatamiz (/start, /help, /top)
    await set_bot_commands(bot)

    # Oylik hisobot schedulerini ishga tushiramiz
    scheduler = setup_scheduler(bot)
    scheduler.start()

    logging.info("Bot ishga tushdi ✅")

    # MUHIM: chat_member update default O'CHIQ — uni albatta yoqamiz!
    # Bu qatorsiz kanalga kirish/chiqish eventlari umuman kelmaydi.
    # scheduler'ni handlerlarga uzatamiz (/restart uni yangilashi uchun).
    await dp.start_polling(
        bot,
        allowed_updates=["message", "chat_member", "callback_query"],
        scheduler=scheduler,
    )


if __name__ == "__main__":
    try:
        logging.basicConfig(level=logging.INFO)
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot to'xtatildi.")
