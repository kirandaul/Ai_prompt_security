from __future__ import annotations

import re
from typing import List

from detectors.base_detector import BaseDetector
from models.threat_finding import ThreatFinding


class SqlInjectionDetector(BaseDetector):
    """
    Detects common SQL Injection patterns.
    """

    name = "SQL_INJECTION_DETECTOR"
    category = "ATTACK"

    PATTERNS = [

        re.compile(
            r"(?i)\bunion\s+select\b"
        ),

        re.compile(
            r"(?i)\bselect\b.+\bfrom\b"
        ),

        re.compile(
            r"(?i)\binsert\s+into\b"
        ),

        re.compile(
            r"(?i)\bupdate\b.+\bset\b"
        ),

        re.compile(
            r"(?i)\bdelete\s+from\b"
        ),

        re.compile(
            r"(?i)\bdrop\s+table\b"
        ),

        re.compile(
            r"(?i)\btruncate\s+table\b"
        ),

        re.compile(
            r"(?i)\bor\s+1\s*=\s*1\b"
        ),

        re.compile(
            r"(?i)'\s*or\s*'.*'='.*"
        ),

        re.compile(
            r"(?i)--"
        ),

        re.compile(
            r"/\*.*?\*/",
            re.DOTALL
        ),

        re.compile(
            r";\s*shutdown",
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

                        severity=85,

                        confidence=0.95,

                        evidence=match.group(),

                        start=match.start(),

                        end=match.end(),

                        metadata={
                            "attack": "SQL_INJECTION"
                        }

                    )

                )

        return findings