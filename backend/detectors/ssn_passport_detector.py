from __future__ import annotations

import re
from typing import List

from detectors.base_detector import BaseDetector
from models.threat_finding import ThreatFinding


class SsnPassportDetector(BaseDetector):
    """
    Detects Social Security Numbers (SSN) and Passport numbers.

    SSN patterns:
    - 123-45-6789
    - 123456789

    Passport patterns:
    - 6-9 character alphanumeric codes
    """

    name = "SSN_PASSPORT_DETECTOR"
    category = "PII"

    # SSN: XXX-XX-XXXX or XXXXXXXXX
    SSN_PATTERN = re.compile(
        r'\b(?!000|666|9\d{2})\d{3}[- ]?(?!00)\d{2}[- ]?(?!0000)\d{4}\b'
    )

    # Passport: typically 6-9 character code (letters, numbers, mix)
    PASSPORT_PATTERN = re.compile(
        r'\b(?:passport|passport\s*(?:no|number|#)|travel\s*document)'
        r'[:\s=]+([A-Z]{1,2}[0-9]{6,8}[A-Z0-9]*)\b',
        re.IGNORECASE
    )

    async def detect(self, text: str) -> List[ThreatFinding]:
        findings: List[ThreatFinding] = []

        if not self.validate(text):
            return findings

        # Detect SSN patterns
        for match in self.SSN_PATTERN.finditer(text):
            ssn = match.group(0)
            # Validate Luhn-like check (simple version)
            if self._is_valid_ssn(ssn):
                findings.append(
                    ThreatFinding(
                        detector=self.name,
                        category=self.category,
                        severity=92,
                        confidence=0.95,
                        evidence=ssn,
                        start=match.start(),
                        end=match.end(),
                        metadata={"type": "SSN"}
                    )
                )

        # Detect Passport patterns
        for match in self.PASSPORT_PATTERN.finditer(text):
            passport = match.group(1)
            findings.append(
                ThreatFinding(
                    detector=self.name,
                    category=self.category,
                    severity=88,
                    confidence=0.90,
                    evidence=passport,
                    start=match.start(1),
                    end=match.end(1),
                    metadata={"type": "PASSPORT"}
                )
            )

        return findings

    @staticmethod
    def _is_valid_ssn(ssn: str) -> bool:
        """Basic SSN validation - just check format and non-invalid ranges."""
        # Remove hyphens and spaces
        clean = ssn.replace('-', '').replace(' ', '')
        
        if not clean.isdigit() or len(clean) != 9:
            return False
        
        # Invalid ranges: 000-00-0000, 666-xx-xxxx, 9xx-xx-xxxx
        area, group, serial = clean[:3], clean[3:5], clean[5:]
        
        if area == '000' or area == '666' or area.startswith('9'):
            return False
        
        if group == '00' or serial == '0000':
            return False
        
        return True
