import aiosqlite
import os
from datetime import datetime
from bot.config import DB_PATH


async def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                first_name TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                analyses_count INTEGER DEFAULT 0,
                last_analysis TEXT,
                balance INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                username TEXT,
                first_name TEXT,
                amount INTEGER NOT NULL,
                service_type TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                screenshot_file_id TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS expert_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                username TEXT,
                first_name TEXT,
                age TEXT,
                nationality TEXT,
                origin TEXT,
                anthropometry TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT (datetime('now')),
                admin_note TEXT
            );

            CREATE TABLE IF NOT EXISTS bot_texts (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT DEFAULT (datetime('now'))
            );
        """)
        # Миграции
        for migration in [
            "ALTER TABLE users ADD COLUMN balance INTEGER DEFAULT 0",
            "ALTER TABLE users ADD COLUMN language TEXT DEFAULT NULL",
        ]:
            try:
                await db.execute(migration)
            except Exception:
                pass
        await db.commit()


async def upsert_user(telegram_id: int, username: str | None, first_name: str | None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO users (telegram_id, username, first_name)
               VALUES (?, ?, ?)
               ON CONFLICT(telegram_id) DO UPDATE SET
                   username = excluded.username,
                   first_name = excluded.first_name""",
            (telegram_id, username, first_name),
        )
        await db.commit()


async def get_language(telegram_id: int) -> str | None:
    async with aiosqlite.connect(DB_PATH) as db:
        row = await (await db.execute(
            "SELECT language FROM users WHERE telegram_id=?", (telegram_id,)
        )).fetchone()
    return row[0] if row else None


async def set_language(telegram_id: int, lang: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET language=? WHERE telegram_id=?", (lang, telegram_id)
        )
        await db.commit()


async def increment_analysis(telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """UPDATE users SET analyses_count = analyses_count + 1,
               last_analysis = datetime('now')
               WHERE telegram_id = ?""",
            (telegram_id,),
        )
        await db.commit()


async def create_expert_request(
    telegram_id: int,
    username: str | None,
    first_name: str | None,
    age: str | None = None,
    nationality: str | None = None,
    origin: str | None = None,
    anthropometry: str | None = None,
) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """INSERT INTO expert_requests
               (telegram_id, username, first_name, age, nationality, origin, anthropometry)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (telegram_id, username, first_name, age, nationality, origin, anthropometry),
        )
        await db.commit()
        return cursor.lastrowid


async def get_stats() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        total = (await (await db.execute("SELECT COUNT(*) as c FROM users")).fetchone())["c"]
        today = (await (await db.execute(
            "SELECT COUNT(*) as c FROM users WHERE date(created_at) = date('now')"
        )).fetchone())["c"]
        analyses = (await (await db.execute(
            "SELECT COALESCE(SUM(analyses_count), 0) as c FROM users"
        )).fetchone())["c"]
        expert_pending = (await (await db.execute(
            "SELECT COUNT(*) as c FROM expert_requests WHERE status='pending'"
        )).fetchone())["c"]
    return {
        "total_users": total,
        "new_today": today,
        "total_analyses": analyses,
        "expert_pending": expert_pending,
    }


async def get_all_telegram_ids() -> list[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        rows = await (await db.execute("SELECT telegram_id FROM users")).fetchall()
    return [r[0] for r in rows]


async def get_recent_users(limit: int = 10) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        rows = await (await db.execute(
            "SELECT * FROM users ORDER BY created_at DESC LIMIT ?", (limit,)
        )).fetchall()
    return [dict(r) for r in rows]


async def get_expert_requests(status: str = "pending", limit: int = 10) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        rows = await (await db.execute(
            "SELECT * FROM expert_requests WHERE status=? ORDER BY created_at DESC LIMIT ?",
            (status, limit),
        )).fetchall()
    return [dict(r) for r in rows]


async def update_expert_status(request_id: int, status: str, note: str | None = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE expert_requests SET status=?, admin_note=? WHERE id=?",
            (status, note, request_id),
        )
        await db.commit()


async def get_bot_text(key: str, default: str = "") -> str:
    async with aiosqlite.connect(DB_PATH) as db:
        row = await (await db.execute(
            "SELECT value FROM bot_texts WHERE key=?", (key,)
        )).fetchone()
    return row[0] if row else default


async def set_bot_text(key: str, value: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO bot_texts (key, value) VALUES (?, ?)
               ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=datetime('now')""",
            (key, value),
        )
        await db.commit()


# ── Платежи ───────────────────────────────────────────────────────────────────

async def create_payment(
    telegram_id: int,
    username: str | None,
    first_name: str | None,
    amount: int,
    service_type: str,
    screenshot_file_id: str,
) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """INSERT INTO payments
               (telegram_id, username, first_name, amount, service_type, screenshot_file_id)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (telegram_id, username, first_name, amount, service_type, screenshot_file_id),
        )
        await db.commit()
        return cursor.lastrowid


async def get_payment(payment_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        row = await (await db.execute(
            "SELECT * FROM payments WHERE id=?", (payment_id,)
        )).fetchone()
    return dict(row) if row else None


async def confirm_payment(payment_id: int) -> dict | None:
    """Подтверждает платёж и начисляет баланс. Возвращает запись платежа."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        row = await (await db.execute(
            "SELECT * FROM payments WHERE id=?", (payment_id,)
        )).fetchone()
        if not row:
            return None
        payment = dict(row)
        await db.execute(
            "UPDATE payments SET status='confirmed' WHERE id=?", (payment_id,)
        )
        await db.execute(
            "UPDATE users SET balance = balance + ? WHERE telegram_id=?",
            (payment["amount"], payment["telegram_id"]),
        )
        await db.commit()
    return payment


async def reject_payment(payment_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        row = await (await db.execute(
            "SELECT * FROM payments WHERE id=?", (payment_id,)
        )).fetchone()
        if not row:
            return None
        await db.execute(
            "UPDATE payments SET status='rejected' WHERE id=?", (payment_id,)
        )
        await db.commit()
    return dict(row)


async def get_user_lang(telegram_id: int) -> str:
    async with aiosqlite.connect(DB_PATH) as db:
        row = await (await db.execute(
            "SELECT lang FROM users WHERE telegram_id=?", (telegram_id,)
        )).fetchone()
    return row[0] if row and row[0] else "ru"


async def get_balance(telegram_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        row = await (await db.execute(
            "SELECT balance FROM users WHERE telegram_id=?", (telegram_id,)
        )).fetchone()
    return row[0] if row else 0


async def add_balance(telegram_id: int, amount: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET balance = balance + ? WHERE telegram_id = ?",
            (amount, telegram_id),
        )
        await db.commit()


async def deduct_balance(telegram_id: int, amount: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET balance = balance - ? WHERE telegram_id=?",
            (amount, telegram_id),
        )
        await db.commit()


async def get_pending_payments(limit: int = 10) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        rows = await (await db.execute(
            "SELECT * FROM payments WHERE status='pending' ORDER BY created_at DESC LIMIT ?",
            (limit,),
        )).fetchall()
    return [dict(r) for r in rows]
