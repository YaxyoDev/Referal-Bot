"""Oylik avtomatik hisobot (APScheduler)."""

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import logging

import database
import utils
from config import ADMIN_IDS


async def send_monthly_report(bot: Bot):
    """
    Oylik hisobot: TOP-10 adminGA yuboriladi,
    keyin referrals jadvali tozalanadi.
    """
    # 1. TOP-10 hisobotni tuzamiz
    top = await database.get_top(limit=10)
    top_text = utils.build_top_text(top)
    users_count, refs_count = await database.get_stats()

    report_text = (
        f"📅 OYLIK HISOBOT\n\n"
        f"🏆 TOP-10:\n{top_text}\n\n"
        f"👥 Jami foydalanuvchilar: {users_count} ta\n"
        f"✅ Jami faol referallar: {refs_count} ta"
    )

    # 2. Har bir adminGA hisobot yuboramiz
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, report_text)
        except Exception as e:
            logging.warning("Hisobotni adminGA (%s) yuborishda xato: %s", admin_id, e)

    # 3. referrals jadvalini tozalaymiz (users'ga tegmaymiz — linklar ishlaydi)
    await database.clear_referrals()


def _add_report_job(scheduler: AsyncIOScheduler, bot: Bot):
    """Oylik hisobot jobini schedulerga qo'shamiz (har oy oxirgi kuni 23:59)."""
    scheduler.add_job(
        send_monthly_report,
        trigger="cron",
        day="last",
        hour=23,
        minute=59,
        args=[bot],
        id="monthly_report",
        replace_existing=True,
    )


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    """Schedulerni sozlaymiz: har oyning oxirgi kuni 23:59 da."""
    scheduler = AsyncIOScheduler()
    _add_report_job(scheduler, bot)
    return scheduler


def restart_scheduler(scheduler: AsyncIOScheduler, bot: Bot):
    """
    Schedulerni yangilaymiz: eski joblarni o'chirib, qaytadan qo'shamiz.
    /restart komandasi shu funksiyani chaqiradi.
    """
    scheduler.remove_all_jobs()
    _add_report_job(scheduler, bot)
    # Agar negadir to'xtab qolgan bo'lsa — qayta ishga tushiramiz
    if not scheduler.running:
        scheduler.start()
