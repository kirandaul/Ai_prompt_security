from __future__ import annotations

import re
from typing import List

from detectors.base_detector import BaseDetector
from models.threat_finding import ThreatFinding


class InternalIpDetector(BaseDetector):
    """
    Detects private/internal IP addresses that should not be exposed:
    - 10.0.0.0/8 (10.0.0.0 - 10.255.255.255)
    - 172.16.0.0/12 (172.16.0.0 - 172.31.255.255)
    - 192.168.0.0/16 (192.168.0.0 - 192.168.255.255)
    - 127.0.0.0/8 (localhost, loopback)
    - Link-local: 169.254.0.0/16
    """

    name = "INTERNAL_IP_DETECTOR"
    category = "INFRA"

    # IPv4 pattern: x.x.x.x where x is 0-255
    IP_PATTERN = re.compile(
        r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
        r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
    )

    async def detect(self, text: str) -> List[ThreatFinding]:
        findings: List[ThreatFinding] = []

        if not self.validate(text):
            return findings

        for match in self.IP_PATTERN.finditer(text):
            ip = match.group(0)
            if self._is_internal_ip(ip):
                # Determine severity based on context
                severity = 65  # Internal IPs are lower severity than credentials
                confidence = 0.95
                
                findings.append(
                    ThreatFinding(
                        detector=self.name,
                        category=self.category,
                        severity=severity,
                        confidence=confidence,
                        evidence=ip,
                        start=match.start(),
                        end=match.end(),
                        metadata={"type": "INTERNAL_IP"}
                    )
                )

        return findings

    @staticmethod
    def _is_internal_ip(ip: str) -> bool:
        """Check if IP is in private/internal ranges."""
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        
        try:
            octets = [int(p) for p in parts]
        except ValueError:
            return False

        a, b, c, d = octets

        # 10.0.0.0/8
        if a == 10:
            return True

        # 172.16.0.0/12 (172.16.0.0 - 172.31.255.255)
        if a == 172 and 16 <= b <= 31:
            return True

        # 192.168.0.0/16
        if a == 192 and b == 168:
            return True

        # 127.0.0.0/8 (loopback/localhost)
        if a == 127:
            return True

        # 169.254.0.0/16 (link-local)
        if a == 169 and b == 254:
            return True

        # 0.0.0.0/8 (this network)
        if a == 0:
            return True

        # 255.255.255.255 (broadcast)
        if a == 255 and b == 255 and c == 255 and d == 255:
            return True

        return False
