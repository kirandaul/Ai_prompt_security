import asyncio
from pathlib import Path
from collections import defaultdict

from detectors.api_key_detector import ApiKeyDetector
from detectors.email_detector import EmailDetector
from detectors.phone_detector import PhoneDetector
from detectors.password_detector import PasswordDetector
from detectors.jwt_detector import JwtDetector
from detectors.private_key_detector import PrivateKeyDetector
from detectors.aws_secret_detector import AwsSecretDetector
from detectors.credit_card_detector import CreditCardDetector
from detectors.aadhaar_detector import AadhaarDetector
from detectors.pan_detector import PanDetector
from detectors.sql_detector import SqlInjectionDetector
from detectors.xss_detector import XssDetector
from detectors.prompt_injection_detector import PromptInjectionDetector
from detectors.jailbreak_detector import JailbreakDetector
from detectors.health_detector import HealthDetector

DETECTORS = [
    ApiKeyDetector(),
    EmailDetector(),
    PhoneDetector(),
    PasswordDetector(),
    JwtDetector(),
    PrivateKeyDetector(),
    AwsSecretDetector(),
    CreditCardDetector(),
    AadhaarDetector(),
    PanDetector(),
    SqlInjectionDetector(),
    XssDetector(),
    PromptInjectionDetector(),
    JailbreakDetector(),
]


# ===========================================================
# POLICY
# ===========================================================

BLOCK_DETECTORS = {
    "API_KEY_DETECTOR",
    "PASSWORD_DETECTOR",
    "JWT_DETECTOR",
    "PRIVATE_KEY_DETECTOR",
    "AWS_SECRET_DETECTOR",
    "PROMPT_INJECTION_DETECTOR",
    "JAILBREAK_DETECTOR",
    "SQL_DETECTOR",
    "XSS_DETECTOR",
    "CREDIT_CARD_DETECTOR",
}

BLOCK_CATEGORIES = {
    "FINANCIAL"
}

REDACT_CATEGORIES = {
    "PII"
}


# ===========================================================
# Scan
# ===========================================================

async def scan(prompt: str, index: int):

    print()
    print("=" * 120)
    print(f"PROMPT #{index}")
    print("=" * 120)
    print(prompt)

    total_findings = 0
    risk_score = 0

    block = False
    redact = False

    reasons = []

    category_summary = defaultdict(int)

    for detector in DETECTORS:

        findings = await detector.detect(prompt)

        if not findings:
            continue

        print()
        print(f"[{detector.name}]")

        for finding in findings:

            total_findings += 1

            # detector already provides severity & confidence
            finding_score = round(finding.score)

            risk_score += finding_score

            category = finding.category.upper()

            category_summary[category] += 1

            # ------------------------
            # Policy Engine
            # ------------------------

            if finding.detector.upper() in BLOCK_DETECTORS:
                block = True
                reasons.append(f"{finding.detector}")

            if category in BLOCK_CATEGORIES:
                block = True
                reasons.append(category)

            if category in REDACT_CATEGORIES:
                redact = True
                reasons.append(category)

            print(f"Evidence      : {finding.evidence}")
            print(f"Category      : {finding.category}")
            print(f"Severity      : {finding.severity}")
            print(f"Confidence    : {finding.confidence}")
            print(f"Metadata      : {finding.metadata}")
            print(f"Risk Added    : {finding_score}")
            print("-" * 60)

    # =======================================================
    # Final Decision
    # =======================================================

    if block:

        action = "BLOCK"
        risk_level = "CRITICAL"

    elif redact:

        action = "ALLOW WITH REDACTION"

        if risk_score >= 150:
            risk_level = "HIGH"
        else:
            risk_level = "MEDIUM"

    else:

        if risk_score >= 300:
            action = "BLOCK"
            risk_level = "CRITICAL"

        elif risk_score >= 200:
            action = "QUARANTINE"
            risk_level = "HIGH"

        elif risk_score >= 100:
            action = "ALLOW WITH REDACTION"
            risk_level = "MEDIUM"

        else:
            action = "ALLOW"
            risk_level = "LOW"

    # =======================================================
    # Summary
    # =======================================================

    print()
    print("=" * 120)
    print("SCAN SUMMARY")
    print("=" * 120)

    print(f"Total Findings : {total_findings}")
    print(f"Risk Score     : {risk_score}")
    print(f"Risk Level     : {risk_level}")
    print(f"Action         : {action}")

    if reasons:

        print()
        print("Reasons")

        for reason in sorted(set(reasons)):
            print(f"  - {reason}")

    print()
    print("Category Summary")

    for category, count in category_summary.items():
        print(f"  {category:<30} {count}")

    print("=" * 120)


# ===========================================================
# Main
# ===========================================================

async def main():

    path = Path("test_prompts.txt")

    prompts = path.read_text(
        encoding="utf-8"
    ).split("====================================")

    for index, prompt in enumerate(prompts, start=1):

        prompt = prompt.strip()

        if prompt:
            await scan(prompt, index)


if __name__ == "__main__":
    asyncio.run(main())