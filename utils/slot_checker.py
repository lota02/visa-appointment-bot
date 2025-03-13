import asyncio
import logging
import sqlite3
from aiogram import Bot

DB_PATH = "user_data.db"
db = sqlite3.connect(DB_PATH)
cursor = db.cursor()

# Ensure the users table has a chat_id column
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    chat_id INTEGER,
    username TEXT,
    last_active TEXT
)
""")
db.commit()

# Mock function to simulate slot checking
async def get_available_slots():
    # Simulate fetching available slots (this should be your real logic)
    return ["March 20, 2025", "March 25, 2025", "April 5, 2025"]

async def check_slots(bot: Bot):
    while True:
        try:
            available_slots = await get_available_slots()

            if available_slots:
                cursor.execute("SELECT chat_id FROM users")
                chat_ids = [row[0] for row in cursor.fetchall()]

                for chat_id in chat_ids:
                    await bot.send_message(
                        chat_id,
                        "🚨 New Visa Appointment Slots Found! 📅\n" +
                        "\n".join(available_slots)
                    )
        except Exception as e:
            logging.error(f"Error checking slots: {e}")
        await asyncio.sleep(3600)  # Check every hour