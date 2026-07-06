# Telegram Referal Bot

Telegram kanal uchun referal bot. Har bir foydalanuvchiga kanalning shaxsiy invite linki beriladi. Kim shu link orqali kanalga qo'shilsa, hisoblanadi. Oy oxirida TOP-10 g'oliblar aniqlanadi.

## Imkoniyatlari

- 🔗 Har bir foydalanuvchiga shaxsiy invite link
- 📊 `/top` — jonli TOP-10 reyting (hamma uchun)
- 📋 `/hisobot` — to'liq hisobot + Excel (faqat admin uchun)
- 📅 Har oy oxirida avtomatik hisobot adminGA yuboriladi
- 🚪 Kanaldan chiqib ketganlar hisobga olinadi (o'chirilmaydi, dalil sifatida qoladi)

## 1-qadam: O'rnatish

Python 3.11 yoki undan yuqori kerak.

```bash
# Kutubxonalarni o'rnatamiz
pip install -r requirements.txt
```

## 2-qadam: Botni yaratish

1. Telegramda [@BotFather](https://t.me/BotFather) ga kiring.
2. `/newbot` buyrug'i bilan yangi bot yarating.
3. Berilgan **tokenni** saqlang (masalan: `123456:ABC-DEF...`).

## 3-qadam: Botni kanalga admin qiling

⚠️ **Eng muhim qadam!** Botsiz link yaratib bo'lmaydi.

1. Kanal sozlamalari → **Administrators** → **Add Administrator**.
2. Botingizni qo'shing.
3. **"Invite Users via Link"** (havola orqali odam taklif qilish) huquqini **YOQING**.

## 4-qadam: Kerakli ID'larni olish

- **CHANNEL_ID**: Kanal ID. Buni bilish uchun [@getidsbot](https://t.me/getidsbot) yoki [@userinfobot](https://t.me/userinfobot) dan foydalaning. Odatda `-100` bilan boshlanadi (masalan: `-1001234567890`).
- **ADMIN_ID**: Sizning Telegram ID'ingiz. Xuddi shu botlardan olasiz.

## 5-qadam: .env faylni to'ldirish

`.env.example` faylidan nusxa oling va `.env` deb nomlang:

```bash
cp .env.example .env
```

`.env` faylni oching va to'ldiring:

```
BOT_TOKEN=BotFather bergan token
CHANNEL_ID=-1001234567890
ADMIN_ID=123456789
```

## 6-qadam: Ishga tushirish

```bash
python main.py
```

"Bot ishga tushdi ✅" degan xabar chiqsa — hammasi tayyor!

## Foydalanish

| Komanda | Kim uchun | Nima qiladi |
|---|---|---|
| `/start` | Hamma | Shaxsiy invite link beradi (ulashish tugmasi bilan) va natijani ko'rsatadi |
| `/help` | Hamma | Botdan foydalanish bo'yicha qo'llanma |
| `/top` | Hamma | Joriy TOP-10 reytingni ko'rsatadi |
| `/hisobot` | Faqat admin | To'liq hisobot + Excel fayl yuboradi |
| `/restart` | Faqat admin | Oylik hisobot schedulerini yangilaydi |

## Muhim eslatmalar

- **Database**: Ma'lumotlar `bot.db` (SQLite) faylida saqlanadi. Uni o'chirmang!
- **Oylik hisobot**: Har oyning oxirgi kuni soat 23:59 da avtomatik ravishda adminga yuboriladi. Shundan so'ng referallar ro'yxati tozalanadi, lekin foydalanuvchilar va ularning linklari saqlanib qoladi.
- **Bot doim ishlab turishi kerak** — server yoki kompyuterda uzluksiz ishlashi lozim (aks holda kanal eventlarini o'tkazib yuboradi).

## Loyiha strukturasi

```
ReferalBot/
├── .env                  # Maxfiy sozlamalar (o'zingiz yaratasiz)
├── .env.example          # Namuna
├── requirements.txt      # Kutubxonalar
├── main.py               # Botni ishga tushirish
├── config.py             # Sozlamalarni o'qish
├── database.py           # DB modellari va funksiyalar
├── handlers.py           # /start, /top, /hisobot
├── channel_events.py     # Kanalga kirish/chiqish
├── scheduler.py          # Oylik avtomatik hisobot
└── utils.py              # Excel export
```
