import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bullscows.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            is_logged_in INTEGER DEFAULT 1,
            games_played INTEGER DEFAULT 0,
            games_won INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            secret_number TEXT NOT NULL,
            attempts_left INTEGER NOT NULL,
            max_attempts INTEGER NOT NULL,
            difficulty TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    # Migration: add is_logged_in column if it doesn't exist
    columns = [row[1] for row in cursor.execute("PRAGMA table_info(users)").fetchall()]
    if "is_logged_in" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN is_logged_in INTEGER DEFAULT 1")

    conn.commit()
    conn.close()


# ── User operations ──────────────────────────────────────────────


def get_logged_in_user(telegram_id: int):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE telegram_id = ? AND is_logged_in = 1",
        (telegram_id,),
    ).fetchone()
    conn.close()
    return row


def username_exists(username: str) -> bool:
    conn = get_connection()
    row = conn.execute(
        "SELECT 1 FROM users WHERE username = ?", (username,)
    ).fetchone()
    conn.close()
    return row is not None


def register_user(telegram_id: int, username: str, password: str) -> bool:
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO users (telegram_id, username, password, is_logged_in) VALUES (?, ?, ?, 1)",
            (telegram_id, username, password),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def login_user(username: str, password: str):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE username = ? AND password = ?",
        (username, password),
    ).fetchone()
    conn.close()
    return row


def set_logged_in(telegram_id: int):
    conn = get_connection()
    conn.execute(
        "UPDATE users SET is_logged_in = 1 WHERE telegram_id = ?", (telegram_id,)
    )
    conn.commit()
    conn.close()


def logout_user(telegram_id: int):
    conn = get_connection()
    conn.execute(
        "UPDATE users SET is_logged_in = 0 WHERE telegram_id = ?", (telegram_id,)
    )
    conn.commit()
    conn.close()


def get_user(telegram_id: int):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
    ).fetchone()
    conn.close()
    return row


def rebind_telegram_id(old_telegram_id: int, user_id: int):
    conn = get_connection()
    conn.execute(
        "UPDATE users SET telegram_id = ?, is_logged_in = 1 WHERE id = ?",
        (old_telegram_id, user_id),
    )
    conn.commit()
    conn.close()


# ── Game operations ──────────────────────────────────────────────


def create_game(user_id: int, secret: str, max_attempts: int, difficulty: str) -> int:
    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO games (user_id, secret_number, attempts_left, max_attempts, difficulty)
           VALUES (?, ?, ?, ?, ?)""",
        (user_id, secret, max_attempts, max_attempts, difficulty),
    )
    game_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return game_id


def get_active_game(user_id: int):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM games WHERE user_id = ? AND is_active = 1 ORDER BY id DESC LIMIT 1",
        (user_id,),
    ).fetchone()
    conn.close()
    return row


def decrement_attempts(game_id: int):
    conn = get_connection()
    conn.execute(
        "UPDATE games SET attempts_left = attempts_left - 1 WHERE id = ?", (game_id,)
    )
    conn.commit()
    conn.close()


def end_game(game_id: int):
    conn = get_connection()
    conn.execute("UPDATE games SET is_active = 0 WHERE id = ?", (game_id,))
    conn.commit()
    conn.close()


def increment_games_played(user_id: int):
    conn = get_connection()
    conn.execute(
        "UPDATE users SET games_played = games_played + 1 WHERE id = ?", (user_id,)
    )
    conn.commit()
    conn.close()


def increment_games_won(user_id: int):
    conn = get_connection()
    conn.execute(
        "UPDATE users SET games_won = games_won + 1 WHERE id = ?", (user_id,)
    )
    conn.commit()
    conn.close()
