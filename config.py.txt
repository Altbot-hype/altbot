import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
FEE_WALLET = os.getenv("FEE_WALLET")
FEE_AMOUNT = float(os.getenv("FEE_AMOUNT"))
HL_API = "[api.hyperliquid.xyz](https://api.hyperliquid.xyz)"
SCAN_INTERVAL = 1
