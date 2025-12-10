"""
Test the literal \\n format used by the server
This should match the server's expected signature!
"""

import hashlib
import hmac

def test_literal_backslash_format():
    """Test with literal \\n instead of actual newlines"""
    print("=" * 80)
    print("[LITERAL_TEST] Testing server's literal \\n format")
    print("=" * 80)
    
    # Server values from logs
    prov_key = "PROV-9SP4-C6WO-D6Z1"
    timestamp = "1757618801"
    method = "POST"
    path = "/v2/provision/register"
    body_sha = "a66b9db17f710cc4813c555533f94e5f1bfbe727fc04052b6d3caa191ecd1c66"
    
    # This is what the server ACTUALLY uses (literal \\n)
    canonical_literal = f"{method}\\n{path}\\n{timestamp}\\n{body_sha}"
    
    # This is what we were using (actual newlines)
    canonical_newlines = f"{method}\n{path}\n{timestamp}\n{body_sha}"
    
    print(f"[LITERAL_TEST] Expected server signature: d9e97456a950c387")
    print(f"[LITERAL_TEST] PROV key: {prov_key}")
    
    print(f"\n[LITERAL_TEST] Literal \\n format:")
    print(f"  String: '{canonical_literal}'")
    print(f"  Bytes: {canonical_literal.encode('utf-8').hex()}")
    
    print(f"\n[LITERAL_TEST] Actual newlines format:")
    print(f"  String: '{canonical_newlines}'")
    print(f"  Bytes: {canonical_newlines.encode('utf-8').hex()}")
    
    # Test HMAC with literal format
    sig_literal = hmac.new(
        prov_key.encode('utf-8'),
        canonical_literal.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    # Test HMAC with newlines format
    sig_newlines = hmac.new(
        prov_key.encode('utf-8'),
        canonical_newlines.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    print(f"\n[LITERAL_TEST] RESULTS:")
    print(f"  Literal \\n:     {sig_literal}")
    print(f"  Actual newlines: {sig_newlines}")
    print(f"  Expected:       d9e97456a950c387...")
    
    print(f"\n[LITERAL_TEST] MATCHES:")
    print(f"  Literal \\n matches:     {sig_literal.startswith('d9e97456a950c387')}")
    print(f"  Actual newlines matches: {sig_newlines.startswith('d9e97456a950c387')}")
    
    if sig_literal.startswith('d9e97456a950c387'):
        print(f"\n[LITERAL_TEST] ✓ SUCCESS! Found the issue - server uses literal \\n")
        print(f"[LITERAL_TEST] Full matching signature: {sig_literal}")
    else:
        print(f"\n[LITERAL_TEST] Still no match, continuing investigation...")

if __name__ == "__main__":
    test_literal_backslash_format()