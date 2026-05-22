from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import threading, asyncio, io
from database import init_db, get_user, save_user
from wallet import create_wallet
from hyperliquid_client import HLClient
from token_resolver import resolve_token
from swap_engine import buy_token, sell_token
from scanner import scanner_loop
from utils.render import render_position_card
from utils.format import format_token
import config

def start(update, context):
    update.message.reply_text(
        "🔥 HypeBot online fren!\n\n"
        "Paste a CA to inspect token\n"
        "or use commands:\n\n"
        "/wallet - create wallet\n"
        "/balance - check balance\n"
        "/buy - buy token\n"
        "/sell - sell token\n"
        "/positions - open positions\n"
        "/help - all commands"
    )

def help_cmd(update, context):
    update.message.reply_text(
        "📋 Commands fren:\n\n"
        "💼 Wallet:\n"
        "/wallet - create/view wallet\n"
        "/balance - check HYPE balance\n\n"
        "📈 Alt.fun Swap:\n"
        "/swap_buy <CA> <amount_hype>\n"
        "/swap_sell <CA> <amount_tokens>\n\n"
        "📊 Hyperliquid Perp:\n"
        "/buy <coin> <size>\n"
        "/sell <coin> <size>\n"
        "/positions - open positions\n\n"
        "Paste any CA for token info 👀"
    )

def wallet_cmd(update, context):
    tid = update.effective_user.id
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    user = loop.run_until_complete(get_user(tid))
    if user:
        return update.message.reply_text(
            f"👛 Your Wallet:\n"
            f"`{user['wallet_address']}`\n\n"
            f"⚠️ Send HYPE for gas fees to start trading!",
            parse_mode="Markdown"
        )

    pk, addr = create_wallet()
    loop.run_until_complete(save_user(tid, pk, addr))
    update.message.reply_text(
        f"🎉 New wallet created fren!\n\n"
        f"Address:\n`{addr}`\n\n"
        f"⚠️ Send HYPE to this address for gas fees!\n"
        f"Ready to send it? 🚀",
        parse_mode="Markdown"
    )

def balance_cmd(update, context):
    tid = update.effective_user.id
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    user = loop.run_until_complete(get_user(tid))

    if not user:
        return update.message.reply_text("❌ No wallet fren. Use /wallet first.")

    from web3 import Web3
    w3 = Web3(Web3.HTTPProvider(config.HYPEREVM_RPC))
    bal = w3.eth.get_balance(user["wallet_address"])
    hype = w3.from_wei(bal, "ether")

    client = HLClient(user["wallet_private_key"])
    hl_bal = client.balance()

    update.message.reply_text(
        f"💰 Balances fren:\n\n"
        f"HYPE: {hype:.4f}\n"
        f"HL Equity: ${hl_bal:.2f}"
    )

def swap_buy_cmd(update, context):
    try:
        ca = context.args[0]
        amount = float(context.args[1])
    except:
        return update.message.reply_text(
            "Usage: /swap_buy <CA> <amount_hype>\n"
            "Example: /swap_buy 0x1234... 0.1"
        )

    tid = update.effective_user.id
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    user = loop.run_until_complete(get_user(tid))

    if not user:
        return update.message.reply_text("❌ No wallet fren. Use /wallet first.")

    update.message.reply_text(f"⏳ Buying token... hang tight fren 👀")

    result = buy_token(user["wallet_private_key"], ca, amount)

    if result["success"]:
        update.message.reply_text(
            f"🟢 Buy executed fren!\n\n"
            f"Token: `{ca[:8]}...{ca[-6:]}`\n"
            f"Amount: {amount} HYPE\n"
            f"TX: `{result['tx'][:16]}...`\n"
            f"Fee: {config.FEE_AMOUNT_HYPE} HYPE sent 🔥",
            parse_mode="Markdown"
        )
    else:
        update.message.reply_text(f"❌ Buy failed fren\n{result['error']}")

def swap_sell_cmd(update, context):
    try:
        ca = context.args[0]
        amount = float(context.args[1])
    except:
        return update.message.reply_text(
            "Usage: /swap_sell <CA> <amount_tokens>\n"
            "Example: /swap_sell 0x1234... 1000"
        )

    tid = update.effective_user.id
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    user = loop.run_until_complete(get_user(tid))

    if not user:
        return update.message.reply_text("❌ No wallet fren. Use /wallet first.")

    update.message.reply_text(f"⏳ Selling token... hang tight fren 👀")

    result = sell_token(user["wallet_private_key"], ca, amount)

    if result["success"]:
        update.message.reply_text(
            f"🔴 Sell executed fren!\n\n"
            f"Token: `{ca[:8]}...{ca[-6:]}`\n"
            f"Amount: {amount} tokens\n"
            f"TX: `{result['tx'][:16]}...`\n"
            f"Fee: {config.FEE_AMOUNT_HYPE} HYPE sent 🔥",
            parse_mode="Markdown"
        )
    else:
        update.message.reply_text(f"❌ Sell failed fren\n{result['error']}")

def buy_cmd(update, context):
    try:
        coin = context.args[0].upper()
        size = float(context.args[1])
    except:
        return update.message.reply_text("Usage: /buy <coin> <size>")

    tid = update.effective_user.id
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    user = loop.run_until_complete(get_user(tid))

    if not user:
        return update.message.reply_text("❌ No wallet fren.")

    client = HLClient(user["wallet_private_key"])
    result = client.buy(coin, size)

    if "error" in str(result):
        return update.message.reply_text(f"❌ Buy failed: {result}")

    update.message.reply_text(
        f"🟢 LONG opened fren!\n\n"
        f"Coin: {coin}\n"
        f"Size: {size}\n"
        f"Fee: {config.FEE_AMOUNT_HYPE} HYPE 🔥"
    )

def sell_cmd(update, context):
    try:
        coin = context.args[0].upper()
        size = float(context.args[1])
    except:
        return update.message.reply_text("Usage: /sell <coin> <size>")

    tid = update.effective_user.id
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    user = loop.run_until_complete(get_user(tid))

    if not user:
        return update.message.reply_text("❌ No wallet fren.")

    client = HLClient(user["wallet_private_key"])
    result = client.sell(coin, size)

    if "error" in str(result):
        return update.message.reply_text(f"❌ Sell failed: {result}")

    update.message.reply_text(
        f"🔴 SHORT opened fren!\n\n"
        f"Coin: {coin}\n"
        f"Size: {size}\n"
        f"Fee: {config.FEE_AMOUNT_HYPE} HYPE 🔥"
    )

def positions_cmd(update, context):
    tid = update.effective_user.id
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    user = loop.run_until_complete(get_user(tid))

    if not user:
        return update.message.reply_text("❌ No wallet fren.")

    client = HLClient(user["wallet_private_key"])
    pos_list = client.positions()

    if not pos_list:
        return update.message.reply_text("📉 No open positions fren.")

    for p in pos_list:
        data = {
            "coin": p["coin"],
            "side": "LONG" if p["size"] > 0 else "SHORT",
            "size": abs(p["size"]),
            "entry": p["entry"],
            "price": p["price"],
            "pnl": p["unreal"],
            "pnl_pct": (p["unreal"] / (abs(p["size"]) * p["entry"])) * 100 if p["entry"] else 0,
            "lev": 5,
            "liq": p["entry"] * 0.72
        }

        img = render_position_card(data)
        bio = io.BytesIO()
        img.save(bio, format="PNG")
        bio.seek(0)
        update.message.reply_photo(bio)

def msg_handler(update, context):
    text = update.message.text.strip()
    if text.startswith("0x") and len(text) == 42:
        update.message.reply_text("🔍 Scanning token fren... 👀")
        info = resolve_token(text)
        if not info:
            return update.message.reply_text("❌ Token not found fren.")
        update.message.reply_text(format_token(info), parse_mode="HTML")

def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(init_db())

    updater = Updater(config.TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_cmd))
    dp.add_handler(CommandHandler("wallet", wallet_cmd))
    dp.add_handler(CommandHandler("balance", balance_cmd))
    dp.add_handler(CommandHandler("swap_buy", swap_buy_cmd))
    dp.add_handler(CommandHandler("swap_sell", swap_sell_cmd))
    dp.add_handler(CommandHandler("buy", buy_cmd))
    dp.add_handler(CommandHandler("sell", sell_cmd))
    dp.add_handler(CommandHandler("positions", positions_cmd))
    dp.add_handler(MessageHandler(Filters.text, msg_handler))

    threading.Thread(target=scanner_loop, daemon=True).start()

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
