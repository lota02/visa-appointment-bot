from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Required tokens for bot functionality
BOT_TOKEN = os.getenv("BOT_TOKEN")
PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN")

# Ensure critical tokens are set
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is missing. Please add it to your .env file.")
if not PAYMENT_PROVIDER_TOKEN:
    raise ValueError("PAYMENT_PROVIDER_TOKEN is missing. Please add it to your .env file.")
