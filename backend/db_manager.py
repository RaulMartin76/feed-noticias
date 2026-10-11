import sqlite3
import json
import os
from typing import List, Dict, Any
import tempfile

def get_writable_db_path() -> str:
    local_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "news_ai_feed.db")
    try:
        test_file = local_path + ".test"
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        return local_path
    except Exception:
        return os.path.join(tempfile.gettempdir(), "news_ai_feed.db")

DB_PATH = get_writable_db_path()

class DatabaseManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS news (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                source TEXT NOT NULL,
                category TEXT NOT NULL,
                date TEXT NOT NULL,
                summary TEXT NOT NULL,
                sentiment TEXT,
                sentiment_badge TEXT,
                hashtags TEXT,
                entities TEXT,
                saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS reddit_discussions (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                subreddit TEXT NOT NULL,
                author TEXT NOT NULL,
                date TEXT NOT NULL,
                summary TEXT NOT NULL,
                sentiment TEXT,
                sentiment_badge TEXT,
                hashtags TEXT,
                saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS favorites (
                news_id TEXT PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (news_id) REFERENCES news (id)
            )
            """)
            conn.commit()

    def clear_all_news(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM news")
            conn.commit()

    def save_news_items(self, items: List[Dict[str, Any]]):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for item in items:
                cursor.execute("""
                INSERT OR REPLACE INTO news (id, title, url, source, category, date, summary, sentiment, sentiment_badge, hashtags, entities)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    item.get("id"),
                    item.get("title"),
                    item.get("url"),
                    item.get("source"),
                    item.get("category", "General"),
                    item.get("date"),
                    item.get("summary"),
                    item.get("sentiment", "Innovación"),
                    item.get("sentiment_badge", "🚀 Innovación"),
                    json.dumps(item.get("hashtags", [])),
                    json.dumps(item.get("entities", []))
                ))
            conn.commit()

    def get_all_news(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM news ORDER BY date DESC, saved_at DESC")
            rows = cursor.fetchall()
            
            result = []
            for row in rows:
                item = dict(row)
                item["hashtags"] = json.loads(item["hashtags"]) if item["hashtags"] else []
                item["entities"] = json.loads(item["entities"]) if item["entities"] else []
                result.append(item)
            return result

    # --- MÉTODOS PARA REDDIT ---
    def clear_all_reddit(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM reddit_discussions")
            conn.commit()

    def save_reddit_items(self, items: List[Dict[str, Any]]):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for item in items:
                cursor.execute("""
                INSERT OR REPLACE INTO reddit_discussions (id, title, url, subreddit, author, date, summary, sentiment, sentiment_badge, hashtags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    item.get("id"),
                    item.get("title"),
                    item.get("url"),
                    item.get("subreddit", "r/AI"),
                    item.get("author", "u/anon"),
                    item.get("date"),
                    item.get("summary"),
                    item.get("sentiment", "Tendencia"),
                    item.get("sentiment_badge", "🔥 Viral"),
                    json.dumps(item.get("hashtags", []))
                ))
            conn.commit()

    def get_all_reddit(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM reddit_discussions ORDER BY date DESC, saved_at DESC")
            rows = cursor.fetchall()
            
            result = []
            for row in rows:
                item = dict(row)
                item["hashtags"] = json.loads(item["hashtags"]) if item["hashtags"] else []
                result.append(item)
            return result

    def get_favorites(self) -> List[str]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT news_id FROM favorites")
            rows = cursor.fetchall()
            return [row["news_id"] for row in rows]

    def add_favorite(self, news_id: str):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR IGNORE INTO favorites (news_id) VALUES (?)", (news_id,))
            conn.commit()

    def remove_favorite(self, news_id: str):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM favorites WHERE news_id = ?", (news_id,))
            conn.commit()
