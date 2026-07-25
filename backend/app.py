from fastapi import FastAPI
from pydantic import BaseModel

from detectors.api_key_detector import ApiKeyDetector
from detectors.aws_secret_detector import AwsSecretDetector
from detectors.credit_card_detector import CreditCardDetector
from detectors.pan_detector import PanDetector

app = FastAPI()


class ScanRequest(BaseModel):
    prompt: str


DETECTORS = [
    ApiKeyDetector(),
    AwsSecretDetector(),
    CreditCardDetector(),
    PanDetector(),
]


@app.get("/")
def home():
    return {"message": "Cybage Browser Prompt Detection Running"}


@app.post("/scan")
async def scan(request: ScanRequest):

    findings = []

    for detector in DETECTORS:
        result = await detector.detect(request.prompt)
        findings.extend(result)

    action = "ALLOW"

    if findings:
        action = "BLOCK"

    return {
        "action": action,
        "totalFindings": len(findings),
        "findings": [
            {
                "detector": f.detector,
                "category": f.category,
                "evidence": f.evidence,
                "severity": f.severity,
                "confidence": f.confidence,
            }
            for f in findings
        ],
    }