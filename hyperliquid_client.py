from hyperliquid.exchange import Exchange
from hyperliquid.info import Info
from eth_account import Account
import config

class HLClient:
    def __init__(self, private_key):
        self.account = Account.from_key(private_key)
        self.exchange = Exchange(self.account, config.HL_API)
        self.info = Info(config.HL_API)

    def price(self, coin):
        try:
            mids = self.info.all_mids()
            return float(mids.get(coin))
        except:
            return None

    def buy(self, coin, size):
        p = self.price(coin)
        if not p:
            return {"error": "Price not found"}
        return self.exchange.order(
            coin, True, size, p * 1.01,
            {"limit": {"tif": "Ioc"}}
        )

    def sell(self, coin, size):
        p = self.price(coin)
        if not p:
            return {"error": "Price not found"}
        return self.exchange.order(
            coin, False, size, p * 0.99,
            {"limit": {"tif": "Ioc"}}
        )

    def send_fee(self):
        return self.exchange.transfer(
            config.FEE_WALLET, float(config.FEE_AMOUNT)
        )

    def balance(self):
        try:
            s = self.info.user_state(self.account.address)
            return float(s.get("marginSummary", {}).get("accountValue", 0))
        except:
            return 0

    def positions(self):
        try:
            s = self.info.user_state(self.account.address)
            arr = s.get("assetPositions", [])
            out = []
            for x in arr:
                p = x.get("position", {})
                if float(p.get("szi", 0)) != 0:
                    out.append({
                        "coin": p.get("coin"),
                        "size": float(p.get("szi")),
                        "entry": float(p.get("entryPx")),
                        "price": float(p.get("entryPx")),
                        "unreal": float(p.get("unrealizedPnl"))
                    })
            mids = self.info.all_mids()
            for x in out:
                x["price"] = float(mids.get(x["coin"]))
            return out
        except:
            return []
