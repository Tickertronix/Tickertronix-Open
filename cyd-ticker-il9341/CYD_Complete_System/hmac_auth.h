#ifndef HMAC_AUTH_H
#define HMAC_AUTH_H

#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <Preferences.h>
#include <mbedtls/md.h>
#include <mbedtls/sha256.h>
#include <mbedtls/base64.h>

// Device credentials structure
struct DeviceCredentials {
  String provisionKey;   // Temporary PROV-XXXX-XXXX-XXXX
  String deviceKey;      // Permanent ESP-XXXX-XXXX
  String hmacSecret;     // 64-char hex for HMAC
  bool isProvisioned;
  String hardwareId;     // ESP32 MAC address

  DeviceCredentials() {
    provisionKey = "";
    deviceKey = "";
    hmacSecret = "";
    isProvisioned = false;
    hardwareId = "";
  }
};

class HMACAuth {
public:
  HMACAuth();

  // Credential management
  void saveCredentials(DeviceCredentials creds);
  DeviceCredentials loadCredentials();
  void clearCredentials();
  String getHardwareId();

  // Configuration
  void setApiBaseUrl(const String& baseUrl);

  // HMAC signature generation
  String generateProvisionSignature(const String& method, const String& path, const String& timestamp, const String& bodyHash, const String& secret);
  String sha256(const String& data);

  // API helpers
  void addProvisionHeaders(HTTPClient& http, const String& method, const String& path, const String& body, const String& deviceKey, const String& secret);
  void addDeviceHeaders(HTTPClient& http, const String& method, const String& path, const String& body, const String& deviceKey, const String& secret);
  String getCurrentTimestamp();

  // Validation
  bool validateProvisionKey(String key);
  String formatProvisionKey(String input);

private:
  Preferences preferences;
  String apiBaseUrl;
  unsigned long cachedEpoch;
  unsigned long epochFetchedAt;
  uint32_t nonceCounter;

  // Internal helpers
  bool computeHmacRaw(const String& key, const String& message, uint8_t* output, size_t outputLen);
  String bytesToHex(const uint8_t* data, size_t length);
  void hexToBytes(String hex, uint8_t* bytes);
  String base64UrlEncode(const uint8_t* data, size_t length);
  unsigned long getCachedEpoch();
  bool syncServerTime();
  unsigned long parseHttpDate(const String& dateHeader);
  unsigned long fallbackEpoch();
  String buildCanonicalPath(const String& path);
  String getDeviceNonce(unsigned long timestamp);
};

// Global instance
extern HMACAuth hmacAuth;

#endif
