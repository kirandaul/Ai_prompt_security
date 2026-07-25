from __future__ import annotations

import re
from typing import List

from detectors.base_detector import BaseDetector
from models.threat_finding import ThreatFinding


class CreditCardDetector(BaseDetector):
    """
    Detects and validates credit card numbers using
    the Luhn Algorithm.
    """

    name = "CREDIT_CARD_DETECTOR"
    category = "FINANCIAL"

    CARD_PATTERN = re.compile(
        r"\b(?:\d[ -]*?){13,19}\b"
    )

    async def detect(self, text: str) -> List[ThreatFinding]:

        findings = []

        if not self.validate(text):
            return findings

        for match in self.CARD_PATTERN.finditer(text):

            candidate = re.sub(r"[ -]", "", match.group())

            if not candidate.isdigit():
                continue

            if not (13 <= len(candidate) <= 19):
                continue

            if not self._is_luhn_valid(candidate):
                continue

            findings.append(
                ThreatFinding(
                    detector=self.name,
                    category=self.category,
                    severity=95,
                    confidence=0.99,
                    evidence=match.group(),
                    start=match.start(),
                    end=match.end(),
                    metadata={
                        "card_length": str(len(candidate)),
                        "validation": "LUHN"
                    }
                )
            )

        return findings

    @staticmethod
    def _is_luhn_valid(number: str) -> bool:

        total = 0
        reverse_digits = number[::-1]

        for index, digit in enumerate(reverse_digits):

            n = int(digit)

            if index % 2 == 1:

                n *= 2

                if n > 9:
                    n -= 9

            total += n

        return total % 10 == 0