import sqlite3
import asyncio
import datetime
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import CallbackQuery 
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton


router = Router()

# Database Connection
DB_PATH = "notifications.db"
db = sqlite3.connect(DB_PATH)
cursor = db.cursor()

# Create notifications table if not exists
cursor.execute('''
    CREATE TABLE IF NOT EXISTS notifications (
        user_id INTEGER PRIMARY KEY,
        notify_time TEXT,
        notify_days TEXT,
        active BOOLEAN
    )
''')
db.commit()

# Function to set notification preferences
def set_notification_preferences(user_id, time, days, active=True):
    cursor.execute('''
        INSERT INTO notifications (user_id, notify_time, notify_days, active)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
        notify_time = excluded.notify_time,
        notify_days = excluded.notify_days,
        active = excluded.active
    ''', (user_id, time, days, active))
    db.commit()

# Function to get notification preferences
def get_notification_preferences(user_id):
    cursor.execute('SELECT * FROM notifications WHERE user_id = ?', (user_id,))
    return cursor.fetchone()

# Send scheduled notifications
async def send_notifications(bot):
    while True:
        now = datetime.datetime.now().strftime("%H:%M")
        today = datetime.datetime.now().strftime("%a")  # e.g., Mon, Tue
        cursor.execute("SELECT user_id, notify_time, notify_days FROM notifications WHERE active = 1")
        for user_id, notify_time, notify_days in cursor.fetchall():
            if now == notify_time and today in notify_days:
                await bot.send_message(user_id, "🔔 Reminder: Stay updated with your visa appointment progress!")
        await asyncio.sleep(60)  

# /notify command - Ask user for notification settings
@router.message(Command("notify"))
async def cmd_notify(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🕒 Set Notification Time", callback_data="set_time")],
        [InlineKeyboardButton(text="📅 Set Notification Days", callback_data="set_days")],
        [InlineKeyboardButton(text="✅ Enable Notifications", callback_data="enable_notifications")],
        [InlineKeyboardButton(text="❌ Disable Notifications", callback_data="disable_notifications")]
    ])

    await message.answer(
        "🔔 **Notification Preferences**\n"
        "Choose an option below to manage your preferences.",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

# Callback for setting notification time
@router.callback_query(lambda c: c.data == "set_time")
async def set_time_callback(callback: CallbackQuery):
    await callback.message.answer("🕒 Please enter your preferred notification time in HH:MM format.")

# Callback for setting notification days
@router.callback_query(lambda c: c.data == "set_days")
async def set_days_callback(callback: CallbackQuery):
    await callback.message.answer("📅 Please enter the days you want notifications (e.g., Mon, Wed, Fri).")

# Callback for enabling notifications
@router.callback_query(lambda c: c.data == "enable_notifications")
async def enable_notifications_callback(callback: CallbackQuery):
    set_notification_preferences(callback.from_user.id, "08:00", "Mon-Fri", True)
    await callback.message.answer("✅ Notifications enabled successfully!")

# Callback for disabling notifications
@router.callback_query(lambda c: c.data == "disable_notifications")
async def disable_notifications_callback(callback: CallbackQuery):
    set_notification_preferences(callback.from_user.id, "", "", False)
    await callback.message.answer("❌ Notifications have been disabled.")