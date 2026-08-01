#!/usr/bin/env python3
"""
Test AWS detection to see what's being flagged
"""

import re

# Copy the exact patterns from aws_secret_detector.py
AWS_SECRET_PATTERN = re.compile(
    r"(?i)(aws[_\-\s]?secret)\s*[:=]\s*['\"]?([A-Za-z0-9_\-/+=]{12,})['\"]?"
)

AWS_KEY_PATTERN = re.compile(
    r"(?i)(aws[_\-\s]?key)\s*[:=]\s*['\"]?([A-Za-z0-9_\-/+=]{12,})['\"]?"
)

ACCESS_KEY_PATTERN = re.compile(
    r"\b(AKIA|ASIA)[A-Z0-9]{16}\b"
)

test_cases = [
    "AWS Secret",
    "my aws secret is 12345",
    "aws_secret=abcdefghijklmnop",
    "aws secret = abcdefghijklmnop",
    "AWS Secret:",
    "Recommendation: ensure information before sending",
    "CYBAGE BROWSER PROMPT DETECTION!",
    "Status: BLOCKED",
    "AWS Secret Access Key",
]

print("Testing AWS detection patterns:\n")

for test in test_cases:
    print(f"Test: '{test}'")
    
    aws_secret_match = AWS_SECRET_PATTERN.search(test)
    aws_key_match = AWS_KEY_PATTERN.search(test)
    access_key_match = ACCESS_KEY_PATTERN.search(test)
    
    if aws_secret_match:
        print(f"  ✓ AWS_SECRET match: {aws_secret_match.group()}")
    if aws_key_match:
        print(f"  ✓ AWS_KEY match: {aws_key_match.group()}")
    if access_key_match:
        print(f"  ✓ ACCESS_KEY match: {access_key_match.group()}")
    
    if not (aws_secret_match or aws_key_match or access_key_match):
        print(f"  ✗ No match")
    
    print()
