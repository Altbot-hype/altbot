from web3 import Web3
from eth_account import Account
import config

w3 = Web3(Web3.HTTPProvider(config.HYPEREVM_RPC))

ROUTER_ABI = [
    {
        "inputs": [
            {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
            {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
            {"internalType": "address[]", "name": "path", "type": "address[]"},
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "deadline", "type": "uint256"}
        ],
        "name": "swapExactTokensForTokens",
        "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
            {"internalType": "address[]", "name": "path", "type": "address[]"},
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "deadline", "type": "uint256"}
        ],
        "name": "swapExactETHForTokens",
        "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
        "stateMutability": "payable",
        "type": "function"
    }
]

ERC20_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "spender", "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "address", "name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]

def send_hype_fee(private_key):
    try:
        account = Account.from_key(private_key)
        nonce = w3.eth.get_transaction_count(account.address)
        fee_wei = w3.to_wei(config.FEE_AMOUNT_HYPE, "ether")

        tx = {
            "to": config.FEE_WALLET,
            "value": fee_wei,
            "gas": 21000,
            "gasPrice": w3.eth.gas_price,
            "nonce": nonce,
            "chainId": w3.eth.chain_id
        }

        signed = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
        return tx_hash.hex()
    except Exception as e:
        return None

def buy_token(private_key, token_address, amount_hype, slippage=0.05):
    try:
        account = Account.from_key(private_key)
        router = w3.eth.contract(
            address=Web3.to_checksum_address(config.ALTFUN_ROUTER),
            abi=ROUTER_ABI
        )

        weth = "0x5555555555555555555555555555555555555555"
        path = [
            Web3.to_checksum_address(weth),
            Web3.to_checksum_address(token_address)
        ]

        amount_in_wei = w3.to_wei(amount_hype, "ether")
        deadline = w3.eth.get_block("latest")["timestamp"] + 300
        nonce = w3.eth.get_transaction_count(account.address)

        tx = router.functions.swapExactETHForTokens(
            0,
            path,
            account.address,
            deadline
        ).build_transaction({
            "from": account.address,
            "value": amount_in_wei,
            "gas": 300000,
            "gasPrice": w3.eth.gas_price,
            "nonce": nonce,
            "chainId": w3.eth.chain_id
        })

        signed = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)

        send_hype_fee(private_key)

        return {"success": True, "tx": tx_hash.hex()}
    except Exception as e:
        return {"success": False, "error": str(e)}

def sell_token(private_key, token_address, amount_tokens, slippage=0.05):
    try:
        account = Account.from_key(private_key)
        router = w3.eth.contract(
            address=Web3.to_checksum_address(config.ALTFUN_ROUTER),
            abi=ROUTER_ABI
        )

        token_contract = w3.eth.contract(
            address=Web3.to_checksum_address(token_address),
            abi=ERC20_ABI
        )

        amount_in_wei = w3.to_wei(amount_tokens, "ether")

        approve_nonce = w3.eth.get_transaction_count(account.address)
        approve_tx = token_contract.functions.approve(
            Web3.to_checksum_address(config.ALTFUN_ROUTER),
            amount_in_wei
        ).build_transaction({
            "from": account.address,
            "gas": 100000,
            "gasPrice": w3.eth.gas_price,
            "nonce": approve_nonce,
            "chainId": w3.eth.chain_id
        })

        signed_approve = account.sign_transaction(approve_tx)
        w3.eth.send_raw_transaction(signed_approve.rawTransaction)

        weth = "0x5555555555555555555555555555555555555555"
        path = [
            Web3.to_checksum_address(token_address),
            Web3.to_checksum_address(weth)
        ]

        deadline = w3.eth.get_block("latest")["timestamp"] + 300
        swap_nonce = w3.eth.get_transaction_count(account.address)

        tx = router.functions.swapExactTokensForTokens(
            amount_in_wei,
            0,
            path,
            account.address,
            deadline
        ).build_transaction({
            "from": account.address,
            "gas": 300000,
            "gasPrice": w3.eth.gas_price,
            "nonce": swap_nonce,
            "chainId": w3.eth.chain_id
        })

        signed = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)

        send_hype_fee(private_key)

        return {"success": True, "tx": tx_hash.hex()}
    except Exception as e:
        return {"success": False, "error": str(e)}
