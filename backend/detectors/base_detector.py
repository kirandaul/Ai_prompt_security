from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from models.threat_finding import ThreatFinding


class BaseDetector(ABC):
    """
    Base class for all threat detectors.

    Every detector must:
        - Scan the supplied text.
        - Return zero or more ThreatFinding objects.
        - Never throw exceptions for malformed input.
    """

    name: str = "BaseDetector"
    category: str = "UNKNOWN"

    @abstractmethod
    async def detect(self, text: str) -> List[ThreatFinding]:
        """
        Scan the input text.

        Args:
            text: Prompt or text to inspect.

        Returns:
            List[ThreatFinding]
        """
        pass

    def validate(self, text: str) -> bool:
        """
        Basic validation.
        """
        return text is not None and len(text.strip()) > 0