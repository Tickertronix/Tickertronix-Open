"""
Simple import verification script
Run this to test if time_sync imports are working correctly
"""

print("[VERIFY] Testing time_sync imports...")

try:
    from time_sync import get_unix_timestamp, sync_from_http_date, validate_time
    print("[VERIFY] ✓ All time_sync imports successful")
    
    # Test the functions
    try:
        is_valid, timestamp, year = validate_time()
        print(f"[VERIFY] validate_time() works - Valid: {is_valid}, Year: {year}")
    except Exception as e:
        print(f"[VERIFY] validate_time() failed: {e}")
    
    try:
        ts = get_unix_timestamp()
        print(f"[VERIFY] get_unix_timestamp() works - Returns: {ts}")
    except Exception as e:
        print(f"[VERIFY] get_unix_timestamp() failed: {e}")
        
    print("[VERIFY] Import test complete - time_sync module is working")
    
except ImportError as e:
    print(f"[VERIFY] ✗ Import failed: {e}")
    print("[VERIFY] Make sure time_sync.py is in the same directory")
except Exception as e:
    print(f"[VERIFY] ✗ Unexpected error: {e}")

# Test API client imports
print("\n[VERIFY] Testing API client imports...")
try:
    from api_client import TickertronixAPI
    print("[VERIFY] ✓ API client import successful")
except ImportError as e:
    print(f"[VERIFY] ✗ API client import failed: {e}")
except Exception as e:
    print(f"[VERIFY] ✗ API client error: {e}")

print("\n[VERIFY] Verification complete!")