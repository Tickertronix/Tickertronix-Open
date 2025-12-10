"""
Time Synchronization Module for CircuitPython Matrix Portal S3
Handles NTP synchronization and proper time management for HMAC authentication
"""

import time
import rtc
import wifi
import socketpool
import ssl
import gc

try:
    import adafruit_ntp
    NTP_AVAILABLE = True
except ImportError:
    print("[TIME] Warning: adafruit_ntp library not found")
    NTP_AVAILABLE = False

class TimeSync:
    """Handles time synchronization for CircuitPython devices"""
    
    def __init__(self, debug=False):
        self.debug = debug
        self.rtc_obj = rtc.RTC()
        self.last_sync_time = 0
        self.sync_interval = 3600  # Sync every hour
        self.ntp_servers = [
            "pool.ntp.org",
            "time.google.com", 
            "time.cloudflare.com",
            "time.nist.gov"
        ]
        self._is_synced = False
        
    def _log(self, message):
        """Debug logging"""
        if self.debug:
            print(f"[TIME_SYNC] {message}")
            
    def check_rtc_validity(self):
        """Check if RTC has a reasonable time set"""
        try:
            current_dt = self.rtc_obj.datetime
            year = current_dt.tm_year
            
            # Check if year is reasonable (2020-2030)
            if 2020 <= year <= 2030:
                self._log(f"RTC has valid time: {current_dt}")
                return True
            else:
                self._log(f"RTC has invalid year: {year}")
                return False
        except Exception as e:
            self._log(f"Error checking RTC: {e}")
            return False
    
    def get_unix_timestamp(self):
        """Get current Unix timestamp, ensuring proper epoch"""
        try:
            # Get current time from system
            current_time = time.time()
            
            # Check if we're already in Unix epoch (time > 1.6B means after ~2020)
            if current_time >= 1600000000:
                self._log(f"Using direct Unix timestamp: {current_time}")
                return int(current_time)
            
            # If time is small, it's likely CircuitPython's 2000-epoch
            # Convert to Unix epoch by adding offset
            unix_time = current_time + 946684800
            self._log(f"Converted CP time {current_time} to Unix {unix_time}")
            return int(unix_time)
            
        except Exception as e:
            self._log(f"Error getting timestamp: {e}")
            # Fallback to a reasonable current time (approximate)
            return 1704067200  # January 1, 2024 as emergency fallback
    
    def sync_with_ntp(self, force=False):
        """Synchronize time using NTP"""
        if not NTP_AVAILABLE:
            self._log("NTP library not available")
            return False
            
        if not wifi.radio.connected:
            self._log("WiFi not connected, cannot sync NTP")
            return False
        
        # Check if sync is needed
        current_mono = time.monotonic()
        if not force and self._is_synced and (current_mono - self.last_sync_time) < self.sync_interval:
            self._log("Recent sync found, skipping")
            return True
        
        self._log("Starting NTP synchronization...")
        
        # Create socket pool
        pool = socketpool.SocketPool(wifi.radio)
        
        # Try each NTP server
        for server in self.ntp_servers:
            try:
                self._log(f"Trying NTP server: {server}")
                
                # Create NTP client
                ntp = adafruit_ntp.NTP(pool, server=server, tz_offset=0)
                
                # Get time from NTP server
                ntp_time = ntp.datetime
                self._log(f"NTP time received: {ntp_time}")
                
                # Set the RTC
                self.rtc_obj.datetime = ntp_time
                self._log("RTC updated successfully")
                
                # Update sync tracking
                self.last_sync_time = current_mono
                self._is_synced = True
                
                # Verify the sync worked
                if self.check_rtc_validity():
                    self._log("NTP sync completed successfully")
                    
                    # Test the time conversion
                    test_timestamp = self.get_unix_timestamp()
                    self._log(f"Test timestamp after sync: {test_timestamp}")
                    
                    return True
                else:
                    self._log("RTC sync failed validation")
                    continue
                    
            except Exception as e:
                self._log(f"NTP sync failed with {server}: {e}")
                continue
            finally:
                # Clean up
                try:
                    del ntp
                    gc.collect()
                except:
                    pass
        
        self._log("All NTP servers failed")
        return False
    
    def sync_from_http_date(self, date_header):
        """Sync time from HTTP Date header as fallback"""
        try:
            self._log(f"Attempting sync from HTTP Date: {date_header}")
            
            # Parse HTTP date: 'Fri, 05 Sep 2025 16:05:19 GMT'
            parts = date_header.split()
            if len(parts) < 6:
                self._log("Invalid date header format")
                return False
            
            day = int(parts[1])
            month_name = parts[2]
            year = int(parts[3])
            time_part = parts[4]
            
            # Convert month name to number
            months = {'Jan':1,'Feb':2,'Mar':3,'Apr':4,'May':5,'Jun':6,
                     'Jul':7,'Aug':8,'Sep':9,'Oct':10,'Nov':11,'Dec':12}
            month = months.get(month_name, 1)
            
            # Parse time
            hour, minute, second = map(int, time_part.split(':'))
            
            # Create time struct (weekday=0, yearday=0, dst=-1 for unknown)
            time_struct = time.struct_time((year, month, day, hour, minute, second, 0, 0, -1))
            
            # Set RTC
            self.rtc_obj.datetime = time_struct
            self._log(f"RTC set from HTTP date: {time_struct}")
            
            # Mark as synced
            self._is_synced = True
            self.last_sync_time = time.monotonic()
            
            return self.check_rtc_validity()
            
        except Exception as e:
            self._log(f"HTTP date sync failed: {e}")
            return False
    
    def ensure_time_sync(self, http_date_header=None):
        """Ensure time is synchronized, trying multiple methods"""
        self._log("Ensuring time synchronization...")
        
        # First, check if RTC already has valid time
        if self.check_rtc_validity():
            current_mono = time.monotonic()
            if self._is_synced and (current_mono - self.last_sync_time) < self.sync_interval:
                self._log("RTC already has valid, recent time")
                return True
        
        # Try NTP sync first
        if self.sync_with_ntp():
            return True
        
        # Fall back to HTTP date header if provided
        if http_date_header:
            if self.sync_from_http_date(http_date_header):
                return True
        
        # Log failure but don't completely fail
        self._log("All time sync methods failed")
        return False
    
    def get_sync_status(self):
        """Get current sync status information"""
        return {
            'is_synced': self._is_synced,
            'last_sync_time': self.last_sync_time,
            'rtc_valid': self.check_rtc_validity(),
            'current_timestamp': self.get_unix_timestamp(),
            'rtc_datetime': self.rtc_obj.datetime if self.check_rtc_validity() else None
        }

# Global instance
time_sync = TimeSync(debug=True)

# Module-level convenience functions for backward compatibility
def sync_time(pool=None, force_ntp=False):
    """Sync time using NTP (module-level convenience function)"""
    return time_sync.sync_with_ntp(force=force_ntp)

def validate_time():
    """Validate current time and return status"""
    timestamp = time_sync.get_unix_timestamp()
    is_valid = time_sync.check_rtc_validity()
    try:
        year = time.localtime(timestamp)[0] if timestamp > 946684800 else 2000
    except:
        year = 2000
    return is_valid, timestamp, year

def get_unix_timestamp():
    """Get current Unix timestamp"""
    return time_sync.get_unix_timestamp()

def sync_from_http_date(date_header):
    """Sync time from HTTP Date header"""
    return time_sync.sync_from_http_date(date_header)