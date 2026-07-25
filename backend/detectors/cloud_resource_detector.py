from __future__ import annotations

import re
from typing import List

from detectors.base_detector import BaseDetector
from models.threat_finding import ThreatFinding


class CloudResourceDetector(BaseDetector):
    """
    Detects cloud infrastructure identifiers that expose environment details:
    - AWS ARNs (arn:aws:service:region:account-id:resource)
    - Azure Resource IDs
    - GCP resource paths
    """

    name = "CLOUD_RESOURCE_DETECTOR"
    category = "INFRA"

    # AWS ARN: arn:aws:service:region:account-id:resource-type/resource-id
    AWS_ARN_PATTERN = re.compile(
        r'arn:aws:[a-z\-]+:[a-z0-9\-]*:[0-9]{12}:[a-z0-9\-_/:]*',
        re.IGNORECASE
    )

    # Azure Resource ID: /subscriptions/{subscription-id}/resourceGroups/{resource-group}/providers/{provider}/{resource-type}/{resource-name}
    AZURE_RESOURCE_PATTERN = re.compile(
        r'/subscriptions/[a-f0-9\-]+/resourceGroups/[a-zA-Z0-9\-_]+/providers/[a-zA-Z]+/[a-zA-Z0-9]+/[a-zA-Z0-9\-_]+',
        re.IGNORECASE
    )

    # GCP Project and resource IDs
    GCP_PATTERN = re.compile(
        r'(?:projects/[a-z][a-z0-9\-]{5,29}|gs://[a-z0-9\-_.]+)',
        re.IGNORECASE
    )

    # Cloud storage paths
    STORAGE_PATH_PATTERN = re.compile(
        r'(?:s3://|gs://|azure://)[a-z0-9\-_.]+(?:/[a-zA-Z0-9\-_.]*)*',
        re.IGNORECASE
    )

    async def detect(self, text: str) -> List[ThreatFinding]:
        findings: List[ThreatFinding] = []

        if not self.validate(text):
            return findings

        # Detect AWS ARNs
        for match in self.AWS_ARN_PATTERN.finditer(text):
            arn = match.group(0)
            findings.append(
                ThreatFinding(
                    detector=self.name,
                    category=self.category,
                    severity=72,
                    confidence=0.98,
                    evidence=arn,
                    start=match.start(),
                    end=match.end(),
                    metadata={"type": "AWS_ARN"}
                )
            )

        # Detect Azure Resources
        for match in self.AZURE_RESOURCE_PATTERN.finditer(text):
            resource = match.group(0)
            findings.append(
                ThreatFinding(
                    detector=self.name,
                    category=self.category,
                    severity=70,
                    confidence=0.95,
                    evidence=resource,
                    start=match.start(),
                    end=match.end(),
                    metadata={"type": "AZURE_RESOURCE_ID"}
                )
            )

        # Detect GCP resources
        for match in self.GCP_PATTERN.finditer(text):
            resource = match.group(0)
            findings.append(
                ThreatFinding(
                    detector=self.name,
                    category=self.category,
                    severity=68,
                    confidence=0.90,
                    evidence=resource,
                    start=match.start(),
                    end=match.end(),
                    metadata={"type": "GCP_RESOURCE"}
                )
            )

        # Detect cloud storage paths
        for match in self.STORAGE_PATH_PATTERN.finditer(text):
            path = match.group(0)
            findings.append(
                ThreatFinding(
                    detector=self.name,
                    category=self.category,
                    severity=65,
                    confidence=0.85,
                    evidence=path,
                    start=match.start(),
                    end=match.end(),
                    metadata={"type": "CLOUD_STORAGE_PATH"}
                )
            )

        return findings
