
import asyncio
import sqlite3
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

# YANGI BOT TOKENINGNI SHU YERGA YOZ
BOT_TOKEN = "8222146544:AAHg3BeV8-xuabK06dHNa3O1lVJnziGhOLA"

DB_NAME = "date.db"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Foydalanuvchilarning suhbat javoblari
users = {}


# =========================
# DATABASE
# =========================

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                registered_at TEXT
            )
        """)


def save_user(user):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.execute("""
            INSERT OR IGNORE INTO users
            (user_id, username, first_name, registered_at)
            VALUES (?, ?, ?, ?)
        """, (
            user.id,
            user.username,
            user.first_name,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        return cursor.rowcount == 1


def get_user_count():
    with sqlite3.connect(DB_NAME) as conn:
        return conn.execute(
            "SELECT COUNT(*) FROM users"
        ).fetchone()[0]


# =========================
# MENYULAR
# =========================

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🎮 Menga o'yin tavsiya qil")],
        [KeyboardButton(text="🌐 Online o'yinlar")],
        [KeyboardButton(text="ℹ️ Yordam")],
    ],
    resize_keyboard=True,
)

genre_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🏎 Poyga"),
            KeyboardButton(text="🧩 Boshqotirma"),
        ],
        [
            KeyboardButton(text="⚔️ Sarguzasht"),
            KeyboardButton(text="😌 Tinchlantiruvchi"),
        ],
        [KeyboardButton(text="🎲 Tasodifiy")],
    ],
    resize_keyboard=True,
)

time_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="⏱ 5-10 daqiqa"),
            KeyboardButton(text="🕒 15-30 daqiqa"),
        ],
        [KeyboardButton(text="⌛ 30 daqiqadan ko'p")],
    ],
    resize_keyboard=True,
)

mood_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="⚡ Faol va tezkor"),
            KeyboardButton(text="🧠 O'ylashni yoqtiraman"),
        ],
        [
            KeyboardButton(text="🌿 Dam olmoqchiman"),
            KeyboardButton(text="😂 Shunchaki ko'ngilxushlik"),
        ],
    ],
    resize_keyboard=True,
)


# =========================
# O'YINLAR
# =========================

GAMES = [
    {
        "name": "Drive Mad",
        "genre": "🏎 Poyga",
        "mood": "⚡ Faol va tezkor",
        "time": "⏱ 5-10 daqiqa",
        "description": "Mashinalarni boshqarish va qiyin yo'llardan o'tish.",
        "online": "https://poki.com/en/g/drive-mad",
        "download": "https://itch.io/search?q=driving+game",
    },
    {
        "name": "Subway Surfers",
        "genre": "🏎 Poyga",
        "mood": "⚡ Faol va tezkor",
        "time": "🕒 15-30 daqiqa",
        "description": "To'siqlardan qochib, imkon qadar uzoqqa yugurish.",
        "online": "https://poki.com/en/g/subway-surfers",
        "download": "https://itch.io/search?q=endless+runner",
    },
    {
        "name": "Stickman Hook",
        "genre": "🧩 Boshqotirma",
        "mood": "🧠 O'ylashni yoqtiraman",
        "time": "⏱ 5-10 daqiqa",
        "description": "Tortilish, sakrash va harakat vaqtini to'g'ri tanlash.",
        "online": "https://poki.com/en/g/stickman-hook",
        "download": "https://itch.io/search?q=physics+puzzle",
    },
    {
        "name": "Shaxmat",
        "genre": "🧩 Boshqotirma",
        "mood": "🧠 O'ylashni yoqtiraman",
        "time": "⌛ 30 daqiqadan ko'p",
        "description": "Strategiya tuzish va raqib yurishlarini oldindan o'ylash.",
        "online": "https://www.chess.com/play",
        "download": "https://itch.io/search?q=chess",
    },
    {
        "name": "2048",
        "genre": "🧩 Boshqotirma",
        "mood": "🌿 Dam olmoqchiman",
        "time": "⏱ 5-10 daqiqa",
        "description": "Bir xil raqamlarni birlashtirib, kattaroq raqam hosil qilish.",
        "online": "https://play2048.co/",
        "download": "https://itch.io/search?q=2048",
    },
    {
        "name": "Adventure Games",
        "genre": "⚔️ Sarguzasht",
        "mood": "😂 Shunchaki ko'ngilxushlik",
        "time": "⌛ 30 daqiqadan ko'p",
        "description": "Yangi dunyolarni kashf qilish va topshiriqlarni bajarish.",
        "online": "https://www.crazygames.com/",
        "download": "https://itch.io/games/tag-adventure",
    },
    {
        "name": "Relaxing Games",
        "genre": "😌 Tinchlantiruvchi",
        "mood": "🌿 Dam olmoqchiman",
        "time": "🕒 15-30 daqiqa",
        "description": "Shoshilmasdan, xotirjam o'ynash uchun o'yinlar.",
        "online": "https://poki.com/",
        "download": "https://itch.io/games/tag-relaxing",
    },
]


def get_recommendation(user):
    genre = user.get("genre")
    mood = user.get("mood")
    time = user.get("time")

    candidates = []

    for game in GAMES:
        score = 0

        if genre == "🎲 Tasodifiy":
            score += 1
        elif game["genre"] == genre:
            score += 3

        if game["mood"] == mood:
            score += 2

        if game["time"] == time:
            score += 1

        candidates.append((score, game))

    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


def game_buttons(game):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🌐 Online o'ynash",
                    url=game["online"],
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬇️ Yuklab olish manbalari",
                    url=game["download"],
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔄 Boshqa o'yin",
                    callback_data="new_game",
                )
            ],
        ]
    )


async def ask_genre(message: Message):
    users[message.from_user.id] = {"step": "genre"}

    await message.answer(
        "🎮 Qaysi turdagi o'yinni yoqtirasan?",
        reply_markup=genre_menu,
    )


# =========================
# START
# =========================

@dp.message(CommandStart())
async def start(message: Message):
    is_new_user = save_user(message.from_user)

    if is_new_user:
        await message.answer(
            "🎉 Xush kelibsan! Sen bazaga yangi foydalanuvchi "
            "sifatida ro'yxatdan o'tding."
        )

    await message.answer(
        "🎮🔍 O'yinlar_qidiruchi_bot ga xush kelibsan!\n\n"
        "Qiziqishing, kayfiyating va bo'sh vaqtingga "
        "qarab o'yin tavsiya qilaman.\n\n"
        "Boshlash uchun tugmani bos!",
        reply_markup=main_menu,
    )


# =========================
# BEKOR QILISH
# =========================

@dp.message(Command("cancel"))
async def cancel(message: Message):
    users.pop(message.from_user.id, None)

    await message.answer(
        "Bekor qilindi. Asosiy menyudan boshlashing mumkin.",
        reply_markup=main_menu,
    )


# =========================
# O'YIN TAVSIYASI
# =========================

@dp.message(F.text == "🎮 Menga o'yin tavsiya qil")
async def recommend_start(message: Message):
    await ask_genre(message)


# =========================
# ONLINE O'YINLAR
# =========================

@dp.message(F.text == "🌐 Online o'yinlar")
async def online_games(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎮 Poki",
                    url="https://poki.com/",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🕹 CrazyGames",
                    url="https://www.crazygames.com/",
                )
            ],
            [
                InlineKeyboardButton(
                    text="♟ Chess.com",
                    url="https://www.chess.com/play",
                )
            ],
        ]
    )

    await message.answer(
        "🌐 Online o'yinlar platformasini tanla:",
        reply_markup=keyboard,
    )


# =========================
# YORDAM
# =========================

@dp.message(F.text == "ℹ️ Yordam")
async def help_message(message: Message):
    await message.answer(
        "📌 Qanday ishlaydi?\n\n"
        "1. O'yin tavsiyasi tugmasini bos.\n"
        "2. O'yin turini tanla.\n"
        "3. Qancha vaqting borligini ayt.\n"
        "4. Kayfiyatingni tanla.\n"
        "5. Bot senga mos o'yin tavsiya qiladi.\n\n"
        "/cancel — savollarni bekor qilish."
    )


# =========================
# FOYDALANUVCHI JAVOBLARI
# =========================

@dp.message(F.text)
async def handle_answers(message: Message):
    user_id = message.from_user.id
    text = message.text.strip()

    if user_id not in users:
        await message.answer(
            "Boshlash uchun menyudan "
            "'🎮 Menga o'yin tavsiya qil' tugmasini bos.",
            reply_markup=main_menu,
        )
        return

    user = users[user_id]
    step = user.get("step")

    if step == "genre":
        valid_genres = [
            "🏎 Poyga",
            "🧩 Boshqotirma",
            "⚔️ Sarguzasht",
            "😌 Tinchlantiruvchi",
            "🎲 Tasodifiy",
        ]

        if text not in valid_genres:
            await message.answer(
                "Iltimos, pastdagi tugmalardan birini tanla.",
                reply_markup=genre_menu,
            )
            return

        user["genre"] = text
        user["step"] = "time"

        await message.answer(
            "⏱ O'ynash uchun qancha vaqting bor?",
            reply_markup=time_menu,
        )
        return

    if step == "time":
        valid_times = [
            "⏱ 5-10 daqiqa",
            "🕒 15-30 daqiqa",
            "⌛ 30 daqiqadan ko'p",
        ]

        if text not in valid_times:
            await message.answer(
                "Iltimos, vaqtni tugmalardan tanla.",
                reply_markup=time_menu,
            )
            return

        user["time"] = text
        user["step"] = "mood"

        await message.answer(
            "😊 Qanday o'yin kayfiyatingga mos?",
            reply_markup=mood_menu,
        )
        return

    if step == "mood":
        valid_moods = [
            "⚡ Faol va tezkor",
            "🧠 O'ylashni yoqtiraman",
            "🌿 Dam olmoqchiman",
            "😂 Shunchaki ko'ngilxushlik",
        ]

        if text not in valid_moods:
            await message.answer(
                "Iltimos, kayfiyatingni tugmalardan tanla.",
                reply_markup=mood_menu,
            )
            return

        user["mood"] = text
        game = get_recommendation(user)
        user["step"] = "done"

        await message.answer(
            f"🎯 Senga tavsiyam: {game['name']}\n\n"
            f"📝 {game['description']}\n\n"
            "Quyidagi tugmalardan foydalan:",
            reply_markup=game_buttons(game),
        )

        await message.answer(
            "Yana tavsiya olish uchun tugmani bos.",
            reply_markup=main_menu,
        )


# =========================
# BOSHQA O'YIN
# =========================

@dp.callback_query(F.data == "new_game")
async def new_game(callback):
    await callback.answer()
    await ask_genre(callback.message)


# =========================
# ISHGA TUSHIRISH
# =========================

async def main():
    init_db()
    print("GAME BOT ishga tushdi!")
    print(f"Bazadagi foydalanuvchilar soni: {get_user_count()}")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
