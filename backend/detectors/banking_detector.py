from __future__ import annotations

import re
from typing import List

from detectors.base_detector import BaseDetector
from models.threat_finding import ThreatFinding


class BankingDetector(BaseDetector):
    """
    Detects banking and financial credentials:
    - IBAN (International Bank Account Numbers)
    - US Routing Numbers
    - SWIFT Codes
    - Bank account connections strings
    """

    name = "BANKING_DETECTOR"
    category = "COMPLIANCE"

    # IBAN: 2 letters (country) + 2 digits (check) + 1-30 alphanumeric
    IBAN_PATTERN = re.compile(
        r'\b([A-Z]{2}[0-9]{2}[A-Z0-9]{1,30})\b'
    )

    # US Routing Number: 9 digits, specific banks range 010000000-129999999, 200000000-299999999
    ROUTING_PATTERN = re.compile(
        r'(?:routing\s*(?:number|#)?|rtn|aba)[:\s=]+([0-9]{9})\b',
        re.IGNORECASE
    )

    # SWIFT Code: 8-11 alphanumeric characters
    SWIFT_PATTERN = re.compile(
        r'\b(?:swift|swift\s*code|bic)[:\s=]+([A-Z]{6}[A-Z0-9]{2}(?:[A-Z0-9]{3})?)\b',
        re.IGNORECASE
    )

    # Bank Account Numbers
    BANK_ACCOUNT_PATTERN = re.compile(
        r'(?:account|acct|account\s*number|acct\s*no)[:\s=]+([0-9]{8,17})\b',
        re.IGNORECASE
    )

    async def detect(self, text: str) -> List[ThreatFinding]:
        findings: List[ThreatFinding] = []

        if not self.validate(text):
            return findings

        # Detect IBAN
        for match in self.IBAN_PATTERN.finditer(text):
            iban = match.group(1)
            if self._is_valid_iban(iban):
                findings.append(
                    ThreatFinding(
                        detector=self.name,
                        category=self.category,
                        severity=85,
                        confidence=0.92,
                        evidence=iban,
                        start=match.start(1),
                        end=match.end(1),
                        metadata={"type": "IBAN"}
                    )
                )

        # Detect Routing Numbers
        for match in self.ROUTING_PATTERN.finditer(text):
            routing = match.group(1)
            if self._is_valid_routing(routing):
                findings.append(
                    ThreatFinding(
                        detector=self.name,
                        category=self.category,
                        severity=80,
                        confidence=0.90,
                        evidence=routing,
                        start=match.start(1),
                        end=match.end(1),
                        metadata={"type": "ROUTING_NUMBER"}
                    )
                )

        # Detect SWIFT Codes
        for match in self.SWIFT_PATTERN.finditer(text):
            swift = match.group(1)
            findings.append(
                ThreatFinding(
                    detector=self.name,
                    category=self.category,
                    severity=70,
                    confidence=0.88,
                    evidence=swift,
                    start=match.start(1),
                    end=match.end(1),
                    metadata={"type": "SWIFT_CODE"}
                )
            )

        # Detect Bank Account Numbers
        for match in self.BANK_ACCOUNT_PATTERN.finditer(text):
            account = match.group(1)
            findings.append(
                ThreatFinding(
                    detector=self.name,
                    category=self.category,
                    severity=82,
                    confidence=0.85,
                    evidence=account,
                    start=match.start(1),
                    end=match.end(1),
                    metadata={"type": "BANK_ACCOUNT"}
                )
            )

        return findings

    @staticmethod
    def _is_valid_iban(iban: str) -> bool:
        """
        Basic IBAN validation using checksum algorithm.
        IBAN format: 2 letters (country) + 2 digits (checksum) + 1-30 alphanumeric
        """
        if not iban or len(iban) < 15 or len(iban) > 34:
            return False
        
        if not (iban[:2].isalpha() and iban[2:4].isdigit()):
            return False
        
        # Move first 4 chars to end and replace letters with numbers
        rearranged = iban[4:] + iban[:4]
        numeric = ''
        for ch in rearranged:
            if ch.isdigit():
                numeric += ch
            else:
                # A=10, B=11, ..., Z=35
                numeric += str(ord(ch) - ord('A') + 10)
        
        # Check mod 97
        try:
            return int(numeric) % 97 == 1
        except (ValueError, OverflowError):
            return False

    @staticmethod
    def _is_valid_routing(routing: str) -> bool:
        """Basic US routing number validation."""
        if not routing.isdigit() or len(routing) != 9:
            return False
        
        # Routing numbers are typically in range 010000000-129999999 or 200000000-299999999
        first_two = int(routing[:2])
        
        # Valid ranges
        if 1 <= first_two <= 12 or 20 <= first_two <= 29:
            # Simple checksum: sum alternating weights
            weights = [3, 7, 1]
            total = 0
            for i, digit in enumerate(routing):
                total += int(digit) * weights[i % 3]
            
            return total % 10 == 0
        
        return False
