"""
Byte-level HMAC debugging to identify implementation differences
This will show every step of HMAC calculation in detail
"""

import adafruit_hashlib as hashlib

def detailed_hmac_sha256(key_str, message_str):
    """HMAC-SHA256 with detailed step-by-step debugging"""
    
    print(f"\n[HMAC_BYTE] Starting HMAC calculation")
    print(f"[HMAC_BYTE] Key: '{key_str}' (len={len(key_str)})")
    print(f"[HMAC_BYTE] Message: '{message_str}' (len={len(message_str)})")
    
    # Convert to bytes
    key = key_str.encode('utf-8')
    message = message_str.encode('utf-8')
    
    print(f"[HMAC_BYTE] Key bytes: {key.hex()}")
    print(f"[HMAC_BYTE] Message bytes: {message.hex()}")
    
    block_size = 64
    print(f"[HMAC_BYTE] Block size: {block_size}")
    
    # Step 1: Key processing
    print(f"\n[HMAC_BYTE] Step 1: Key processing")
    original_key_len = len(key)
    
    if len(key) > block_size:
        print(f"[HMAC_BYTE] Key too long ({len(key)} > {block_size}), hashing...")
        h = hashlib.sha256()
        h.update(key)
        key = h.digest()
        print(f"[HMAC_BYTE] Hashed key: {key.hex()}")
    else:
        print(f"[HMAC_BYTE] Key fits in block size ({len(key)} <= {block_size})")
    
    if len(key) < block_size:
        padding_needed = block_size - len(key)
        print(f"[HMAC_BYTE] Padding key with {padding_needed} zero bytes")
        key = key + b'\x00' * padding_needed
        print(f"[HMAC_BYTE] Padded key: {key.hex()}")
    
    # Step 2: Create padded keys
    print(f"\n[HMAC_BYTE] Step 2: Creating padded keys")
    o_key_pad = bytes([0x5C ^ b for b in key])
    i_key_pad = bytes([0x36 ^ b for b in key])
    
    print(f"[HMAC_BYTE] ipad constant: {bytes([0x36] * block_size).hex()}")
    print(f"[HMAC_BYTE] opad constant: {bytes([0x5C] * block_size).hex()}")
    print(f"[HMAC_BYTE] i_key_pad: {i_key_pad.hex()}")
    print(f"[HMAC_BYTE] o_key_pad: {o_key_pad.hex()}")
    
    # Step 3: Inner hash
    print(f"\n[HMAC_BYTE] Step 3: Inner hash calculation")
    inner_input = i_key_pad + message
    print(f"[HMAC_BYTE] Inner input: {inner_input.hex()}")
    print(f"[HMAC_BYTE] Inner input length: {len(inner_input)}")
    
    h_inner = hashlib.sha256()
    h_inner.update(inner_input)
    inner_hash = h_inner.digest()
    
    print(f"[HMAC_BYTE] Inner hash: {inner_hash.hex()}")
    
    # Step 4: Outer hash
    print(f"\n[HMAC_BYTE] Step 4: Outer hash calculation")
    outer_input = o_key_pad + inner_hash
    print(f"[HMAC_BYTE] Outer input: {outer_input.hex()}")
    print(f"[HMAC_BYTE] Outer input length: {len(outer_input)}")
    
    h_outer = hashlib.sha256()
    h_outer.update(outer_input)
    final_hash = h_outer.digest()
    signature = h_outer.hexdigest()
    
    print(f"[HMAC_BYTE] Final hash: {final_hash.hex()}")
    print(f"[HMAC_BYTE] Final signature: {signature}")
    
    return signature

def test_with_server_values():
    """Test with the exact values that should match server"""
    print("=" * 80)
    print("[HMAC_BYTE] Testing with server expected values")
    print("=" * 80)
    
    # Server values from logs
    prov_key = "PROV-9SP4-C6WO-D6Z1"
    timestamp = "1757618801"
    method = "POST"
    path = "/v2/provision/register"
    body_sha = "a66b9db17f710cc4813c555533f94e5f1bfbe727fc04052b6d3caa191ecd1c66"
    
    # Test the canonical string that should produce d9e97456a950c387
    canonical = f"{method}\n{path}\n{timestamp}\n{body_sha}"
    
    print(f"[HMAC_BYTE] Expected server signature: d9e97456a950c387")
    print(f"[HMAC_BYTE] Canonical string (with \\n shown):")
    print(f"[HMAC_BYTE] '{canonical}'")
    print(f"[HMAC_BYTE] Canonical bytes: {canonical.encode('utf-8').hex()}")
    
    # Test with direct PROV key
    print(f"\n[HMAC_BYTE] Testing with direct PROV key as secret:")
    signature = detailed_hmac_sha256(prov_key, canonical)
    
    print(f"\n[HMAC_BYTE] RESULT:")
    print(f"[HMAC_BYTE] Generated: {signature}")
    print(f"[HMAC_BYTE] Expected:  d9e97456a950c387...")
    print(f"[HMAC_BYTE] Match: {signature.startswith('d9e97456a950c387')}")
    
    # Also test with SHA256 of PROV key
    print(f"\n[HMAC_BYTE] Testing with SHA256 of PROV key as secret:")
    h_key = hashlib.sha256()
    h_key.update(prov_key.encode('utf-8'))
    prov_key_hash = h_key.hexdigest()
    
    signature2 = detailed_hmac_sha256(prov_key_hash, canonical)
    
    print(f"\n[HMAC_BYTE] RESULT (SHA256 key):")
    print(f"[HMAC_BYTE] Generated: {signature2}")
    print(f"[HMAC_BYTE] Expected:  d9e97456a950c387...")
    print(f"[HMAC_BYTE] Match: {signature2.startswith('d9e97456a950c387')}")

if __name__ == "__main__":
    test_with_server_values()