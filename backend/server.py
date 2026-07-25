"""
server.py — Production API that the Chrome extension calls.

This bridges the rich detector framework (detectors/*.py) to the exact JSON
contract the extension's detection.js expects:

    POST /api/scan   { "prompt": "<text>" }
    ->  { "allowSend": bool,
          "severity": "CRITICAL|HIGH|MEDIUM|LOW|SAFE",
          "findings": [ { "severity": "HIGH", "reason": "...",
                          "action": "BLOCK|WARN", "category": "...",
                          "confidence": 0.0-1.0, "evidence": "AK****LE" } ] }

Design notes
------------
* Every detector runs concurrently.
* Overlapping matches are collapsed to the highest-scoring one (fewer false
  positives / duplicate noise).
* Low-confidence matches are dropped below MIN_CONFIDENCE.
* Evidence is MASKED — the raw secret is never echoed back to the client.
* Raw prompts are never logged.
* CORS is restricted to the AI sites (+ localhost for development).

Run:
    cd backend
    uvicorn server:app --host 127.0.0.1 --port 3000 --reload
"""
from __future__ import annotations

import asyncio
from typing import List

from fastapi import FastAPI, Depends, HTTPException, Response, Cookie, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from typing import Optional

import base64
import binascii

import auth
import ocr
import risk
import storage
import tier2_secrets
from models.threat_finding import ThreatFinding

from detectors.api_key_detector import ApiKeyDetector
from detectors.email_detector import EmailDetector
from detectors.phone_detector import PhoneDetector
from detectors.password_detector import PasswordDetector
from detectors.jwt_detector import JwtDetector
from detectors.private_key_detector import PrivateKeyDetector
from detectors.aws_secret_detector import AwsSecretDetector
from detectors.credit_card_detector import CreditCardDetector
from detectors.aadhaar_detector import AadhaarDetector
from detectors.pan_detector import PanDetector
from detectors.sql_detector import SqlInjectionDetector
from detectors.xss_detector import XssDetector
from detectors.prompt_injection_detector import PromptInjectionDetector
from detectors.jailbreak_detector import JailbreakDetector
from detectors.health_detector import HealthDetector

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MAX_PROMPT_LENGTH = 20000     # mirror the extension's MAX_SCAN_LENGTH
MIN_CONFIDENCE = 0.50         # drop findings below this confidence
MAX_FINDINGS = 50             # cap response size

DETECTORS = [
    ApiKeyDetector(),
    EmailDetector(),
    PhoneDetector(),
    PasswordDetector(),
    JwtDetector(),
    PrivateKeyDetector(),
    AwsSecretDetector(),
    CreditCardDetector(),
    AadhaarDetector(),
    PanDetector(),
    SqlInjectionDetector(),
    XssDetector(),
    PromptInjectionDetector(),
    JailbreakDetector(),
    HealthDetector(),
]

# Human-readable labels for the panel. The raw detector name is the fallback.
REASON_LABELS = {
    "API_KEY_DETECTOR": "API Key / Secret",
    "AWS_SECRET_DETECTOR": "AWS Secret",
    "CREDIT_CARD_DETECTOR": "Credit Card Number",
    "EMAIL_DETECTOR": "Email Address",
    "PHONE_DETECTOR": "Phone Number",
    "AADHAAR_DETECTOR": "Aadhaar Number",
    "PAN_DETECTOR": "PAN Number",
    "PASSWORD_DETECTOR": "Password",
    "PRIVATE_KEY_DETECTOR": "Private Key",
    "JWT_DETECTOR": "JWT Token",
    "SQL_INJECTION_DETECTOR": "SQL Injection Attempt",
    "XSS_DETECTOR": "XSS Attempt",
    "PROMPT_INJECTION_DETECTOR": "Prompt Injection",
    "JAILBREAK_DETECTOR": "Jailbreak Attempt",
    "HEALTH_DETECTOR": "Health Information",
}

# CORS: the content script's fetch carries the AI site's Origin header.
ALLOWED_ORIGINS = [
    "https://chatgpt.com",
    "https://chat.openai.com",
    "https://claude.ai",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# ---------------------------------------------------------------------------
# Mapping helpers
# ---------------------------------------------------------------------------

def severity_to_level(severity: int) -> str:
    """Map the detectors' 0-100 severity scale to the extension's levels."""
    if severity >= 90:
        return "CRITICAL"
    if severity >= 70:
        return "HIGH"
    if severity >= 40:
        return "MEDIUM"
    return "LOW"


def action_for(level: str) -> str:
    return "BLOCK" if level in ("CRITICAL", "HIGH") else "WARN"


def reason_for(finding: ThreatFinding) -> str:
    label = REASON_LABELS.get(finding.detector, finding.detector.replace("_", " ").title())
    meta = finding.metadata or {}
    if finding.detector == "TIER2_SECRETS":
        return meta.get("type") or "Secret / Token"
    provider = meta.get("provider")
    if finding.detector == "API_KEY_DETECTOR" and provider and provider not in ("HighEntropy",):
        return f"{provider} API Key / Secret"
    return label


def mask_evidence(evidence: str) -> str:
    """Never echo the raw secret. Show only enough to recognise it."""
    if not evidence:
        return ""
    s = str(evidence)
    s = " ".join(s.split())          # collapse whitespace/newlines
    if len(s) <= 6:
        return "*" * len(s)
    return f"{s[:2]}{'*' * min(len(s) - 4, 8)}{s[-2:]}"


def resolve_overlaps(findings: List[ThreatFinding]) -> List[ThreatFinding]:
    """
    Collapse overlapping spans, keeping the highest-scoring finding for each
    region. This removes duplicate noise (e.g. a card number also flagged as a
    high-entropy string) and reduces false positives.
    """
    ordered = sorted(findings, key=lambda f: f.score, reverse=True)
    kept: List[ThreatFinding] = []
    for f in ordered:
        overlaps = any(not (f.end <= k.start or f.start >= k.end) for k in kept)
        if not overlaps:
            kept.append(f)
    kept.sort(key=lambda f: f.start)
    return kept


# ---------------------------------------------------------------------------
# Core scan
# ---------------------------------------------------------------------------

def redact(text: str, raw_findings: List[ThreatFinding]) -> str:
    """Replace each detected span with [REDACTED:<reason>] so the stored copy
    keeps context for auditing but never persists the actual secret."""
    if not raw_findings:
        return text
    parts = []
    cursor = 0
    for f in sorted(raw_findings, key=lambda x: x.start):
        if f.start < cursor:  # overlap already handled, skip
            continue
        parts.append(text[cursor:f.start])
        parts.append(f"[REDACTED:{reason_for(f)}]")
        cursor = f.end
    parts.append(text[cursor:])
    return "".join(parts)


async def analyze(prompt: str):
    """Returns (result_dict, kept_raw_findings)."""
    text = (prompt or "")[:MAX_PROMPT_LENGTH]

    if not text.strip():
        empty = {"allowSend": True, "severity": "SAFE", "action": "ALLOW", "findings": [], "summary": {}}
        return empty, []

    async def run(detector):
        try:
            return await detector.detect(text)
        except Exception:
            # Base contract: a detector must never break the whole scan.
            return []

    results = await asyncio.gather(*(run(d) for d in DETECTORS))

    raw: List[ThreatFinding] = []
    for group in results:
        raw.extend(group)

    raw = [f for f in raw if f.confidence >= MIN_CONFIDENCE]

    # Tier-2 escalation: if Tier-1 did NOT already catch a strong secret, run the
    # deeper detect-secrets scan to catch tokens the regex misses (Slack, Stripe,
    # Azure, GitLab, …). Skipped when Tier-1 already found a secret (fast path).
    tier1_has_secret = any(f.severity >= 75 for f in raw)
    if not tier1_has_secret:
        raw.extend(tier2_secrets.scan(text))

    raw = resolve_overlaps(raw)
    raw = raw[:MAX_FINDINGS]

    findings = []
    summary: dict = {}
    highest = "SAFE"
    order = {"SAFE": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}

    for f in raw:
        level = severity_to_level(f.severity)
        if order[level] > order[highest]:
            highest = level
        category = (f.category or "UNKNOWN").upper()
        summary[category] = summary.get(category, 0) + 1
        findings.append({
            "severity": level,
            "reason": reason_for(f),
            "action": action_for(level),
            "category": category,
            "confidence": round(float(f.confidence), 2),
            "evidence": mask_evidence(f.evidence),
        })

    # Score the whole prompt and derive the decision (Tier-1 policy).
    assessment = risk.assess(findings)
    allow_send = assessment["decision"] != "BLOCK"

    result = {
        "allowSend": allow_send,
        "severity": highest,
        "action": assessment["decision"],
        "riskScore": assessment["risk_score"],
        "decision": assessment["decision"],
        "confidence": assessment["confidence"],
        "needsDeeperScan": assessment["needs_deeper_scan"],
        "findings": findings,
        "summary": summary,
    }
    return result, raw


async def scan_prompt(prompt: str) -> dict:
    """Public helper (used by tests) — result only, no logging."""
    result, _raw = await analyze(prompt)
    return result


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(title="Cybage Browser Prompt Detection API", version="1.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"https://.*\.(openai\.com|claude\.ai)$",
    allow_credentials=False,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type"],
    max_age=600,
)


class ScanRequest(BaseModel):
    prompt: str = Field(default="", max_length=MAX_PROMPT_LENGTH + 1000)
    client_id: Optional[str] = Field(default=None, max_length=100)
    source: Optional[str] = Field(default=None, max_length=200)
    user_agent: Optional[str] = Field(default=None, max_length=400)


@app.on_event("startup")
async def _startup():
    storage.init_db()


@app.get("/health")
async def health():
    return {"status": "ok", "detectors": len(DETECTORS)}


async def _scan_and_log(body: ScanRequest, http: Optional[Request] = None) -> dict:
    result, raw = await analyze(body.prompt)

    # Auto-correct text: the prompt with every sensitive value replaced by a
    # placeholder, so the user can send a safe version instead of the secret.
    sanitized = redact((body.prompt or "")[:MAX_PROMPT_LENGTH], raw)
    result["sanitized"] = sanitized

    ip = None
    if http is not None and http.client:
        # Respect a reverse-proxy header if present, else the socket peer.
        ip = http.headers.get("x-forwarded-for", http.client.host).split(",")[0].strip()
    user_agent = body.user_agent or (http.headers.get("user-agent") if http else None)

    # Store a redacted audit record — who (client_id / ip), where (source), what
    # severity — without persisting the actual sensitive value.
    try:
        storage.log_scan(
            client_id=body.client_id,
            source=body.source,
            severity=result["severity"],
            action=result["action"],
            allow_send=result["allowSend"],
            findings_count=len(result["findings"]),
            categories=sorted(result.get("summary", {}).keys()),
            redacted_prompt=sanitized,
            ip=ip,
            user_agent=user_agent,
        )
    except Exception:
        pass  # logging must never break a scan

    return result


@app.post("/api/scan")
async def api_scan(body: ScanRequest, http: Request):
    return await _scan_and_log(body, http)


# Legacy alias so existing clients hitting /scan keep working.
@app.post("/scan")
async def legacy_scan(body: ScanRequest, http: Request):
    return await _scan_and_log(body, http)


# --- Image scanning (OCR then detect) -----------------------------------------

MAX_IMAGE_BYTES = 8 * 1024 * 1024  # 8 MB


class ImageScanRequest(BaseModel):
    image: str = Field(default="")  # data URL or bare base64
    client_id: Optional[str] = Field(default=None, max_length=100)
    source: Optional[str] = Field(default=None, max_length=200)
    user_agent: Optional[str] = Field(default=None, max_length=400)


def _decode_image(data: str) -> bytes:
    if not data:
        return b""
    if data.startswith("data:"):
        data = data.split(",", 1)[-1]  # strip the data URL header
    try:
        return base64.b64decode(data, validate=False)
    except (binascii.Error, ValueError):
        return b""


@app.post("/api/scan-image")
async def api_scan_image(body: ImageScanRequest, http: Request):
    if not ocr.available():
        return {"ocr": False, "allowSend": True, "severity": "SAFE", "findings": [],
                "message": "OCR engine not installed on the backend."}

    raw = _decode_image(body.image)
    if not raw or len(raw) > MAX_IMAGE_BYTES:
        return {"ocr": True, "allowSend": True, "severity": "SAFE", "findings": [],
                "message": "No readable image."}

    # OCR is CPU-bound; run it off the event loop so the API stays responsive.
    import asyncio
    text = await asyncio.to_thread(ocr.extract_text, raw)

    result, rawf = await analyze(text)
    result["ocr"] = True
    result["extracted_chars"] = len(text)
    # Mark findings as coming from an image so the UI can label them.
    for f in result["findings"]:
        f["reason"] = f"🖼 {f['reason']} (in image)"

    ip = None
    if http.client:
        ip = http.headers.get("x-forwarded-for", http.client.host).split(",")[0].strip()

    try:
        storage.log_scan(
            client_id=body.client_id,
            source=(body.source or "") + " [image]",
            severity=result["severity"],
            action=result["action"],
            allow_send=result["allowSend"],
            findings_count=len(result["findings"]),
            categories=sorted(result.get("summary", {}).keys()),
            redacted_prompt="[image] " + redact(text, rawf),
            ip=ip,
            user_agent=body.user_agent or http.headers.get("user-agent"),
        )
    except Exception:
        pass

    return result


@app.get("/api/logs")
async def api_logs(limit: int = 50, client_id: Optional[str] = None):
    return {"logs": storage.recent(limit=min(limit, 500), client_id=client_id)}


@app.get("/api/stats")
async def api_stats():
    return storage.stats()


# ---------------------------------------------------------------------------
# Admin authentication + dashboard API
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    username: str
    password: str


def require_admin(psg_session: Optional[str] = Cookie(default=None)) -> str:
    user = auth.verify_token(psg_session)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


@app.post("/api/login")
async def login(body: LoginRequest, response: Response):
    if not auth.verify_credentials(body.username, body.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = auth.create_token(body.username)
    response.set_cookie(
        key=auth.COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=auth.SESSION_TTL_SECONDS,
    )
    return {"ok": True, "user": body.username}


@app.post("/api/logout")
async def logout(response: Response):
    response.delete_cookie(auth.COOKIE_NAME)
    return {"ok": True}


@app.get("/api/me")
async def me(user: str = Depends(require_admin)):
    return {"user": user}


@app.get("/api/admin/overview")
async def admin_overview(user: str = Depends(require_admin)):
    return {
        "overview": storage.overview(),
        "severity": storage.severity_breakdown(),
        "timeseries": storage.timeseries(days=14),
        "categories": storage.category_breakdown(),
        "top_clients": storage.top_clients(limit=8),
    }


@app.get("/api/admin/benchmark")
async def admin_benchmark(user: str = Depends(require_admin), limit: int = Query(default=50, le=300)):
    """Latest accuracy run + the cases we got wrong (false positives/negatives)."""
    run = storage.latest_benchmark()
    if not run:
        return {"run": None, "wrong": []}
    wrong = (storage.benchmark_cases(run["id"], outcome="FP", limit=limit)
             + storage.benchmark_cases(run["id"], outcome="FN", limit=limit))
    return {"run": run, "wrong": wrong}


@app.get("/api/admin/logs")
async def admin_logs(
    user: str = Depends(require_admin),
    limit: int = Query(default=50, le=500),
    offset: int = Query(default=0, ge=0),
    severity: Optional[str] = None,
    source: Optional[str] = None,
    client_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    search: Optional[str] = None,
):
    return storage.query_logs(
        limit=limit, offset=offset, severity=severity, source=source,
        client_id=client_id, date_from=date_from, date_to=date_to, search=search,
    )
