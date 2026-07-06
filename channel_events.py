"""Kanalga kirish/chiqishni kuzatish (chat_member update)."""

import logging
from html import escape

from aiogram import Bot, Router
from aiogram.types import ChatMemberUpdated

import database
from config import CHANNEL_ID

router = Router()


def _is_join(event: ChatMemberUpdated) -> bool:
    """Odam kanalga YANGI qo'shildimi? (a'zo emasdan -> a'zo)."""
    was_member = event.old_chat_member.status in ("member", "administrator", "creator")
    is_member = event.new_chat_member.status in ("member", "administrator", "creator")
    return not was_member and is_member


def _is_leave(event: ChatMemberUpdated) -> bool:
    """Odam kanaldan chiqib ketdimi? (a'zo -> a'zo emas)."""
    was_member = event.old_chat_member.status in ("member", "administrator", "creator")
    is_member = event.new_chat_member.status in ("member", "administrator", "creator")
    return was_member and not is_member


@router.chat_member()
async def on_chat_member(event: ChatMemberUpdated, bot: Bot):
    """Kanaldagi a'zolik o'zgarishlarini qayta ishlaymiz."""
    # --- DIAGNOSTIKA LOGI (muammoni topgach o'chirib tashlash mumkin) ---
    invite = event.invite_link.invite_link if event.invite_link else None
    logging.info(
        "[chat_member] chat.id=%s (kutilgan CHANNEL_ID=%s) | user=%s (%s) | "
        "old=%s -> new=%s | invite_link=%s",
        event.chat.id,
        CHANNEL_ID,
        event.new_chat_member.user.full_name,
        event.new_chat_member.user.id,
        event.old_chat_member.status,
        event.new_chat_member.status,
        invite,
    )

    # Faqat bizning kanalimizni kuzatamiz
    if event.chat.id != CHANNEL_ID:
        logging.warning("[chat_member] chat.id CHANNEL_ID ga mos kelmadi — o'tkazib yuborildi.")
        return

    joined_user = event.new_chat_member.user

    # --- ODAM QO'SHILDI ---
    if _is_join(event):
        # Qaysi link bilan kirganini aniqlaymiz
        if not event.invite_link:
            logging.warning("[chat_member] QO'SHILDI, lekin invite_link YO'Q — hisoblanmadi.")
            return  # Link orqali emas — hisoblamaymiz

        owner = await database.get_owner_by_link(event.invite_link.invite_link)
        if owner is None:
            logging.warning(
                "[chat_member] Link DB dagi hech kimga mos kelmadi: %s",
                event.invite_link.invite_link,
            )
            return  # Bu link bizniki emas

        # O'zini o'zi taklif qilishni hisoblamaymiz
        if owner.telegram_id == joined_user.id:
            logging.info("[chat_member] O'zini o'zi taklif qildi — hisoblanmadi.")
            return

        # Referalni yozamiz
        await database.add_referral(
            owner_id=owner.telegram_id,
            joined_user_id=joined_user.id,
            joined_user_name=joined_user.full_name,
        )
        logging.info(
            "[chat_member] REFERAL YOZILDI: egasi=%s, kirgan=%s",
            owner.telegram_id,
            joined_user.id,
        )

        # Link egasiga xabar yuboramiz
        total = await database.count_referrals(owner.telegram_id)
        try:
            await bot.send_message(
                owner.telegram_id,
                f"🎉 Sizning linkingiz orqali <b>{escape(joined_user.full_name)}</b> "
                f"kanalga qo'shildi!\n"
                f"Jami: <b>{total}</b> ta",
            )
            logging.info("[chat_member] Egaga xabar yuborildi: %s", owner.telegram_id)
        except Exception as e:
            # Xabar bormasa sababini logga yozamiz (egasi botni /start qilmagan
            # yoki bloklagan bo'lishi mumkin). Bot ishlashda davom etadi.
            logging.warning(
                "[chat_member] Egaga (%s) xabar yuborilmadi: %s",
                owner.telegram_id,
                e,
            )

    # --- ODAM CHIQIB KETDI ---
    elif _is_leave(event):
        # referrals jadvalida left=True qilamiz (o'chirmaymiz)
        await database.mark_referral_left(joined_user.id)
        logging.info("[chat_member] CHIQIB KETDI, left=True: user=%s", joined_user.id)
