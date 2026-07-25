from __future__ import annotations

import re
from typing import List

from detectors.base_detector import BaseDetector
from models.threat_finding import ThreatFinding


class InjectionDetector(BaseDetector):
    """
    Detects code injection attack patterns:
    - Command Injection (shell metacharacters: ; | & > < ` $(...)  )
    - LDAP Injection (* | & wildcards and LDAP operators)
    - Path Traversal (../ patterns)
    """

    name = "INJECTION_DETECTOR"
    category = "ATTACK"

    # Command injection patterns with dangerous shell metacharacters
    COMMAND_INJECTION_PATTERNS = [
        # Semicolon + command (rm -rf, etc.)
        re.compile(r';\s*(?:rm|cat|chmod|chown|kill|shutdown|reboot|dd|mkfs|format)\b', re.IGNORECASE),
        # Pipe operators
        re.compile(r'\|\s*(?:cat|nc|ncat|base64|whoami|id|uname|pwd)\b', re.IGNORECASE),
        # Backticks or $(...)
        re.compile(r'[`$]\(.*?(?:rm|cat|chmod|kill|shutdown|bash|sh|cmd|powershell)\b', re.IGNORECASE),
        # Command substitution with && or ||
        re.compile(r'(?:&&|;\s*)[a-zA-Z0-9_\-]+\s+(?:/etc|/usr|/bin|/dev|/proc)', re.IGNORECASE),
        # Output redirection with dangerous operations
        re.compile(r'>\s*(?:/etc|/dev|/proc|/tmp)', re.IGNORECASE),
    ]

    # LDAP injection patterns
    LDAP_INJECTION_PATTERNS = [
        # Wildcard LDAP operators: * | & ) (
        re.compile(r'\(\w+=[^)]*[*|&)(\[\]]+', re.IGNORECASE),
        # Common LDAP injection: *)(uid=*
        re.compile(r'\*\)\s*\((?:uid|cn|mail|ou|dc)=', re.IGNORECASE),
        # Filter bypass patterns
        re.compile(r'(?:admin|root).*?\*\s*\)', re.IGNORECASE),
    ]

    # Path traversal patterns
    PATH_TRAVERSAL_PATTERNS = [
        re.compile(r'\.\.[\\/](?:\.\.[\\\/]){2,}'),  # Multiple ../
        re.compile(r'(?:\.\.[\\/])+(?:etc|windows|passwd|shadow)', re.IGNORECASE),
    ]

    async def detect(self, text: str) -> List[ThreatFinding]:
        findings: List[ThreatFinding] = []

        if not self.validate(text):
            return findings

        # Detect command injection attempts
        for pattern in self.COMMAND_INJECTION_PATTERNS:
            for match in pattern.finditer(text):
                payload = match.group(0)
                findings.append(
                    ThreatFinding(
                        detector=self.name,
                        category=self.category,
                        severity=95,
                        confidence=0.92,
                        evidence=payload,
                        start=match.start(),
                        end=match.end(),
                        metadata={"type": "COMMAND_INJECTION"}
                    )
                )

        # Detect LDAP injection attempts
        for pattern in self.LDAP_INJECTION_PATTERNS:
            for match in pattern.finditer(text):
                payload = match.group(0)
                findings.append(
                    ThreatFinding(
                        detector=self.name,
                        category=self.category,
                        severity=88,
                        confidence=0.88,
                        evidence=payload,
                        start=match.start(),
                        end=match.end(),
                        metadata={"type": "LDAP_INJECTION"}
                    )
                )

        # Detect path traversal attempts
        for pattern in self.PATH_TRAVERSAL_PATTERNS:
            for match in pattern.finditer(text):
                payload = match.group(0)
                findings.append(
                    ThreatFinding(
                        detector=self.name,
                        category=self.category,
                        severity=80,
                        confidence=0.85,
                        evidence=payload,
                        start=match.start(),
                        end=match.end(),
                        metadata={"type": "PATH_TRAVERSAL"}
                    )
                )

        return findings
