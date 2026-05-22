from eth_account import Account
from web3 import Web3
import logging

logger = logging.getLogger(__name__)

class WalletManager:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider("https://rpc.hyperliquid.xyz/evm"))
    
    def create_wallet(self):
        """Create new wallet"""
        try:
            account = Account.create()
            return {
                "address": account.address,
                "private_key": account.key.hex(),
                "public_key": account.address
            }
        except Exception as e:
            logger.error(f"Error creating wallet: {e}")
            return None
    
    def get_balance(self, address):
        """Get HYPE balance"""
        try:
            if not Web3.is_address(address):
                return None
            
            balance_wei = self.w3.eth.get_balance(Web3.to_checksum_address(address))
            balance_hype = Web3.from_wei(balance_wei, 'ether')
            return float(balance_hype)
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            return None
    
    def validate_private_key(self, private_key):
        """Validate private key"""
        try:
            account = Account.from_key(private_key)
            return {
                "address": account.address,
                "valid": True
            }
        except Exception as e:
            logger.error(f"Invalid private key: {e}")
            return {"valid": False, "error": str(e)}

def format_wallet_message(user_data):
    """Format wallet info for Telegram"""
    balance = user_data.get("balance", 0)
    msg = f"👛 *Your Wallet*\n\n"
    msg += f"📍 Address:\n`{user_data['wallet_address']}`\n\n"
    msg += f"💰 Balance: `{balance:.4f} HYPE`\n\n"
    msg += f"⚠️ *Keep your private key safe!*\n"
    msg += f"🔒 Private key is encrypted and stored locally\n\n"
    msg += f"Use /deposit to add HYPE to your wallet"
    return msg
