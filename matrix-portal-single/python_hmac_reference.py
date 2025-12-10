"""
Reference HMAC calculation using standard Python libraries
This will show what the correct signature should be
"""

import hashlib
import hmac

def manual_hmac_sha256(key_str, message_str):
    """Manual HMAC-SHA256 implementation matching the CircuitPython version"""
    
    print(f"\n[PYTHON_HMAC] Starting HMAC calculation")
    print(f"[PYTHON_HMAC] Key: '{key_str}' (len={len(key_str)})")
    print(f"[PYTHON_HMAC] Message: '{message_str}' (len={len(message_str)})")
    
    # Convert to bytes
    key = key_str.encode('utf-8')
    message = message_str.encode('utf-8')
    
    print(f"[PYTHON_HMAC] Key bytes: {key.hex()}")
    print(f"[PYTHON_HMAC] Message bytes: {message.hex()}")
    
    block_size = 64
    print(f"[PYTHON_HMAC] Block size: {block_size}")
    
    # Step 1: Key processing
    print(f"\n[PYTHON_HMAC] Step 1: Key processing")
    
    if len(key) > block_size:
        print(f"[PYTHON_HMAC] Key too long ({len(key)} > {block_size}), hashing...")
        h = hashlib.sha256()
        h.update(key)
        key = h.digest()
        print(f"[PYTHON_HMAC] Hashed key: {key.hex()}")
    else:
        print(f"[PYTHON_HMAC] Key fits in block size ({len(key)} <= {block_size})")
    
    if len(key) < block_size:
        padding_needed = block_size - len(key)
        print(f"[PYTHON_HMAC] Padding key with {padding_needed} zero bytes")
        key = key + b'\x00' * padding_needed
        print(f"[PYTHON_HMAC] Padded key: {key.hex()}")
    
    # Step 2: Create padded keys
    print(f"\n[PYTHON_HMAC] Step 2: Creating padded keys")
    o_key_pad = bytes([0x5C ^ b for b in key])
    i_key_pad = bytes([0x36 ^ b for b in key])
    
    print(f"[PYTHON_HMAC] ipad constant: {bytes([0x36] * block_size).hex()}")
    print(f"[PYTHON_HMAC] opad constant: {bytes([0x5C] * block_size).hex()}")
    print(f"[PYTHON_HMAC] i_key_pad: {i_key_pad.hex()}")
    print(f"[PYTHON_HMAC] o_key_pad: {o_key_pad.hex()}")
    
    # Step 3: Inner hash
    print(f"\n[PYTHON_HMAC] Step 3: Inner hash calculation")
    inner_input = i_key_pad + message
    print(f"[PYTHON_HMAC] Inner input: {inner_input.hex()}")
    print(f"[PYTHON_HMAC] Inner input length: {len(inner_input)}")
    
    h_inner = hashlib.sha256()
    h_inner.update(inner_input)
    inner_hash = h_inner.digest()
    
    print(f"[PYTHON_HMAC] Inner hash: {inner_hash.hex()}")
    
    # Step 4: Outer hash
    print(f"\n[PYTHON_HMAC] Step 4: Outer hash calculation")
    outer_input = o_key_pad + inner_hash
    print(f"[PYTHON_HMAC] Outer input: {outer_input.hex()}")
    print(f"[PYTHON_HMAC] Outer input length: {len(outer_input)}")
    
    h_outer = hashlib.sha256()
    h_outer.update(outer_input)
    final_hash = h_outer.digest()
    signature = h_outer.hexdigest()
    
    print(f"[PYTHON_HMAC] Final hash: {final_hash.hex()}")
    print(f"[PYTHON_HMAC] Final signature: {signature}")
    
    return signature

def test_with_builtin_hmac(key_str, message_str):
    """Test using Python's built-in HMAC library for comparison"""
    key = key_str.encode('utf-8')
    message = message_str.encode('utf-8')
    
    signature = hmac.new(key, message, hashlib.sha256).hexdigest()
    print(f"[PYTHON_HMAC] Built-in HMAC result: {signature}")
    return signature

def test_server_values():
    """Test with the exact values that should match server"""
    print("=" * 80)
    print("[PYTHON_HMAC] Testing with server expected values")
    print("=" * 80)
    
    # Server values from logs
    prov_key = "PROV-9SP4-C6WO-D6Z1"
    timestamp = "1757618801"
    method = "POST"
    path = "/v2/provision/register"
    body_sha = "a66b9db17f710cc4813c555533f94e5f1bfbe727fc04052b6d3caa191ecd1c66"
    
    # Test the canonical string that should produce d9e97456a950c387
    canonical = f"{method}\n{path}\n{timestamp}\n{body_sha}"
    
    print(f"[PYTHON_HMAC] Expected server signature: d9e97456a950c387")
    print(f"[PYTHON_HMAC] Canonical string:")
    print(repr(canonical))
    print(f"[PYTHON_HMAC] Canonical bytes: {canonical.encode('utf-8').hex()}")
    
    print(f"\n[PYTHON_HMAC] Testing with direct PROV key as secret:")
    
    # Test with built-in HMAC first
    builtin_sig = test_with_builtin_hmac(prov_key, canonical)
    
    # Test with manual implementation
    manual_sig = manual_hmac_sha256(prov_key, canonical)
    
    print(f"\n[PYTHON_HMAC] COMPARISON:")
    print(f"[PYTHON_HMAC] Built-in:  {builtin_sig}")
    print(f"[PYTHON_HMAC] Manual:    {manual_sig}")
    print(f"[PYTHON_HMAC] Expected:  d9e97456a950c387...")
    print(f"[PYTHON_HMAC] Built-in matches expected: {builtin_sig.startswith('d9e97456a950c387')}")
    print(f"[PYTHON_HMAC] Manual matches expected: {manual_sig.startswith('d9e97456a950c387')}")
    print(f"[PYTHON_HMAC] Built-in == Manual: {builtin_sig == manual_sig}")
    
    # Also test with SHA256 of PROV key
    print(f"\n[PYTHON_HMAC] Testing with SHA256 of PROV key:")
    prov_key_hash = hashlib.sha256(prov_key.encode('utf-8')).hexdigest()
    print(f"[PYTHON_HMAC] PROV key SHA256: {prov_key_hash}")
    
    builtin_sig2 = test_with_builtin_hmac(prov_key_hash, canonical)
    manual_sig2 = manual_hmac_sha256(prov_key_hash, canonical)
    
    print(f"\n[PYTHON_HMAC] COMPARISON (SHA256 key):")
    print(f"[PYTHON_HMAC] Built-in:  {builtin_sig2}")
    print(f"[PYTHON_HMAC] Manual:    {manual_sig2}")
    print(f"[PYTHON_HMAC] Expected:  d9e97456a950c387...")
    print(f"[PYTHON_HMAC] Built-in matches expected: {builtin_sig2.startswith('d9e97456a950c387')}")
    print(f"[PYTHON_HMAC] Manual matches expected: {manual_sig2.startswith('d9e97456a950c387')}")

if __name__ == "__main__":
    test_server_values()