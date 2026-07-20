import sqlite3
from datetime import datetime

import config


def _get_connection() -> sqlite3.Connection:
    """Opens a fresh connection to the configured SQLite database file."""
    return sqlite3.connect(config.DB_NAME)


def init_db() -> None:
    """Initializes the SQLite database and creates the table if it doesn't exist."""
    conn = _get_connection()
    try:
        c = conn.cursor()
        c.execute(
            """CREATE TABLE IF NOT EXISTS summaries
               (id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT,
                summary TEXT,
                rating INTEGER,
                category TEXT,
                created_at DATETIME)"""
        )
        conn.commit()
    finally:
        conn.close()


def save_summary(filename: str, summary: str, rating: int, category: str) -> None:
    """Saves a new analysis record to the database."""
    conn = _get_connection()
    try:
        c = conn.cursor()
        c.execute(
            """INSERT INTO summaries (filename, summary, rating, category, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (filename, summary, rating, category, datetime.now()),
        )
        conn.commit()
    finally:
        conn.close()


def get_summaries_by_category(category: str):
    """Retrieves all past summaries belonging to a specific category, most recent first."""
    conn = _get_connection()
    try:
        c = conn.cursor()
        c.execute(
            """SELECT id, filename, created_at
               FROM summaries
               WHERE category = ?
               ORDER BY created_at DESC""",
            (category,),
        )
        return c.fetchall()
    finally:
        conn.close()


def get_summary_by_id(summary_id: int):
    """Retrieves a single complete analysis record using its unique ID."""
    conn = _get_connection()
    try:
        c = conn.cursor()
        c.execute(
            """SELECT filename, summary, rating, category, created_at
               FROM summaries
               WHERE id = ?""",
            (summary_id,),
        )
        return c.fetchone()
    finally:
        conn.close()
