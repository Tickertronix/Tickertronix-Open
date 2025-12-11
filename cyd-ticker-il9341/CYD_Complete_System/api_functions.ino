// ========== API FUNCTIONS ==========

bool sendHubHeartbeat() {
  // Only used for local hub mode (no HMAC) to register the CYD as a device
  if (!localHubMode) return false;
  if (!WiFi.isConnected()) {
    Serial.println("[HUB] Heartbeat skipped (no WiFi)");
    return false;
  }

  // Prefer the saved deviceKey; fall back to hardware-derived ID
  String deviceId = credentials.deviceKey;
  if (deviceId.length() == 0) {
    String hw = hmacAuth.getHardwareId();
    if (hw.length() > 0) {
      deviceId = "LOCAL-" + hw;
    }
  }
  if (deviceId.length() == 0) {
    Serial.println("[HUB] Heartbeat skipped (no device id)");
    return false;
  }

  HTTPClient http;
  String url = API_BASE_URL + "/device/" + deviceId + "/heartbeat";
  Serial.println("[HUB] Heartbeat -> " + url);

  if (!http.begin(url)) {
    Serial.println("[HUB] Heartbeat http.begin failed");
    return false;
  }

  http.addHeader("Content-Type", "application/json");
  String payload = "{\"device_type\":\"cyd_il9341\",\"device_name\":\"CYD Display\"}";
  int httpCode = http.POST(payload);
  String response = http.getString();
  http.end();

  Serial.println("[HUB] Heartbeat code: " + String(httpCode));
  if (httpCode != 200) {
    Serial.println("[HUB] Heartbeat response: " + response);
  }

  return httpCode == 200;
}

bool registerDevice(String provKey) {
  if (!WiFi.isConnected()) {
    provisioningError = "No WiFi connection";
    return false;
  }

  hmacAuth.setApiBaseUrl(API_BASE_URL);

  // Update NTP time for accurate timestamps
  Serial.println("[API] Updating NTP time...");
  timeClient.update();
  Serial.println("[API] NTP update complete. Current time: " + String(timeClient.getEpochTime()));

  // Force another update to ensure sync
  timeClient.forceUpdate();
  Serial.println("[API] Forced NTP update. Current time: " + String(timeClient.getEpochTime()));

  Serial.println("[API] Starting device registration with PROV key");

  HTTPClient http;
  http.begin(API_BASE_URL + "/api/v2/provision/register");
  http.addHeader("Content-Type", "application/json");

  // Generate hardware ID from MAC address
  String hardwareId = hmacAuth.getHardwareId();

  // Build JSON payload
  String payload = "{";
  payload += "\"friendly_name\":\"CYD Display\",";
  payload += "\"device_info\":{";
  payload += "\"hardware_id\":\"" + hardwareId + "\",";
  payload += "\"firmware_version\":\"2.0.0\"";
  payload += "}";
  payload += "}";

  // Add HMAC authentication headers using PROV key as both identifier and secret
  Serial.println("[API] Using PROV key: " + provKey);

  hmacAuth.addProvisionHeaders(http, "POST", "/api/v2/provision/register", payload, provKey, provKey);

  Serial.println("[API] Sending registration request...");
  Serial.println("[API] Payload: " + payload);

  int httpCode = http.POST(payload);
  String response = http.getString();

  Serial.println("[API] Response code: " + String(httpCode));
  Serial.println("[API] Response: " + response);

  http.end();

  if (httpCode == 201 || httpCode == 200) {
    // Parse JSON response to extract credentials
    return parseRegistrationResponse(response, provKey);
  } else {
    // Handle error
    if (httpCode == 401) {
      provisioningError = "Invalid or expired code";
    } else if (httpCode == 404) {
      provisioningError = "Code not found";
    } else if (httpCode >= 500) {
      provisioningError = "Server error - try again";
    } else {
      provisioningError = "Network error: " + String(httpCode);
    }
    return false;
  }
}

bool parseRegistrationResponse(String response, String provKey) {
  // Simple JSON parsing (could be improved with ArduinoJson library)
  int deviceKeyStart = response.indexOf("\"device_key\":\"") + 14;
  int deviceKeyEnd = response.indexOf("\"", deviceKeyStart);

  int hmacSecretStart = response.indexOf("\"hmac_secret\":\"") + 15;
  int hmacSecretEnd = response.indexOf("\"", hmacSecretStart);

  if (deviceKeyStart > 13 && deviceKeyEnd > deviceKeyStart &&
      hmacSecretStart > 14 && hmacSecretEnd > hmacSecretStart) {

    String deviceKey = response.substring(deviceKeyStart, deviceKeyEnd);
    String hmacSecret = response.substring(hmacSecretStart, hmacSecretEnd);

    Serial.println("[API] Extracted device_key: " + deviceKey);
    Serial.println("[API] Extracted hmac_secret: " + hmacSecret.substring(0, 8) + "...");

    // Save credentials
    DeviceCredentials creds;
    creds.provisionKey = provKey;
    creds.deviceKey = deviceKey;
    creds.hmacSecret = hmacSecret;
    creds.isProvisioned = true;
    creds.hardwareId = hmacAuth.getHardwareId();

    hmacAuth.saveCredentials(creds);

    // Update global credentials
    credentials = creds;

    Serial.println("[API] Registration successful - credentials saved");
    return true;
  } else {
    provisioningError = "Invalid response format";
    Serial.println("[API] Failed to parse registration response");
    return false;
  }
}

bool fetchTickerData() {
  if (!WiFi.isConnected()) {
    Serial.println("[API] No WiFi connection");
    return false;
  }

  // Register with the hub so the device shows up in /devices
  sendHubHeartbeat();

  // Local hub fetch (no HMAC) -> /prices
  HTTPClient http;
  String url = API_BASE_URL + "/prices";
  Serial.println("[API] Fetching hub prices from: " + url);

  if (!http.begin(url)) {
    Serial.println("[API] Failed to begin HTTP client");
    return false;
  }

  int httpCode = http.GET();
  String response = http.getString();

  Serial.println("[API] Hub response code: " + String(httpCode));

  http.end();

  if (httpCode == 200) {
    return parseHubPrices(response);
  }

  Serial.println("[API] Failed to fetch hub data: " + String(httpCode));
  return false;
}

static String extractJsonString(const String& json, const String& key) {
  String pattern = "\"" + key + "\"";
  int idx = json.indexOf(pattern);
  if (idx == -1) return "";
  idx = json.indexOf(':', idx);
  if (idx == -1) return "";
  idx++;
  while (idx < json.length() && json.charAt(idx) == ' ') {
    idx++;
  }
  if (idx >= json.length() || json.charAt(idx) != '"') {
    return "";
  }
  idx++;
  int end = json.indexOf('"', idx);
  if (end == -1) return "";
  return json.substring(idx, end);
}

static float extractJsonNumber(const String& json, const String& key) {
  String pattern = "\"" + key + "\"";
  int idx = json.indexOf(pattern);
  if (idx == -1) return 0;
  idx = json.indexOf(':', idx);
  if (idx == -1) return 0;
  idx++;
  while (idx < json.length() && json.charAt(idx) == ' ') {
    idx++;
  }
  int end = idx;
  while (end < json.length() && json.charAt(end) != ',' && json.charAt(end) != '}' && json.charAt(end) != ']') {
    end++;
  }
  String value = json.substring(idx, end);
  value.trim();
  if (value.startsWith("\"") && value.endsWith("\"")) {
    value = value.substring(1, value.length() - 1);
  }
  if (value.length() == 0) return 0;
  if (value.equalsIgnoreCase("null")) return 0;
  return value.toFloat();
}

bool parseTickerData(String response) {
  // Clear existing assets
  assetCount = 0;

  Serial.println("[API] Parsing ticker data response...");

  int arrayStart = response.indexOf("\"tickers\"");
  if (arrayStart == -1) {
    Serial.println("[API] No 'tickers' array in response");
    return false;
  }
  arrayStart = response.indexOf('[', arrayStart);
  if (arrayStart == -1) {
    Serial.println("[API] Tickera array missing '['");
    return false;
  }

  int cursor = arrayStart;
  int parsedCount = 0;

  while (parsedCount < RAM_CACHE_SIZE) {
    int objStart = response.indexOf('{', cursor);
    if (objStart == -1) break;
    int objEnd = response.indexOf('}', objStart);
    if (objEnd == -1) break;

    String item = response.substring(objStart, objEnd + 1);

    // Debug: Print the raw JSON item
    Serial.println("[DEBUG] Raw JSON item: " + item.substring(0, min(200, (int)item.length())));

    String ticker = extractJsonString(item, "ticker");
    if (ticker.length() == 0) {
      cursor = objEnd + 1;
      continue;
    }

    float lastPrice = extractJsonNumber(item, "last_price");
    float priceChange = extractJsonNumber(item, "price_change");
    float percentChange = extractJsonNumber(item, "percent_change");
    String tickerType = extractJsonString(item, "ticker_type");

    // Extract baseCurrency for crypto symbols
    String baseCurrency = "";
    if (tickerType == "crypto") {
      baseCurrency = extractJsonString(item, "baseCurrency");

      // If baseCurrency not in API response, extract from ticker
      if (baseCurrency.length() == 0) {
        // Remove USD/USDT/USDC suffix
        if (ticker.endsWith("USDT")) {
          baseCurrency = ticker.substring(0, ticker.length() - 4);
        } else if (ticker.endsWith("USDC")) {
          baseCurrency = ticker.substring(0, ticker.length() - 4);
        } else if (ticker.endsWith("USD")) {
          baseCurrency = ticker.substring(0, ticker.length() - 3);
        } else {
          baseCurrency = ticker;
        }
        Serial.println("[DEBUG] Extracted baseCurrency from ticker: " + baseCurrency);
      } else {
        Serial.println("[DEBUG] Using baseCurrency from API: " + baseCurrency);
      }
    }

    // Use baseCurrency for crypto, full ticker for others
    if (baseCurrency.length() > 0 && tickerType == "crypto") {
      assets[parsedCount].symbol = baseCurrency;  // Use BTC instead of BTCUSD
      Serial.println("[API] Using baseCurrency: " + baseCurrency + " for ticker: " + ticker);
    } else {
      assets[parsedCount].symbol = ticker;  // Use full ticker for stocks/forex
    }

    assets[parsedCount].price = lastPrice;
    assets[parsedCount].change = priceChange;
    assets[parsedCount].changePercent = percentChange;
    assets[parsedCount].type = tickerType.length() > 0 ? tickerType : "stock";
    assets[parsedCount].isValid = true;
    assets[parsedCount].lastUpdate = millis();

    Serial.println("[API] Parsed: " + assets[parsedCount].symbol + " (from " + ticker + ") $" + String(lastPrice) + " (" + String(priceChange, 2) + ") type=" + assets[parsedCount].type);

    parsedCount++;
    cursor = objEnd + 1;
  }

  bool truncated = false;
  if (parsedCount >= RAM_CACHE_SIZE) {
    // If additional objects remain, mark as truncated
    int nextObj = response.indexOf('{', cursor);
    truncated = (nextObj != -1);
  }

  assetCount = parsedCount;
  totalPages = (assetCount + ASSETS_PER_PAGE - 1) / ASSETS_PER_PAGE;
  if (totalPages == 0) {
    totalPages = 1;
  }

  // Always start on page 1 (index 0) when new data loads
  currentAssetPage = 0;

  if (assetCount > 0) {
    Serial.println("[API] Successfully parsed " + String(assetCount) + " tickers");
    if (truncated) {
      Serial.println("[API] Warning: ticker list truncated at RAM cache limit" );
    }
    lastDataUpdate = millis();

    // Reset auto-cycling timer to prevent immediate page switching
    extern unsigned long lastAutoUpdate;
    lastAutoUpdate = millis();
    Serial.println("[API] Reset auto-cycling timer - starting on page 1");

    return true;
  } else {
    Serial.println("[API] No ticker data found in response");
    return false;
  }
}

bool parseHubPrices(String response) {
  assetCount = 0;

  Serial.println("[API] Parsing hub /prices response...");

  int arrayStart = response.indexOf('[');
  if (arrayStart == -1) {
    Serial.println("[API] No array found in response");
    return false;
  }

  int cursor = arrayStart;
  int parsedCount = 0;

  while (parsedCount < RAM_CACHE_SIZE) {
    int objStart = response.indexOf('{', cursor);
    if (objStart == -1) break;
    int objEnd = response.indexOf('}', objStart);
    if (objEnd == -1) break;

    String item = response.substring(objStart, objEnd + 1);

    String ticker = extractJsonString(item, "symbol");
    if (ticker.length() == 0) {
      cursor = objEnd + 1;
      continue;
    }

    String tickerType = extractJsonString(item, "asset_class");
    float lastPrice = extractJsonNumber(item, "last_price");
    float changeAmount = extractJsonNumber(item, "change_amount");
    float changePercent = extractJsonNumber(item, "change_percent");

    assets[parsedCount].symbol = ticker;
    assets[parsedCount].price = lastPrice;
    assets[parsedCount].change = changeAmount;
    assets[parsedCount].changePercent = changePercent;
    assets[parsedCount].type = tickerType.length() > 0 ? tickerType : "stock";
    assets[parsedCount].isValid = true;
    assets[parsedCount].lastUpdate = millis();

    Serial.println("[API] Parsed hub asset: " + ticker + " $" + String(lastPrice) + " (" + String(changePercent, 2) + "%) type=" + assets[parsedCount].type);

    parsedCount++;
    cursor = objEnd + 1;
  }

  // Stable reorder: stocks -> crypto -> forex
  auto classPriority = [](const String& cls) -> int {
    String c = cls;
    c.toLowerCase();
    if (c.startsWith("stock")) return 0;
    if (c == "crypto") return 1;
    if (c == "forex") return 2;
    return 3;
  };

  static Asset sorted[RAM_CACHE_SIZE];  // static to avoid large stack use
  int sortedCount = 0;
  for (int pass = 0; pass < 3; pass++) {
    for (int i = 0; i < parsedCount; i++) {
      if (classPriority(assets[i].type) == pass) {
        sorted[sortedCount++] = assets[i];
      }
    }
  }
  // Copy back
  for (int i = 0; i < sortedCount; i++) {
    assets[i] = sorted[i];
  }

  assetCount = sortedCount;
  totalPages = (assetCount + ASSETS_PER_PAGE - 1) / ASSETS_PER_PAGE;
  if (totalPages == 0) {
    totalPages = 1;
  }
  currentAssetPage = 0;

  if (assetCount > 0) {
    lastDataUpdate = millis();
    extern unsigned long lastAutoUpdate;
    lastAutoUpdate = millis();
    Serial.println("[API] Parsed " + String(assetCount) + " assets from hub");
    return true;
  }

  Serial.println("[API] No assets parsed from hub response");
  return false;
}

// Helper function to update timestamp in HMAC auth
void updateHMACTimestamp() {
  // Override the getCurrentTimestamp function to use NTP client
  if (timeClient.isTimeSet()) {
    // NTP time is available
  } else {
    // Fallback to internal time
    timeClient.update();
  }
}
