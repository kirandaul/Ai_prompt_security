from __future__ import annotations

import re
from typing import List

from detectors.base_detector import BaseDetector
from models.threat_finding import ThreatFinding


class PanDetector(BaseDetector):
    """
    Detects Indian PAN numbers.

    Format

    ABCDE1234F
    """

    name = "PAN_DETECTOR"
    category = "PII"

    PAN_PATTERN = re.compile(
        r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"
    )

    async def detect(self, text: str) -> List[ThreatFinding]:

        findings = []

        if not self.validate(text):
            return findings

        for match in self.PAN_PATTERN.finditer(text):

            pan = match.group()

            findings.append(
                ThreatFinding(
                    detector=self.name,
                    category=self.category,
                    severity=80,
                    confidence=0.99,
                    evidence=pan,
                    start=match.start(),
                    end=match.end(),
                    metadata={
                        "country": "IN",
                        "document": "PAN"
                    }
                )
            )

        return findings