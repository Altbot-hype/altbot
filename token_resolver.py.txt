import requests

ALT = "[hyperindex.alt.fun](https://hyperindex.alt.fun/api/token/)"
META = "[api.hyperliquid.xyz](https://api.hyperliquid.xyz/meta)"

def resolve_token(ca):
    try:
        d = requests.get(ALT + ca).json()
    except:
        return None

    try:
        meta = requests.get(META).json()
        uni = meta.get("universe", [])
        hl = None
        for x in uni:
            if x.get("asset") == d["symbol"]:
                hl = x.get("perp")
        d["hl_market"] = hl
    except:
        d["hl_market"] = None

    return d
