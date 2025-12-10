#!/usr/bin/env python3
import hashlib
import hmac
import json
import requests
import time

def test_both_formats():
    """Test both HMAC formats against live API"""
    prov_key = "PROV-09HD-ASMA-NFYU"  # Known test key from server code
    api_url = "https://urchin-app-yhhfp.ondigitalocean.app/api/v2/provision/register"
    
    # Request data
    request_data = {
        "device_type": "embedded_display",
        "firmware_version": "1.0.0", 
        "hardware_id": "TEST-DEVICE-001"
    }
    
    # Prepare request
    method = "POST"
    path = "/v2/provision/register"
    timestamp = str(int(time.time()))
    body_json = json.dumps(request_data, separators=(',', ':')).encode('utf-8')
    body_sha = hashlib.sha256(body_json).hexdigest()
    
    print(f"Testing PROV key: {prov_key}")
    print(f"Timestamp: {timestamp}")
    print(f"Body SHA: {body_sha}")
    print()
    
    # Format 1: Actual newlines (embedded client format)
    print("=== TEST 1: Actual newlines (\\n) ===")
    canonical1 = f"{method}\n{path}\n{timestamp}\n{body_sha}"
    sig1 = hmac.new(prov_key.encode(), canonical1.encode(), hashlib.sha256).hexdigest()
    print(f"Canonical: {repr(canonical1)}")
    print(f"Signature: {sig1}")
    
    headers1 = {
        'Content-Type': 'application/json',
        'x-device-key': prov_key,
        'x-ttx-ts': timestamp,
        'x-ttx-sig': sig1
    }
    
    try:
        resp1 = requests.post(api_url, json=request_data, headers=headers1, timeout=10)
        print(f"Response: {resp1.status_code}")
        if resp1.status_code != 401:
            print(f"Body: {resp1.text}")
        print()
    except Exception as e:
        print(f"Error: {e}")
        print()
    
    # Format 2: Literal backslash-n (server format)  
    print("=== TEST 2: Literal backslash-n (\\\\n) ===")
    canonical2 = f"{method}\\n{path}\\n{timestamp}\\n{body_sha}"
    sig2 = hmac.new(prov_key.encode(), canonical2.encode(), hashlib.sha256).hexdigest()
    print(f"Canonical: {repr(canonical2)}")
    print(f"Signature: {sig2}")
    
    headers2 = {
        'Content-Type': 'application/json',
        'x-device-key': prov_key,
        'x-ttx-ts': timestamp,
        'x-ttx-sig': sig2
    }
    
    try:
        resp2 = requests.post(api_url, json=request_data, headers=headers2, timeout=10)
        print(f"Response: {resp2.status_code}")
        if resp2.status_code != 401:
            print(f"Body: {resp2.text}")
        print()
    except Exception as e:
        print(f"Error: {e}")
        print()
        
    # Summary
    print("=== SUMMARY ===")
    if resp1.status_code == 401 and resp2.status_code == 401:
        print("❌ Both formats failed - PROV key may not exist or other issue")
    elif resp1.status_code != 401:
        print("✅ Format 1 (actual newlines) works!")
    elif resp2.status_code != 401:
        print("✅ Format 2 (literal backslash-n) works!")

if __name__ == "__main__":
    test_both_formats()