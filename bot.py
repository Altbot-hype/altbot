import logging
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters, ConversationHandler
import asyncio
import sys
from cryptography.fernet import Fernet

sys.path.insert(0, '/root/altbot')

from altfun_token_fetcher import get_token_info, format_token_message
from swap_engine import SwapEngine, format_swap_result
from wallet_manager import WalletManager, format_wallet_message
from database import UserDatabase
from config import TELEGRAM_BOT_TOKEN, OWNER_ADDRESS, ENCRYPTION_KEY

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Global instances
db = UserDatabase()
wallet_manager = WalletManager()

# Encryption for private keys
try:
    cipher = Fernet(ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY)
except:
    logger.error("Invalid ENCRYPTION_KEY. Generate new one using: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"")
    cipher = None

# Conversation states
WAITING_FOR_AMOUNT = 1

# ============================================
# WALLET COMMANDS
# ============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command - create wallet if needed"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "User"
    
    if db.user_exists(user_id):
        await update.message.reply_text(
            f"👋 Welcome back, {username}!\n\n"
            "Paste a contract address to buy tokens",
            parse_mode="Markdown"
        )
    else:
        await create_wallet_cmd(update, context)

async def create_wallet_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Create new wallet for user"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "User"
    
    if db.user_exists(user_id):
        await update.message.reply_text(
            "✅ You already have a wallet!\n\n"
            "Use /wallet to view it"
        )
        return
    
    # Create new wallet
    wallet = wallet_manager.create_wallet()
    if not wallet:
        await update.message.reply_text("❌ Error creating wallet. Try again.")
        return
    
    # Save to database (encrypt private key)
    if cipher:
        encrypted_key = cipher.encrypt(wallet['private_key'].encode()).decode()
    else:
        encrypted_key = wallet['private_key']
    
    db.create_user(user_id, username, wallet['address'], encrypted_key)
    
    await update.message.reply_text(
        f"🎉 *Wallet Created!*\n\n"
        f"📍 Address:\n`{wallet['address']}`\n\n"
        f"🔐 Private Key:\n`{wallet['private_key']}`\n\n"
        f"⚠️ *SAVE YOUR PRIVATE KEY!*\n"
        f"This is your only access to this wallet!\n\n"
        f"Send HYPE to this address to start trading",
        parse_mode="Markdown"
    )

async def wallet_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show wallet information"""
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    if not user:
        await update.message.reply_text(
            "❌ No wallet found.\n\n"
            "Use /start to create one"
        )
        return
    
    # Get balance
    balance = wallet_manager.get_balance(user['wallet_address']) or 0
    
    msg = format_wallet_message({
        "wallet_address": user['wallet_address'],
        "balance": balance
    })
    
    await update.message.reply_text(msg, parse_mode="Markdown")

async def history_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show transaction history"""
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    if not user:
        await update.message.reply_text("❌ No wallet found.")
        return
    
    txs = db.get_user_transactions(user_id, limit=5)
    
    if not txs:
        await update.message.reply_text("📭 No transactions yet")
        return
    
    msg = "📊 *Recent Transactions*\n\n"
    for tx in txs:
        msg += f"• {tx['type'].upper()}: `{tx['amount']} HYPE`\n"
        msg += f"  Status: `{tx['status']}`\n"
        msg += f"  TX: `{tx['tx_hash'][:16]}...`\n\n"
    
    await update.message.reply_text(msg, parse_mode="Markdown")

# ============================================
# TOKEN LOOKUP & SWAP
# ============================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages - check for contract address"""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    # Check if user has wallet
    user = db.get_user(user_id)
    if not user:
        await update.message.reply_text(
            "❌ No wallet found.\n\n"
            "Use /start to create one"
        )
        return
    
    # Check for contract address
    if text.startswith("0x") and len(text) == 42:
        await update.message.reply_text("🔍 Scanning token...", parse_mode="Markdown")
        
        # Fetch token info
        info = get_token_info(text)
        
        if not info:
            await update.message.reply_text(
                "❌ *Token Not Found*\n\n"
                "• Invalid address\n"
                "• Not on HyperEVM\n"
                "• Not ERC20 compatible",
                parse_mode="Markdown"
            )
            return
        
        # Save token info to context
        context.user_data['token_info'] = info
        
        # Send token info
        token_msg = format_token_message(info)
        await update.message.reply_text(token_msg, parse_mode="Markdown")
        
        # Ask for amount
        await update.message.reply_text(
            "💵 *How much HYPE to spend?*\n\n"
            "Example: `0.5`\n"
            "Type `/cancel` to abort",
            parse_mode="Markdown"
        )
        
        return WAITING_FOR_AMOUNT

async def handle_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle amount input and execute swap"""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    # Check if token info exists
    if 'token_info' not in context.user_data:
        await update.message.reply_text("❌ No token selected.")
        return
    
    # Parse amount
    try:
        amount = float(text)
        if amount <= 0:
            await update.message.reply_text("❌ Amount must be positive!")
            return
        if amount > 100:
            await update.message.reply_text("❌ Max 100 HYPE per transaction")
            return
    except ValueError:
        await update.message.reply_text("❌ Invalid amount! Use: `0.5`", parse_mode="Markdown")
        return
    
    user = db.get_user(user_id)
    if not user:
        await update.message.reply_text("❌ Wallet not found.")
        return
    
    token_info = context.user_data['token_info']
    
    # Decrypt private key
    try:
        if cipher:
            decrypted_key = cipher.decrypt(user['private_key'].encode()).decode()
        else:
            decrypted_key = user['private_key']
    except Exception as e:
        logger.error(f"Decryption error: {e}")
        await update.message.reply_text("❌ Security error. Try again.")
        return
    
    # Execute swap
    await update.message.reply_text(
        f"⏳ *Processing Swap...*\n\n"
        f"🪙 Token: `{token_info['symbol']}`\n"
        f"💵 Amount: `{amount} HYPE`\n"
        f"💸 Fee: `0.005 HYPE` → Your Account\n\n"
        f"Please wait...",
        parse_mode="Markdown"
    )
    
    try:
        swap_engine = SwapEngine(
            private_key=decrypted_key,
            owner_address=OWNER_ADDRESS
        )
        result = swap_engine.swap_hype_for_token(token_info['address'], amount)
        
        if result.get("success"):
            # Save transaction
            db.save_transaction(
                user_id=user_id,
                tx_type="BUY",
                token_address=token_info['address'],
                amount=amount,
                fee=0.005,
                tx_hash=result['tx'],
                status="completed"
            )
            
            swap_msg = format_swap_result(result)
            await update.message.reply_text(swap_msg, parse_mode="Markdown")
            
            await update.message.reply_text(
                f"🎉 Transaction complete!\n\n"
                f"Token: {token_info['symbol']}\n"
                f"Amount: {amount} HYPE\n"
                f"Fee collected: 0.005 HYPE"
            )
        else:
            await update.message.reply_text(
                f"❌ *Swap Failed*\n\n`{result.get('error')}`",
                parse_mode="Markdown"
            )
            db.save_transaction(
                user_id=user_id,
                tx_type="BUY",
                token_address=token_info['address'],
                amount=amount,
                fee=0.005,
                tx_hash="FAILED",
                status="failed"
            )
    
    except Exception as e:
        logger.error(f"Swap error: {e}")
        await update.message.reply_text(f"❌ Error: `{str(e)}`", parse_mode="Markdown")
    
    # End conversation
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel operation"""
    context.user_data.clear()
    await update.message.reply_text("❌ Cancelled.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command"""
    await update.message.reply_text(
        "📋 *AltBot Commands*\n\n"
        "👛 *Wallet:*\n"
        "/start - Create wallet\n"
        "/wallet - View wallet & balance\n"
        "/history - Transaction history\n\n"
        "🔍 *Token Lookup:*\n"
        "Paste contract address (0x...)\n"
        "Enter amount → Swap executes\n\n"
        "💸 *Fees:*\n"
        "0.005 HYPE per transaction\n\n"
        "⚠️ *Always verify tokens before buying!*",
        parse_mode="Markdown"
    )

async def main():
    """Start bot"""
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Conversation handler
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)],
        states={
            WAITING_FOR_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_amount),
                CommandHandler("cancel", cancel),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    # Register handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("wallet", wallet_cmd))
    app.add_handler(CommandHandler("history", history_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("Bot starting...")
    await app.run_polling()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped")
