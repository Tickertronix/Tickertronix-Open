#!/usr/bin/env python3
"""
Test script to validate PROV key against Tickertronix API
"""
import hashlib
import hmac
import json
import requests
import time
from datetime import datetime

def test_prov_key_format(prov_key, api_base_url, use_literal_backslash_n=True):
    """Test PROV key with specific canonical format"""
    format_desc = "literal \\\\n" if use_literal_backslash_n else "actual \\n"
    print(f"Testing PROV key: {prov_key} (format: {format_desc})")
    print(f"API Base URL: {api_base_url}")
    print("-" * 50)
    
    # 1. Test key format validation
    if not prov_key.startswith('PROV-') or len(prov_key) != 19:
        print("❌ INVALID: Key format is incorrect")
        return False
        
    parts = prov_key.split('-')
    if len(parts) != 4 or parts[0] != 'PROV':
        print("❌ INVALID: Key structure is incorrect")
        return False
        
    for i, part in enumerate(parts[1:], 1):
        if len(part) != 4 or not part.isalnum() or not part.isupper():
            print(f"❌ INVALID: Part {i} '{part}' is incorrect format")
            return False
    
    print("✅ Key format validation passed")
    
    # 2. Test API endpoint with HMAC authentication
    endpoint = f"{api_base_url}/api/v2/provision/register"
    print(f"Testing endpoint: {endpoint}")
    
    # Prepare request data
    request_data = {
        "device_type": "embedded_display",
        "firmware_version": "1.0.0",
        "hardware_id": "TEST-DEVICE-001"
    }
    
    # Generate HMAC signature
    timestamp = str(int(time.time()))
    method = "POST"
    path = "/v2/provision/register"
    
    body_json = json.dumps(request_data, separators=(',', ':')).encode('utf-8')
    body_sha = hashlib.sha256(body_json).hexdigest()
    
    if use_literal_backslash_n:
        canonical = f"{method}\\n{path}\\n{timestamp}\\n{body_sha}"
    else:
        canonical = f"{method}\n{path}\n{timestamp}\n{body_sha}"
    print(f"Canonical string: {repr(canonical)}")
    
    signature = hmac.new(
        prov_key.encode('utf-8'),
        canonical.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    headers = {
        'Content-Type': 'application/json',
        'x-device-key': prov_key,
        'x-ttx-ts': timestamp,
        'x-ttx-sig': signature
    }
    
    print(f"Request headers: {headers}")
    print(f"Request body: {json.dumps(request_data)}")
    
    try:
        response = requests.post(
            endpoint,
            json=request_data,
            headers=headers,
            timeout=10
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            print(f"Response body: {json.dumps(response_data, indent=2)}")
        except:
            print(f"Response body (raw): {response.text}")
            
        if response.status_code == 200:
            print("✅ PROV key is VALID and working!")
            return True
        elif response.status_code == 401:
            print("❌ PROV key authentication FAILED")
            return False
        elif response.status_code == 404:
            print("❌ PROV key NOT FOUND or expired")
            return False
        else:
            print(f"⚠️  Unexpected response: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return False

def test_wrong_url():
    """Test the wrong URL that device was using"""
    wrong_url = "https://api.tickertronix.com/api/v2/provision/register"
    print(f"\\nTesting WRONG URL: {wrong_url}")
    
    try:
        response = requests.get(wrong_url, timeout=5)
        print(f"Response status: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error (expected): {e}")

if __name__ == "__main__":
    # Test parameters
    PROV_KEYS_TO_TEST = [
        "PROV-9SP4-C6WO-D6Z1",  # Original key to test
        "PROV-09HD-ASMA-NFYU",  # Hardcoded test key from API
        "PROV-IIBA-DH1D-BL8L",  # Key from migration scripts
        "PROV-WLU1-4M5P-VVJI",  # Key from device config
    ]
    CORRECT_API_URL = "https://urchin-app-yhhfp.ondigitalocean.app"
    
    print("🔧 Tickertronix PROV Key Validator")
    print("=" * 60)
    print(f"Timestamp: {datetime.now()}")
    print()
    
    # Test all PROV keys against correct API
    success_count = 0
    for i, prov_key in enumerate(PROV_KEYS_TO_TEST):
        print(f"\\n🔍 Testing key {i+1}/{len(PROV_KEYS_TO_TEST)}: {prov_key}")
        print("-" * 40)
        success = test_prov_key(prov_key, CORRECT_API_URL)
        if success:
            success_count += 1
    
    # Test wrong URL that device was using
    test_wrong_url()
    
    print("\\n" + "=" * 60)
    print(f"🎯 RESULTS: {success_count}/{len(PROV_KEYS_TO_TEST)} keys are valid and working")
    
    if success_count > 0:
        if PROV_KEYS_TO_TEST[0] in [key for key in PROV_KEYS_TO_TEST[:success_count]]:
            print("🎉 CONCLUSION: Original PROV key WORKS!")
        else:
            print("⚠️  CONCLUSION: Original PROV key doesn't work, but others do")
    else:
        print("❌ CONCLUSION: No PROV keys are working - API or authentication issue")