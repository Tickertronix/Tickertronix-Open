"""
Time Synchronization Module for CircuitPython
Provides NTP and HTTP date synchronization for Matrix Portal S3

Usage:
    from time_sync import sync_time
    if sync_time(pool):
        print("Time synchronized successfully")
"""

import time
import rtc
import gc

# Month name mapping for HTTP date parsing
MONTH_MAP = {
    'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
    'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
}

def sync_with_ntp(pool):
    """
    Sync system time using NTP
    Returns True if successful, False otherwise
    """
    try:
        import adafruit_ntp
        
        print("[TIME_SYNC] Attempting NTP synchronization...")
        
        # Create NTP client with multiple server fallbacks
        ntp_servers = [
            "pool.ntp.org",
            "time.nist.gov", 
            "time.google.com",
            "0.pool.ntp.org"
        ]
        
        for server in ntp_servers:
            try:
                print(f"[TIME_SYNC] Trying NTP server: {server}")
                ntp = adafruit_ntp.NTP(pool, server=server, tz_offset=0)
                
                # Get current time from NTP
                current_time = ntp.datetime
                
                # Set the RTC
                rtc.RTC().datetime = current_time
                
                # Verify the sync worked
                new_time = time.time()
                print(f"[TIME_SYNC] NTP sync successful with {server}")
                print(f"[TIME_SYNC] System time now: {new_time}")
                
                # Sanity check: should be between 2024-2026
                if 1704067200 <= new_time <= 1767139200:  # 2024-2026
                    return True
                else:
                    print(f"[TIME_SYNC] NTP returned invalid time: {new_time}")
                    continue
                    
            except Exception as e:
                print(f"[TIME_SYNC] NTP server {server} failed: {e}")
                continue
        
        print("[TIME_SYNC] All NTP servers failed")
        return False
        
    except ImportError:
        print("[TIME_SYNC] adafruit_ntp library not available")
        return False
    except Exception as e:
        print(f"[TIME_SYNC] NTP sync failed: {e}")
        return False

def sync_from_http_date(date_string):
    """
    Sync system time from HTTP Date header
    Format: "Wed, 11 Sep 2025 15:30:00 GMT"
    Returns True if successful, False otherwise
    """
    try:
        print(f"[TIME_SYNC] Parsing HTTP date: {date_string}")
        
        # Parse date string
        parts = date_string.strip().split()
        if len(parts) < 5:
            return False
            
        # Extract components
        day = int(parts[1])
        month = MONTH_MAP.get(parts[2])
        year = int(parts[3])
        time_part = parts[4]
        
        if not month:
            return False
            
        # Parse time
        hour, minute, second = map(int, time_part.split(':'))
        
        # Create time structure
        dt = time.struct_time((year, month, day, hour, minute, second, 0, 0, -1))
        
        # Set RTC
        rtc.RTC().datetime = dt
        
        # Verify the sync worked
        new_time = time.time()
        print(f"[TIME_SYNC] HTTP date sync successful")
        print(f"[TIME_SYNC] System time now: {new_time}")
        
        return True
        
    except Exception as e:
        print(f"[TIME_SYNC] HTTP date sync failed: {e}")
        return False

def get_unix_timestamp():
    """
    Get current Unix timestamp with proper epoch handling
    Returns Unix timestamp (seconds since 1970) or None if invalid
    """
    try:
        current_time = time.time()
        
        # If already Unix timestamp (>= 2024)
        if current_time >= 1704067200:  # Jan 1, 2024
            # Double check it's not too far in future
            if current_time <= 1767139200:  # Jan 1, 2026
                return int(current_time)
        
        # If CircuitPython 2000-epoch, convert carefully
        if 0 < current_time < 1000000000:  # Reasonable 2000-epoch range
            unix_time = current_time + 946684800
            
            # Sanity check result (2024-2026)
            if 1704067200 <= unix_time <= 1767139200:
                return int(unix_time)
        
        print(f"[TIME_SYNC] Invalid system time: {current_time}")
        return None
        
    except Exception as e:
        print(f"[TIME_SYNC] Failed to get timestamp: {e}")
        return None

def sync_time(pool, force_ntp=False):
    """
    Main time synchronization function
    
    Args:
        pool: SocketPool for network requests
        force_ntp: If True, always try NTP even if time seems correct
    
    Returns:
        True if time is synchronized, False otherwise
    """
    try:
        # Check if time is already reasonable
        current_time = get_unix_timestamp()
        if current_time and not force_ntp:
            print(f"[TIME_SYNC] Time already synchronized: {current_time}")
            return True
        
        print("[TIME_SYNC] Starting time synchronization...")
        
        # Try NTP first
        if sync_with_ntp(pool):
            return True
        
        # Fallback to HTTP date from a reliable server
        try:
            import adafruit_requests
            import ssl
            
            session = adafruit_requests.Session(pool, ssl.create_default_context())
            
            # Try multiple HTTP servers
            http_servers = [
                "http://worldtimeapi.org/api/timezone/UTC",
                "https://httpbin.org/get",
                "https://api.github.com"
            ]
            
            for url in http_servers:
                try:
                    print(f"[TIME_SYNC] Trying HTTP date from: {url}")
                    response = session.get(url, timeout=10)
                    
                    date_header = response.headers.get('date') or response.headers.get('Date')
                    if date_header and sync_from_http_date(date_header):
                        response.close()
                        session.close()
                        return True
                    
                    response.close()
                    
                except Exception as e:
                    print(f"[TIME_SYNC] HTTP server {url} failed: {e}")
                    continue
            
            session.close()
            
        except Exception as e:
            print(f"[TIME_SYNC] HTTP fallback failed: {e}")
        
        print("[TIME_SYNC] All synchronization methods failed")
        return False
        
    except Exception as e:
        print(f"[TIME_SYNC] Sync error: {e}")
        return False
    finally:
        # Clean up memory
        gc.collect()

def validate_time():
    """
    Validate that system time is reasonable
    Returns (is_valid, timestamp, year)
    """
    try:
        timestamp = get_unix_timestamp()
        if not timestamp:
            return False, None, None
        
        # Convert to struct_time to get year
        tm = time.localtime(timestamp)
        year = tm.tm_year
        
        # Check if year is reasonable (2024-2026 for current use)
        is_valid = 2024 <= year <= 2026
        
        return is_valid, timestamp, year
        
    except Exception as e:
        print(f"[TIME_SYNC] Validation error: {e}")
        return False, None, None

# Test function
def test_time_sync(pool):
    """Test time synchronization functionality"""
    print("[TIME_SYNC] === TIME SYNC TEST ===")
    
    # Show initial state
    is_valid, timestamp, year = validate_time()
    print(f"[TIME_SYNC] Initial time - Valid: {is_valid}, Timestamp: {timestamp}, Year: {year}")
    
    # Force sync
    if sync_time(pool, force_ntp=True):
        is_valid, timestamp, year = validate_time()
        print(f"[TIME_SYNC] After sync - Valid: {is_valid}, Timestamp: {timestamp}, Year: {year}")
        return True
    else:
        print("[TIME_SYNC] Synchronization failed")
        return False