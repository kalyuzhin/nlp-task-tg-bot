import sqlite3
from contextlib import closing
from typing import Optional

DB_PATH = "bot.db"


def init_db() -> None:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        with conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS contexts (
                    user_id INTEGER PRIMARY KEY,
                    history TEXT NOT NULL
                )
                """
            )


def get_context(user_id: int) -> Optional[str]:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.execute(
            "SELECT history FROM contexts WHERE user_id = ?",
            (user_id,),
        )
        row = cur.fetchone()
        return row[0] if row else None


def save_context(user_id: int, history: str) -> None:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        with conn:
            conn.execute(
                """
                INSERT INTO contexts (user_id, history)
                VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET history = excluded.history
                """,
                (user_id, history),
            )


def clear_context(user_id: int) -> None:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        with conn:
            conn.execute(
                "DELETE FROM contexts WHERE user_id = ?",
                (user_id,),
            )
