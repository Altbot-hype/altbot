from web3 import Web3
import config

w3 = Web3(Web3.HTTPProvider(config.HYPEREVM_RPC))

ERC20_ABI = [
    {
        "inputs": [],
        "name": "name",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "symbol",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function"
    }
]

FACTORY_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "tokenA", "type": "address"},
            {"internalType": "address", "name": "tokenB", "type": "address"}
        ],
        "name": "getPair",
        "outputs": [{"internalType": "address", "name": "pair", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    }
]

PAIR_ABI = [
    {
        "inputs": [],
        "name": "getReserves",
        "outputs": [
            {"internalType": "uint112", "name": "reserve0", "type": "uint112"},
            {"internalType": "uint112", "name": "reserve1", "type": "uint112"},
            {"internalType": "uint32", "name": "blockTimestampLast", "type": "uint32"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "token0",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    }
]

WETH = "0x5555555555555555555555555555555555555555"

def get_token_info(token_address):
    try:
        addr = Web3.to_checksum_address(token_address)
        contract = w3.eth.contract(address=addr, abi=ERC20_ABI)

        name = contract.functions.name().call()
        symbol = contract.functions.symbol().call()
        supply_raw = contract.functions.totalSupply().call()
        decimals = contract.functions.decimals().call()
        supply = supply_raw / (10 ** decimals)

        price, market_cap = get_price(addr, decimals)

        return {
            "address": token_address,
            "name": name,
            "symbol": symbol,
            "supply": supply,
            "decimals": decimals,
            "price": price,
            "market_cap": market_cap
        }
    except Exception as e:
        return None

def get_price(token_address, decimals=18):
    try:
        factory = w3.eth.contract(
            address=Web3.to_checksum_address(config.ALTFUN_FACTORY),
            abi=FACTORY_ABI
        )

        pair_address = factory.functions.getPair(
            Web3.to_checksum_address(token_address),
            Web3.to_checksum_address(WETH)
        ).call()

        if pair_address == "0x0000000000000000000000000000000000000000":
            return None, None

        pair = w3.eth.contract(
            address=Web3.to_checksum_address(pair_address),
            abi=PAIR_ABI
        )

        reserves = pair.functions.getReserves().call()
        token0 = pair.functions.token0().call()

        if token0.lower() == token_address.lower():
            token_reserve = reserves[0]
            weth_reserve = reserves[1]
        else:
            token_reserve = reserves[1]
            weth_reserve = reserves[0]

        if token_reserve == 0:
            return None, None

        price = (weth_reserve / 1e18) / (token_reserve / (10 ** decimals))

        token_contract = w3.eth.contract(
            address=Web3.to_checksum_address(token_address),
            abi=ERC20_ABI
        )
        supply = token_contract.functions.totalSupply().call() / (10 ** decimals)
        market_cap = price * supply

        return price, market_cap
    except:
        return None, None
