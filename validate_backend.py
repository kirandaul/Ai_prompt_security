#!/usr/bin/env python3
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

try:
    print("Loading server...")
    from server import DETECTORS, REASON_LABELS
    
    print(f"✓ Loaded {len(DETECTORS)} detectors:")
    for d in DETECTORS:
        print(f"  - {d.name}")
    
    print(f"\n✓ Loaded {len(REASON_LABELS)} reason labels")
    
    # Verify new detectors are present
    detector_names = [d.name for d in DETECTORS]
    required_new = [
        "SSN_PASSPORT_DETECTOR",
        "BANKING_DETECTOR",
        "INTERNAL_IP_DETECTOR",
        "CLOUD_RESOURCE_DETECTOR",
        "CONFIG_DETECTOR",
        "INJECTION_DETECTOR"
    ]
    
    missing = [d for d in required_new if d not in detector_names]
    if missing:
        print(f"\n✗ MISSING DETECTORS: {missing}")
        sys.exit(1)
    else:
        print(f"\n✓ All {len(required_new)} new detectors present!")
    
    print("\n✓✓✓ Backend validation successful!")
    
except Exception as e:
    print(f"✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
