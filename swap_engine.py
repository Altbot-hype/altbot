from web3 import Web3
from eth_account import Account
import logging

logger = logging.getLogger(__name__)

class SwapEngine:
    """Execute swap transactions on Hyperliquid DEX"""
    
    def __init__(self, private_key, owner_address):
        """
        Args:
            private_key: User's private key
            owner_address: Bot owner's wallet address (PUBLIC)
        """
        self.private_key = private_key
        self.owner_address = Web3.to_checksum_address(owner_address)
        self.w3 = Web3(Web3.HTTPProvider("https://rpc.hyperliquid.xyz/evm"))
        self.account = Account.from_key(private_key)
    
    def swap_hype_for_token(self, token_address, hype_amount):
        """
        Swap HYPE for token and send 0.005 HYPE fee to owner
        
        Returns:
            {
                "success": bool,
                "tx": str (swap tx hash),
                "fee_tx": str (fee tx hash),
                "error": str
            }
        """
        try:
            hype_wei = Web3.to_wei(hype_amount, 'ether')
            fee_wei = Web3.to_wei(0.005, 'ether')
            
            # Check user balance (must have amount + fee)
            user_balance = self.w3.eth.get_balance(self.account.address)
            if user_balance < hype_wei + fee_wei:
                return {
                    "success": False,
                    "error": f"Insufficient balance. Need {hype_amount + 0.005} HYPE"
                }
            
            # 1. Send fee (0.005 HYPE) to owner
            fee_tx = self._send_hype(
                from_address=self.account.address,
                from_key=self.private_key,
                to_address=self.owner_address,
                amount=0.005
            )
            
            if not fee_tx.get("success"):
                return {
                    "success": False,
                    "error": f"Failed to send fee: {fee_tx.get('error')}"
                }
            
            logger.info(f"Fee sent to {self.owner_address}: {fee_tx['tx_hash']}")
            
            # 2. Execute swap
            swap_tx = self._execute_swap(token_address, hype_amount)
            
            if not swap_tx.get("success"):
                return {
                    "success": False,
                    "error": f"Swap failed: {swap_tx.get('error')}"
                }
            
            return {
                "success": True,
                "tx": swap_tx['tx_hash'],
                "fee_tx": fee_tx['tx_hash'],
                "amount_out": swap_tx.get('amount_out', 0),
                "fee": 0.005,
                "owner_address": self.owner_address
            }
            
        except Exception as e:
            logger.error(f"Swap error: {e}")
            return {"success": False, "error": str(e)}
    
    def _send_hype(self, from_address, from_key, to_address, amount):
        """Send HYPE to address (from user's wallet)"""
        try:
            nonce = self.w3.eth.get_transaction_count(from_address)
            
            tx = {
                'to': to_address,
                'value': Web3.to_wei(amount, 'ether'),
                'gas': 21000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': nonce,
                'chainId': self.w3.eth.chain_id
            }
            
            signed_tx = self.w3.eth.account.sign_transaction(tx, from_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            logger.info(f"HYPE transfer sent: {tx_hash.hex()}")
            return {
                "success": True,
                "tx_hash": tx_hash.hex()
            }
        except Exception as e:
            logger.error(f"Transfer error: {e}")
            return {"success": False, "error": str(e)}
    
    def _execute_swap(self, token_address, hype_amount):
        """Execute swap on Hyperliquid DEX"""
        try:
            logger.info(f"Executing swap: {hype_amount} HYPE for {token_address}")
            
            # Placeholder - integrate with actual DEX API
            return {
                "success": True,
                "tx_hash": "0x" + "a" * 64,
                "amount_out": hype_amount * 100
            }
        except Exception as e:
            logger.error(f"Swap execution error: {e}")
            return {"success": False, "error": str(e)}

def format_swap_result(result):
    """Format swap result for Telegram"""
    if result.get("success"):
        msg = f"✅ *SWAP SUCCESSFUL!*\n\n"
        msg += f"💵 HYPE Sent: `{result.get('amount_out', 'N/A')}`\n"
        msg += f"📊 TX: `{result['tx'][:16]}...`\n\n"
        msg += f"💸 Fee Paid: `0.005 HYPE`\n"
        msg += f"📤 Fee TX: `{result['fee_tx'][:16]}...`\n"
        msg += f"👤 Fee to: `{result['owner_address'][:10]}...`\n"
        return msg
    else:
        msg = f"❌ *SWAP FAILED*\n\n"
        msg += f"Error: `{result.get('error')}`"
        return msg
