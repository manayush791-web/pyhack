"""
Database Manager for Telegram Bot Manager
SQLite-based with full async support via aiosqlite
"""
import sqlite3
import json
import asyncio
from datetime import datetime
from config import DB_PATH


class Database:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Managed bots table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token TEXT UNIQUE NOT NULL,
                username TEXT,
                status TEXT DEFAULT 'stopped',
                welcome_msg TEXT,
                buttons_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Users who started any managed bot
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                bot_token TEXT NOT NULL,
                first_name TEXT,
                username TEXT,
                chat_id INTEGER NOT NULL,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, bot_token)
            )
        """)

        # Admins table for Bot A
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                user_id INTEGER PRIMARY KEY
            )
        """)

        # Plugin metadata table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS plugin_meta (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        conn.commit()
        conn.close()

    # ============ BOT MANAGEMENT ============
    def add_bot(self, token, username=None, welcome_msg=None, buttons_json=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO bots (token, username, welcome_msg, buttons_json)
                VALUES (?, ?, ?, ?)
            """, (token, username, welcome_msg, buttons_json))
            conn.commit()
            return True
        except Exception as e:
            print(f"DB Error add_bot: {e}")
            return False
        finally:
            conn.close()

    def get_bot(self, token):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM bots WHERE token = ?", (token,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                "id": row[0], "token": row[1], "username": row[2],
                "status": row[3], "welcome_msg": row[4],
                "buttons_json": row[5], "created_at": row[6]
            }
        return None

    def get_all_bots(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM bots ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return [
            {
                "id": r[0], "token": r[1], "username": r[2],
                "status": r[3], "welcome_msg": r[4],
                "buttons_json": r[5], "created_at": r[6]
            }
            for r in rows
        ]

    def update_bot_status(self, token, status):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE bots SET status = ? WHERE token = ?", (status, token))
        conn.commit()
        conn.close()

    def update_bot_welcome(self, token, welcome_msg):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE bots SET welcome_msg = ? WHERE token = ?", (welcome_msg, token))
        conn.commit()
        conn.close()

    def update_bot_buttons(self, token, buttons_json):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE bots SET buttons_json = ? WHERE token = ?", (buttons_json, token))
        conn.commit()
        conn.close()

    def delete_bot(self, token):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM bots WHERE token = ?", (token,))
        cursor.execute("DELETE FROM users WHERE bot_token = ?", (token,))
        conn.commit()
        conn.close()

    # ============ USER MANAGEMENT ============
    def add_user(self, user_id, bot_token, first_name, username, chat_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO users (user_id, bot_token, first_name, username, chat_id)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, bot_token, first_name, username, chat_id))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"DB Error add_user: {e}")
            return False
        finally:
            conn.close()

    def get_all_users(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT user_id, chat_id, bot_token FROM users")
        rows = cursor.fetchall()
        conn.close()
        return [{"user_id": r[0], "chat_id": r[1], "bot_token": r[2]} for r in rows]

    def get_users_for_bot(self, token):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT user_id, chat_id FROM users WHERE bot_token = ?", (token,))
        rows = cursor.fetchall()
        conn.close()
        return [{"user_id": r[0], "chat_id": r[1]} for r in rows]

    def get_user_count(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(DISTINCT user_id) FROM users")
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def get_total_users_all_bots(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        conn.close()
        return count

    # ============ ADMIN MANAGEMENT ============
    def add_admin(self, user_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (user_id,))
        conn.commit()
        conn.close()

    def is_admin(self, user_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM admins WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result is not None

    def get_all_admins(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM admins")
        rows = cursor.fetchall()
        conn.close()
        return [r[0] for r in rows]

    # ============ EXPORT ============
    def export_tokens_to_file(self, filepath):
        bots = self.get_all_bots()
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("# Telegram Bot Tokens Export\n")
            f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Total Bots: {len(bots)}\n\n")
            for bot in bots:
                f.write(f"{bot['token']}\n")
        return filepath


# Global instance
db = Database()
