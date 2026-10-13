"""
ZED VISION - SQLite Experiment & Session Metadata Store
Persists tracking runs, ablation results, and diagnostic events locally.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional

from backend.app.core.config import config


class ExperimentStore:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or config.experiments_db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS experiments (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    video_name TEXT NOT NULL,
                    is_oie INTEGER NOT NULL,
                    config_json TEXT NOT NULL,
                    metrics_json TEXT NOT NULL,
                    status TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    video_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    is_oie INTEGER NOT NULL,
                    metrics_json TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS diagnostic_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    frame_idx INTEGER NOT NULL,
                    event_type TEXT NOT NULL,
                    track_id INTEGER NOT NULL,
                    event_json TEXT NOT NULL
                )
            """)
            conn.commit()

    def save_experiment(
        self,
        exp_id: str,
        name: str,
        video_name: str,
        is_oie: bool,
        config_dict: Dict[str, Any],
        metrics_dict: Dict[str, Any],
        status: str = "COMPLETED"
    ) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO experiments
                (id, name, created_at, video_name, is_oie, config_json, metrics_json, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                exp_id,
                name,
                datetime.now(timezone.utc).isoformat(),
                video_name,
                1 if is_oie else 0,
                json.dumps(config_dict),
                json.dumps(metrics_dict),
                status
            ))
            conn.commit()

    def list_experiments(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM experiments ORDER BY created_at DESC")
            rows = cursor.fetchall()
            results = []
            for r in rows:
                results.append({
                    "id": r["id"],
                    "name": r["name"],
                    "created_at": r["created_at"],
                    "video_name": r["video_name"],
                    "is_oie": bool(r["is_oie"]),
                    "config": json.loads(r["config_json"]),
                    "metrics": json.loads(r["metrics_json"]),
                    "status": r["status"]
                })
            return results

    def get_experiment(self, exp_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM experiments WHERE id = ?", (exp_id,))
            r = cursor.fetchone()
            if not r:
                return None
            return {
                "id": r["id"],
                "name": r["name"],
                "created_at": r["created_at"],
                "video_name": r["video_name"],
                "is_oie": bool(r["is_oie"]),
                "config": json.loads(r["config_json"]),
                "metrics": json.loads(r["metrics_json"]),
                "status": r["status"]
            }

    def save_session(
        self,
        session_id: str,
        video_name: str,
        is_oie: bool,
        status: str = "INITIALIZED",
        metrics: Optional[Dict[str, Any]] = None
    ) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO sessions
                (session_id, created_at, video_name, status, is_oie, metrics_json)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                datetime.now(timezone.utc).isoformat(),
                video_name,
                status,
                1 if is_oie else 0,
                json.dumps(metrics) if metrics else None
            ))
            conn.commit()

    def list_sessions(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sessions ORDER BY created_at DESC LIMIT 20")
            rows = cursor.fetchall()
            results = []
            for r in rows:
                results.append({
                    "session_id": r["session_id"],
                    "created_at": r["created_at"],
                    "video_name": r["video_name"],
                    "status": r["status"],
                    "is_oie": bool(r["is_oie"]),
                    "metrics": json.loads(r["metrics_json"]) if r["metrics_json"] else None
                })
            return results
