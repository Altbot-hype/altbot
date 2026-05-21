from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import threading, asyncio, io
from database import init_db, get_user, save_user
from wallet import create_wallet
from hyperliquid_client import HLClient
from token_resolver import resolve_token
from scanner import scanner_loop
from utils.render import render_position_card
from utils.format import format_token
import config

def start(update, context):
    update.message.reply_text("🔥 HypeBot online fren!\nUse /wallet or paste a CA.")

def wallet_cmd(update, context):
    tid = update.effective_user.id
    loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)

    user = loop.run_until_complete(get_user(tid))
    if user:
        return update.message.reply_text(f"👛 Wallet: {user['wallet_address']}")

    pk, addr = create_wallet()
    loop.run_until_complete(save_user(tid, pk, addr))
    update.message.reply_text(f"🎉 New wallet created!\n{addr}")

def balance_cmd(update, context):
    tid = update.effective_user.id
    loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
    user = loop.run_until_complete(get_user(tid))

    if not user:
        return update.message.reply_text("❌ No wallet fren.")

    client = HLClient(user["wallet_private_key"])
    bal = client.balance()
    update.message.reply_text(f"💰 Equity: ${bal}")

def buy_cmd(update, context):
    try:
        coin = context.args[0].upper()
        size = float(context.args[1])
    except:
        return update.message.reply_text("Usage: /buy COIN SIZE")

    tid = update.effective_user.id
    loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
    user = loop.run_until_complete(get_user(tid))
    if not user:
        return update.message.reply_text("❌ No wallet fren.")

    client = HLClient(user["wallet_private_key"])
    client.buy(coin, size)
    client.send_fee()

    update.message.reply_text(f"🟢 Bought {size} {coin}\n🔥 Fee sent ({config.FEE_AMOUNT} USDC)")

def sell_cmd(update, context):
    try:
        coin = context.args[0].upper()
        size = float(context.args[1])
    except:
        return update.message.reply_text("Usage: /sell COIN SIZE")

    tid = update.effective_user.id
    loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
    user = loop.run_until_complete(get_user(tid))
    if not user:
        return update.message.reply_text("❌ No wallet fren.")

    client = HLClient(user["wallet_private_key"])
    client.sell(coin, size)
    client.send_fee()

    update.message.reply_text(f"🔴 Sold {size} {coin}\n🔥 Fee sent ({config.FEE_AMOUNT} USDC)")

def positions_cmd(update, context):
    tid = update.effective_user.id
    loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
    user = loop.run_until_complete(get_user(tid))

    if not user:
        return update.message.reply_text("❌ No wallet fren.")

    client = HLClient(user["wallet_private_key"])
    pos_list = client.positions()
    if not pos_list:
        return update.message.reply_text("📉 No open positions.")

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
        info = resolve_token(text)
        if not info:
            return update.message.reply_text("❌ Token not found.")
        update.message.reply_text(format_token(info), parse_mode="HTML")

def main():
    loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
    loop.run_until_complete(init_db())

    updater = Updater(config.TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("wallet", wallet_cmd))
    dp.add_handler(CommandHandler("balance", balance_cmd))
    dp.add_handler(CommandHandler("buy", buy_cmd))
    dp.add_handler(CommandHandler("sell", sell_cmd))
    dp.add_handler(CommandHandler("positions", positions_cmd))
    dp.add_handler(MessageHandler(Filters.text, msg_handler))

    threading.Thread(target=scanner_loop, daemon=True).start()

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
