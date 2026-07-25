#!/usr/bin/env python3
"""
Test PAN detector directly on document text.
"""

import asyncio
from detectors.pan_detector import PanDetector


async def test_pan():
    detector = PanDetector()
    
    # Test cases
    test_texts = [
        "My PAN Number is BTKPD9226K",
        "BTKPD9226K",
        "My Pan Number is BT KPD9226K",  # With space
        "My Pan is BTKPD9226K and that's it",
        "My Pan Number is BTKPD9226K still why check once",
    ]
    
    for text in test_texts:
        print(f"\nTesting: {text}")
        results = await detector.detect(text)
        print(f"Found {len(results)} findings:")
        for result in results:
            print(f"  - {result.evidence} (confidence: {result.confidence})")


if __name__ == "__main__":
    asyncio.run(test_pan())
