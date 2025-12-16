#include "hmac_auth.h"
#include <NTPClient.h>
#include <cstring>
#include <cstdlib>
#include <cstdio>

// Global instance
HMACAuth hmacAuth;

HMACAuth::HMACAuth() : apiBaseUrl(""), cachedEpoch(0), epochFetchedAt(0), nonceCounter(0) {}

void HMACAuth::setApiBaseUrl(const String& baseUrl) {
  apiBaseUrl = baseUrl;
  apiBaseUrl.trim();
  if (apiBaseUrl.endsWith("/")) {
    apiBaseUrl.remove(apiBaseUrl.length() - 1);
  }
}

void HMACAuth::saveCredentials(DeviceCredentials creds) {
  preferences.begin("tickertronix", false);

  preferences.putString("provKey", creds.provisionKey);
  preferences.putString("deviceKey", creds.deviceKey);
  preferences.putString("hmacSecret", creds.hmacSecret);
  preferences.putBool("provisioned", creds.isProvisioned);
  preferences.putString("hardwareId", creds.hardwareId);

  preferences.end();

  Serial.println("[CREDS] Credentials saved to preferences");
}

DeviceCredentials HMACAuth::loadCredentials() {
  DeviceCredentials creds;
  preferences.begin("tickertronix", true);

  creds.provisionKey = preferences.getString("provKey", "");
  creds.deviceKey = preferences.getString("deviceKey", "");
  creds.hmacSecret = preferences.getString("hmacSecret", "");
  creds.isProvisioned = preferences.getBool("provisioned", false);
  creds.hardwareId = preferences.getString("hardwareId", "");

  preferences.end();

  if (creds.hardwareId.isEmpty()) {
    creds.hardwareId = getHardwareId();
    if (creds.isProvisioned) {
      saveCredentials(creds);
    }
  }

  Serial.println("[CREDS] Loaded credentials - Provisioned: " + String(creds.isProvisioned ? "YES" : "NO"));
  if (creds.isProvisioned) {
    Serial.println("[CREDS] Device Key: " + creds.deviceKey);
  }

  return creds;
}

void HMACAuth::clearCredentials() {
  preferences.begin("tickertronix", false);
  preferences.clear();
  preferences.end();

  Serial.println("[CREDS] All credentials cleared");
}

String HMACAuth::getHardwareId() {
  String mac = WiFi.macAddress();
  mac.replace(":", "");
  mac.toUpperCase();
  return mac;
}

String HMACAuth::sha256(const String& data) {
  mbedtls_sha256_context ctx;
  mbedtls_sha256_init(&ctx);
  mbedtls_sha256_starts(&ctx, 0);
  mbedtls_sha256_update(&ctx, (const unsigned char*)data.c_str(), data.length());

  unsigned char hash[32];
  mbedtls_sha256_finish(&ctx, hash);
  mbedtls_sha256_free(&ctx);

  return bytesToHex(hash, sizeof(hash));
}

bool HMACAuth::computeHmacRaw(const String& key, const String& message, uint8_t* output, size_t outputLen) {
  if (outputLen < 32) {
    return false;
  }

  const mbedtls_md_info_t* md_info = mbedtls_md_info_from_type(MBEDTLS_MD_SHA256);
  if (!md_info) {
    Serial.println("[HMAC] Failed to get MD info");
    return false;
  }

  int result = mbedtls_md_hmac(md_info,
                               (const unsigned char*)key.c_str(), key.length(),
                               (const unsigned char*)message.c_str(), message.length(),
                               output);
  if (result != 0) {
    Serial.println("[HMAC] Failed to generate HMAC: " + String(result));
    return false;
  }
  return true;
}

String HMACAuth::generateProvisionSignature(const String& method,
                                            const String& path,
                                            const String& timestamp,
                                            const String& bodyHash,
                                            const String& secret) {
  String canonical = method + "\\n" + path + "\\n" + timestamp + "\\n" + bodyHash;
  Serial.println("[HMAC] Canonical string (escaped newlines): " + canonical);

  uint8_t hmacBytes[32];
  if (!computeHmacRaw(secret, canonical, hmacBytes, sizeof(hmacBytes))) {
    return "";
  }

  String signature = bytesToHex(hmacBytes, sizeof(hmacBytes));
  Serial.println("[HMAC] Generated signature: " + signature);
  return signature;
}

String HMACAuth::buildCanonicalPath(const String& path) {
  if (path.startsWith("/api/v2")) {
    return path.substring(4);
  }
  return path;
}

String HMACAuth::base64UrlEncode(const uint8_t* data, size_t length) {
  size_t outLen = 0;
  unsigned char buffer[72];
  if (mbedtls_base64_encode(buffer, sizeof(buffer), &outLen, data, length) != 0 || outLen >= sizeof(buffer)) {
    return "";
  }

  buffer[outLen] = '\0';
  String encoded = String((char*)buffer);
  encoded.replace("+", "-");
  encoded.replace("/", "_");
  while (encoded.endsWith("=")) {
    encoded.remove(encoded.length() - 1);
  }
  return encoded;
}

String HMACAuth::getDeviceNonce(unsigned long timestamp) {
  nonceCounter = (nonceCounter + 1) & 0xFFFFFFFF;
  char buffer[17];
  snprintf(buffer, sizeof(buffer), "%08lx%08lx", (unsigned long)(timestamp & 0xFFFFFFFF), (unsigned long)nonceCounter);
  return String(buffer);
}

void HMACAuth::addProvisionHeaders(HTTPClient& http,
                                   const String& method,
                                   const String& path,
                                   const String& body,
                                   const String& deviceKey,
                                   const String& secret) {
  String timestamp = getCurrentTimestamp();
  String bodyHash = body.length() > 0 ? sha256(body) : sha256("");
  String canonicalPath = buildCanonicalPath(path);

  Serial.println("[HMAC] Body: " + body);
  Serial.println("[HMAC] Body hash: " + bodyHash);
  Serial.println("[HMAC] Secret: " + secret);
  Serial.println("[HMAC] Original path: " + path + " -> Canonical path: " + canonicalPath);

  String signature = generateProvisionSignature(method, canonicalPath, timestamp, bodyHash, secret);

  http.addHeader("x-device-key", deviceKey);
  http.addHeader("x-ttx-ts", timestamp);
  http.addHeader("x-ttx-sig", signature);

  Serial.println("[HMAC] Provision headers added - Device: " + deviceKey + ", TS: " + timestamp);
}

void HMACAuth::addDeviceHeaders(HTTPClient& http,
                                const String& method,
                                const String& path,
                                const String& body,
                                const String& deviceKey,
                                const String& secret) {
  (void)method;
  (void)path;
  (void)body;

  String timestamp = getCurrentTimestamp();
  unsigned long tsValue = strtoul(timestamp.c_str(), nullptr, 10);
  String nonce = getDeviceNonce(tsValue);

  String message = deviceKey + "." + timestamp + "." + nonce;
  uint8_t hmacBytes[32];
  if (!computeHmacRaw(secret, message, hmacBytes, sizeof(hmacBytes))) {
    Serial.println("[HMAC] Failed to compute device signature");
    return;
  }

  String signature = base64UrlEncode(hmacBytes, sizeof(hmacBytes));

  http.addHeader("X-Device-Key", deviceKey);
  http.addHeader("X-Device-Ts", timestamp);
  http.addHeader("X-Device-Nonce", nonce);
  http.addHeader("X-Device-Sig", signature);

  Serial.println("[HMAC] Device headers added - Key: " + deviceKey + ", TS: " + timestamp + ", Nonce: " + nonce);
}

unsigned long HMACAuth::getCachedEpoch() {
  if (cachedEpoch == 0 || epochFetchedAt == 0) {
    return 0;
  }
  unsigned long nowMs = millis();
  unsigned long elapsed = nowMs >= epochFetchedAt ? (nowMs - epochFetchedAt) : 0;
  unsigned long advanced = cachedEpoch + (elapsed / 1000);

  if (elapsed <= 600000UL) { // 10 minute cache window
    return advanced;
  }
  return 0;
}

unsigned long HMACAuth::fallbackEpoch() {
  extern NTPClient timeClient;
  unsigned long ntpTime = timeClient.getEpochTime();
  time_t systemTime = time(nullptr);
  bool ntpIsSet = timeClient.isTimeSet();

  Serial.println("[HMAC] Fallback epoch - NTP set: " + String(ntpIsSet) + ", NTP time: " + String(ntpTime) + ", system time: " + String(systemTime));

  if (ntpIsSet && ntpTime > 1000000000UL) {
    return ntpTime;
  }
  if (systemTime > 1000000000UL) {
    return (unsigned long)systemTime;
  }
  return (unsigned long)(millis() / 1000);
}

unsigned long HMACAuth::parseHttpDate(const String& dateHeader) {
  if (dateHeader.length() < 29) {
    return 0;
  }

  char monthStr[4] = {0};
  int day = 0, year = 0, hour = 0, minute = 0, second = 0;
  if (sscanf(dateHeader.c_str(), "%*3s, %d %3s %d %d:%d:%d", &day, monthStr, &year, &hour, &minute, &second) != 6) {
    return 0;
  }

  const char* months = "JanFebMarAprMayJunJulAugSepOctNovDec";
  int month = 0;
  for (int i = 0; i < 12; i++) {
    if (strncmp(monthStr, months + (i * 3), 3) == 0) {
      month = i + 1;
      break;
    }
  }
  if (month == 0) {
    return 0;
  }

  auto isLeap = [](int y) {
    return (y % 4 == 0) && ((y % 100 != 0) || (y % 400 == 0));
  };

  static const int monthDays[12] = {31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};
  unsigned long days = 0;
  for (int y = 1970; y < year; y++) {
    days += isLeap(y) ? 366UL : 365UL;
  }
  for (int m = 1; m < month; m++) {
    if (m == 2 && isLeap(year)) {
      days += 29UL;
    } else {
      days += monthDays[m - 1];
    }
  }
  days += (unsigned long)(day - 1);

  unsigned long epoch = days * 86400UL + (unsigned long)hour * 3600UL + (unsigned long)minute * 60UL + (unsigned long)second;
  return epoch;
}

bool HMACAuth::syncServerTime() {
  if (apiBaseUrl.length() == 0 || WiFi.status() != WL_CONNECTED) {
    return false;
  }

  String healthUrl = apiBaseUrl;
  if (healthUrl.endsWith("/api/v2")) {
    healthUrl += "/health";
  } else if (healthUrl.endsWith("/api/v2/")) {
    healthUrl += "health";
  } else {
    healthUrl += "/api/v2/health";
  }

  HTTPClient http;
  http.setReuse(false);

  if (!http.begin(healthUrl)) {
    Serial.println("[TIME] Failed to begin health request: " + healthUrl);
    return false;
  }

  const char* headerKeys[] = {"Date", "date"};
  http.collectHeaders(headerKeys, 2);

  int code = http.GET();
  if (code != 200) {
    Serial.println("[TIME] Health request failed: " + String(code));
    http.end();
    return false;
  }

  String dateHeader = http.header("Date");
  if (dateHeader.length() == 0) {
    dateHeader = http.header("date");
  }

  unsigned long epoch = parseHttpDate(dateHeader);
  http.end();

  if (epoch == 0) {
    Serial.println("[TIME] Failed to parse Date header: " + dateHeader);
    return false;
  }

  cachedEpoch = epoch;
  epochFetchedAt = millis();
  Serial.println("[TIME] Synced epoch from server: " + String(epoch));
  return true;
}

String HMACAuth::getCurrentTimestamp() {
  unsigned long epoch = getCachedEpoch();
  if (epoch == 0) {
    if (syncServerTime()) {
      epoch = getCachedEpoch();
    }
  }

  if (epoch == 0) {
    epoch = fallbackEpoch();
  }

  return String(epoch);
}

String HMACAuth::bytesToHex(const uint8_t* data, size_t length) {
  String hex = "";
  for (size_t i = 0; i < length; i++) {
    if (data[i] < 16) hex += "0";
    hex += String(data[i], HEX);
  }
  hex.toLowerCase();
  return hex;
}

void HMACAuth::hexToBytes(String hex, uint8_t* bytes) {
  for (size_t i = 0; i < hex.length(); i += 2) {
    String byteString = hex.substring(i, i + 2);
    bytes[i / 2] = (uint8_t)strtol(byteString.c_str(), NULL, 16);
  }
}

bool HMACAuth::validateProvisionKey(String key) {
  if (key.length() != 19) return false;
  if (!key.startsWith("PROV-")) return false;

  if (key.charAt(9) != '-' || key.charAt(14) != '-') return false;

  String segments[3] = {
    key.substring(5, 9),
    key.substring(10, 14),
    key.substring(15, 19)
  };

  for (int i = 0; i < 3; i++) {
    for (int j = 0; j < 4; j++) {
      char c = segments[i].charAt(j);
      if (!isAlphaNumeric(c)) return false;
    }
  }

  return true;
}

String HMACAuth::formatProvisionKey(String input) {
  String clean = input;
  clean.replace("-", "");
  clean.toUpperCase();

  if (!clean.startsWith("PROV")) {
    clean = "PROV" + clean;
  }

  if (clean.length() >= 16) {
    String formatted = clean.substring(0, 4) + "-" +
                       clean.substring(4, 8) + "-" +
                       clean.substring(8, 12) + "-" +
                       clean.substring(12, 16);
    if (formatted.length() > 19) {
      formatted = formatted.substring(0, 19);
    }
    return formatted;
  }

  return clean;
}
