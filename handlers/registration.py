from aiogram import Router, types, F
from aiogram.types import Message, LabeledPrice, PreCheckoutQuery, SuccessfulPayment
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import BOT_TOKEN, PAYMENT_PROVIDER_TOKEN  # Ensure these are defined in config.py
import re
import sqlite3
from datetime import datetime

router = Router()

# Database setup
DB_PATH = "user_data.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# FSM for Booking Steps
class BookingSteps(StatesGroup):
    DS160 = State()
    CREDENTIALS = State()
    DATE_RANGE = State()
    CONFIRMATION = State()

# Temporary storage for editing details
user_details = {}

@router.message(Command("cancel"))
async def cancel_process(message: Message, state: FSMContext):
    await state.clear()
    await message.reply("❌ Process canceled. You can start again by typing /register.")

@router.message(Command("register"))
async def register_user(message: Message, state: FSMContext):
    chat_id = message.chat.id
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"
    last_active = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_db_connection() as db:
        cursor = db.cursor()
        cursor.execute('''
            INSERT INTO users (user_id, chat_id, username, last_active)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                chat_id = excluded.chat_id,
                username = excluded.username,
                last_active = excluded.last_active
        ''', (user_id, chat_id, username, last_active))
        db.commit()

    await message.reply(
        "Let's begin your registration process!\n"
        "1️⃣ Please enter your DS-160 form number.\n"
        "Example: AA00123BCD\n"
        "If you get stuck at any point, type /cancel to restart."
    )
    await state.set_state(BookingSteps.DS160)

@router.message(BookingSteps.DS160)
async def collect_ds160(message: Message, state: FSMContext):
    ds160_pattern = r"^AA\d{5,8}[A-Z]{2,3}$"  
    if not re.match(ds160_pattern, message.text.strip()):
        await message.reply("❌ Invalid DS-160 format. Please use a valid format like 'AA00123BCD'.")
        return

    await state.update_data(ds160=message.text.strip())
    await message.reply(
        "✅ DS-160 received!\n"
        "2️⃣ Now, please enter your USTravelDocs/AIS credentials in the format: username|password"
    )
    await state.set_state(BookingSteps.CREDENTIALS)

@router.message(BookingSteps.CREDENTIALS)
async def collect_credentials(message: Message, state: FSMContext):
    if "|" not in message.text.strip():
        await message.reply("❌ Invalid credentials format. Please use the format: username|password.")
        return

    await state.update_data(credentials=message.text.strip().split("|"))
    await message.reply(
        "✅ Credentials saved!\n"
        "3️⃣ Lastly, please enter your preferred date range in the format: YYYY-MM-DD to YYYY-MM-DD"
    )
    await state.set_state(BookingSteps.DATE_RANGE)

@router.message(BookingSteps.DATE_RANGE)
async def confirm_booking(message: Message, state: FSMContext):
    date_pattern = r"^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01]) to \d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$"
    if not re.match(date_pattern, message.text.strip()):
        await message.reply("❌ Invalid date format. Please use YYYY-MM-DD to YYYY-MM-DD (e.g., 2025-04-01 to 2025-04-30).")
        return

    data = await state.get_data()
    data["date_range"] = message.text.strip()

    with get_db_connection() as db:
        cursor = db.cursor()
        cursor.execute('''
            INSERT INTO user_details (user_id, ds160, credentials, date_range)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                ds160 = excluded.ds160,
                credentials = excluded.credentials,
                date_range = excluded.date_range
        ''', (message.from_user.id, data['ds160'], "|".join(data['credentials']), data['date_range']))
        db.commit()

    details = (
        f"📋 Confirm your details:\n"
        f"DS-160: {data['ds160']}\n"
        f"Username: {data['credentials'][0]} (hidden)\n"
        f"Date Range: {data['date_range']}\n"
        "If you need to modify any detail, use the /edit command followed by the field name.\n"
        "Example: /edit ds160 or /edit date_range\n"
        "Once you're satisfied, please use the /pay command to proceed with payment."
    )
    await message.reply(details)
    await state.set_state(BookingSteps.CONFIRMATION)

@router.message(Command("pay"))
async def process_payment(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state != BookingSteps.CONFIRMATION:
        await message.reply("❌ Please complete the registration process before proceeding with payment.")
        return

    chat_id = message.chat.id  # Explicitly retrieve chat_id

    if not chat_id:  # Extra safeguard
        await message.reply("❌ Error processing payment. Please try again or contact support.")
        return

    try:
        await message.bot.send_invoice(
            chat_id=chat_id,
            title="Visa Appointment Payment",
            description="Payment for your visa appointment booking.",
            payload="visa_booking_payload",
            provider_token=PAYMENT_PROVIDER_TOKEN,
            currency="USD",
            prices=[LabeledPrice(label="Visa Appointment Fee", amount=5000)],  # $50.00
            start_parameter="payment-test"
        )
        await state.clear()

    except Exception as e:
        await message.reply(f"❌ Payment error: {e}")

@router.pre_checkout_query()
async def pre_checkout_query(pre_checkout: PreCheckoutQuery):
    await pre_checkout.answer(ok=True)
    await pre_checkout.bot.send_message(pre_checkout.from_user.id, "✅ Payment is being processed...")

@router.message(F.successful_payment)
async def successful_payment(message: Message):
    await message.reply("💰 Payment successful! Your appointment has been booked successfully.")




