
import asyncio
import html
import sqlite3
from datetime import datetime

import aiohttp
from aiogram import Bot, Dispatcher, F, BaseMiddleware
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    BufferedInputFile,
)

# YANGI TOKENINGNI SHU YERGA YOZ
BOT_TOKEN = "9135853103:AAHfqBZ4WbOFjm8arBvRMnXw5ge4ZXtsN58"

DB_NAME = "data.db"
dp = Dispatcher()

# Har bir foydalanuvchining qidiruv natijalari
user_results = {}


# 1. MA'LUMOTLAR BAZASI
def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                first_seen TEXT NOT NULL,
                last_seen TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS searches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                query TEXT NOT NULL,
                searched_at TEXT NOT NULL
            )
        """)

    print("✅ data.db bazasi tayyor!")


# 2. FOYDALANUVCHINI SAQLASH
def save_user(user):
    if user is None:
        return

    now = datetime.now().astimezone().isoformat(
        timespec="seconds"
    )

    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            INSERT INTO users (
                user_id, username, first_name,
                last_name, first_seen, last_seen
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name,
                last_name = excluded.last_name,
                last_seen = excluded.last_seen
        """, (
            user.id,
            user.username,
            user.first_name,
            user.last_name,
            now,
            now,
        ))


class UserTrackingMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        user = None

        if isinstance(event, (Message, CallbackQuery)):
            user = event.from_user

        if user:
            save_user(user)

        return await handler(event, data)


dp.update.outer_middleware(UserTrackingMiddleware())


# 3. QIDIRUV TARIXI
def save_search(user_id: int, query: str):
    now = datetime.now().astimezone().isoformat(
        timespec="seconds"
    )

    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            INSERT INTO searches (user_id, query, searched_at)
            VALUES (?, ?, ?)
        """, (user_id, query, now))


# 4. ITUNESDAN 10 TA QO'SHIQ QIDIRISH
async def search_songs(query: str):
    url = "https://itunes.apple.com/search"

    params = {
        "term": query,
        "entity": "song",
        "media": "music",
        "limit": 10,
        "country": "US",
    }

    timeout = aiohttp.ClientTimeout(total=30)

    async with aiohttp.ClientSession(
        timeout=timeout,
        trust_env=True,
    ) as session:
        async with session.get(url, params=params) as response:
            print("iTunes status:", response.status)
            response.raise_for_status()

            # iTunes ba'zan text/javascript qaytaradi
            data = await response.json(content_type=None)

    songs = data.get("results", [])

    print(f"Qidiruv: {query} | Natijalar: {len(songs)}")

    return songs


# 5. HAR BIR QO'SHIQ UCHUN TUGMALAR
def make_song_keyboard(songs):
    buttons = []

    for index, song in enumerate(songs):
        buttons.append([
            InlineKeyboardButton(
                text=f"🎧 Tinglash {index + 1}",
                callback_data=f"play:{index}",
            ),
            InlineKeyboardButton(
                text="🔗 Rasmiy havola",
                url=(
                    song.get("trackViewUrl")
                    or song.get("collectionViewUrl")
                    or "https://music.apple.com/"
                ),
            ),
        ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


# 6. AUDIO NAMUNANI TELEGRAMGA YUBORISH
async def send_song_preview(
    message: Message,
    song: dict,
    index: int,
):
    preview_url = song.get("previewUrl")

    if not preview_url:
        await message.answer(
            "🎧 Bu qo'shiq uchun audio namuna mavjud emas.\n"
            "🔗 Rasmiy havoladan foydalaning."
        )
        return

    title = song.get("trackName", "Noma'lum qo'shiq")
    artist = song.get("artistName", "Noma'lum ijrochi")

    timeout = aiohttp.ClientTimeout(total=45)

    try:
        async with aiohttp.ClientSession(
            timeout=timeout,
            trust_env=True,
        ) as session:
            async with session.get(preview_url) as response:
                response.raise_for_status()
                audio_data = await response.read()

        if not audio_data:
            await message.answer("😕 Audio namuna bo'sh qaytdi.")
            return

        audio_file = BufferedInputFile(
            audio_data,
            filename=f"preview_{index + 1}.m4a",
        )

        await message.answer_audio(
            audio=audio_file,
            title=title,
            performer=artist,
            caption=(
                f"🎵 <b>{html.escape(title)}</b>\n"
                f"👤 {html.escape(artist)}\n"
                "ℹ️ Qisqa audio namuna"
            ),
            parse_mode="HTML",
        )

    except (aiohttp.ClientError, asyncio.TimeoutError) as error:
        print("AUDIO XATOSI:", repr(error))
        await message.answer(
            "⚠️ Audio yuklanmadi. Rasmiy havolani ochib ko'ring."
        )


# 7. BOSH MENYU
@dp.message(CommandStart())
async def start(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔎 Qo'shiq qidirish",
                    callback_data="search_help",
                )
            ],
            [
                InlineKeyboardButton(
                    text="ℹ️ Yordam",
                    callback_data="help",
                )
            ],
        ]
    )

    await message.answer(
        "🎵 <b>Musiqa Qidiruvchi botga xush kelibsiz!</b>\n\n"
        "Qo'shiq yoki ijrochi nomini yozing.\n"
        "Men 10 tagacha natijani topib beraman.\n\n"
        "Masalan: The Weeknd",
        reply_markup=keyboard,
        parse_mode="HTML",
    )


@dp.message(Command("help"))
async def help_command(message: Message):
    await message.answer(
        "🔎 Qo'shiq nomi yoki ijrochi ismini yozing.\n\n"
        "🎧 Tinglash — mavjud audio namunani yuboradi.\n"
        "🔗 Rasmiy havola — qo'shiq sahifasini ochadi.\n\n"
        "/start — bosh menyu\n"
        "/help — yordam"
    )


@dp.callback_query(F.data == "search_help")
async def search_help(callback: CallbackQuery):
    await callback.message.answer(
        "🔍 Endi qo'shiq nomini yoki ijrochi ismini yozing."
    )
    await callback.answer()


@dp.callback_query(F.data == "help")
async def help_button(callback: CallbackQuery):
    await callback.message.answer(
        "Qo'shiq nomini yozing. Men 10 tagacha natija, "
        "rasmiy havola va tinglash tugmasini chiqaraman."
    )
    await callback.answer()


# 8. QO'SHIQNI TUGMA ORQALI TINGLASH
@dp.callback_query(F.data.startswith("play:"))
async def play_song(callback: CallbackQuery):
    await callback.answer()

    try:
        index = int(callback.data.split(":")[1])
        songs = user_results.get(callback.from_user.id, [])

        if index < 0 or index >= len(songs):
            await callback.message.answer(
                "⚠️ Qidiruv natijalari topilmadi. "
                "Qo'shiqni qayta qidiring."
            )
            return

        await send_song_preview(
            callback.message,
            songs[index],
            index + 1,
        )

    except (ValueError, IndexError):
        await callback.message.answer(
            "⚠️ Tugmada xatolik. Qo'shiqni qayta qidiring."
        )


# 9. QO'SHIQLARNI QIDIRISH VA NATIJALARNI CHIQARISH
@dp.message(F.text)
async def find_music(message: Message):
    query = message.text.strip()

    if query.startswith("/"):
        return

    if len(query) < 2 or len(query) > 150:
        await message.answer(
            "Iltimos, 2–150 ta belgidan iborat qidiruv yozing."
        )
        return

    status = await message.answer("🔎 Qo'shiqlar qidirilmoqda...")

    try:
        songs = await search_songs(query)

        if message.from_user:
            save_search(message.from_user.id, query)

        if not songs:
            await status.edit_text(
                "😕 Hech narsa topilmadi. Boshqa nom bilan urinib ko'ring."
            )
            return

        # Natijalarni foydalanuvchi ID si bo'yicha saqlash
        user_results[message.from_user.id] = songs

        lines = [
            f"🎵 <b>Qidiruv natijalari:</b> "
            f"{html.escape(query)}\n"
        ]

        for index, song in enumerate(songs, start=1):
            title = html.escape(
                song.get("trackName", "Noma'lum qo'shiq")
            )
            artist = html.escape(
                song.get("artistName", "Noma'lum ijrochi")
            )
            album = html.escape(
                song.get("collectionName", "Noma'lum albom")
            )
            link = (
                song.get("trackViewUrl")
                or song.get("collectionViewUrl")
                or "https://music.apple.com/"
            )

            safe_link = html.escape(link, quote=True)

            lines.append(
                f"\n<b>{index}. {title}</b>\n"
                f"👤 Ijrochi: {artist}\n"
                f"💿 Albom: {album}\n"
                f'<a href="{safe_link}">🔗 Qo\'shiq havolasi</a>'
            )

        await status.edit_text(
            "\n".join(lines),
            reply_markup=make_song_keyboard(songs),
            parse_mode="HTML",
            disable_web_page_preview=True,
        )

    except (aiohttp.ClientError, asyncio.TimeoutError) as error:
        print("ITUNES / INTERNET XATOSI:", repr(error))
        await status.edit_text(
            "🌐 Musiqa xizmatiga ulanishda xato yuz berdi."
        )

    except Exception as error:
        print("KUTILMAGAN XATO:", repr(error))
        await status.edit_text(
            "❌ Xatolik yuz berdi. Terminalni tekshiring."
        )


# 10. BOTNI ISHGA TUSHIRISH
async def main():
    init_db()

    if not BOT_TOKEN:
        print("❌ BOT_TOKEN qatoriga bot tokenini kiriting!")
        return

    bot = Bot(token=BOT_TOKEN)
    print("🎵 Bot ishga tushmoqda...")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
