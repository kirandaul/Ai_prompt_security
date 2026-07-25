from __future__ import annotations

import re
from typing import List

from detectors.base_detector import BaseDetector
from models.threat_finding import ThreatFinding


class EmailDetector(BaseDetector):
    """
    Detects email addresses.

    Examples:
        john.doe@gmail.com
        admin@company.co.in
        support@example.org
    """

    name = "EMAIL_DETECTOR"
    category = "PII"

    EMAIL_PATTERN = re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        re.IGNORECASE,
    )

    async def detect(self, text: str) -> List[ThreatFinding]:

        findings: List[ThreatFinding] = []

        if not self.validate(text):
            return findings

        for match in self.EMAIL_PATTERN.finditer(text):

            email = match.group()

            findings.append(
                ThreatFinding(
                    detector=self.name,
                    category=self.category,
                    severity=40,
                    confidence=0.99,
                    evidence=email,
                    start=match.start(),
                    end=match.end(),
                    metadata={
                        "domain": email.split("@")[1],
                        "type": "EMAIL"
                    }
                )
            )

        return findings