from web3 import Web3
import config

w3 = Web3(Web3.HTTPProvider(config.HYPEREVM_RPC))

ERC20_ABI = [
    {"inputs":[],"name":"name","outputs":[{"type":"string"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"symbol","outputs":[{"type":"string"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"totalSupply","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"decimals","outputs":[{"type":"uint8"}],"stateMutability":"view","type":"function"}
]

BONDING_ABI = [
    {
        "inputs":[{"internalType":"address","name":"token","type":"address"}],
        "name":"getTokenInfo",
        "outputs":[
            {"internalType":"uint256","name":"supply","type":"uint256"},
            {"internalType":"uint256","name":"price","type":"uint256"},
            {"internalType":"uint256","name":"marketCap","type":"uint256"},
            {"internalType":"address","name":"creator","type":"address"}
        ],
        "stateMutability":"view",
        "type":"function"
    }
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

        try:
            bonding = w3.eth.contract(
                address=Web3.to_checksum_address(config.ALTFUN_BONDING),
                abi=BONDING_ABI
            )
            info = bonding.functions.getTokenInfo(addr).call()
            supply = info[0] / (10 ** decimals)
            price = info[1] / 1e18
            market_cap = info[2] / 1e18
            creator = info[3]
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
