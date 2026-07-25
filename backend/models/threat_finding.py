from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(slots=True)
class ThreatFinding:
    detector: str
    category: str
    severity: int
    confidence: float
    evidence: str
    start: int
    end: int
    metadata: Dict[str, str] = field(default_factory=dict)

    @property
    def score(self) -> float:
        return self.severity * self.confidence