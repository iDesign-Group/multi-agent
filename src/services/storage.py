import sqlite3
import json
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from ..config import DB_PATH


class StorageService:
    """SQLite-backed persistence for competitive research runs and evaluation audits."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS research_runs (
                    run_id TEXT PRIMARY KEY,
                    company_name TEXT NOT NULL,
                    industry TEXT NOT NULL,
                    analysis_period TEXT NOT NULL,
                    status TEXT NOT NULL,
                    confidence_score REAL DEFAULT 0.0,
                    claims_validated INTEGER DEFAULT 0,
                    claims_review INTEGER DEFAULT 0,
                    report_json TEXT,
                    pdf_path TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def save_run(
        self,
        run_id: str,
        company_name: str,
        industry: str,
        analysis_period: str,
        status: str,
        confidence_score: float,
        claims_validated: int,
        claims_review: int,
        report_data: Optional[Dict[str, Any]] = None,
        pdf_path: Optional[str] = None,
    ) -> None:
        """Saves or updates a research run in SQLite."""
        report_json = json.dumps(report_data) if report_data else None
        created_at = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO research_runs (
                    run_id, company_name, industry, analysis_period,
                    status, confidence_score, claims_validated, claims_review,
                    report_json, pdf_path, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    company_name,
                    industry,
                    analysis_period,
                    status,
                    confidence_score,
                    claims_validated,
                    claims_review,
                    report_json,
                    pdf_path,
                    created_at,
                ),
            )
            conn.commit()

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Fetches a specific run by ID."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM research_runs WHERE run_id = ?", (run_id,))
            row = cur.fetchone()
            if not row:
                return None
            data = dict(row)
            if data["report_json"]:
                data["report"] = json.loads(data["report_json"])
            return data

    def list_runs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Lists recent research runs."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT run_id, company_name, industry, analysis_period, status, confidence_score, claims_validated, claims_review, created_at, pdf_path FROM research_runs ORDER BY created_at DESC LIMIT ?",
                (limit,),
            )
            return [dict(row) for row in cur.fetchall()]
