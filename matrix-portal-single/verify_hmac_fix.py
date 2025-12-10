"""
Verify the HMAC fix using adafruit_hashlib
This should now match the server's expected signature
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

def test_fixed_implementation():
    """Test the fixed implementation that should match server"""
    print("=" * 80)
    print("[VERIFY_FIX] Testing fixed HMAC implementation")
    print("=" * 80)
    
    # Server values from logs
    prov_key = "PROV-9SP4-C6WO-D6Z1"
    timestamp = "1757618801"
    method = "POST"
    path = "/v2/provision/register"
    body_sha = "a66b9db17f710cc4813c555533f94e5f1bfbe727fc04052b6d3caa191ecd1c66"
    
    # Use literal \n format to match server (THIS IS THE FIX!)
    canonical = f"{method.upper()}\\n{path}\\n{timestamp}\\n{body_sha}"
    
    print(f"[VERIFY_FIX] Expected server signature: d9e97456a950c387")
    print(f"[VERIFY_FIX] PROV key: {prov_key}")
    print(f"[VERIFY_FIX] Canonical string: '{canonical}'")
    print(f"[VERIFY_FIX] Canonical bytes: {canonical.encode('utf-8').hex()}")
    
    # Calculate HMAC using adafruit_hashlib (same as CircuitPython device)
    signature = manual_hmac_sha256(prov_key, canonical)
    
    print(f"\n[VERIFY_FIX] RESULT:")
    print(f"[VERIFY_FIX] Generated signature: {signature}")
    print(f"[VERIFY_FIX] Expected signature:  d9e97456a950c387ba1fb9704c30bb591ae02d9972ec43a7969c95de0a23b505")
    print(f"[VERIFY_FIX] First 16 chars match: {signature[:16] == 'd9e97456a950c387'}")
    print(f"[VERIFY_FIX] Full signature match: {signature == 'd9e97456a950c387ba1fb9704c30bb591ae02d9972ec43a7969c95de0a23b505'}")
    
    if signature.startswith('d9e97456a950c387'):
        print(f"\n[VERIFY_FIX] ✓ SUCCESS! HMAC fix is working correctly!")
        print(f"[VERIFY_FIX] The CircuitPython device should now authenticate successfully")
    else:
        print(f"\n[VERIFY_FIX] ✗ FAILURE! Still not matching server signature")

if __name__ == "__main__":
    test_fixed_implementation()