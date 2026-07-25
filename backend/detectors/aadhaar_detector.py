from __future__ import annotations

import re
from typing import List

from detectors.base_detector import BaseDetector
from models.threat_finding import ThreatFinding
from utils.verhoeff import validate


class AadhaarDetector(BaseDetector):
    """
    Aadhaar detector.

    Supports

    123412341234

    1234 1234 1234

    1234-1234-1234
    """

    name = "AADHAAR_DETECTOR"
    category = "PII"

    PATTERN = re.compile(
        r"\b\d{4}[- ]?\d{4}[- ]?\d{4}\b"
    )

    async def detect(self, text: str) -> List[ThreatFinding]:

        findings = []

        if not self.validate(text):
            return findings

        for match in self.PATTERN.finditer(text):

            raw = match.group()

            normalized = re.sub(r"[- ]", "", raw)

            if len(normalized) != 12:
                continue

            # first digit cannot be 0 or 1
            if normalized[0] in ("0", "1"):
                continue

            # checksum validation
            if not validate(normalized):
                continue

            findings.append(

                ThreatFinding(

                    detector=self.name,

                    category=self.category,

                    severity=85,

                    confidence=0.99,

                    evidence=raw,

                    start=match.start(),

                    end=match.end(),

                    metadata={

                        "country": "IN",

                        "document": "AADHAAR"

                    }

                )

            )

        return findings