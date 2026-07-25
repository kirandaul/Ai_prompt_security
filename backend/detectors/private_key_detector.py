from __future__ import annotations

import re
from typing import List

from detectors.base_detector import BaseDetector
from models.threat_finding import ThreatFinding


class PrivateKeyDetector(BaseDetector):
    """
    Detects PEM formatted private keys.
    """

    name = "PRIVATE_KEY_DETECTOR"
    category = "SECRET"

    PRIVATE_KEY_PATTERN = re.compile(
        r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----.*?-----END (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----",
        re.DOTALL,
    )

    async def detect(self, text: str) -> List[ThreatFinding]:

        findings = []

        if not self.validate(text):
            return findings

        for match in self.PRIVATE_KEY_PATTERN.finditer(text):

            findings.append(
                ThreatFinding(
                    detector=self.name,
                    category=self.category,
                    severity=100,
                    confidence=1.0,
                    evidence="PRIVATE KEY",
                    start=match.start(),
                    end=match.end(),
                    metadata={
                        "key_type": "PEM"
                    }
                )
            )

        return findings