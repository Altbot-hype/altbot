def format_token(d):
    return f"""
🔥 <b>{d['name']}</b> detected fren!

🏷 Symbol: <b>{d['symbol']}</b>
💰 MC: <b>${d['marketCap']}</b>
🧱 Creator: {d['creator']}
🎯 HL Market: {d['hl_market']}

Wanna smash it? 🚀
Use /buy or /sell
"""
