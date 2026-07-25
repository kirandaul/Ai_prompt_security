from __future__ import annotations

import math
import re
from typing import List

from detectors.base_detector import BaseDetector
from models.threat_finding import ThreatFinding


class ApiKeyDetector(BaseDetector):
    """
    Detects secrets, API keys and tokens.

    Supported:

    • OpenAI Keys
    • GitHub PAT
    • Bearer Tokens
    • API Keys
    • AWS Keys
    • Secret Keys
    • Client Secrets
    • Access Keys
    • Tokens
    • Generic high-entropy secrets
    """

    name = "API_KEY_DETECTOR"
    category = "SECRET"

    PATTERNS = {

        # --------------------------
        # OpenAI
        # --------------------------
        "OpenAI": re.compile(
            r"sk-[A-Za-z0-9]{20,}",
            re.IGNORECASE
        ),

        # --------------------------
        # GitHub
        # --------------------------
        "GitHub": re.compile(
            r"(ghp|github_pat)_[A-Za-z0-9_]{20,}",
            re.IGNORECASE
        ),

        # --------------------------
        # Bearer
        # --------------------------
        "Bearer": re.compile(
            r"Bearer\s+[A-Za-z0-9\-._~+/]+=*",
            re.IGNORECASE
        ),

        # --------------------------
        # API Key
        # --------------------------
        "ApiKey": re.compile(
            r'(?i)(api[_\-\s]?key)\s*[:=]\s*["\']?([A-Za-z0-9_\-]{16,})["\']?'
        ),

        # --------------------------
        # AWS Key
        # --------------------------
        "AwsKey": re.compile(
            r'(?i)(aws[_\-\s]?key)\s*[:=]\s*["\']?([A-Za-z0-9_\-]{16,})["\']?'
        ),

        # --------------------------
        # Secret
        # --------------------------
        "Secret": re.compile(
            r'(?i)(secret|secret[_\-\s]?key|client[_\-\s]?secret)\s*[:=]\s*["\']?([A-Za-z0-9_\-]{16,})["\']?'
        ),

        # --------------------------
        # Token
        # --------------------------
        "Token": re.compile(
            r'(?i)(token|access[_\-\s]?token|refresh[_\-\s]?token)\s*[:=]\s*["\']?([A-Za-z0-9_\-]{16,})["\']?'
        ),

        # --------------------------
        # Access Key
        # --------------------------
        "AccessKey": re.compile(
            r'(?i)(access[_\-\s]?key)\s*[:=]\s*["\']?([A-Za-z0-9_\-]{16,})["\']?'
        ),

        # --------------------------
        # Generic Assignment
        # --------------------------
        "GenericSecret": re.compile(
            r'(?i)(password|passwd|pwd|credential|secret|token|apikey|api[_\-\s]?key|client[_\-\s]?secret|private[_\-\s]?key|access[_\-\s]?key|aws[_\-\s]?key)\s*[:=]\s*["\']?([A-Za-z0-9!@#$%^&*()_\-+=]{12,})["\']?'
        ),
    }

    async def detect(self, text: str) -> List[ThreatFinding]:

        findings: List[ThreatFinding] = []

        if not self.validate(text):
            return findings

        for provider, pattern in self.PATTERNS.items():

            for match in pattern.finditer(text):

                evidence = match.group()

                severity = self._severity(provider)

                confidence = self._confidence(provider)

                findings.append(

                    ThreatFinding(

                        detector=self.name,

                        category=self.category,

                        severity=severity,

                        confidence=confidence,

                        evidence=evidence,

                        start=match.start(),

                        end=match.end(),

                        metadata={
                            "provider": provider
                        }

                    )

                )

        # --------------------------
        # High entropy scan
        # --------------------------

        words = re.findall(r"[A-Za-z0-9_\-]{20,}", text)

        for word in words:

            if self._entropy(word) >= 4.0:

                findings.append(

                    ThreatFinding(

                        detector=self.name,

                        category=self.category,

                        severity=70,

                        confidence=0.70,

                        evidence=word,

                        start=text.find(word),

                        end=text.find(word) + len(word),

                        metadata={
                            "provider": "HighEntropy"
                        }

                    )

                )

        return findings

    def _severity(self, provider: str) -> int:

        return {

            "OpenAI": 100,
            "GitHub": 100,
            "Bearer": 95,
            "ApiKey": 90,
            "AwsKey": 95,
            "Secret": 90,
            "Token": 85,
            "AccessKey": 90,
            "GenericSecret": 80,

        }.get(provider, 70)

    def _confidence(self, provider: str) -> float:

        return {

            "OpenAI": 0.99,
            "GitHub": 0.99,
            "Bearer": 0.98,
            "ApiKey": 0.95,
            "AwsKey": 0.95,
            "Secret": 0.90,
            "Token": 0.90,
            "AccessKey": 0.95,
            "GenericSecret": 0.85,

        }.get(provider, 0.75)

    @staticmethod
    def _entropy(text: str) -> float:

        if not text:
            return 0

        entropy = 0

        for char in set(text):

            p = text.count(char) / len(text)

            entropy -= p * math.log2(p)

        return entropy