from __future__ import annotations

import re
from typing import List

from detectors.base_detector import BaseDetector
from models.threat_finding import ThreatFinding


class JailbreakDetector(BaseDetector):
    """
    Detects common LLM jailbreak attempts.
    """

    name = "JAILBREAK_DETECTOR"
    category = "JAILBREAK"

    RULES = [

        ("DAN",
         100,
         re.compile(r"\bDAN\b", re.I)),

        ("DO_ANYTHING_NOW",
         100,
         re.compile(r"do anything now", re.I)),

        ("NO_LIMITS",
         95,
         re.compile(r"no limitations?|without restrictions?", re.I)),

        ("UNFILTERED",
         95,
         re.compile(r"unfiltered response", re.I)),

        ("BYPASS",
         90,
         re.compile(
             r"bypass\s+(all|any|the|your)?\s*"
             r"(rules|filters|restrictions|safeguards|guardrails|policies|moderation)",
             re.I)),

        # "pretend you have no content policy" style prompts
        ("NO_CONTENT_POLICY",
         95,
         re.compile(r"no\s+(content\s+)?(policy|policies|filters?|moderation|guidelines)", re.I)),

        ("JAILBREAK",
         100,
         re.compile(r"jailbreak", re.I)),

        ("ROLEPLAY_ATTACK",
         85,
         re.compile(r"roleplay as", re.I)),

        ("ACT_AS",
         80,
         re.compile(r"act as", re.I)),

        ("UNRESTRICTED_AI",
         90,
         re.compile(r"unrestricted ai", re.I)),

        ("IGNORE_ETHICS",
         95,
         re.compile(r"ignore ethics|ignore safety|ignore policies", re.I)),

        ("DISABLE_FILTERS",
         100,
         re.compile(r"disable (all )?(filters|moderation|guardrails)", re.I)),

        ("RAW_OUTPUT",
         85,
         re.compile(r"respond with raw output", re.I)),

        ("SIMULATION",
         75,
         re.compile(r"this is only a simulation", re.I))
    ]

    async def detect(self, text: str) -> List[ThreatFinding]:

        findings: List[ThreatFinding] = []

        if not self.validate(text):
            return findings

        for rule_name, severity, pattern in self.RULES:

            for match in pattern.finditer(text):

                findings.append(

                    ThreatFinding(

                        detector=self.name,

                        category=self.category,

                        severity=severity,

                        confidence=0.98,

                        evidence=match.group(),

                        start=match.start(),

                        end=match.end(),

                        metadata={
                            "rule": rule_name
                        }

                    )

                )

        return findings