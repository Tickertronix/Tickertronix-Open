"""
Simple HMAC test to verify our implementation
Run this to test HMAC calculation independently
"""

import adafruit_hashlib as hashlib

def manual_hmac_sha256(key_str, message_str):
    """Manual HMAC-SHA256 implementation matching api_client.py"""
    
    # Convert to bytes
    key = key_str.encode('utf-8')
    message = message_str.encode('utf-8')
    
    # HMAC-SHA256 implementation (ipad/opad method)
    block_size = 64
    
    # Key padding/hashing
    if len(key) > block_size:
        h = hashlib.sha256()
        h.update(key)
        key = h.digest()
    if len(key) < block_size:
        key = key + b'\x00' * (block_size - len(key))
        
    # Create padded keys
    o_key_pad = bytes([0x5C ^ b for b in key])
    i_key_pad = bytes([0x36 ^ b for b in key])
    
    # Calculate HMAC
    # Inner hash
    h_inner = hashlib.sha256()
    h_inner.update(i_key_pad + message)
    inner_hash = h_inner.digest()
    
    # Outer hash
    h_outer = hashlib.sha256()
    h_outer.update(o_key_pad + inner_hash)
    signature = h_outer.hexdigest()
    
    return signature

def test_hmac():
    """Test HMAC with known values"""
    print("[HMAC_TEST] Testing HMAC implementation...")
    
    # Test 1: RFC test vector
    # Key: "key", Message: "The quick brown fox jumps over the lazy dog"
    # Expected: 0xf7bc83f430538424b13298e6aa6fb143ef4d59a14946175997479dbc2d1a3cd8
    key1 = "key"
    msg1 = "The quick brown fox jumps over the lazy dog"
    result1 = manual_hmac_sha256(key1, msg1)
    expected1 = "f7bc83f430538424b13298e6aa6fb143ef4d59a14946175997479dbc2d1a3cd8"
    
    print(f"[HMAC_TEST] Test 1:")
    print(f"  Key: '{key1}'")
    print(f"  Message: '{msg1}'")
    print(f"  Result:   {result1}")
    print(f"  Expected: {expected1}")
    print(f"  Match: {result1 == expected1}")
    
    # Test 2: Our PROV key with a simple message
    prov_key = "PROV-9SP4-C6WO-D6Z1"
    
    # Calculate SHA256 of PROV key (what server uses)
    h_key = hashlib.sha256()
    h_key.update(prov_key.encode('utf-8'))
    prov_key_hash = h_key.hexdigest()
    
    print(f"\n[HMAC_TEST] Test 2 - PROV key:")
    print(f"  PROV key: '{prov_key}'")
    print(f"  SHA256:   '{prov_key_hash}'")
    print(f"  First 12: '{prov_key_hash[:12]}'")
    
    # Test with simple canonical string
    canonical = "POST\n/api/v2/provision/register\n1757618000\nabc123"
    
    # Test both direct key and hashed key
    sig_direct = manual_hmac_sha256(prov_key, canonical)
    sig_hashed = manual_hmac_sha256(prov_key_hash, canonical)
    
    print(f"\n[HMAC_TEST] Test 3 - Canonical string:")
    print(f"  Message: '{canonical}'")
    print(f"  Direct key HMAC:  {sig_direct}")
    print(f"  Hashed key HMAC:  {sig_hashed}")

if __name__ == "__main__":
    test_hmac()