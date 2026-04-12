import sqlite3
from pathlib import Path
from datetime import datetime


class SQLiteRepository:
    def __init__(self, db_path="data/anomaly_logs.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._create_table()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _create_table(self):
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS detection_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            transcript TEXT NOT NULL,
            score_tm REAL NOT NULL,
            score_llm REAL NOT NULL,
            score_final REAL NOT NULL,
            label_final TEXT NOT NULL,
            justification TEXT NOT NULL
        )
        """)

        conn.commit()
        conn.close()

    def insert_log(
        self,
        transcript: str,
        score_tm: float,
        score_llm: float,
        score_final: float,
        label_final: str,
        justification: str
    ):
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO detection_logs (
            timestamp,
            transcript,
            score_tm,
            score_llm,
            score_final,
            label_final,
            justification
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            transcript,
            score_tm,
            score_llm,
            score_final,
            label_final,
            justification
        ))

        conn.commit()
        conn.close()

    def get_last_logs(self, limit=10):
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT id, timestamp, transcript, score_tm, score_llm, score_final, label_final, justification
        FROM detection_logs
        ORDER BY id DESC
        LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        conn.close()
        return rows