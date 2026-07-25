"""
storage.py — lightweight SQLite log of scan events.

Zero external dependencies (uses the stdlib sqlite3). One row per prompt scan.

PRIVACY: we store a REDACTED copy of the prompt (detected secrets replaced with
[REDACTED:<reason>]) plus metadata — never the raw secret. Flip STORE_PROMPTS
to False to keep only metadata.
"""
from __future__ import annotations

import json
import os
import sqlite3
import threading
from datetime import datetime, timezone
from typing import List, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "psg_logs.db")
STORE_PROMPTS = True  # store the redacted prompt text (metadata is always stored)

_lock = threading.Lock()
_conn: Optional[sqlite3.Connection] = None


def _connect() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA journal_mode=WAL;")
    return _conn


def init_db() -> None:
    with _lock:
        conn = _connect()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS scans (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at      TEXT    NOT NULL,
                client_id       TEXT,
                source          TEXT,
                severity        TEXT,
                action          TEXT,
                allow_send      INTEGER,
                findings_count  INTEGER,
                categories      TEXT,
                redacted_prompt TEXT,
                ip              TEXT,
                user_agent      TEXT,
                scan_type       TEXT DEFAULT 'text'
            )
            """
        )
        # Lightweight migration: add new columns if an older DB predates them.
        existing = {r["name"] for r in conn.execute("PRAGMA table_info(scans)")}
        for col in ("ip", "user_agent", "scan_type"):
            if col not in existing:
                conn.execute(f"ALTER TABLE scans ADD COLUMN {col} TEXT")
                if col == "scan_type":
                    conn.execute("UPDATE scans SET scan_type = 'text' WHERE scan_type IS NULL")

        # --- accuracy benchmark tables (separate from the live audit log) ---
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS benchmark_runs (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at  TEXT NOT NULL,
                total       INTEGER, tp INTEGER, fp INTEGER, tn INTEGER, fn INTEGER,
                accuracy    REAL, precision_ REAL, recall REAL, f1 REAL,
                duration_ms INTEGER
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS benchmark_cases (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id    INTEGER NOT NULL,
                prompt    TEXT,
                category  TEXT,
                expected  INTEGER,
                detected  INTEGER,
                outcome   TEXT,
                risk_score INTEGER,
                findings  TEXT
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_bcase_run ON benchmark_cases(run_id, outcome)")
        conn.commit()


# ---------------------------------------------------------------------------
# Accuracy benchmark
# ---------------------------------------------------------------------------

def save_benchmark(summary: dict, cases: List[dict]) -> int:
    with _lock:
        conn = _connect()
        cur = conn.execute(
            """
            INSERT INTO benchmark_runs (created_at, total, tp, fp, tn, fn,
                                        accuracy, precision_, recall, f1, duration_ms)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                datetime.now(timezone.utc).isoformat(timespec="seconds"),
                summary["total"], summary["tp"], summary["fp"], summary["tn"], summary["fn"],
                summary["accuracy"], summary["precision"], summary["recall"], summary["f1"],
                summary.get("duration_ms", 0),
            ),
        )
        run_id = cur.lastrowid
        conn.executemany(
            """
            INSERT INTO benchmark_cases (run_id, prompt, category, expected, detected,
                                         outcome, risk_score, findings)
            VALUES (?,?,?,?,?,?,?,?)
            """,
            [
                (run_id, c["prompt"], c["category"], 1 if c["expected"] else 0,
                 1 if c["detected"] else 0, c["outcome"], c.get("risk_score", 0),
                 json.dumps(c.get("findings", [])))
                for c in cases
            ],
        )
        conn.commit()
    return run_id


def latest_benchmark() -> Optional[dict]:
    with _lock:
        conn = _connect()
        row = conn.execute("SELECT * FROM benchmark_runs ORDER BY id DESC LIMIT 1").fetchone()
        if not row:
            return None
        run = dict(row)
        by_cat = conn.execute(
            """
            SELECT category, outcome, COUNT(*) AS c
            FROM benchmark_cases WHERE run_id = ? GROUP BY category, outcome
            """,
            (run["id"],),
        ).fetchall()
    run["precision"] = run.pop("precision_", 0)
    breakdown: dict = {}
    for r in by_cat:
        breakdown.setdefault(r["category"], {})[r["outcome"]] = r["c"]
    run["by_category"] = breakdown
    return run


def benchmark_cases(run_id: int, outcome: Optional[str] = None, limit: int = 100) -> List[dict]:
    with _lock:
        conn = _connect()
        if outcome:
            rows = conn.execute(
                "SELECT * FROM benchmark_cases WHERE run_id=? AND outcome=? ORDER BY id LIMIT ?",
                (run_id, outcome, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM benchmark_cases WHERE run_id=? ORDER BY id LIMIT ?",
                (run_id, limit),
            ).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["expected"] = bool(d["expected"])
        d["detected"] = bool(d["detected"])
        try:
            d["findings"] = json.loads(d["findings"] or "[]")
        except (ValueError, TypeError):
            d["findings"] = []
        out.append(d)
    return out


def log_scan(
    *,
    client_id: Optional[str],
    source: Optional[str],
    severity: str,
    action: str,
    allow_send: bool,
    findings_count: int,
    categories: List[str],
    redacted_prompt: str,
    ip: Optional[str] = None,
    user_agent: Optional[str] = None,
    scan_type: str = "text",
) -> None:
    with _lock:
        conn = _connect()
        conn.execute(
            """
            INSERT INTO scans (created_at, client_id, source, severity, action,
                               allow_send, findings_count, categories, redacted_prompt,
                               ip, user_agent, scan_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(timespec="seconds"),
                client_id,
                source,
                severity,
                action,
                1 if allow_send else 0,
                findings_count,
                json.dumps(categories),
                redacted_prompt if STORE_PROMPTS else None,
                ip,
                user_agent,
                scan_type,
            ),
        )
        conn.commit()


def recent(limit: int = 50, client_id: Optional[str] = None) -> List[dict]:
    with _lock:
        conn = _connect()
        if client_id:
            rows = conn.execute(
                "SELECT * FROM scans WHERE client_id = ? ORDER BY id DESC LIMIT ?",
                (client_id, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM scans ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["allow_send"] = bool(d["allow_send"])
        try:
            d["categories"] = json.loads(d["categories"] or "[]")
        except (ValueError, TypeError):
            d["categories"] = []
        out.append(d)
    return out


def stats() -> dict:
    with _lock:
        conn = _connect()
        total = conn.execute("SELECT COUNT(*) AS c FROM scans").fetchone()["c"]
        by_sev = conn.execute(
            "SELECT severity, COUNT(*) AS c FROM scans GROUP BY severity"
        ).fetchall()
        by_client = conn.execute(
            "SELECT client_id, COUNT(*) AS c FROM scans GROUP BY client_id ORDER BY c DESC LIMIT 20"
        ).fetchall()
    return {
        "total": total,
        "by_severity": {row["severity"]: row["c"] for row in by_sev},
        "by_client": {(row["client_id"] or "unknown"): row["c"] for row in by_client},
    }


# ---------------------------------------------------------------------------
# Analytics for the admin dashboard
# ---------------------------------------------------------------------------

def overview() -> dict:
    """Hero metrics for the dashboard top row."""
    with _lock:
        conn = _connect()
        row = conn.execute(
            """
            SELECT
                COUNT(*)                                             AS total_scans,
                COALESCE(SUM(CASE WHEN allow_send = 0 THEN 1 ELSE 0 END), 0) AS threats_blocked,
                COALESCE(SUM(findings_count), 0)                     AS items_flagged,
                COALESCE(SUM(CASE WHEN allow_send = 0 THEN findings_count ELSE 0 END), 0) AS secrets_protected,
                COUNT(DISTINCT client_id)                           AS active_clients
            FROM scans
            """
        ).fetchone()
    return {
        "total_scans": row["total_scans"],
        "threats_blocked": row["threats_blocked"],
        "items_flagged": row["items_flagged"],
        "secrets_protected": row["secrets_protected"],
        "active_clients": row["active_clients"],
    }


def severity_breakdown() -> dict:
    with _lock:
        conn = _connect()
        rows = conn.execute(
            "SELECT severity, COUNT(*) AS c FROM scans GROUP BY severity"
        ).fetchall()
    return {row["severity"]: row["c"] for row in rows}


def timeseries(days: int = 14) -> list:
    """Scans per day for the last `days` days (blocked vs allowed)."""
    with _lock:
        conn = _connect()
        rows = conn.execute(
            """
            SELECT substr(created_at, 1, 10) AS day,
                   COUNT(*) AS total,
                   SUM(CASE WHEN allow_send = 0 THEN 1 ELSE 0 END) AS blocked
            FROM scans
            GROUP BY day
            ORDER BY day DESC
            LIMIT ?
            """,
            (days,),
        ).fetchall()
    data = [{"day": r["day"], "total": r["total"], "blocked": r["blocked"] or 0} for r in rows]
    data.reverse()
    return data


def category_breakdown() -> dict:
    """Count findings per category by expanding the stored JSON arrays."""
    with _lock:
        conn = _connect()
        rows = conn.execute("SELECT categories FROM scans").fetchall()
    counts: dict = {}
    for r in rows:
        try:
            cats = json.loads(r["categories"] or "[]")
        except (ValueError, TypeError):
            cats = []
        for c in cats:
            counts[c] = counts.get(c, 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: kv[1], reverse=True))


def top_clients(limit: int = 8) -> list:
    with _lock:
        conn = _connect()
        rows = conn.execute(
            """
            SELECT client_id,
                   COUNT(*) AS scans,
                   SUM(CASE WHEN allow_send = 0 THEN 1 ELSE 0 END) AS blocked
            FROM scans
            GROUP BY client_id
            ORDER BY blocked DESC, scans DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [
        {"client_id": r["client_id"] or "unknown", "scans": r["scans"], "blocked": r["blocked"] or 0}
        for r in rows
    ]


def query_logs(
    *,
    limit: int = 50,
    offset: int = 0,
    severity: Optional[str] = None,
    source: Optional[str] = None,
    client_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    search: Optional[str] = None,
) -> dict:
    """Filtered, paginated log query for the events table."""
    where = []
    params: list = []
    if severity:
        where.append("severity = ?"); params.append(severity)
    if source:
        where.append("source = ?"); params.append(source)
    if client_id:
        where.append("client_id = ?"); params.append(client_id)
    if date_from:
        where.append("created_at >= ?"); params.append(date_from)
    if date_to:
        where.append("created_at <= ?"); params.append(date_to + "T23:59:59")
    if search:
        where.append("redacted_prompt LIKE ?"); params.append(f"%{search}%")

    clause = ("WHERE " + " AND ".join(where)) if where else ""
    with _lock:
        conn = _connect()
        total = conn.execute(f"SELECT COUNT(*) AS c FROM scans {clause}", params).fetchone()["c"]
        rows = conn.execute(
            f"SELECT * FROM scans {clause} ORDER BY id DESC LIMIT ? OFFSET ?",
            params + [min(limit, 500), offset],
        ).fetchall()

    logs = []
    for r in rows:
        d = dict(r)
        d["allow_send"] = bool(d["allow_send"])
        try:
            d["categories"] = json.loads(d["categories"] or "[]")
        except (ValueError, TypeError):
            d["categories"] = []
        logs.append(d)
    return {"total": total, "count": len(logs), "logs": logs}
