def format_token(d):
    price = f"${d['price']:.8f}" if d['price'] else "N/A"
    mc = f"${d['market_cap']:,.0f}" if d['market_cap'] else "N/A"
    creator = f"{d['creator'][:8]}...{d['creator'][-6:]}" if d['creator'] else "N/A"
    supply = f"{d['supply']:,.0f}" if d['supply'] else "N/A"

    return (
        f"🔥 <b>{d['name']}</b> detected fren!\n\n"
        f"🏷 Symbol: <b>{d['symbol']}</b>\n"
        f"💵 Price: <b>{price}</b>\n"
        f"💰 MC: <b>{mc}</b>\n"
        f"📦 Supply: <b>{supply}</b>\n"
        f"🧱 Creator: <code>{creator}</code>\n\n"
        f"Wanna smash it? 🚀\n"
        f"Use /swap_buy {d['address']} &lt;amount&gt;"
    )
