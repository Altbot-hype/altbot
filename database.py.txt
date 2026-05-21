import aiosqlite

DB_PATH = "users.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users(
            telegram_id INTEGER PRIMARY KEY,
            wallet_private_key TEXT,
            wallet_address TEXT
        )
        """)
        await db.commit()

async def get_user(tid):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users WHERE telegram_id = ?", (tid,))
        row = await cur.fetchone()
        return dict(row) if row else None

async def save_user(tid, priv, addr):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        INSERT OR REPLACE INTO users
        (telegram_id, wallet_private_key, wallet_address)
        VALUES (?, ?, ?)
        """, (tid, priv, addr))
        await db.commit()
