"""
risk.py — turn a list of findings into ONE overall risk score + a decision.

This is the policy layer that sits on top of the detectors. It answers:
  1. How risky is this whole prompt?  (risk_score 0-100)
  2. What do we do?                    (BLOCK / REDACT / WARN / ALLOW)
  3. Are we confident, or should a deeper (Tier-2) scan run?

Tier 1 = the fast regex + validation detectors (always run).
If `needs_deeper_scan` is True, the prompt is a gray area where a heavier
method (NER / ML / entropy) would add value — see risk.py callers.
"""
from __future__ import annotations

from typing import List

# Points contributed per finding at full confidence.
SEV_POINTS = {"CRITICAL": 100, "HIGH": 75, "MEDIUM": 40, "LOW": 15, "SAFE": 0}
ORDER = {"SAFE": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}

# Score thresholds for the decision.
BLOCK_AT = 70    # >= this, or any CRITICAL/HIGH finding -> block
REDACT_AT = 35   # >= this -> allow but strongly suggest redaction (auto-fix)
WARN_AT = 15     # >= this -> allow with a warning


def assess(findings: List[dict]) -> dict:
    """
    findings: mapped findings, each {severity: str, confidence: float, ...}
    Returns a dict with risk_score, risk_level, decision, confidence,
    needs_deeper_scan.
    """
    if not findings:
        return {
            "risk_score": 0,
            "risk_level": "SAFE",
            "decision": "ALLOW",
            "confidence": 1.0,
            "needs_deeper_scan": False,
        }

    points = []
    highest = "SAFE"
    for f in findings:
        sev = str(f.get("severity", "MEDIUM")).upper()
        conf = float(f.get("confidence", 0.9))
        points.append(SEV_POINTS.get(sev, 40) * conf)
        if ORDER.get(sev, 0) > ORDER.get(highest, 0):
            highest = sev

    # The strongest finding drives the score; extra findings add a diminishing
    # amount (many secrets in one prompt = higher risk, but it saturates at 100).
    top = max(points)
    rest = sum(points) - top
    risk_score = int(min(100, round(top + 0.35 * rest)))

    has_high = any(str(f.get("severity", "")).upper() in ("CRITICAL", "HIGH") for f in findings)
    max_conf = round(max(float(f.get("confidence", 0.9)) for f in findings), 2)

    # Secrets (CRITICAL/HIGH) always block — they must never leave the device.
    if has_high or risk_score >= BLOCK_AT:
        decision = "BLOCK"
    elif risk_score >= REDACT_AT:
        decision = "REDACT"
    elif risk_score >= WARN_AT:
        decision = "WARN"
    else:
        decision = "ALLOW"

    # Gray area: a borderline score, or findings we are not confident about
    # (e.g. only entropy/heuristic hits). These are the cases a Tier-2 method
    # (Presidio NER, detect-secrets, ML) should double-check.
    needs_deeper_scan = (
        (REDACT_AT <= risk_score < BLOCK_AT and max_conf < 0.85)
        or (not has_high and max_conf < 0.70)
    )

    return {
        "risk_score": risk_score,
        "risk_level": highest,
        "decision": decision,
        "confidence": max_conf,
        "needs_deeper_scan": needs_deeper_scan,
    }
