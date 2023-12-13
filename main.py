import asyncio
import logging
import sys
import sqlite3 as sqlite
from aiogram import Bot
from aiogram.enums import ParseMode

from handlers import cmd_start_handler
from loader import dp, msg_router, callback_router
from loader import TOKEN


async def main() -> None:
    try:
        conn = sqlite.connect('my_database.db')
        cursor = conn.cursor()

        cursor.execute('''CREATE TABLE IF NOT EXISTS Users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        gender TEXT,
        link_id INTEGER,
        hidden INTEGER
        )''')
    except Exception as e:
        print(e)
    dp.include_router(msg_router)
    dp.include_router(callback_router)
    msg_router.message.register(cmd_start_handler)
    callback_router.message.register(cmd_start_handler)
    bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
