"""
Simple test script for time synchronization
Copy this to your Matrix Portal S3 and run to test time sync

Usage:
1. Copy time_sync.py and this file to your device
2. Connect to WiFi 
3. Run this script to test time synchronization
"""

import time
import wifi
import socketpool
import ssl
import adafruit_requests

def test_wifi_connection():
    """Test WiFi connectivity"""
    print("[TEST] Checking WiFi connection...")
    
    if not wifi.radio.connected:
        print("[TEST] ERROR: WiFi not connected")
        print("[TEST] Please connect to WiFi first")
        return False
    
    print(f"[TEST] WiFi connected: {wifi.radio.ap_info.ssid}")
    print(f"[TEST] IP address: {wifi.radio.ipv4_address}")
    return True

def test_basic_time():
    """Test basic time functionality"""
    print("[TEST] === BASIC TIME TEST ===")
    
    try:
        current_time = time.time()
        print(f"[TEST] Raw time.time(): {current_time}")
        
        # Check what this looks like as a year
        if current_time > 1577836800:  # Unix timestamp
            tm = time.localtime(current_time)
            print(f"[TEST] Interpreted as Unix time: {tm.tm_year}-{tm.tm_mon:02d}-{tm.tm_mday:02d}")
        elif current_time > 0:
            # Try as 2000-epoch
            unix_time = current_time + 946684800
            tm = time.localtime(unix_time)
            print(f"[TEST] As 2000-epoch + 946684800: {tm.tm_year}-{tm.tm_mon:02d}-{tm.tm_mday:02d}")
        
        return True
        
    except Exception as e:
        print(f"[TEST] Basic time test failed: {e}")
        return False

def test_time_sync():
    """Test our time synchronization module"""
    print("[TEST] === TIME SYNC MODULE TEST ===")
    
    try:
        from time_sync import sync_time, validate_time, test_time_sync
        
        # Create socket pool
        pool = socketpool.SocketPool(wifi.radio)
        
        # Test our time sync
        return test_time_sync(pool)
        
    except ImportError:
        print("[TEST] ERROR: time_sync module not found")
        print("[TEST] Make sure time_sync.py is on your device")
        return False
    except Exception as e:
        print(f"[TEST] Time sync test failed: {e}")
        return False

def test_ntp_libraries():
    """Test if required libraries are available"""
    print("[TEST] === LIBRARY AVAILABILITY TEST ===")
    
    libraries = {
        'adafruit_ntp': False,
        'rtc': False,
        'time': False,
        'adafruit_requests': False
    }
    
    for lib in libraries:
        try:
            __import__(lib)
            libraries[lib] = True
            print(f"[TEST] ✓ {lib} available")
        except ImportError:
            print(f"[TEST] ✗ {lib} not available")
    
    return all(libraries.values())

def test_manual_ntp():
    """Test NTP manually without our module"""
    print("[TEST] === MANUAL NTP TEST ===")
    
    try:
        import adafruit_ntp
        import rtc
        
        pool = socketpool.SocketPool(wifi.radio)
        
        print("[TEST] Attempting manual NTP sync...")
        ntp = adafruit_ntp.NTP(pool, server="pool.ntp.org", tz_offset=0)
        
        print("[TEST] Getting NTP time...")
        ntp_time = ntp.datetime
        print(f"[TEST] NTP returned: {ntp_time}")
        
        print("[TEST] Setting RTC...")
        rtc.RTC().datetime = ntp_time
        
        print("[TEST] Checking system time after NTP...")
        new_time = time.time()
        print(f"[TEST] New system time: {new_time}")
        
        # Convert to readable format
        tm = time.localtime(new_time)
        print(f"[TEST] Date: {tm.tm_year}-{tm.tm_mon:02d}-{tm.tm_mday:02d} {tm.tm_hour:02d}:{tm.tm_min:02d}:{tm.tm_sec:02d}")
        
        # Check if year is reasonable
        if 2024 <= tm.tm_year <= 2026:
            print("[TEST] ✓ NTP sync successful - year is reasonable")
            return True
        else:
            print(f"[TEST] ✗ NTP sync failed - year {tm.tm_year} is not reasonable")
            return False
            
    except Exception as e:
        print(f"[TEST] Manual NTP test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("[TEST] ========================================")
    print("[TEST] Matrix Portal S3 Time Sync Test")
    print("[TEST] ========================================")
    
    tests = [
        ("WiFi Connection", test_wifi_connection),
        ("Library Availability", test_ntp_libraries), 
        ("Basic Time", test_basic_time),
        ("Manual NTP", test_manual_ntp),
        ("Time Sync Module", test_time_sync)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n[TEST] Running: {test_name}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"[TEST] {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n[TEST] ========================================")
    print("[TEST] TEST RESULTS SUMMARY")
    print("[TEST] ========================================")
    
    for test_name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"[TEST] {test_name}: {status}")
    
    total_passed = sum(results.values())
    total_tests = len(results)
    
    print(f"\n[TEST] Overall: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("[TEST] 🎉 All tests passed! Time sync should work.")
    else:
        print("[TEST] ⚠️  Some tests failed. Check the output above.")

if __name__ == "__main__":
    main()