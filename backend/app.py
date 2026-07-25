from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from detectors.api_key_detector import ApiKeyDetector
from detectors.aws_secret_detector import AwsSecretDetector
from detectors.credit_card_detector import CreditCardDetector
from detectors.pan_detector import PanDetector
from document_detector import DocumentDetector


app = FastAPI()


# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # For local testing
    #allow_credentials=True,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)



class ScanRequest(BaseModel):
    prompt: str
    client_id: str | None = None
    source: str | None = None
    user_agent: str | None = None


class DocumentScanRequest(BaseModel):
    document: str  # Base64 encoded file content
    filename: str
    document_type: str | None = None
    client_id: str | None = None
    source: str | None = None
    user_agent: str | None = None



DETECTORS = [
    ApiKeyDetector(),
    AwsSecretDetector(),
    CreditCardDetector(),
    PanDetector(),
]

# Initialize document detector with text detectors
document_detector = DocumentDetector(detectors=DETECTORS)



@app.get("/")
def home():
    return {
        "message": "Cybage Browser Prompt Detection Running"
    }



@app.post("/api/scan")
async def scan(request: ScanRequest):

    findings = []


    for detector in DETECTORS:

        result = await detector.detect(
            request.prompt
        )

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

        ]
    }



@app.post("/api/scan-document")
async def scan_document(request: DocumentScanRequest):
    """
    Scan uploaded document for sensitive information.
    
    Supports: PDF, DOCX, XLSX, CSV, TXT
    Max file size: 25 MB
    """
    
    result = await document_detector.scan_document(
        document_base64=request.document,
        filename=request.filename,
        document_type=request.document_type
    )
    
    return result
