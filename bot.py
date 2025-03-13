import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, types, Router
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from handlers import registration
from handlers.registration import BookingSteps
from utils.notifications import router as notification_router, send_notifications
from utils.slot_checker import check_slots
import datetime

# Enable logging
logging.basicConfig(level=logging.INFO)

# Initialize bot, storage, and router
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(registration.router)
dp.include_router(notification_router)

# SQLite Database Setup
conn = sqlite3.connect("user_data.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    chat_id INTEGER NOT NULL,
    username TEXT,
    last_active TEXT
)
""")
conn.commit()

# Session Management Dictionary (Temporary In-Memory Solution)
sessions = {}

# Main Menu Keyboard
def main_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📝 Register"),
                KeyboardButton(text="📅 Check Slots")
            ],
            [
                KeyboardButton(text="🔔 Notification Preferences"),
                KeyboardButton(text="❓ Help")
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return keyboard

# /start command
@router.message(Command("start"))
async def send_welcome(message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    username = message.from_user.username or "Unknown"
    sessions[user_id] = {"last_active": datetime.datetime.now()}

    # Store user data in SQLite
    cursor.execute(
        "INSERT OR REPLACE INTO users (user_id, chat_id, username, last_active) VALUES (?, ?, ?, ?)",
        (user_id, chat_id, username, str(datetime.datetime.now()))
    )
    conn.commit()

    await message.reply(
        "👋 Welcome to the Visa Appointment Bot!\n"
        "I'm here to help you register, check slots, set notifications, and more.\n"
        "Choose an option from the menu below to get started.",
        reply_markup=main_menu()
    )

# Button Click Handlers
@router.message(lambda message: message.text == "📝 Register")
async def handle_register_button(message: Message, state: FSMContext):
    await message.reply("📋 Starting the registration process... Please follow the instructions.")
    await message.reply(
        "Let's begin your registration process!\n"
        "1️⃣ Please enter your DS-160 form number.\n"
        "Example: AA00123BCD\n"
        "If you get stuck at any point, type /cancel to restart."
    )
    await state.set_state(BookingSteps.DS160)

@router.message(lambda message: message.text == "📅 Check Slots")
async def handle_check_slots_button(message: Message):
    await message.reply("🗓 Checking available slots...")

@router.message(lambda message: message.text == "🔔 Notification Preferences")
async def handle_notification_prefs_button(message: Message):
    await message.reply("🔔 Here you can manage your notification preferences.")

@router.message(lambda message: message.text == "❓ Help")
async def handle_help_button(message: Message):
    await message.reply(
        "🆘 **Help Menu**\n\n"
        "📋 /start — Start the bot and see the welcome message.\n"
        "📝 /register — Begin the registration process for your visa appointment.\n"
        "💳 /pay — Proceed with payment for your visa appointment.\n"
        "🔔 /notify — Set your notification preferences.\n"
        "📅 /checkslots — Check available slots for your appointment.\n"
        "❌ /cancel — Cancel the current process.\n\n"
        "If you encounter any issues, feel free to ask for assistance. 😊",
        parse_mode="Markdown"
    )

# Middleware to keep sessions active
@router.message()
async def update_session_activity(message: Message):
    user_id = message.from_user.id
    if user_id in sessions:
        sessions[user_id]["last_active"] = datetime.datetime.now()

        # Update user activity in SQLite
        cursor.execute(
            "UPDATE users SET last_active = ? WHERE user_id = ?",
            (str(datetime.datetime.now()), user_id)
        )
        conn.commit()

# Session cleanup logic
async def cleanup_sessions():
    while True:
        now = datetime.datetime.now()
        expired_sessions = [
            user_id
            for user_id, data in sessions.items()
            if (now - data["last_active"]).seconds > 3600
        ]
        for user_id in expired_sessions:
            del sessions[user_id]
        await asyncio.sleep(600)

# Automatic Booking Logic with Notification
async def automatic_booking(user_data, user_id):
    try:
        await asyncio.sleep(3)  # Simulate booking delay
        await bot.send_message(user_id, "✅ Booking confirmed! Your appointment is successfully scheduled.")
        return True
    except Exception as e:
        await bot.send_message(user_id, f"❌ Booking failed: {str(e)}")
        return False

# Main function
async def main():
    dp.include_router(router)
    asyncio.create_task(send_notifications(bot))  
    asyncio.create_task(cleanup_sessions())  
    asyncio.create_task(check_slots(bot))  

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
