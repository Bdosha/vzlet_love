import sqlite3

import aiosqlite
import pandas as pd

DB_PATH = 'database.db'


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_info (
                user_id  INTEGER PRIMARY KEY,
                username TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS ban (
                id       INTEGER PRIMARY KEY,
                username TEXT
            )
        """)
        await db.commit()


async def upsert_user(user_id: int, username: str | None) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO user_info(user_id) VALUES(?)",
            (user_id,),
        )
        await db.execute(
            "UPDATE user_info SET username = ? WHERE user_id = ?",
            (username, user_id),
        )
        await db.commit()


async def all_users() -> list[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM user_info") as cursor:
            rows = await cursor.fetchall()
    return [row[0] for row in rows]


async def ban(user_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT username FROM user_info WHERE user_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
        username = row[0] if row else None
        await db.execute(
            "INSERT OR IGNORE INTO ban(id, username) VALUES(?, ?)",
            (user_id, username),
        )
        await db.commit()


async def unban(user_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM ban WHERE id = ?", (user_id,))
        await db.commit()


async def check_ban(user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT 1 FROM ban WHERE id = ?", (user_id,)
        ) as cursor:
            return await cursor.fetchone() is not None


def export_sheet() -> None:
    df = pd.read_sql_query("SELECT * FROM user_info", sqlite3.connect(DB_PATH))
    df.to_excel('Пользователи.xlsx', index=False)
