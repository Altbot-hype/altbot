from altfun_api import get_token_info
from hyperliquid.info import Info
import config

def resolve_token(ca):
    info = get_token_info(ca)
    if not info:
        return None

    try:
        hl_info = Info(config.HL_API)
        mids = hl_info.all_mids()
        sym = info["symbol"]
        hl_price = mids.get(sym)
        info["hl_market"] = sym if hl_price else None
        info["hl_price"] = hl_price
    except:
        info["hl_market"] = None
        info["hl_price"] = None

    return info
