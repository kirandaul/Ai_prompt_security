from __future__ import annotations

import re
from typing import List

from detectors.base_detector import BaseDetector
from models.threat_finding import ThreatFinding


class XssDetector(BaseDetector):
    """
    Detects Cross Site Scripting (XSS)
    payloads.
    """

    name = "XSS_DETECTOR"
    category = "ATTACK"

    PATTERNS = [

        re.compile(
            r"<script.*?>.*?</script>",
            re.IGNORECASE | re.DOTALL
        ),

        re.compile(
            r"javascript:",
            re.IGNORECASE
        ),

        re.compile(
            r"onerror\s*=",
            re.IGNORECASE
        ),

        re.compile(
            r"onload\s*=",
            re.IGNORECASE
        ),

        re.compile(
            r"onclick\s*=",
            re.IGNORECASE
        ),

        re.compile(
            r"<iframe",
            re.IGNORECASE
        ),

        re.compile(
            r"<img.*?onerror",
            re.IGNORECASE
        ),

        re.compile(
            r"<svg",
            re.IGNORECASE
        ),

        re.compile(
            r"document\.cookie",
            re.IGNORECASE
        ),

        re.compile(
            r"alert\s*\(",
            re.IGNORECASE
        )
    ]

    async def detect(self, text: str) -> List[ThreatFinding]:

        findings = []

        if not self.validate(text):
            return findings

        for pattern in self.PATTERNS:

            for match in pattern.finditer(text):

                findings.append(

                    ThreatFinding(

                        detector=self.name,

                        category=self.category,

                        severity=80,

                        confidence=0.95,

                        evidence=match.group(),

                        start=match.start(),

                        end=match.end(),

                        metadata={
                            "attack": "XSS"
                        }

                    )

                )

        return findings