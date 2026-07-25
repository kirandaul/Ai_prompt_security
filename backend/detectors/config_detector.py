from __future__ import annotations

import re
from typing import List

from detectors.base_detector import BaseDetector
from models.threat_finding import ThreatFinding


class ConfigDetector(BaseDetector):
    """
    Detects configuration files and connection strings exposed in prompts:
    - Database connection strings
    - Configuration file patterns
    - Environment variable assignments
    - API endpoints with credentials
    """

    name = "CONFIG_DETECTOR"
    category = "INFRA"

    # Database connection strings (various formats)
    DB_CONN_PATTERNS = [
        # postgres://user:pass@host:port/db
        re.compile(
            r'(?:postgres|mysql|mongodb|mssql|oracle|sqlite)://'
            r'(?:[a-zA-Z0-9._\-]+):(?:[a-zA-Z0-9!@#$%^&*()_\-+=]*)'
            r'@[a-zA-Z0-9.\-]+(?::[0-9]+)?(?:/[a-zA-Z0-9_\-]*)?',
            re.IGNORECASE
        ),
        # JDBC connection strings
        re.compile(
            r'jdbc:(?:mysql|postgresql|oracle|mssql)://[a-zA-Z0-9:@/._\-]*',
            re.IGNORECASE
        ),
    ]

    # Configuration file patterns
    CONFIG_FILE_PATTERNS = [
        # Config key=value with sensitive indicators
        re.compile(
            r'(?:password|secret|api_key|token|key|auth|credential)\s*=\s*["\']?([a-zA-Z0-9!@#$%^&*()_\-+=]+)["\']?',
            re.IGNORECASE
        ),
    ]

    # Environment variable assignments
    ENV_PATTERN = re.compile(
        r'(?:export\s+)?(?:DB_PASSWORD|DB_USER|API_KEY|SECRET_KEY|TOKEN|ACCESS_TOKEN|'
        r'PRIVATE_KEY|AWS_SECRET|STRIPE_KEY|SLACK_TOKEN)\s*=\s*["\']?([a-zA-Z0-9!@#$%^&*()_\-+=]{10,})["\']?',
        re.IGNORECASE
    )

    # .env or configuration file indicators
    DOTENV_PATTERN = re.compile(
        r'^\s*(?!#)(?:DATABASE_URL|MONGO_URI|REDIS_URL|ELASTICSEARCH_HOST)\s*=\s*(.+?)$',
        re.MULTILINE | re.IGNORECASE
    )

    async def detect(self, text: str) -> List[ThreatFinding]:
        findings: List[ThreatFinding] = []

        if not self.validate(text):
            return findings

        # Detect database connection strings
        for pattern in self.DB_CONN_PATTERNS:
            for match in pattern.finditer(text):
                conn_str = match.group(0)
                findings.append(
                    ThreatFinding(
                        detector=self.name,
                        category=self.category,
                        severity=88,
                        confidence=0.96,
                        evidence=conn_str,
                        start=match.start(),
                        end=match.end(),
                        metadata={"type": "DATABASE_CONNECTION"}
                    )
                )

        # Detect configuration file assignments
        for pattern in self.CONFIG_FILE_PATTERNS:
            for match in pattern.finditer(text):
                config_value = match.group(1)
                # Only flag if it looks like a real value (has special chars or is long)
                if len(config_value) >= 8 or any(c in config_value for c in '!@#$%^&*()_-+=/'):
                    findings.append(
                        ThreatFinding(
                            detector=self.name,
                            category=self.category,
                            severity=80,
                            confidence=0.80,
                            evidence=config_value,
                            start=match.start(1),
                            end=match.end(1),
                            metadata={"type": "CONFIG_VALUE"}
                        )
                    )

        # Detect environment variable assignments
        for match in self.ENV_PATTERN.finditer(text):
            env_value = match.group(1)
            findings.append(
                ThreatFinding(
                    detector=self.name,
                    category=self.category,
                    severity=85,
                    confidence=0.92,
                    evidence=env_value,
                    start=match.start(1),
                    end=match.end(1),
                    metadata={"type": "ENV_VARIABLE"}
                )
            )

        # Detect .env style variables
        for match in self.DOTENV_PATTERN.finditer(text):
            url_value = match.group(1).strip()
            if url_value and len(url_value) > 5:
                findings.append(
                    ThreatFinding(
                        detector=self.name,
                        category=self.category,
                        severity=82,
                        confidence=0.88,
                        evidence=url_value,
                        start=match.start(1),
                        end=match.end(1),
                        metadata={"type": "ENV_URL"}
                    )
                )

        return findings
