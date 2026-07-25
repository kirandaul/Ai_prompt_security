from __future__ import annotations

import re
from typing import List

from detectors.base_detector import BaseDetector
from models.threat_finding import ThreatFinding


class AwsSecretDetector(BaseDetector):
    """
    Detect AWS credentials and generic AWS secret assignments.
    """

    name = "AWS_SECRET_DETECTOR"
    category = "SECRET"

    PATTERNS = {

        # -------------------------------------------------
        # Real AWS Access Key
        # Example:
        # AKIAIOSFODNN7EXAMPLE
        # -------------------------------------------------
        "ACCESS_KEY": re.compile(
            r"\b(AKIA|ASIA)[A-Z0-9]{16}\b"
        ),

        # -------------------------------------------------
        # Real Secret Access Key
        # -------------------------------------------------
        "SECRET_ACCESS_KEY": re.compile(
            r"(?i)(aws_secret_access_key|secret_access_key)\s*[:=]\s*['\"]?([A-Za-z0-9/+=]{40})['\"]?"
        ),

        # -------------------------------------------------
        # aws key =
        # aws_key =
        # -------------------------------------------------
        "AWS_KEY": re.compile(
            r"(?i)(aws[_\-\s]?key)\s*[:=]\s*['\"]?([A-Za-z0-9_\-/+=]{12,})['\"]?"
        ),

        # -------------------------------------------------
        # aws secret =
        # aws_secret =
        # -------------------------------------------------
        "AWS_SECRET": re.compile(
            r"(?i)(aws[_\-\s]?secret)\s*[:=]\s*['\"]?([A-Za-z0-9_\-/+=]{12,})['\"]?"
        ),

        # -------------------------------------------------
        # access key =
        # access_key =
        # -------------------------------------------------
        "ACCESS_KEY_GENERIC": re.compile(
            r"(?i)(access[_\-\s]?key)\s*[:=]\s*['\"]?([A-Za-z0-9_\-/+=]{12,})['\"]?"
        ),

        # -------------------------------------------------
        # secret key =
        # secret_key =
        # -------------------------------------------------
        "SECRET_KEY": re.compile(
            r"(?i)(secret[_\-\s]?key)\s*[:=]\s*['\"]?([A-Za-z0-9_\-/+=]{12,})['\"]?"
        ),

        # -------------------------------------------------
        # client secret =
        # -------------------------------------------------
        "CLIENT_SECRET": re.compile(
            r"(?i)(client[_\-\s]?secret)\s*[:=]\s*['\"]?([A-Za-z0-9_\-/+=]{12,})['\"]?"
        ),
    }

    async def detect(self, text: str) -> List[ThreatFinding]:

        findings: List[ThreatFinding] = []

        if not self.validate(text):
            return findings

        for provider, pattern in self.PATTERNS.items():

            for match in pattern.finditer(text):

                # ACCESS_KEY uses entire match
                if provider == "ACCESS_KEY":

                    evidence = match.group()

                    start = match.start()

                    end = match.end()

                else:

                    evidence = match.group(2)

                    start = match.start(2)

                    end = match.end(2)

                severity = self._severity(provider)

                confidence = self._confidence(provider)

                findings.append(

                    ThreatFinding(

                        detector=self.name,

                        category=self.category,

                        severity=severity,

                        confidence=confidence,

                        evidence=evidence,

                        start=start,

                        end=end,

                        metadata={
                            "aws_type": provider
                        }

                    )

                )

        return findings

    def _severity(self, provider: str) -> int:

        return {

            "ACCESS_KEY": 100,

            "SECRET_ACCESS_KEY": 100,

            "AWS_KEY": 90,

            "AWS_SECRET": 90,

            "ACCESS_KEY_GENERIC": 85,

            "SECRET_KEY": 85,

            "CLIENT_SECRET": 85,

        }.get(provider, 80)

    def _confidence(self, provider: str) -> float:

        return {

            "ACCESS_KEY": 0.99,

            "SECRET_ACCESS_KEY": 0.99,

            "AWS_KEY": 0.95,

            "AWS_SECRET": 0.95,

            "ACCESS_KEY_GENERIC": 0.90,

            "SECRET_KEY": 0.90,

            "CLIENT_SECRET": 0.90,

        }.get(provider, 0.80)