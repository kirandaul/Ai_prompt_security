from __future__ import annotations

import re
from typing import List

from detectors.base_detector import BaseDetector
from models.threat_finding import ThreatFinding


class JwtDetector(BaseDetector):
    """
    Detects JSON Web Tokens (JWT).

    Format:
    header.payload.signature
    """

    name = "JWT_DETECTOR"
    category = "SECRET"

    JWT_PATTERN = re.compile(
        r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b"
    )

    async def detect(self, text: str) -> List[ThreatFinding]:

        findings = []

        if not self.validate(text):
            return findings

        for match in self.JWT_PATTERN.finditer(text):

            findings.append(
                ThreatFinding(
                    detector=self.name,
                    category=self.category,
                    severity=90,
                    confidence=0.99,
                    evidence=match.group(),
                    start=match.start(),
                    end=match.end(),
                    metadata={
                        "token_type": "JWT"
                    }
                )
            )

        return findings