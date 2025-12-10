"""
WiFi Manager for Matrix Portal S3
Handles WiFi connection with retry logic and provisioning fallback
"""

import wifi
import socketpool
import supervisor
import time
import json
import os

# Configuration Constants
WIFI_CREDENTIALS_FILE = "wifi.dat"
DEVICE_CONFIG_FILE = "device_config.json"
MAX_CONNECT_ATTEMPTS = 3
CONNECT_RETRY_DELAY = 5  # seconds
CONNECT_TIMEOUT = 10  # seconds

def save_credentials(ssid, password):
    """Save WiFi credentials to a file in the format: ssid;password."""
    try:
        with open(WIFI_CREDENTIALS_FILE, "w") as file:
            file.write(f"{ssid};{password}")
        print(f"[WIFI] Saved credentials for SSID: {ssid}")
        return True
    except Exception as e:
        print(f"[WIFI] Error saving credentials: {e}")
        return False

def load_credentials():
    """Load WiFi credentials from a file in the format: ssid;password."""
    try:
        with open(WIFI_CREDENTIALS_FILE, "r") as file:
            data = file.read().strip()
            if ';' in data:
                ssid, password = data.split(";", 1)
                print(f"[WIFI] Loaded credentials for SSID: {ssid}")
                return ssid, password
            else:
                print("[WIFI] Invalid credentials format")
                return None, None
    except Exception as e:
        print(f"[WIFI] No saved credentials: {e}")
        return None, None

def load_device_config():
    """Load device configuration including PROV key."""
    try:
        with open(DEVICE_CONFIG_FILE, "r") as file:
            config = json.loads(file.read())
            return config
    except Exception as e:
        print(f"[WIFI] No device config found: {e}")
        return None

def connect_to_network(ssid, password, timeout=CONNECT_TIMEOUT):
    """
    Attempt to connect to a WiFi network with timeout.
    Returns True if connected successfully, otherwise False.
    """
    try:
        # Ensure radio is enabled
        if not wifi.radio.enabled:
            wifi.radio.enabled = True
            time.sleep(1)
        
        # Disconnect if already connected
        if wifi.radio.connected:
            print("[WIFI] Disconnecting from current network...")
            wifi.radio.enabled = False
            time.sleep(1)
            wifi.radio.enabled = True
            time.sleep(1)
        
        print(f"[WIFI] Connecting to {ssid}...")
        start_time = time.monotonic()
        
        # Start connection
        wifi.radio.connect(ssid, password)
        
        # Wait for connection with timeout
        while not wifi.radio.connected:
            if time.monotonic() - start_time > timeout:
                print(f"[WIFI] Connection timeout after {timeout}s")
                return False
            time.sleep(0.5)
        
        # Verify IP address
        if wifi.radio.ipv4_address:
            print(f"[WIFI] Connected! IP: {wifi.radio.ipv4_address}")
            return True
        else:
            print("[WIFI] Connected but no IP address assigned")
            return False
            
    except Exception as e:
        print(f"[WIFI] Connection failed: {e}")
        return False

def connect_to_saved_network_with_retry():
    """
    Attempt to connect to saved WiFi network with multiple retries.
    Returns True if connected successfully, otherwise False.
    """
    ssid, password = load_credentials()
    if not ssid:
        print("[WIFI] No saved credentials found")
        return False
    
    for attempt in range(1, MAX_CONNECT_ATTEMPTS + 1):
        print(f"[WIFI] Connection attempt {attempt}/{MAX_CONNECT_ATTEMPTS}")
        
        if connect_to_network(ssid, password):
            print(f"[WIFI] Successfully connected on attempt {attempt}")
            return True
        
        if attempt < MAX_CONNECT_ATTEMPTS:
            print(f"[WIFI] Retrying in {CONNECT_RETRY_DELAY} seconds...")
            time.sleep(CONNECT_RETRY_DELAY)
    
    print(f"[WIFI] Failed to connect after {MAX_CONNECT_ATTEMPTS} attempts")
    return False

def start_provisioning():
    """Start the provisioning portal for WiFi and device setup."""
    print("[WIFI] Starting provisioning portal...")
    try:
        import provisioning_v2
        provisioning_v2.start()
    except Exception as e:
        print(f"[WIFI] Failed to start provisioning: {e}")
        # If provisioning fails, restart the device
        time.sleep(5)
        supervisor.reload()

def get_connection():
    """
    Main function to establish WiFi connection.
    Tries saved credentials first, then falls back to provisioning.
    Returns wifi.radio object when connected.
    """
    print("[WIFI] Initializing WiFi connection...")
    
    # Check if device is provisioned
    device_config = load_device_config()
    
    if not device_config or 'device_key' not in device_config:
        print("[WIFI] Device not provisioned, starting setup...")
        start_provisioning()
        # This won't return as provisioning will reload the device
        while True:
            time.sleep(1)
    
    # Try connecting to saved network
    if connect_to_saved_network_with_retry():
        print("[WIFI] Using saved network connection")
        return wifi.radio
    
    # If connection fails, start provisioning
    print("[WIFI] Unable to connect to saved network")
    print("[WIFI] Starting provisioning portal for reconfiguration...")
    
    # Clear invalid WiFi credentials
    try:
        os.remove(WIFI_CREDENTIALS_FILE)
        print("[WIFI] Cleared invalid WiFi credentials")
    except:
        pass
    
    start_provisioning()
    # This won't return as provisioning will reload the device
    while True:
        time.sleep(1)

def test_connection():
    """Test the current WiFi connection status."""
    if wifi.radio.connected:
        print(f"[WIFI] Connected to: {wifi.radio.ap_info.ssid if wifi.radio.ap_info else 'Unknown'}")
        print(f"[WIFI] IP Address: {wifi.radio.ipv4_address}")
        print(f"[WIFI] Signal Strength: {wifi.radio.ap_info.rssi if wifi.radio.ap_info else 'Unknown'} dBm")
        return True
    else:
        print("[WIFI] Not connected to any network")
        return False

def disconnect():
    """Disconnect from current WiFi network."""
    try:
        if wifi.radio.connected:
            wifi.radio.enabled = False
            time.sleep(1)
            wifi.radio.enabled = True
            print("[WIFI] Disconnected from network")
        return True
    except Exception as e:
        print(f"[WIFI] Error disconnecting: {e}")
        return False

