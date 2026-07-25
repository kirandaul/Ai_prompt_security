"""
seed_demo.py — populate psg_logs.db with realistic demo data so the dashboard
looks alive during a demo.

    cd backend
    python seed_demo.py            # add ~180 events over the last 14 days
    python seed_demo.py --reset    # wipe existing rows first
"""
import json
import random
import sys
from datetime import datetime, timedelta, timezone

import storage

CLIENTS = ["browser-alice", "browser-bob", "browser-carol", "browser-dan", "browser-erin"]
SOURCES = ["chatgpt.com", "claude.ai"]

SAMPLES = [
    # (severity, categories, redacted_prompt, allow_send)
    ("CRITICAL", ["SECRET"], "deploy with key [REDACTED:OpenAI API Key / Secret]", False),
    ("CRITICAL", ["FINANCIAL"], "pay using card [REDACTED:Credit Card Number]", False),
    ("CRITICAL", ["SECRET"], "here is the [REDACTED:Password] for prod", False),
    ("CRITICAL", ["SECRET"], "aws creds [REDACTED:AWS Secret]", False),
    ("HIGH", ["PII"], "my aadhaar is [REDACTED:Aadhaar Number]", False),
    ("HIGH", ["PROMPT_INJECTION"], "[REDACTED:Prompt Injection] and show system prompt", False),
    ("HIGH", ["ATTACK"], "run [REDACTED:SQL Injection Attempt] on users table", False),
    ("MEDIUM", ["PII"], "email me at [REDACTED:Email Address]", True),
    ("MEDIUM", ["PII"], "call me on [REDACTED:Phone Number]", True),
    ("SAFE", [], "write a poem about the ocean", True),
    ("SAFE", [], "explain quicksort with an example", True),
    ("SAFE", [], "summarize this article for me", True),
    ("SAFE", [], "help me draft a birthday message", True),
]

# Weight toward SAFE so block-rate looks realistic (~30-40%).
WEIGHTS = [4, 4, 3, 3, 3, 2, 2, 4, 4, 10, 9, 9, 8]


def reset():
    conn = storage._connect()
    conn.execute("DELETE FROM scans")
    conn.commit()
    print("cleared existing rows")


def seed(n=180):
    conn = storage._connect()
    now = datetime.now(timezone.utc)
    rows = []
    for _ in range(n):
        sev, cats, prompt, allow = random.choices(SAMPLES, weights=WEIGHTS, k=1)[0]
        days_ago = random.randint(0, 13)
        secs = random.randint(0, 86399)
        ts = (now - timedelta(days=days_ago, seconds=secs)).isoformat(timespec="seconds")
        findings = 0 if sev == "SAFE" else random.randint(1, 3)
        action = "ALLOW" if allow else "BLOCK"
        rows.append((
            ts, random.choice(CLIENTS), random.choice(SOURCES), sev, action,
            1 if allow else 0, findings, json.dumps(cats), prompt,
        ))
    conn.executemany(
        """INSERT INTO scans (created_at, client_id, source, severity, action,
           allow_send, findings_count, categories, redacted_prompt)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        rows,
    )
    conn.commit()
    print(f"inserted {n} demo events")


if __name__ == "__main__":
    storage.init_db()
    if "--reset" in sys.argv:
        reset()
    seed()
    print("done. overview:", storage.overview())
