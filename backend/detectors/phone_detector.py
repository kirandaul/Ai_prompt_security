from __future__ import annotations

import re
from typing import List

from detectors.base_detector import BaseDetector
from models.threat_finding import ThreatFinding


class PhoneDetector(BaseDetector):
    """
    Detects phone numbers.

    Supports:
    - Indian Mobile Numbers
    - International Numbers
    - Numbers with +, -, spaces, ()
    """

    name = "PHONE_DETECTOR"
    category = "PII"

    PHONE_PATTERNS = [

        # +91 9876543210
        re.compile(r"\+91[-\s]?[6-9]\d{9}"),

        # 9876543210
        re.compile(r"\b[6-9]\d{9}\b"),

        # +1 987-654-3210
        re.compile(r"\+\d{1,3}[-\s]?\(?\d+\)?([-\s]?\d+){2,4}")
    ]

    async def detect(self, text: str) -> List[ThreatFinding]:

        findings: List[ThreatFinding] = []

        if not self.validate(text):
            return findings

        for pattern in self.PHONE_PATTERNS:

            for match in pattern.finditer(text):

                findings.append(
                    ThreatFinding(
                        detector=self.name,
                        category=self.category,
                        severity=45,
                        confidence=0.97,
                        evidence=match.group(),
                        start=match.start(),
                        end=match.end(),
                        metadata={
                            "type": "PHONE_NUMBER"
                        }
                    )
                )

        return findings