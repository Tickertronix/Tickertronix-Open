"""
Fixed provisioning portal for Matrix Portal S3 (v2 DIY flow)
Simplified HTML generation for better CircuitPython compatibility
"""

import wifi
import socketpool
import supervisor
import time
import json
import random

AP_SSID = "TickerSetup"  # Matches Flutter app documentation
AP_PSK = ""  # Open network for easier connection

def _get_wifi_networks():
    """Scan for available WiFi networks"""
    networks = []
    try:
        for network in wifi.radio.start_scanning_networks():
            if network.ssid and network.ssid not in [n['ssid'] for n in networks]:
                networks.append({
                    'ssid': network.ssid,
                    'rssi': network.rssi
                })
        wifi.radio.stop_scanning_networks()
        # Sort by signal strength
        networks.sort(key=lambda x: x['rssi'], reverse=True)
    except Exception as e:
        print(f"[PROVISION] WiFi scan error: {e}")
    return networks[:10]  # Return top 10 networks

def _generate_html_form(hub_url="http://tickertronixhub.local:5001"):
    """Generate HTML form with WiFi network dropdown"""
    networks = _get_wifi_networks()
    
    # Build network options
    network_options = ""
    for net in networks:
        ssid = net["ssid"]
        rssi = str(net["rssi"])
        network_options = network_options + '<option value="' + ssid + '">' + ssid + ' (' + rssi + ' dBm)</option>\n'
    
    # Build complete HTML page
    html = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n"
    html = html + """<!DOCTYPE html>
<html>
<head>
<meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Tickertronix Setup</title>
<style>
body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
}
.container {
    max-width: 400px;
    margin: 0 auto;
    background: white;
    border-radius: 16px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    padding: 30px;
}
h1 {
    color: #333;
    margin: 0 0 10px 0;
    font-size: 28px;
    text-align: center;
}
.subtitle {
    color: #666;
    margin: 0 0 30px 0;
    font-size: 14px;
    text-align: center;
}
.form-group {
    margin-bottom: 20px;
}
label {
    display: block;
    color: #555;
    font-weight: bold;
    margin-bottom: 8px;
    font-size: 14px;
}
input, select {
    width: 100%;
    padding: 12px;
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    font-size: 16px;
    box-sizing: border-box;
}
.info {
    background: #f0f4ff;
    border-left: 4px solid #667eea;
    padding: 12px;
    margin: 20px 0;
    border-radius: 4px;
    font-size: 14px;
    color: #555;
}
.btn {
    width: 100%;
    padding: 14px;
    background: #667eea;
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 16px;
    font-weight: bold;
    cursor: pointer;
}
.status {
    text-align: center;
    margin-top: 20px;
    color: #666;
    font-size: 14px;
}
</style>
</head>
<body>
<div class='container'>
    <h1>Tickertronix</h1>
    <p class='subtitle'>Matrix Portal Setup</p>
    
    <form method='POST' action='/save'>
        <div class='form-group'>
            <label>WiFi Network</label>
            <select name='ssid' required>
                <option value=''>Select your WiFi network...</option>
"""
    
    # Add network options
    html = html + network_options
    
    # Continue with rest of form
    html = html + """            </select>
        </div>
        
        <div class='form-group'>
            <label>WiFi Password</label>
            <input name='password' type='password' placeholder='Enter WiFi password'>
        </div>
        
        <div class='form-group'>
            <label>Hub URL</label>
            <input name='hub_url' placeholder='http://<hub-ip>:5001' value='""" + hub_url + """' required>
        </div>
        
        <div class='info'>
            Enter your WiFi and local hub URL. Forex prices will poll hourly from your hub.
        </div>
        
        <input type='submit' value='Save & Connect' class='btn'>
    </form>
    
    <div class='status'>
        Device IP: 192.168.4.1
    </div>
</div>
</body>
</html>"""
    
    return html

HTML_OK = """HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n
<html><head>
<meta name='viewport' content='width=device-width,initial-scale=1'>
<style>
body {
    font-family: Arial;
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100vh;
    margin: 0;
    background: #4CAF50;
}
.msg {
    background: white;
    padding: 30px;
    border-radius: 10px;
    text-align: center;
}
h2 { color: #4CAF50; margin: 0; }
p { color: #666; margin: 10px 0 0 0; }
</style>
</head><body>
<div class='msg'>
    <h2>Success!</h2>
    <p>Configuration saved. Device is restarting...</p>
    <p>Please wait 10 seconds</p>
</div>
</body></html>"""

def _parse_form(body):
    """Parse URL-encoded form data"""
    out = {}
    for pair in body.split('&'):
        if '=' in pair:
            k, v = pair.split('=', 1)
            # URL decode
            v = v.replace('+', ' ')
            v = v.replace('%20', ' ')
            v = v.replace('%3A', ':').replace('%2F', '/').replace('%40', '@')
            v = v.replace('%2D', '-')  # Handle dashes in PROV key
            out[k] = v
    return out

def _parse_query_string(path):
    """Parse query string parameters from URL"""
    params = {}
    if '?' in path:
        query = path.split('?', 1)[1]
        for pair in query.split('&'):
            if '=' in pair:
                k, v = pair.split('=', 1)
                # URL decode
                v = v.replace('%20', ' ')
                v = v.replace('%2D', '-')
                params[k] = v
    return params

def _save_wifi(ssid, password):
    """Save WiFi credentials"""
    try:
        with open('wifi.dat', 'w') as f:
            f.write(ssid + ";" + password)
        print("[PROVISION] Saved WiFi: " + ssid)
        return True
    except Exception as e:
        print("[PROVISION] Failed to save wifi.dat: " + str(e))
        print("[PROVISION] Ensure A1 switch is connected to GND")
        return False

def _save_device_config(hub_url):
    """Save hub configuration and ensure a device_key exists"""
    def _generate_key():
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        return "PROV-" + "".join(random.choice(alphabet) for _ in range(8))

    cfg = {}
    try:
        with open('device_config.json', 'r') as f:
            cfg = json.loads(f.read()) or {}
    except Exception:
        cfg = {}

    if not cfg.get('device_key') and not cfg.get('device_id'):
        cfg['device_key'] = _generate_key()
    cfg.setdefault('device_type', 'matrix_portal_scroll')

    cfg['hub_base_url'] = hub_url
    cfg['provisioned_at'] = time.time()

    try:
        with open('device_config.json', 'w') as f:
            f.write(json.dumps(cfg))
        print("[PROVISION] Saved hub URL:", hub_url)
        print("[PROVISION] Device key:", cfg.get('device_key'))
        return True
    except Exception as e:
        print("[PROVISION] Failed to save device_config.json:", e)
        return False

def start():
    """Start provisioning portal"""
    print("[PROVISION] Starting provisioning portal...")
    
    # Reset radio if needed
    try:
        if wifi.radio.connected:
            wifi.radio.enabled = False
            time.sleep(0.5)
            wifi.radio.enabled = True
    except Exception:
        pass
    
    # Start access point
    if AP_PSK:
        wifi.radio.start_ap(AP_SSID, AP_PSK)
    else:
        wifi.radio.start_ap(AP_SSID)  # Open network
    
    print("[PROVISION] AP started: " + AP_SSID)
    print("[PROVISION] Connect to WiFi and browse to http://192.168.4.1")
    
    # Create socket server
    pool = socketpool.SocketPool(wifi.radio)
    s = pool.socket(pool.AF_INET, pool.SOCK_STREAM)
    s.settimeout(5)  # Increased timeout for better reliability
    s.bind(("0.0.0.0", 80))
    s.listen(1)
    print("[PROVISION] Web server listening on port 80")
    
    while True:
        client = None
        try:
            client, addr = s.accept()
            # CircuitPython uses recv_into instead of recv
            buffer = bytearray(2048)
            num_bytes = client.recv_into(buffer)
            
            if num_bytes == 0:
                if client:
                    client.close()
                continue
            
            # Only decode the bytes we actually received
            req = buffer[:num_bytes]
            text = req.decode('utf-8', 'ignore')
            lines = text.split('\n')
            
            if not lines:
                if client:
                    client.close()
                continue
            
            first = lines[0].strip()
            
            if first.startswith('GET /'):
                # Parse path and query string
                path = first.split(' ')[1]
                params = _parse_query_string(path)
                hub_param = params.get('hub_url', '')
                try:
                    # Seed from existing config if present
                    with open('device_config.json', 'r') as f:
                        cfg = json.loads(f.read())
                        hub_param = hub_param or cfg.get('hub_base_url', '')
                except Exception:
                    pass

                default_hub = hub_param or "http://tickertronixhub.local:5001"
                html = _generate_html_form(default_hub)
                client.send(html.encode('utf-8'))
                
            elif first.startswith('POST /save'):
                # Parse form data
                body = ''
                parts = text.split('\r\n\r\n', 1)
                if len(parts) > 1:
                    body = parts[1]
                
                data = _parse_form(body)
                ssid = data.get('ssid', '').strip()
                password = data.get('password', '').strip()
                hub_url = data.get('hub_url', '').strip()
                
                # Validate inputs
                if not ssid:
                    client.send(b"HTTP/1.1 400 Bad Request\r\n\r\nMissing SSID")
                elif not hub_url:
                    client.send(b"HTTP/1.1 400 Bad Request\r\n\r\nMissing hub URL")
                else:
                    # Save configuration
                    wifi_ok = _save_wifi(ssid, password)
                    key_ok = _save_device_config(hub_url)
                    
                    if wifi_ok and key_ok:
                        client.send(HTML_OK.encode('utf-8'))
                        client.close()
                        print("[PROVISION] Configuration saved successfully")
                        print("[PROVISION] Reloading in 3 seconds...")
                        time.sleep(3)
                        supervisor.reload()
                    else:
                        client.send(b"HTTP/1.1 500 Internal Server Error\r\n\r\nFailed to save configuration")
            
            else:
                client.send(b"HTTP/1.1 404 Not Found\r\n\r\n")
            
            if client:
                client.close()
                
        except OSError as e:
            # Socket timeout and EAGAIN are normal, just continue
            if e.errno == 116 or e.errno == 11:  # ETIMEDOUT or EAGAIN
                continue
            else:
                print("[PROVISION] Socket error: " + str(e))
        except Exception as e:
            print("[PROVISION] Error: " + str(e))
        finally:
            try:
                if client:
                    client.close()
            except:
                pass
            time.sleep(0.01)  # Small delay between requests
