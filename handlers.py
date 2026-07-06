"""Handlerlar: /start, /help, /top, /hisobot, /restart komandalari."""

import re
from html import escape
from urllib.parse import quote

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

import database
import utils
from config import ADMIN_IDS, CHANNEL_ID
from scheduler import restart_scheduler, send_monthly_report
from states import Registration

router = Router()

PHONE_REGEX = re.compile(r"^\+?998\d{9}$")


def _share_keyboard(invite_link: str) -> InlineKeyboardMarkup:
    """'Havolani ulashish' inline tugmasi — Telegram ulashish oynasini ochadi."""
    share_text = quote("Ushbu kanalga qo'shiling! 👇")
    share_url = f"https://t.me/share/url?url={quote(invite_link)}&text={share_text}"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📤 Havolani ulashish", url=share_url)]
        ]
    )


def _phone_keyboard() -> ReplyKeyboardMarkup:
    """Telefon raqamni tugma orqali yuborish uchun klaviatura."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Raqamni yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Ro'yxatdan o'tgan bo'lsa — to'g'ridan-to'g'ri ma'lumot, bo'lmasa — ismni so'raymiz."""
    db_user = await database.get_user(message.from_user.id)

    if db_user:
        await _send_main_info(message, db_user)
        return

    await state.set_state(Registration.waiting_name)
    await message.answer(
        "Assalomu alaykum! 👋\nRo'yxatdan o'tish uchun to'liq ismingizni kiriting:",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(Registration.waiting_name)
async def process_name(message: Message, state: FSMContext):
    """Ismni qabul qilamiz, keyin telefon raqam so'raymiz."""
    name = (message.text or "").strip()
    if not name or len(name) < 2:
        await message.answer("Iltimos, ismingizni to'g'ri kiriting:")
        return

    await state.update_data(full_name=name)
    await state.set_state(Registration.waiting_phone)
    await message.answer(
        "Rahmat! Endi telefon raqamingizni yuboring — pastdagi tugma orqali "
        "yoki qo'lda yozing (masalan: +998901234567):",
        reply_markup=_phone_keyboard(),
    )


@router.message(Registration.waiting_phone, F.contact)
async def process_phone_contact(message: Message, state: FSMContext, bot: Bot):
    """Telefon raqam 'contact' tugmasi orqali yuborilganda."""
    await _finish_registration(message, state, bot, message.contact.phone_number)


@router.message(Registration.waiting_phone, F.text)
async def process_phone_text(message: Message, state: FSMContext, bot: Bot):
    """Telefon raqam matn orqali yuborilganda."""
    phone = message.text.strip().replace(" ", "").replace("-", "")
    if not PHONE_REGEX.match(phone):
        await message.answer(
            "❌ Format noto'g'ri. Masalan: +998901234567\n"
            "Yoki pastdagi tugmadan foydalaning."
        )
        return

    await _finish_registration(message, state, bot, phone)


async def _finish_registration(message: Message, state: FSMContext, bot: Bot, phone: str):
    """Ism va telefon yig'ilgandan keyin — user yaratamiz, link beramiz."""
    data = await state.get_data()
    full_name = data["full_name"]
    user = message.from_user

    db_user = await database.create_user(
        telegram_id=user.id,
        full_name=full_name,
        username=user.username,
        phone_number=phone,
    )
    await state.clear()

    try:
        link = await bot.create_chat_invite_link(chat_id=CHANNEL_ID, name=f"ref_{user.id}")
        await database.set_invite_link(user.id, link.invite_link)
        db_user.invite_link = link.invite_link
    except Exception as e:
        await message.answer(
            "❌ Link yaratishda xatolik. Bot kanalda admin ekanini tekshiring.\n"
            f"Xato: {escape(str(e))}",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    await message.answer("✅ Ro'yxatdan o'tdingiz!", reply_markup=ReplyKeyboardRemove())
    await _send_main_info(message, db_user)


async def _send_main_info(message: Message, db_user):
    """Foydalanuvchiga shaxsiy link va statistikasini yuboradi."""
    count = await database.count_referrals(db_user.telegram_id)
    safe_name = escape(db_user.full_name)

    text = (
        f"Salom, <b>{safe_name}</b>! 👋\n\n"
        f"Bu — sizning shaxsiy taklif linkingiz (ustiga bosib nusxalang):\n"
        f"<code>{escape(db_user.invite_link)}</code>\n\n"
        f"Do'stlaringizga tarqating! Kim shu link orqali kanalga qo'shilsa, "
        f"siz uchun hisoblanadi. Eng ko'p odam qo'shganlar oy oxirida g'olib bo'ladi. 🏆\n\n"
        f"📊 Sizning hozirgi natijangiz: <b>{count}</b> ta"
    )
    await message.answer(text, reply_markup=_share_keyboard(db_user.invite_link))
    
##########################################################################################
#                                           HELP
##########################################################################################

from apscheduler.schedulers.asyncio import AsyncIOScheduler

@router.message(Command("help"))
async def cmd_help(message: Message):
    """Botdan qanday foydalanishni tushuntiramiz."""
    text = (
        "ℹ️ <b>Referal bot qo'llanmasi</b>\n\n"
        "Bu bot orqali siz kanalga do'stlaringizni taklif qilib, "
        "eng faol taklif qiluvchilar reytingida qatnashasiz.\n\n"
        "<b>Qanday ishlaydi?</b>\n"
        "1️⃣ /start bosing — sizga <b>shaxsiy taklif linki</b> beriladi.\n"
        "2️⃣ Linkni do'stlaringizga yuboring (📤 <i>Havolani ulashish</i> tugmasi bilan).\n"
        "3️⃣ Kim shu link orqali kanalga qo'shilsa — siz uchun hisoblanadi.\n"
        "4️⃣ /top orqali reytingdagi o'rningizni kuzatib boring.\n\n"
        "<b>Komandalar:</b>\n"
        "• /start — shaxsiy linkni olish va natijani ko'rish\n"
        "• /top — joriy TOP-10 reyting\n"
        "• /help — shu qo'llanma\n\n"
        "🏆 Oy oxirida eng ko'p odam qo'shganlar g'olib bo'ladi!"
    )
    await message.answer(text)


@router.message(Command("top"))
async def cmd_top(message: Message):
    """Joriy TOP-10 reytingni ko'rsatamiz (hamma uchun ochiq)."""
    top = await database.get_top(limit=10)
    top_text = utils.build_top_text(top)

    # Foydalanuvchining o'z natijasi va o'rni
    my_count, my_rank = await database.get_user_rank(message.from_user.id)
    if my_rank > 0:
        my_line = f"\n\nSizning natijangiz: <b>{my_count}</b> ta ({my_rank}-o'rin)"
    else:
        my_line = "\n\nSizning natijangiz: <b>0</b> ta (hali reytingda yo'qsiz)"

    await message.answer(f"🏆 <b>TOP-10 Referal Reytingi</b>\n\n{top_text}{my_line}")


@router.message(Command("hisobot"))
async def cmd_hisobot(message: Message, bot: Bot):
    """To'liq hisobot (FAQAT admin uchun)."""
    if message.from_user.id not in ADMIN_IDS:
        return

    # TOP-10 va umumiy statistika
    top = await database.get_top(limit=10)
    top_text = utils.build_top_text(top)
    users_count, refs_count = await database.get_stats()

    report_text = (
        f"📋 <b>HISOBOT</b>\n\n"
        f"🏆 <b>TOP-10:</b>\n{top_text}\n\n"
        f"👥 Jami foydalanuvchilar: <b>{users_count}</b> ta\n"
        f"✅ Jami faol referallar: <b>{refs_count}</b> ta"
    )
    await message.answer(report_text)


@router.message(Command("restart"))
async def cmd_restart(message: Message, bot: Bot, scheduler: AsyncIOScheduler):
    """
    Qo'lda 'yangi oyni boshlash' (FAQAT admin uchun):
      1. Joriy hisobot + Excel adminGA yuboriladi (ma'lumot yo'qolmasligi uchun)
      2. referrals jadvali TOZALANADI
      3. Scheduler yangilanadi
    Eslatma: admin /restart yozmasa ham, har oy oxirida bu jarayon avtomatik bo'ladi.
    """
    if message.from_user.id not in ADMIN_IDS:
        return

    try:
        # Hisobot yuboriladi va referrals tozalanadi (avtomatik oylik hisobot bilan bir xil)
        await send_monthly_report(bot)
        # Scheduler yangilanadi (joblar qayta o'rnatiladi)
        restart_scheduler(scheduler, bot)
    except Exception as e:
        await message.answer(f"❌ Restart xatosi: {escape(str(e))}")
        return

    # Keyingi ishga tushish vaqtini ko'rsatamiz
    jobs = scheduler.get_jobs()
    next_run = jobs[0].next_run_time if jobs else None
    when = next_run.strftime("%Y-%m-%d %H:%M") if next_run else "noma'lum"

    await message.answer(
        "🔄 <b>Restart bajarildi!</b>\n\n"
        "✅ Hisobot yuborildi (yuqoriga qarang)\n"
        "🧹 Referrals jadvali tozalandi\n"
        f"📅 Keyingi avtomatik hisobot: <b>{when}</b>"
    )
