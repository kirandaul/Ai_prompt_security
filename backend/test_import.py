#!/usr/bin/env python3
"""Test importing document detector"""

print("Testing imports...")

try:
    from document_detector import DocumentDetector
    print("✅ DocumentDetector imported successfully")
except Exception as e:
    print(f"❌ Failed to import DocumentDetector: {e}")
    import traceback
    traceback.print_exc()

try:
    from detectors.pan_detector import PanDetector
    print("✅ PanDetector imported successfully")
except Exception as e:
    print(f"❌ Failed to import PanDetector: {e}")
    import traceback
    traceback.print_exc()

try:
    from document_parsers.base_parser import BaseDocumentParser
    print("✅ BaseDocumentParser imported successfully")
except Exception as e:
    print(f"❌ Failed to import BaseDocumentParser: {e}")
    import traceback
    traceback.print_exc()

print("\nAll imports successful!")
