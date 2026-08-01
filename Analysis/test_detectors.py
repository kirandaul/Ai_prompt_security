#!/usr/bin/env python3
"""Quick test of new detectors."""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from detectors.ssn_passport_detector import SsnPassportDetector
from detectors.banking_detector import BankingDetector
from detectors.internal_ip_detector import InternalIpDetector
from detectors.cloud_resource_detector import CloudResourceDetector
from detectors.config_detector import ConfigDetector
from detectors.injection_detector import InjectionDetector


async def test_detectors():
    print("Testing new detectors...\n")
    
    # Test SSN/Passport
    ssn_det = SsnPassportDetector()
    result = await ssn_det.detect("SSN: 733-03-2530")
    print(f"SSN Detector: {len(result)} findings - {[f.detector for f in result]}")
    
    result = await ssn_det.detect("Passport: P99331200")
    print(f"Passport Detector: {len(result)} findings - {[f.detector for f in result]}")
    
    # Test Banking
    bank_det = BankingDetector()
    result = await bank_det.detect("IBAN: DE47229529652851421293")
    print(f"Banking IBAN: {len(result)} findings")
    
    result = await bank_det.detect("routing number: 021000021")
    print(f"Banking Routing: {len(result)} findings")
    
    # Test IP
    ip_det = InternalIpDetector()
    result = await ip_det.detect("Internal IP: 192.168.1.1")
    print(f"Internal IP: {len(result)} findings")
    
    # Test Cloud
    cloud_det = CloudResourceDetector()
    result = await cloud_det.detect("arn:aws:iam::123456789012:role/MyRole")
    print(f"AWS ARN: {len(result)} findings")
    
    # Test Config
    config_det = ConfigDetector()
    result = await config_det.detect("postgresql://admin:SecurePass@db.internal:5432/production")
    print(f"DB Connection: {len(result)} findings")
    
    # Test Injection
    inj_det = InjectionDetector()
    result = await inj_det.detect("; rm -rf /")
    print(f"Command Injection: {len(result)} findings")
    
    result = await inj_det.detect("*)(uid=*")
    print(f"LDAP Injection: {len(result)} findings")
    
    print("\nAll detectors loaded successfully!")


if __name__ == "__main__":
    asyncio.run(test_detectors())
