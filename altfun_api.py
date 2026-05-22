from web3 import Web3
import requests
import config

w3 = Web3(Web3.HTTPProvider(config.HYPEREVM_RPC))

ERC20_ABI = [
    {"inputs":[],"name":"name","outputs":[{"type":"string"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"symbol","outputs":[{"type":"string"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"totalSupply","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"decimals","outputs":[{"type":"uint8"}],"stateMutability":"view","type":"function"}
]

def get_token_info(token_address):
    try:
        addr = Web3.to_checksum_address(token_address)
        contract = w3.eth.contract(address=addr, abi=ERC20_ABI)

        name = contract.functions.name().call()
        symbol = contract.functions.symbol().call()
        supply_raw = contract.functions.totalSupply().call()
        decimals = contract.functions.decimals().call()
        supply = supply_raw / (10 ** decimals)

        price = None
        market_cap = None
        creator = None

        # Alt.fun web API dene
        try:
            r = requests.get(
                f"[alt.fun](https://alt.fun/api/token/{token_address})",
                timeout=5
            )
            if r.status_code == 200:
                data = r.json()
                price = data.get("price")
                market_cap = data.get("marketCap")
                creator = data.get("creator")
        except:
            pass

        # Alt.fun API çalışmazsa ikinci kaynak dene
        if not price:
            try:
                r2 = requests.get(
                    f"[api.alt.fun](https://api.alt.fun/tokens/{token_address})",
                    timeout=5
                )
                if r2.status_code == 200:
                    data2 = r2.json()
                    price = data2.get("price")
                    market_cap = data2.get("marketCap")
                    creator = data2.get("creator")
            except:
                pass

        return {
            "address": token_address,
            "name": name,
            "symbol": symbol,
            "supply": round(supply, 2),
            "decimals": decimals,
            "price": price,
            "market_cap": market_cap,
            "creator": creator
        }
    except Exception as e:
        return None
