import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
FEE_WALLET = os.getenv("FEE_WALLET")
FEE_AMOUNT_HYPE = float(os.getenv("FEE_AMOUNT_HYPE", "0.005"))

HL_API = "[api.hyperliquid.xyz](https://api.hyperliquid.xyz)"
HYPEREVM_RPC = "[rpc.hyperliquid.xyz](https://rpc.hyperliquid.xyz/evm)"

ALTFUN_ROUTER = "0x70c7eC6f85B960379b7ee60Af72E0f419d915878"
ALTFUN_FACTORY = "0xd5E5Fef4cFeFb67bbA0aA1dc74B2Cd196B4786AC"
ALTFUN_BONDING = "0xb68811BcC0e4FcD825aA49F9453b065ddF752FcB"

SCAN_INTERVAL = 1
