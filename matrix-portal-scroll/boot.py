"""
Matrix Portal S3 Boot Configuration with Hardware Provisioning Switch
Connect a switch between pin A1 and GND to enable provisioning mode

Behavior:
- A1 OPEN (disconnected): Normal mode. USB mass‑storage writable from host and device.
- A1 CLOSED (to GND): Provisioning mode. USB mass‑storage write‑protected for host;
  device firmware can write provisioning files (wifi.dat, device_config.json).
"""

import board
import digitalio
import storage
import supervisor
import time
import os

print("[BOOT] Matrix Portal S3 Starting...")

# Disable auto-reload to prevent restarts during API calls
supervisor.runtime.autoreload = False

# Setup provisioning mode switch on pin A1
# Switch CLOSED (A1 to GND): Provisioning Mode (host write‑protected; device can write)
# Switch OPEN (A1 floating with pullup): Normal Mode (host writable)
provision_switch = digitalio.DigitalInOut(board.A1)
provision_switch.direction = digitalio.Direction.INPUT
provision_switch.pull = digitalio.Pull.UP

# Setup onboard LED for status indication
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

# Check if factory reset is requested (UP button held during boot)
factory_reset_button = digitalio.DigitalInOut(board.BUTTON_UP)
factory_reset_button.direction = digitalio.Direction.INPUT
factory_reset_button.pull = digitalio.Pull.UP

# Factory reset takes priority over provisioning mode
if not factory_reset_button.value:
    print("[BOOT] Factory reset requested!")
    
    # Flash LED rapidly for factory reset
    for _ in range(10):
        led.value = True
        time.sleep(0.05)
        led.value = False
        time.sleep(0.05)
    
    # Make filesystem writable temporarily and enable USB drive
    storage.remount("/", readonly=False)
    try:
        storage.enable_usb_drive()
    except Exception:
        pass
    
    # Delete configuration files
    try:
        os.remove("wifi.dat")
        print("[BOOT] Removed wifi.dat")
    except:
        pass
    
    try:
        os.remove("device_config.json")
        print("[BOOT] Removed device_config.json")
    except:
        pass
    
    print("[BOOT] Factory reset complete. Restarting...")
    time.sleep(2)
    supervisor.reload()

# Check provisioning switch (A1 pin)
if not provision_switch.value:  # Switch closed (A1 connected to GND)
    print("[BOOT] ========================================")
    print("[BOOT] PROVISIONING MODE ACTIVE")
    print("[BOOT] A1 switch is CLOSED (connected to GND)")
    print("[BOOT] USB mass‑storage is WRITE‑PROTECTED (host cannot modify)")
    print("[BOOT] Device firmware CAN write provisioning files")
    print("[BOOT] ========================================")
    
    # Device can write while host cannot
    storage.remount("/", readonly=False)
    try:
        storage.disable_usb_drive()
    except Exception:
        pass
    
    # Flash LED slowly to indicate provisioning mode
    for _ in range(5):
        led.value = True
        time.sleep(0.2)
        led.value = False
        time.sleep(0.2)
    
    print("[BOOT] Ready for provisioning")
    print("[BOOT] Connect to WiFi: TickerSetup")
    print("[BOOT] Browse to: http://192.168.4.1")
    print("[BOOT] After provisioning, flip switch back and reset")
    
else:  # Switch open (A1 has pullup, reading HIGH)
    print("[BOOT] ========================================")
    print("[BOOT] NORMAL MODE")
    print("[BOOT] A1 switch is OPEN (not connected)")
    print("[BOOT] USB mass‑storage is WRITABLE from host")
    print("[BOOT] ========================================")
    
    # Host and device can both write in normal mode
    try:
        storage.remount("/", readonly=False)
    except Exception:
        pass
    try:
        storage.enable_usb_drive()
    except Exception:
        pass
    
    # Quick LED flash to indicate normal mode
    led.value = True
    time.sleep(0.1)
    led.value = False
    
    # Check if device is configured
    try:
        os.stat("device_config.json")
        os.stat("wifi.dat")
        print("[BOOT] Device is configured and ready")
    except Exception:
        print("[BOOT] WARNING: Device not configured!")
        print("[BOOT] To provision: Close A1 switch and reset")
        # Flash LED as warning
        for _ in range(3):
            led.value = True
            time.sleep(0.5)
            led.value = False
            time.sleep(0.5)

# Clean up pins
factory_reset_button.deinit()
provision_switch.deinit()
led.deinit()

print("[BOOT] Boot sequence complete")
print("[BOOT] Hold UP button during reset for factory reset")
