from __future__ import annotations

import re
from typing import List

from detectors.base_detector import BaseDetector
from models.threat_finding import ThreatFinding


class PasswordDetector(BaseDetector):
    """
    Detects passwords shared in prompts.

    Examples:

    password = MyPassword123

    pwd: Secret@123

    my password is admin123

    passwd = qwerty
    """

    name = "PASSWORD_DETECTOR"
    category = "SECRET"

    # A password keyword, then a connector (is / : / = / ->), then the value.
    # The value must contain a digit or special character via the (?=\S*[\d\W])
    # lookahead — so real passwords ("1234567890", "Prod@123", "Hunter2!") are
    # caught, but plain-English sentences ("password is required", "password
    # reset flow") are NOT flagged. The keyword may be preceded by other words
    # ("my aws password is ..."), which the earlier version missed.
    PASSWORD_PATTERNS = [
        re.compile(
            r'(?i)\b(?:password|passwd|pwd|passcode|passphrase|pin)\b'
            r'\s*(?:is|are|:|=|:=|->)\s*'
            r'["\']?((?=\S*(?:\d|[^\w\s]))\S{3,})'
        ),
    ]

    async def detect(self, text: str) -> List[ThreatFinding]:

        findings: List[ThreatFinding] = []

        if not self.validate(text):
            return findings

        for pattern in self.PASSWORD_PATTERNS:

            for match in pattern.finditer(text):

                password = match.group(1).strip("\"'.,;")

                findings.append(
                    ThreatFinding(
                        detector=self.name,
                        category=self.category,
                        severity=95,
                        confidence=0.99,
                        evidence=password,
                        start=match.start(),
                        end=match.end(),
                        metadata={
                            "type": "PASSWORD"
                        }
                    )
                )

        return findings