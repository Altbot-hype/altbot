from eth_account import Account
import secrets

def create_wallet():
    pk = "0x" + secrets.token_hex(32)
    addr = Account.from_key(pk).address
    return pk, addr
