from __future__ import annotations

import re
from typing import List

from detectors.base_detector import BaseDetector
from models.threat_finding import ThreatFinding


class PromptInjectionDetector(BaseDetector):
    """
    Detects prompt injection attempts.

    These are attempts to manipulate the LLM into
    ignoring previous instructions or revealing
    hidden/system prompts.
    """

    name = "PROMPT_INJECTION_DETECTOR"
    category = "PROMPT_INJECTION"

    RULES = [

        ("IGNORE_PREVIOUS",
         95,
         re.compile(r"ignore (all )?(previous|prior|above) instructions?", re.I)),

        ("IGNORE_SYSTEM",
         100,
         re.compile(r"ignore (the )?system prompt", re.I)),

        ("OVERRIDE",
         90,
         re.compile(r"override (your )?instructions?", re.I)),

        ("NEW_INSTRUCTIONS",
         85,
         re.compile(r"from now on", re.I)),

        ("DISREGARD",
         85,
         re.compile(r"disregard (all )?(previous|prior)", re.I)),

        ("REVEAL_PROMPT",
         100,
         re.compile(r"(show|display|reveal|print).*(system prompt|hidden prompt)", re.I)),

        ("PROMPT_LEAK",
         100,
         re.compile(r"(repeat|output).*(initial instructions|system instructions)", re.I)),

        ("ROLE_CHANGE",
         80,
         re.compile(r"you are now", re.I)),

        ("DEVELOPER_MODE",
         95,
         re.compile(r"developer mode", re.I)),

        ("SIMULATE_SYSTEM",
         80,
         re.compile(r"pretend to be", re.I)),

        ("DO_NOT_FOLLOW",
         90,
         re.compile(r"do not follow your", re.I))
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

                        confidence=0.97,

                        evidence=match.group(),

                        start=match.start(),

                        end=match.end(),

                        metadata={
                            "rule": rule_name
                        }

                    )

                )

        return findings