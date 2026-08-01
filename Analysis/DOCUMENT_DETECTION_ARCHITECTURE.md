# Document Detection Architecture

## Current State (Text + Image + Audio)
```
┌─────────────────────────────────────────────────────────┐
│              ChatGPT / Claude Interface                 │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │         User Types Prompt                        │  │
│  │  "My credit card is 4111111111111111"            │  │
│  └────────────────┬─────────────────────────────────┘  │
│                   │                                      │
│                   ↓                                      │
│  ┌──────────────────────────────────────────────────┐  │
│  │    Browser Extension (content.js)                │  │
│  │    - Detects input changes                       │  │
│  │    - Sends text to backend                       │  │
│  └────────────────┬─────────────────────────────────┘  │
│                   │                                      │
└───────────────────┼──────────────────────────────────────┘
                    │
                    ↓
        ┌───────────────────────────┐
        │  Backend API (app.py)      │
        ├───────────────────────────┤
        │ POST /api/scan (text)      │
        │ POST /api/scan-image       │
        │ POST /api/scan-audio       │
        └────────────────┬───────────┘
                         │
        ┌────────────────┼────────────────┐
        ↓                ↓                ↓
    ┌────────────┐  ┌──────────┐   ┌──────────┐
    │   Text     │  │  Image   │   │  Audio   │
    │ Detectors  │  │  Parser  │   │  Parser  │
    │   (21)     │  │  (OCR)   │   │  (Transcribe)
    └────────────┘  └──────────┘   └──────────┘
```

## Future State (With Document Detection)
```
┌─────────────────────────────────────────────────────────┐
│              ChatGPT / Claude Interface                 │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  1. User Types Prompt                            │  │
│  │  2. User Uploads File (report.pdf)               │  │
│  │  3. User Attaches Screenshot (image.png)         │  │
│  └────────────────┬─────────────────────────────────┘  │
│                   │                                      │
│         ┌─────────┼─────────┐                           │
│         ↓         ↓         ↓                           │
│  ┌────────────────────────────────────┐               │
│  │    Browser Extension               │               │
│  │  content.js + document_scanner.js  │               │
│  │  - Detects input changes           │               │
│  │  - Detects file uploads    ← NEW   │               │
│  │  - Sends data to backend           │               │
│  └────────────────┬────────────────────┘               │
│                   │                                      │
└───────────────────┼──────────────────────────────────────┘
                    │
        ┌───────────┼───────────┐
        ↓           ↓           ↓
┌────────────────────────────────────────┐
│         Backend API (app.py)           │
├────────────────────────────────────────┤
│ POST /api/scan (text)                  │
│ POST /api/scan-image                   │
│ POST /api/scan-audio                   │
│ POST /api/scan-document ← NEW           │
└────────────────┬───────────────────────┘
                 │
    ┌────────────┼────────────┬───────────────┐
    ↓            ↓            ↓               ↓
┌────────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐
│    Text    │ │  Image   │ │  Audio   │ │  Document        │
│ Detectors  │ │  Parser  │ │ Parser   │ │  Parsers ← NEW   │
│   (21)     │ │ (OCR)    │ │(Transcrbe)│ │ ├─ PDF Parser   │
└────────────┘ └──────────┘ └──────────┘ │ ├─ DOCX Parser  │
                                          │ ├─ XLSX Parser  │
                                          │ └─ CSV Parser   │
                                          └──────────┬───────┘
                                                     │
                                                     ↓
                                          ┌──────────────────────┐
                                          │ Extract Text/Metadata│
                                          │ (21 detectors scan)  │
                                          └──────────┬───────────┘
                                                     │
                                                     ↓
                                          ┌──────────────────────┐
                                          │ Return Findings      │
                                          │ with Page Numbers    │
                                          └──────────────────────┘
```

---

## Request/Response Flow for Documents

### Request:
```json
POST /api/scan-document

{
  "document": "JVBERi0xLjQKJeLjz9MNCiXi48/DDS8x... (base64 encoded PDF)",
  "filename": "financial_report.pdf",
  "document_type": "pdf",
  "client_id": "ext-123456",
  "source": "chatgpt.com"
}
```

### Response:
```json
{
  "action": "BLOCK",
  "severity": "HIGH",
  "totalFindings": 3,
  "findings": [
    {
      "detector": "PAN_DETECTOR",
      "reason": "PAN Number",
      "evidence": "BT123456L",
      "location": "Page 2, Metadata (Author field)",
      "severity": "HIGH",
      "confidence": 0.99
    },
    {
      "detector": "BANKING_DETECTOR",
      "reason": "Bank Account Number",
      "evidence": "9876543210",
      "location": "Page 3, Table: Account Details",
      "severity": "HIGH",
      "confidence": 0.95
    },
    {
      "detector": "EMAIL_DETECTOR",
      "reason": "Email Address",
      "evidence": "john.doe@company.com",
      "location": "Page 1, Header: Contact",
      "severity": "MEDIUM",
      "confidence": 0.92
    }
  ],
  "document_metadata": {
    "filename": "financial_report.pdf",
    "total_pages": 5,
    "size_bytes": 245632,
    "created_date": "2024-01-15",
    "author": "John Doe",
    "pages_with_findings": [1, 2, 3]
  },
  "summary": {
    "total_findings": 3,
    "critical_count": 0,
    "high_count": 2,
    "medium_count": 1,
    "extraction_method": "pypdf",
    "processing_time_ms": 850,
    "success": true
  }
}
```

---

## Extension UI Integration

### Current (Text Only):
```
User types in prompt
  ↓
Detection panel shows
  ↓
"PAN Number - BLOCK"
  ↓
User removes, then sends
```

### New (With Documents):
```
User types prompt + uploads file
  ↓
Both text and document scanned
  ↓
Combined detection panel:
  "Text: Found 0 issues ✅"
  "Document: Found PAN in Page 2 ⚠️"
  ↓
If CRITICAL found:
  - Block upload
  - Show "Can't submit like that" popup
  - List findings with page numbers
  ↓
User removes/redacts file or replaces it
  ↓
Auto-rescan → Send enabled
```

---

## Backend Folder Structure

### Before:
```
backend/
├── detectors/              # 21 text detectors
├── app.py                 # Main API
├── ocr.py                 # Image OCR
└── ...
```

### After:
```
backend/
├── detectors/             # Text detectors (unchanged)
│
├── document_parsers/      # NEW FOLDER - Document extraction
│   ├── __init__.py
│   ├── base_parser.py
│   ├── pdf_parser.py      # PDF extraction
│   ├── docx_parser.py     # Word extraction
│   ├── xlsx_parser.py     # Excel extraction
│   ├── csv_parser.py      # CSV extraction
│   ├── txt_parser.py      # Text extraction
│   └── metadata_extractor.py
│
├── document_detector.py   # NEW FILE - Main document scanning
├── app.py                 # Updated with new endpoint
├── ocr.py                 # Image OCR (unchanged)
└── ...
```

---

## Data Flow: Document Upload

### Step 1: Browser Detection
```
User clicks file input OR drags file
  ↓
extension/document_scanner.js intercepts
  ↓
Reads file with FileReader API
  ↓
Converts to base64
```

### Step 2: API Request
```
POST /api/scan-document
  ↓
Backend receives base64 file
  ↓
Validates file type (PDF, DOCX, etc)
  ↓
Validates file size (< 25MB)
```

### Step 3: Document Parsing
```
Determine file type
  ↓
Load appropriate parser:
  - PDF → pdf_parser.py
  - DOCX → docx_parser.py
  - XLSX → xlsx_parser.py
  - CSV → csv_parser.py
  ↓
Extract text + metadata
  ↓
Track location: "Page X, Line Y, Column Z"
```

### Step 4: Detection
```
For each page/section:
  Run all 21 detectors on text
  ↓
Collect findings
  ↓
Aggregate by severity
  ↓
Return with locations
```

### Step 5: Browser Response
```
Extension receives findings
  ↓
Shows in detection panel:
  "Document: 3 issues found"
  "- Page 2: PAN Number (HIGH)"
  "- Page 3: Bank Account (HIGH)"
  ↓
If HIGH/CRITICAL:
  Block file upload button
  Show "Can't submit" popup
  ↓
Findings with locations help user redact
```

---

## Parsing Examples

### PDF Example:
```
Input: financial_report.pdf
  ↓
Parse with pdfplumber
  ↓
Output:
{
  "total_pages": 5,
  "pages": [
    {
      "page_num": 1,
      "text": "...",
      "tables": [...],
      "images": [...]
    },
    ...
  ],
  "metadata": {
    "author": "John Doe",
    "created": "2024-01-15",
    "title": "Financial Report"
  }
}
```

### DOCX Example:
```
Input: report.docx
  ↓
Parse with python-docx
  ↓
Output:
{
  "sections": [
    {
      "type": "paragraph",
      "text": "...",
      "style": "Heading1"
    },
    {
      "type": "table",
      "rows": [...],
      "text": "..."  # All text extracted
    }
  ],
  "metadata": {
    "author": "...",
    "created": "...",
    "modified": "..."
  }
}
```

---

## File Type Support Priority

### Must Have (Phase 1):
- ✅ PDF (.pdf)
- ✅ Word (.docx)
- ✅ Excel (.xlsx)
- ✅ CSV (.csv)
- ✅ Text (.txt)

### Nice to Have (Phase 2):
- PowerPoint (.pptx)
- RTF (.rtf)
- ODT (.odt)

### Low Priority (Phase 3):
- Images with embedded text (.png, .jpg)
- Archives (.zip, .rar)

---

## Error Handling Matrix

| Error | Cause | Handler |
|-------|-------|---------|
| File too large | > 25MB | Return error message |
| Unsupported type | .exe, .bin | Reject early |
| Corrupt file | Invalid structure | Try best-effort parse, partial results |
| Encoding issue | Non-UTF8 text | Fallback to chardet |
| Timeout | Large file | Return partial results |
| Out of memory | Huge document | Stream processing |

---

## Security Considerations

1. **File Type Validation** - Whitelist only safe formats
2. **File Size Limits** - Prevent DoS via huge files
3. **Sandboxed Parsing** - Parse in isolated process
4. **Virus Scanning** - Consider VirusTotal integration
5. **Metadata Stripping** - Remove potentially identifying info after scan
6. **Rate Limiting** - Limit document uploads per user/hour

---

## Success Metrics

After implementation, measure:
- ✅ Detection accuracy: 95%+ on sensitive data in documents
- ✅ False positive rate: < 2%
- ✅ Processing time: < 2 seconds for typical 5-page PDF
- ✅ Format support: 99% of user documents
- ✅ Error handling: All errors handled gracefully
- ✅ Security: No sensitive data stored or logged

---

## Next Steps

1. **Answer the 6 planning questions** - Provide requirements
2. **Confirm document formats** - Which are most important?
3. **Approve architecture** - Any changes needed?
4. **Discuss timeline** - Can you dedicate 10-12 days?
5. **Get buy-in** - Stakeholders ready?

Once confirmed, I'll create the detailed implementation plan with specific code structures and step-by-step tasks.
