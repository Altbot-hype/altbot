import sqlite3
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class UserDatabase:
    def __init__(self, db_path="users.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Users table
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            wallet_address TEXT UNIQUE,
            private_key TEXT,
            created_at TIMESTAMP,
            balance REAL DEFAULT 0
        )''')
        
        # Transactions table
        c.execute('''CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            tx_type TEXT,
            token_address TEXT,
            amount REAL,
            fee REAL,
            tx_hash TEXT,
            status TEXT,
            created_at TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized")
    
    def create_user(self, user_id, username, wallet_address, private_key):
        """Create new user"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('''INSERT INTO users (user_id, username, wallet_address, private_key, created_at)
                         VALUES (?, ?, ?, ?, ?)''',
                      (user_id, username, wallet_address, private_key, datetime.now()))
            conn.commit()
            conn.close()
            logger.info(f"User {user_id} created with wallet {wallet_address}")
            return True
        except sqlite3.IntegrityError:
            logger.warning(f"User {user_id} already exists or wallet duplicate")
            return False
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return False
    
    def get_user(self, user_id):
        """Get user information"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            user = c.fetchone()
            conn.close()
            
            if user:
                return {
                    "user_id": user[0],
                    "username": user[1],
                    "wallet_address": user[2],
                    "private_key": user[3],
                    "created_at": user[4],
                    "balance": user[5]
                }
            return None
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None
    
    def user_exists(self, user_id):
        """Check if user exists"""
        return self.get_user(user_id) is not None
    
    def save_transaction(self, user_id, tx_type, token_address, amount, fee, tx_hash, status="pending"):
        """Save transaction record"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('''INSERT INTO transactions 
                         (user_id, tx_type, token_address, amount, fee, tx_hash, status, created_at)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                      (user_id, tx_type, token_address, amount, fee, tx_hash, status, datetime.now()))
            conn.commit()
            conn.close()
            logger.info(f"Transaction saved for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving transaction: {e}")
            return False
    
    def get_user_transactions(self, user_id, limit=10):
        """Get user's transactions"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('''SELECT * FROM transactions WHERE user_id = ? 
                         ORDER BY created_at DESC LIMIT ?''', (user_id, limit))
            txs = c.fetchall()
            conn.close()
            
            return [{
                "id": tx[0],
                "user_id": tx[1],
                "type": tx[2],
                "token": tx[3],
                "amount": tx[4],
                "fee": tx[5],
                "tx_hash": tx[6],
                "status": tx[7],
                "created_at": tx[8]
            } for tx in txs]
        except Exception as e:
            logger.error(f"Error getting transactions: {e}")
            return []
