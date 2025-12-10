"""
Debug HMAC calculation to match server exactly
Test with known values from server logs
"""

import adafruit_hashlib as hashlib

def manual_hmac_sha256(key_str, message_str):
    """Manual HMAC-SHA256 matching our client implementation"""
    key = key_str.encode('utf-8')
    message = message_str.encode('utf-8')
    
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

def test_server_expected():
    """Test with exact values from server logs"""
    print("[DEBUG] Testing server expected values...")
    
    prov_key = "PROV-9SP4-C6WO-D6Z1"
    
    # Calculate SHA256 of PROV key (what server uses)
    h_key = hashlib.sha256()
    h_key.update(prov_key.encode('utf-8'))
    prov_key_hash = h_key.hexdigest()
    
    print(f"[DEBUG] PROV key: {prov_key}")
    print(f"[DEBUG] SHA256: {prov_key_hash}")
    print(f"[DEBUG] First 12: {prov_key_hash[:12]}")
    
    # Test case from logs: ts=1757618801, expected=d9e97456a950c387
    timestamp = "1757618801"
    method = "POST"
    path = "/v2/provision/register"
    body_sha = "a66b9db17f710cc4813c555533f94e5f1bfbe727fc04052b6d3caa191ecd1c66"
    
    # Try different canonical string formats
    formats = {
        'newlines': f"{method}\n{path}\n{timestamp}\n{body_sha}",
        'spaces': f"{method} {path} {timestamp} {body_sha}",
        'concat': f"{method}{path}{timestamp}{body_sha}",
        'pipes': f"{method}|{path}|{timestamp}|{body_sha}",
        'url_style': f"{method}&{path}&{timestamp}&{body_sha}",
    }
    
    server_expected = "d9e97456a950c387"
    
    print(f"\n[DEBUG] Looking for signature starting with: {server_expected}")
    print(f"[DEBUG] Testing timestamp: {timestamp}")
    
    for fmt_name, canonical in formats.items():
        # Test with SHA256 hash of PROV key
        sig_hash = manual_hmac_sha256(prov_key_hash, canonical)
        
        # Test with direct PROV key  
        sig_direct = manual_hmac_sha256(prov_key, canonical)
        
        print(f"\n[DEBUG] Format: {fmt_name}")
        print(f"  Canonical: '{canonical}'")
        print(f"  Hash key:   {sig_hash[:16]} {'✓ MATCH!' if sig_hash.startswith(server_expected) else ''}")
        print(f"  Direct key: {sig_direct[:16]} {'✓ MATCH!' if sig_direct.startswith(server_expected) else ''}")

if __name__ == "__main__":
    test_server_expected()