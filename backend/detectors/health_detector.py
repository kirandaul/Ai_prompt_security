from __future__ import annotations

import re
from typing import List

from detectors.base_detector import BaseDetector
from models.threat_finding import ThreatFinding


class HealthDetector(BaseDetector):

    name = "HEALTH_DETECTOR"
    category = "HEALTH"

    PATTERNS = [
        re.compile(
            r"\b("
            r"diabetes|cancer|covid(?:-19)?|hiv|aids|"
            r"tuberculosis|asthma|hypertension|"
            r"heart attack|stroke|epilepsy|"
            r"depression|anxiety|bipolar|schizophrenia|"
            r"pregnant|pregnancy"
            r")\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\b("
            r"blood pressure|blood sugar|hba1c|cholesterol|"
            r"mri|ct scan|ecg|x-ray|biopsy|"
            r"prescription|medical history|diagnosis|"
            r"treatment plan|patient id|mrn"
            r")\b",
            re.IGNORECASE,
        ),
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
                        severity=95,
                        confidence=0.98,
                        evidence=match.group(),
                        start=match.start(),
                        end=match.end(),
                        metadata={"type": "Health Information"},
                    )
                )

        return findings