# Document Detection System - Implementation Plan

## Goal
Detect sensitive information in uploaded documents (PDF, DOCX, TXT, etc.) before they're sent to AI chat interfaces, similar to existing text/image/audio detection.

## Current State

### What Exists:
- ✅ Text detection (prompts) - 21 detectors
- ✅ Image detection (via OCR) - ocr.py
- ✅ Audio detection (implied)
- ❌ **Document detection - NOT YET**

### Endpoints:
- `POST /api/scan` - Text scanning
- `POST /api/scan-image` - Image scanning (implied from content.js reference)
- ❌ **`POST /api/scan-document` - MISSING**

---

## Requirements Gathering Questions

**[1]** Which document formats should be supported?
   - a. **Common office** - PDF, DOCX, XLSX, PPTX
   - b. **Text files only** - TXT, CSV, MD
   - c. **All common** - PDF + Office + Text + more
   - d. **Other** - Specify your preference

**[2]** How should document content be extracted?
   - a. **Server-side extraction** - Backend parses file, returns text/metadata
   - b. **Client-side extraction** - Browser reads file, sends text to backend
   - c. **Hybrid** - Client extracts, server validates and scans

**[3]** What should be detected in documents?
   - a. **All text content** - Scan extracted text through all 21 detectors
   - b. **Metadata only** - Filename, author, timestamps, properties
   - c. **Both** - Full text + metadata + embedded data
   - d. **Custom** - Specific document types need different rules

**[4]** File size limits - what's acceptable?
   - a. **Small** - 1-5 MB max
   - b. **Medium** - 10-25 MB max
   - c. **Large** - 50+ MB max
   - d. **User choice** - Configurable

**[5]** How should results be reported?
   - a. **Per page** - "Page 3: Found PAN number"
   - b. **Per section** - "Table 2: Found API key"
   - c. **Full text** - All findings aggregated
   - d. **Location + context** - "Line 45, Column 12: Found email"

**[6]** Integration point - where in UI should document upload be detected?
   - a. **File input interception** - Scan when user selects file
   - b. **Before send** - Scan when user tries to attach + send
   - c. **On drag/drop** - Scan when file dragged to chat
   - d. **All above** - Multiple detection points

(Answer using format: "1=a, 2=b, 3=c, 4=d, 5=e, 6=f" or provide your own answers)

---

## Proposed Architecture

### Backend Structure:
```
backend/
├── detectors/                    (existing - 21 text detectors)
├── document_parsers/             (NEW)
│   ├── __init__.py
│   ├── base_parser.py           (Base class for all parsers)
│   ├── pdf_parser.py            (Extract text from PDF)
│   ├── docx_parser.py           (Extract text from DOCX)
│   ├── xlsx_parser.py           (Extract text from Excel)
│   ├── csv_parser.py            (Extract text from CSV)
│   ├── txt_parser.py            (Plain text)
│   └── metadata_extractor.py    (Extract file metadata)
├── document_detector.py          (NEW - Main document scanning)
└── app.py                        (Updated with new endpoint)
```

### API Endpoint:
```
POST /api/scan-document

Request:
{
  "document": base64_string,      // File content as base64
  "filename": "report.pdf",       // Original filename
  "document_type": "pdf",         // File type
  "client_id": "xxx",
  "source": "chatgpt.com"
}

Response:
{
  "action": "BLOCK|ALLOW",
  "severity": "HIGH|CRITICAL|etc",
  "findings": [
    {
      "detector": "PAN_DETECTOR",
      "reason": "PAN Number",
      "evidence": "BT123456L",
      "location": "Page 3, Table 2",  // NEW: Where in document
      "severity": "HIGH",
      "confidence": 0.99
    }
  ],
  "document_metadata": {
    "filename": "report.pdf",
    "pages": 5,
    "size_bytes": 102400,
    "sensitive_fields": ["Author: John Doe", "Company: Acme Inc"]
  },
  "summary": {
    "total_pages_scanned": 5,
    "pages_with_findings": [3, 5],
    "content_type": "pdf",
    "extraction_success": true
  }
}
```

### Extension Integration:
```
extension/
├── content.js                    (Updated - file upload detection)
├── document_scanner.js           (NEW - Handle document uploads)
└── ...
```

---

## Implementation Tasks

### Phase 1: Backend Document Parsing

**Task 1.1: Base Parser Class**
- Create `backend/document_parsers/base_parser.py`
- Define interface for all parsers
- Methods: `parse()`, `extract_text()`, `extract_metadata()`
- Return standardized format: `{"pages": [...], "metadata": {...}, "text": "..."}`

**Task 1.2: PDF Parser**
- Use `pypdf` or `pdfplumber` library
- Extract text per page with location tracking
- Preserve page numbers, table structure
- Handle encrypted PDFs gracefully

**Task 1.3: Office Document Parsers (DOCX, XLSX)**
- Use `python-docx` for DOCX
- Use `openpyxl` for XLSX
- Extract text with formatting info
- Track source (table, header, body, etc.)

**Task 1.4: Text & CSV Parsers**
- Simple TXT parser (line-based)
- CSV parser (column detection)
- Both maintain position info (line numbers, column names)

**Task 1.5: Metadata Extractor**
- Extract file properties: Author, Created date, etc.
- Detect embedded sensitive info in metadata
- Check for hidden content/tracked changes

### Phase 2: Backend Detection

**Task 2.1: Document Detector**
- Create `backend/document_detector.py`
- Main orchestrator class
- Logic: Parse file → Extract text → Scan with all 21 detectors → Aggregate findings

**Task 2.2: Add Endpoint to app.py**
- `POST /api/scan-document`
- Handle base64 file content
- File type validation (allow list)
- Max file size enforcement
- Return detailed findings with locations

**Task 2.3: Error Handling**
- Invalid file format → Return error
- Corrupt file → Graceful failure
- Timeout on large files → Partial results
- Encoding issues → Fallback handling

### Phase 3: Extension Frontend

**Task 3.1: File Upload Detection**
- Create `extension/document_scanner.js`
- Intercept file input changes
- Listen for drag/drop events
- Detect file selections

**Task 3.2: File Submission Blocking**
- Show preview of detections
- Block upload if CRITICAL found
- Similar to text blocking (button disable + popup)
- Show affected page numbers

**Task 3.3: UI Integration**
- Update content.js to handle file uploads
- Show document-specific warnings
- Display: "Found PAN in Page 3, Table 2"
- Allow user to remove/redact before sending

### Phase 4: Testing

**Task 4.1: Unit Tests**
- Test each parser independently
- Test metadata extraction
- Test with malformed files

**Task 4.2: Integration Tests**
- Test full pipeline: upload → parse → scan → respond
- Test with real PDFs, DOCXs, etc.
- Test file size limits
- Test corrupted files

**Task 4.3: End-to-End Tests**
- User uploads document with PAN
- Document blocked from sending
- Document blocking works like text blocking

---

## Technology Stack

### Required Libraries:

```
# Python backend
pypdf==4.0.1              # PDF parsing
pdfplumber==0.10.3        # Alternative PDF (better table support)
python-docx==0.8.11       # DOCX parsing
openpyxl==3.11.2          # XLSX/CSV parsing
chardet==5.2.0            # Encoding detection
```

### Optional Libraries:
```
pillow==10.0.0            # Image extraction from PDFs
python-pptx==0.6.21       # PowerPoint support
```

---

## Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Large file timeout | Medium | Implement async processing, streaming |
| Memory overflow | High | Chunk processing, max file size limits |
| Malicious PDFs | High | Use sandboxed extraction, validate thoroughly |
| Encoding issues | Medium | Use chardet, fallback to UTF-8 |
| Slow processing | Medium | Cache results, implement async |

---

## Success Criteria

- ✅ Detect all 21 sensitive info types in documents
- ✅ Support PDF, DOCX, XLSX, CSV, TXT formats
- ✅ Block HIGH/CRITICAL findings from being uploaded
- ✅ Show location of findings (page, line, table)
- ✅ Process documents < 5MB in < 2 seconds
- ✅ Handle corrupted files gracefully
- ✅ No false positives on legitimate business documents

---

## Timeline Estimate

| Phase | Tasks | Estimate |
|-------|-------|----------|
| Phase 1 | Parser setup + PDF/Office parsing | 3-4 days |
| Phase 2 | Backend detection endpoint | 2-3 days |
| Phase 3 | Extension UI + file upload detection | 2-3 days |
| Phase 4 | Testing + bug fixes | 2-3 days |
| **Total** | | **10-12 days** |

---

## Files to Create

### Backend:
```
backend/document_parsers/__init__.py (100 lines)
backend/document_parsers/base_parser.py (50 lines)
backend/document_parsers/pdf_parser.py (150 lines)
backend/document_parsers/docx_parser.py (100 lines)
backend/document_parsers/xlsx_parser.py (100 lines)
backend/document_parsers/csv_parser.py (80 lines)
backend/document_parsers/txt_parser.py (50 lines)
backend/document_parsers/metadata_extractor.py (100 lines)
backend/document_detector.py (200 lines)
```

### Extension:
```
extension/document_scanner.js (300 lines)
```

### Tests:
```
backend/tests/test_document_parsers.py (500 lines)
backend/tests/test_document_detector.py (300 lines)
```

### Updated:
```
backend/app.py (add /api/scan-document endpoint, +100 lines)
backend/requirements.txt (add 4 libraries)
extension/content.js (add file upload handling, +50 lines)
extension/manifest.json (add permissions for file access)
```

---

## Questions for You

Before I create the detailed implementation plan, please answer:

**[1]** Which document formats are most important for your use case?
**[2]** Should documents be extracted on backend (server processes) or frontend (browser loads)?
**[3]** Do you need page-level tracking of findings?
**[4]** What's your max acceptable file size?
**[5]** Should document metadata (author, dates) be scanned for sensitive info?
**[6]** How should blocking work - prevent upload entirely, or show warning + allow redaction?

This will help me create a precise, actionable implementation plan. 📋