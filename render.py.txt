from PIL import Image, ImageDraw, ImageFont

BG = (18, 22, 28)
PANEL = (24, 29, 37)
TEXT = (220, 230, 240)
GREEN = (24, 200, 132)
RED = (240, 74, 74)
CYAN = (0, 221, 255)
FADE = (40, 50, 60)

def render_position_card(pos):
    img = Image.new("RGB", (900, 480), BG)
    d = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype("arial.ttf", 40)
        font_text = ImageFont.truetype("arial.ttf", 32)
    except:
        font_title = ImageFont.load_default()
        font_text = ImageFont.load_default()

    d.rectangle([(20, 20), (880, 110)], fill=PANEL)
    
    title = f"{pos['coin']} {pos['side']} 🟢" if pos["pnl"] >= 0 else f"{pos['coin']} {pos['side']} 🔴"
    d.text((40, 40), title, fill=CYAN, font=font_title)

    flavor = "lookin spicy 👀" if pos["pnl"] >= 0 else "down bad fren 😭"
    d.text((40, 90), f"({flavor})", fill=TEXT, font=font_text)

    d.rectangle([(20, 130), (880, 135)], fill=FADE)

    y = 160
    def line(label, val, color=TEXT):
        nonlocal y
        d.text((40, y), f"{label}: {val}", fill=color, font=font_text)
        y += 55

    line("Entry", f"${pos['entry']}")
    line("Price", f"${pos['price']}")
    pnl_color = GREEN if pos["pnl"] >= 0 else RED
    line("PnL", f"{pos['pnl']:+.2f} USD ({pos['pnl_pct']:+.2f}%)", pnl_color)
    line("Size", pos["size"])
    line("Leverage", f"{pos['lev']}x")
    line("Liq Price", f"${pos['liq']}")

    return img
