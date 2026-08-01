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
                hostname        TEXT,
                user_agent      TEXT,
                scan_type       TEXT DEFAULT 'text',
                activation_key  TEXT
            )
            """
        )
        # Lightweight migration: add new columns if an older DB predates them.
        existing = {r["name"] for r in conn.execute("PRAGMA table_info(scans)")}
        for col in ("ip", "user_agent", "scan_type", "hostname", "activation_key"):
            if col not in existing:
                conn.execute(f"ALTER TABLE scans ADD COLUMN {col} TEXT")

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
        
        # --- Extension activation keys ---
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS activation_keys (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at      TEXT    NOT NULL,
                key             TEXT    UNIQUE NOT NULL,
                extension_id    TEXT    NOT NULL,
                hostname        TEXT,
                user_agent      TEXT,
                is_active       INTEGER DEFAULT 1,
                last_used       TEXT,
                expires_at      TEXT
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_akey_key ON activation_keys(key)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_akey_ext ON activation_keys(extension_id)")
        
        # Migration: add activation_keys table if missing
        existing = {r["name"] for r in conn.execute("PRAGMA table_info(activation_keys)")}
        if not existing:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS activation_keys (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at      TEXT    NOT NULL,
                    key             TEXT    UNIQUE NOT NULL,
                    extension_id    TEXT    NOT NULL,
                    hostname        TEXT,
                    user_agent      TEXT,
                    is_active       INTEGER DEFAULT 1,
                    last_used       TEXT,
                    expires_at      TEXT
                )
                """
            )
        
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
    hostname: Optional[str] = None,
    user_agent: Optional[str] = None,
    scan_type: str = "text",
    activation_key: Optional[str] = None,
) -> None:
    with _lock:
        conn = _connect()
        conn.execute(
            """
            INSERT INTO scans (created_at, client_id, source, severity, action,
                               allow_send, findings_count, categories, redacted_prompt,
                               ip, hostname, user_agent, scan_type, activation_key)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                hostname,
                user_agent,
                scan_type,
                activation_key,
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
            SELECT hostname,
                   COUNT(*) AS scans,
                   SUM(CASE WHEN allow_send = 0 THEN 1 ELSE 0 END) AS blocked
            FROM scans
            GROUP BY hostname
            ORDER BY blocked DESC, scans DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [
        {"hostname": r["hostname"] or "unknown", "scans": r["scans"], "blocked": r["blocked"] or 0}
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


# ---------------------------------------------------------------------------
# Extension Activation Keys
# ---------------------------------------------------------------------------

import secrets
import hashlib


def generate_activation_key(extension_id: str, hostname: Optional[str] = None, user_agent: Optional[str] = None) -> str:
    """Generate a unique activation key for an extension."""
    with _lock:
        conn = _connect()
        # Generate a secure random key (32 bytes = 64 hex chars)
        key = secrets.token_hex(32)
        
        try:
            conn.execute(
                """
                INSERT INTO activation_keys (created_at, key, extension_id, hostname, user_agent, is_active)
                VALUES (?, ?, ?, ?, ?, 1)
                """,
                (
                    datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    key,
                    extension_id,
                    hostname,
                    user_agent,
                )
            )
            conn.commit()
            return key
        except sqlite3.IntegrityError:
            # Key collision (extremely rare), retry
            return generate_activation_key(extension_id, hostname, user_agent)


def validate_activation_key(key: str) -> dict | None:
    """Validate an activation key and return key info if valid."""
    with _lock:
        conn = _connect()
        row = conn.execute(
            """
            SELECT * FROM activation_keys 
            WHERE key = ? AND is_active = 1
            """,
            (key,)
        ).fetchone()
        
        if not row:
            return None
        
        # Update last_used timestamp
        conn.execute(
            "UPDATE activation_keys SET last_used = ? WHERE key = ?",
            (datetime.now(timezone.utc).isoformat(timespec="seconds"), key)
        )
        conn.commit()
        
        return dict(row)


def deactivate_key(key: str) -> bool:
    """Deactivate an activation key."""
    with _lock:
        conn = _connect()
        cursor = conn.execute(
            "UPDATE activation_keys SET is_active = 0 WHERE key = ?",
            (key,)
        )
        conn.commit()
        return cursor.rowcount > 0


def get_keys_by_extension(extension_id: str) -> List[dict]:
    """Get all keys for an extension."""
    with _lock:
        conn = _connect()
        rows = conn.execute(
            """
            SELECT * FROM activation_keys 
            WHERE extension_id = ? 
            ORDER BY created_at DESC
            """,
            (extension_id,)
        ).fetchall()
    return [dict(r) for r in rows]


def get_all_activation_keys(limit: int = 100) -> List[dict]:
    """Get all activation keys with full details."""
    with _lock:
        conn = _connect()
        rows = conn.execute(
            """
            SELECT id, created_at, key, extension_id, hostname, user_agent, 
                   is_active, last_used, expires_at
            FROM activation_keys 
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,)
        ).fetchall()
    
    keys = []
    for r in rows:
        keys.append({
            "id": r["id"],
            "key": r["key"],
            "key_short": r["key"][:16] + "..." if r["key"] else "",
            "extension_id": r["extension_id"],
            "hostname": r["hostname"],
            "created_at": r["created_at"],
            "last_used": r["last_used"],
            "is_active": bool(r["is_active"]),
            "status": "🟢 Active" if r["is_active"] else "🔴 Inactive",
            "user_agent": r["user_agent"][:50] if r["user_agent"] else "N/A",
            "expires_at": r["expires_at"]
        })
    return keys


def reactivate_key(key: str) -> bool:
    """Reactivate a deactivated key."""
    with _lock:
        conn = _connect()
        cursor = conn.execute(
            "UPDATE activation_keys SET is_active = 1 WHERE key = ?",
            (key,)
        )
        conn.commit()
        return cursor.rowcount > 0


def delete_key(key: str) -> bool:
    """Delete an activation key."""
    with _lock:
        conn = _connect()
        cursor = conn.execute(
            "DELETE FROM activation_keys WHERE key = ?",
            (key,)
        )
        conn.commit()
        return cursor.rowcount > 0


def get_key_usage(key: str) -> dict:
    """Get usage statistics for a specific activation key.
    
    Shows all scans that used THIS SPECIFIC KEY.
    Returns which hostnames/people used it and how many times.
    """
    with _lock:
        conn = _connect()
        
        # Verify key exists
        key_info = conn.execute(
            "SELECT created_at FROM activation_keys WHERE key = ?",
            (key,)
        ).fetchone()
        
        if not key_info:
            return None
        
        # Get all scans that used THIS SPECIFIC KEY
        rows = conn.execute(
            """
            SELECT DISTINCT hostname, COUNT(*) as count, MAX(created_at) as last_used
            FROM scans
            WHERE activation_key = ?
            GROUP BY hostname
            ORDER BY count DESC
            """,
            (key,)
        ).fetchall()
        
        hostnames = [
            {
                "hostname": r["hostname"] or "unknown",
                "count": r["count"],
                "last_used": r["last_used"]
            }
            for r in rows
        ]
        
        total_requests = sum(h["count"] for h in hostnames)
        first_used = key_info["created_at"]
        last_used = max([h["last_used"] for h in hostnames], default=None)
        
        return {
            "key": key[:8] + "..." + key[-4:],
            "total_requests": total_requests,
            "hostnames": hostnames,
            "first_used": first_used,
            "last_used": last_used
        }
