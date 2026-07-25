"""
tier2_secrets.py — Tier-2 deeper secret scan using detect-secrets (Yelp).

Runs ONLY when Tier-1 (regex) did not already find a strong secret, so the fast
path stays fast. Uses only the STRUCTURED token detectors (Slack, Stripe, AWS,
GitLab, Twilio, SendGrid, private keys, JWT, …) — the noisy generic entropy
plugins are deliberately excluded so ordinary prose is never flagged.

Degrades gracefully if detect-secrets is not installed.
"""
from __future__ import annotations

from typing import List, Optional

from models.threat_finding import ThreatFinding

_available: Optional[bool] = None

# High-precision, structured detectors that add coverage beyond Tier-1 regex.
PLUGINS = [{"name": n} for n in [
    "AWSKeyDetector",
    "PrivateKeyDetector",
    "JwtTokenDetector",
    "GitHubTokenDetector",
    "GitLabTokenDetector",
    "SlackDetector",
    "StripeDetector",
    "AzureStorageKeyDetector",
    "NpmDetector",
    "SendGridDetector",
    "TwilioKeyDetector",
    "MailchimpDetector",
    "DiscordBotTokenDetector",
    "TelegramBotTokenDetector",
    "SquareOAuthDetector",
    "ArtifactoryDetector",
    "BasicAuthDetector",
    "IbmCloudIamDetector",
    "SoftlayerDetector",
]]


def available() -> bool:
    global _available
    if _available is None:
        try:
            import detect_secrets  # noqa: F401
            _available = True
        except Exception:
            _available = False
    return _available


def scan(text: str) -> List[ThreatFinding]:
    if not text or not available():
        return []
    try:
        from detect_secrets.core.scan import scan_line
        from detect_secrets.settings import transient_settings
    except Exception:
        return []

    findings: List[ThreatFinding] = []
    offset = 0
    try:
        with transient_settings({"plugins_used": PLUGINS}):
            for line in text.splitlines(keepends=True):
                for secret in scan_line(line):
                    value = getattr(secret, "secret_value", None)
                    if not value:
                        continue
                    idx = line.find(value)
                    start = offset + (idx if idx >= 0 else 0)
                    end = start + len(value) if idx >= 0 else offset + len(line)
                    findings.append(
                        ThreatFinding(
                            detector="TIER2_SECRETS",
                            category="SECRET",
                            severity=95,
                            confidence=0.9,
                            evidence=value,
                            start=start,
                            end=end,
                            metadata={"type": secret.type, "tier": "2"},
                        )
                    )
                offset += len(line)
    except Exception:
        return findings
    return findings
