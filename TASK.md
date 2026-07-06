# Telegram Referal Bot — Texnik Topshiriq

## Loyiha haqida

Telegram kanal uchun referal bot. Har bir foydalanuvchiga kanalning shaxsiy invite linki beriladi. Kim shu link orqali kanalga qo'shilsa, database'ga yoziladi. Oy oxirida TOP-10 eng ko'p odam taklif qilganlar hisoboti chiqadi.

## Texnologiyalar (Stack)

- Python 3.11+
- Aiogram 3 (eng oxirgi versiya)
- SQLAlchemy 2.0 (async) + aiosqlite
- APScheduler (oylik hisobot uchun)
- openpyxl (Excel export uchun)
- python-dotenv (.env fayl uchun)

## MUHIM QOIDALAR (Kod yozish uslubi)

1. **Kod ODDIY va TUSHUNARLI bo'lsin.** Murakkab pattern'lar, ortiqcha abstraksiyalar, dependency injection, service layer'lar KERAK EMAS. Oddiy funksiyalar yetadi.
2. **Clean code:** funksiyalar qisqa, nomlari tushunarli, har bir funksiya bitta ish qilsin.
3. **Kommentlar O'ZBEK TILIDA** yozilsin. Har bir muhim joyga qisqa izoh.
4. **Xatolarni handle qilish:** try/except kerakli joylarda, lekin ortiqcha emas.
5. Ortiqcha fayl yaratma. Quyidagi strukturadan chiqma.

## Loyiha strukturasi

```
referal_bot/
├── .env                  # BOT_TOKEN, CHANNEL_ID, ADMIN_ID
├── .env.example          # Namuna
├── requirements.txt
├── main.py               # Botni ishga tushirish
├── config.py             # .env dan sozlamalarni o'qish
├── database.py           # SQLAlchemy modellari va DB funksiyalari
├── handlers.py           # /start, /top, /hisobot handlerlari
├── channel_events.py     # Kanalga kirish/chiqish (chat_member) handlerlari
├── scheduler.py          # Oylik avtomatik hisobot
└── utils.py              # Excel export va yordamchi funksiyalar
```

## Database strukturasi

### `users` jadvali
| Ustun | Tur | Izoh |
|---|---|---|
| id | Integer, PK, autoincrement | |
| telegram_id | BigInteger, unique, index | Foydalanuvchi Telegram ID |
| full_name | String | Ismi |
| username | String, nullable | @username |
| invite_link | String, unique, nullable | Shaxsiy kanal invite linki |
| created_at | DateTime | Ro'yxatdan o'tgan vaqt |

### `referrals` jadvali
| Ustun | Tur | Izoh |
|---|---|---|
| id | Integer, PK, autoincrement | |
| owner_id | BigInteger, FK -> users.telegram_id | Link egasi |
| joined_user_id | BigInteger | Kirgan odam Telegram ID |
| joined_user_name | String | Kirgan odam ismi |
| joined_at | DateTime | Kirgan vaqt |
| left | Boolean, default=False | Chiqib ketganmi |

**Constraint:** `UniqueConstraint(owner_id, joined_user_id)` — bir odam bir linkdan faqat 1 marta hisoblanadi.

## Funksional talablar

### 1. /start komandasi (handlers.py)
- Foydalanuvchi ma'lumotlarini (telegram_id, full_name, username) database'ga saqla. Agar oldin bor bo'lsa, qayta saqlama.
- Agar userda invite_link YO'Q bo'lsa:
  - `bot.create_chat_invite_link(chat_id=CHANNEL_ID, name=f"ref_{telegram_id}")` bilan yangi link yarat
  - Linkni users jadvaliga saqla
- Agar link BOR bo'lsa — eskisini ishlatiladi (yangi yaratma!)
- Userga xabar yubor:
  - Salomlashish
  - Shaxsiy linki
  - "Do'stlaringizga tarqating, eng ko'p odam qo'shganlar oy oxirida g'olib bo'ladi" degan matn
  - Uning hozirgi natijasi (nechta odam qo'shgani)

### 2. Kanalga kirishni kuzatish (channel_events.py)
- `ChatMemberUpdated` handler yoz (kanal uchun, `chat_member` update)
- Yangi odam kanalga QO'SHILGANDA:
  - `update.invite_link` orqali qaysi link bilan kirganini aniqla
  - Linkni users jadvalidan qidir, egasini top
  - Agar link bizniki bo'lsa — referrals jadvaliga yoz (owner_id, joined_user_id, joined_user_name, joined_at)
  - Agar bu juftlik (owner_id + joined_user_id) oldin bor bo'lsa — qayta yozma, faqat left=False qil
  - O'zini o'zi taklif qilishni hisoblama (owner_id == joined_user_id bo'lsa skip)
  - Link egasiga xabar yubor: "🎉 Sizning linkingiz orqali [ism] kanalga qo'shildi! Jami: N ta"
- Odam kanaldan CHIQIB KETGANDA:
  - referrals jadvalida shu odamni top, left=True qil
  - (O'chirib tashlama! Dalil sifatida qoladi)

### 3. /top komandasi (handlers.py)
- Hamma uchun ochiq
- Joriy TOP-10 ni chiqaradi (left=False bo'lganlar bo'yicha)
- Format:
```
🏆 TOP-10 Referal Reytingi

1. Kartoshkabek — 25 ta
2. Baqlajon — 18 ta
...

Sizning natijangiz: 5 ta (7-o'rin)
```

### 4. /hisobot komandasi (handlers.py)
- FAQAT ADMIN uchun (ADMIN_ID bilan tekshir)
- TOP-10 ro'yxati + jami statistika (nechta user, nechta referal)
- Excel fayl ham yuborilsin (hamma referallar ro'yxati)

### 5. Oylik avtomatik hisobot (scheduler.py)
- APScheduler cron: har oyning oxirgi kuni 23:59 da (cron: `day='last', hour=23, minute=59`)
- Qiladigan ishlari (tartib bilan):
  1. TOP-10 hisobotni tuz
  2. Hamma referallarni Excel'ga export qil
  3. Excel + hisobot matnini ADMINGA yubor
  4. `referrals` jadvalini TOZALA (users jadvaliga TEGMA — linklar ishlashda davom etadi)

### 6. Excel export (utils.py)
- openpyxl bilan
- Ustunlar: № | Link egasi | Kirgan odam | Kirgan vaqti | Holati (Kanalda / Chiqib ketgan)
- Fayl nomi: `hisobot_2026_07.xlsx` (yil_oy formatida)

## Config (.env)

```
BOT_TOKEN=your_bot_token
CHANNEL_ID=-1001234567890
ADMIN_ID=123456789
```

## MUHIM texnik eslatmalar

1. **Bot kanalda ADMIN bo'lishi shart** — "Invite users via link" huquqi bilan. README'da yozib qo'y.
2. **Aiogram 3'da `chat_member` update default O'CHIQ!** Dispatcher'ni ishga tushirganda albatta yoqish kerak:
```python
await dp.start_polling(bot, allowed_updates=["message", "chat_member", "callback_query"])
```
Bu qatorsiz kanal eventi UMUMAN kelmaydi — eng ko'p uchraydigan xato shu.
3. Database fayl: `bot.db` (SQLite), loyiha papkasida.
4. Botni ishga tushirganda jadvallarni avtomatik yarat (`create_all`).

## Yakunda

- `README.md` yoz: qanday o'rnatish, .env to'ldirish, botni kanalga admin qilish, ishga tushirish — hammasi O'ZBEK TILIDA, qadam-baqadam.
- `requirements.txt` versiyalari bilan.
- Kodni tekshir: hamma import ishlashini, sintaksis xatolar yo'qligini tasdiqlagach tugat.