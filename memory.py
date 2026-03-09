"""
memory.py — Long-term memory with meaningful session names
Sessions are auto-named from the first user message (e.g. "Property taxes in Sri Lanka")
"""

import logging
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

import config

logger = logging.getLogger("verite.memory")


class MemoryManager:

    def __init__(self, db_path: Path = config.MEMORY_DB_PATH):
        self.db_path = str(db_path)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id  TEXT PRIMARY KEY,
                    created_at  TEXT NOT NULL,
                    user_label  TEXT
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id  TEXT NOT NULL,
                    role        TEXT NOT NULL,
                    content     TEXT NOT NULL,
                    created_at  TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                );

                CREATE INDEX IF NOT EXISTS idx_messages_session
                    ON messages(session_id, id);
            """)

    def new_session(self) -> str:
        session_id = str(uuid.uuid4())
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO sessions (session_id, created_at) VALUES (?, ?)",
                (session_id, datetime.utcnow().isoformat()),
            )
        return session_id

    def set_session_label(self, session_id: str, first_message: str) -> None:
        """
        Auto-generate a meaningful label from the first user message.
        Truncate to 40 chars for display.
        """
        label = first_message.strip()
        # Capitalise and truncate
        label = label[0].upper() + label[1:] if label else "New conversation"
        if len(label) > 40:
            label = label[:37] + "..."
        with self._connect() as conn:
            conn.execute(
                "UPDATE sessions SET user_label = ? WHERE session_id = ?",
                (label, session_id),
            )

    def list_sessions(self, limit: int = 20) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT s.session_id, s.created_at, s.user_label,
                       COUNT(m.id) AS message_count
                FROM sessions s
                LEFT JOIN messages m ON s.session_id = m.session_id
                GROUP BY s.session_id
                ORDER BY s.created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    def save_message(self, session_id: str, role: str, content: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO messages (session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
                (session_id, role, content, datetime.utcnow().isoformat()),
            )
        # Auto-label session from first user message
        if role == "user":
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT user_label FROM sessions WHERE session_id = ?",
                    (session_id,),
                ).fetchone()
                if row and not row["user_label"]:
                    self.set_session_label(session_id, content)

    def load_session_messages(self, session_id: str, limit: int | None = None) -> list[dict]:
        if limit:
            query = """
                SELECT role, content FROM (
                    SELECT role, content, id FROM messages
                    WHERE session_id = ? ORDER BY id DESC LIMIT ?
                ) sub ORDER BY id
            """
            params = [session_id, limit]
        else:
            query  = "SELECT role, content FROM messages WHERE session_id = ? ORDER BY id"
            params = [session_id]

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [{"role": r["role"], "content": r["content"]} for r in rows]

    def get_long_term_context(self, current_session_id: str) -> list[dict]:
        sessions = self.list_sessions(limit=10)
        previous = next(
            (s for s in sessions if s["session_id"] != current_session_id),
            None,
        )
        if not previous:
            return []
        return self.load_session_messages(
            previous["session_id"],
            limit=config.LONG_TERM_LOAD_TURNS,
        )

    def delete_session(self, session_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
