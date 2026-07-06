"""Sozlamalar: .env fayldan qiymatlarni o'qiydi."""

import os
import ast

from dotenv import load_dotenv

# .env faylni yuklaymiz
load_dotenv()

# Bot tokeni
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Kanal ID (butun son bo'lishi kerak)
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))



ADMIN_IDS = ast.literal_eval(os.getenv("ADMIN_ID", ""))

# Database fayli
DB_URL = "sqlite+aiosqlite:///bot.db"

# Sozlamalar to'g'ri to'ldirilganini tekshiramiz
if not BOT_TOKEN or CHANNEL_ID == 0 or not ADMIN_IDS:
    raise ValueError(
        "BOT_TOKEN, CHANNEL_ID va ADMIN_ID .env faylda to'ldirilishi shart! "
        ".env.example dan namuna oling."
    )
