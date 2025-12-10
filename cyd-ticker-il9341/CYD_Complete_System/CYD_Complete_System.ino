#include <WiFi.h>
#include <HTTPClient.h>
#include <TFT_eSPI.h>
#include <SPI.h>
#include <Preferences.h>
#include <SD.h>
#include <WiFiUdp.h>
#include <NTPClient.h>
#include <mbedtls/md.h>
#include <mbedtls/sha256.h>
#include "hmac_auth.h"

// Fix for newer ESP32 Arduino Core
#ifndef VSPI
#define VSPI SPI
#endif

// CYD touchscreen pins - VSPI (working configuration)
#define XPT2046_IRQ 36
#define XPT2046_MOSI 32
#define XPT2046_MISO 39
#define XPT2046_CLK 25
#define XPT2046_CS 33

// SD Card pins
#define SD_CS 5
#define SD_MOSI 23
#define SD_MISO 19
#define SD_SCK 18

TFT_eSPI tft = TFT_eSPI();
SPIClass touchSPI(VSPI);
Preferences preferences;

// Touch calibration coefficients (will be calculated during calibration)
struct TouchCalibration {
  float alphaX, betaX, deltaX;  // X transformation coefficients
  float alphaY, betaY, deltaY;  // Y transformation coefficients
  bool isCalibrated;            // Calibration status
};

TouchCalibration touchCal = {0, 0, 0, 0, 0, 0, false};

// Calibration points (screen coordinates)
const int calibPoints[6][2] = {
  {40, 40},    // Top-left
  {280, 40},   // Top-right  
  {160, 120},  // Center
  {40, 200},   // Bottom-left
  {280, 200},  // Bottom-right
  {160, 200}   // Bottom-center
};

// Colors - EXACT original CYD values (no modifications needed with correct TFT_eSPI config)
#define BG_COLOR TFT_BLACK
#define TEXT_COLOR TFT_WHITE
#define GREEN_COLOR TFT_GREEN
#define RED_COLOR TFT_RED
#define BLUE_COLOR TFT_CYAN
#define YELLOW_COLOR TFT_YELLOW
#define ORANGE_COLOR TFT_ORANGE
#define BORDER_COLOR TFT_DARKGREY
#define KEY_COLOR TFT_DARKGREY
#define KEY_PRESSED_COLOR TFT_CYAN
#define SUCCESS_COLOR TFT_GREEN
#define ERROR_COLOR TFT_RED
#define SELECTED_COLOR TFT_BLUE

// Additional color definitions for compatibility
#define WHITE TFT_WHITE
#define BLACK TFT_BLACK
#define LIGHT_GRAY TFT_LIGHTGREY
#define LIGHT_BLUE TFT_CYAN

// New UI colors - EXACT original CYD values
#define DARK_BLUE 0x0014        // Darker blue for top bar
#define BUTTON_GRAY 0x4208      // Medium gray for buttons
#define BUTTON_GREEN 0x2444     // Dark green for active buttons
#define BUTTON_ORANGE 0xC320    // Orange for settings button
#define DARK_GREEN 0x0200       // Dark green for positive change background
#define DARK_RED 0x8000         // Dark red for negative change background

// API Configuration (local hub default)
String API_BASE_URL = "http://tickertronixhub.local:5001";
bool localHubMode = true;  // When true, talk to the LAN hub (no cloud/HMAC)

// Device credentials (loaded from preferences)
DeviceCredentials credentials;

// NTP Client for timestamps
WiFiUDP ntpUDP;
NTPClient timeClient(ntpUDP, "pool.ntp.org", 0, 60000);

// Financial data structure
struct Asset {
  String symbol;
  String name;
  float price;
  float change;
  float changePercent;
  String type; // "stock", "crypto", "forex"
  bool isValid;
  unsigned long lastUpdate;
};

// Asset tracking with SD card support
const int MAX_ASSETS = 200; // Increased for SD card storage
const int RAM_CACHE_SIZE = 200; // Assets cached in RAM
Asset assets[RAM_CACHE_SIZE];
int assetCount = 0;
bool sdCardAvailable = false;

// App states
enum AppState {
  TOUCH_CALIBRATION,
  WIFI_SETUP,
  PROVISIONING_CHECK,
  PROVISIONING_ENTRY,
  PROVISIONING_ACTIVATE,
  PROVISIONING_ERROR,
  TICKER_APP
};
AppState currentAppState = TOUCH_CALIBRATION;

// WiFi states
enum WiFiState {
  WIFI_SCAN,
  NETWORK_SELECT,
  PASSWORD_ENTRY,
  CONNECTING,
  WIFI_SUCCESS,
  WIFI_ERROR
};
WiFiState currentWiFiState = WIFI_SCAN;

// Non-blocking WiFi connection variables
unsigned long wifiConnectionStart = 0;
int wifiConnectionAttempts = 0;
const int MAX_WIFI_ATTEMPTS = 30;
const unsigned long WIFI_ATTEMPT_INTERVAL = 500; // ms between attempts

// Ticker display states
enum TickerState {
  TICKER_GRID,           // Grid view of 9 assets
  TICKER_SINGLE,         // Single asset full screen
  TICKER_SETTINGS,       // Settings menu
  TICKER_DEVICE_SETTINGS // Device settings menu
};
TickerState currentTickerState = TICKER_GRID;

// Display modes
enum DisplayMode {
  MODE_GRID,
  MODE_SINGLE
};
DisplayMode displayMode = MODE_GRID;
bool isTemporarySingleView = false;  // Distinguishes between single mode and temporary single view

// Network scanning variables
int networkCount = 0;
String ssidList[20];
int rssiList[20];
int encryptionList[20];
int currentPage = 0;
const int networksPerPage = 6;

// Touch variables
bool isTouched = false;
int touchX = 0;
int touchY = 0;
unsigned long lastTouchTime = 0;
const int debounceDelay = 50; // Further reduced for testing
unsigned long lastModeSwitch = 0;  // Track last auto/manual switch
const unsigned long MODE_SWITCH_DELAY = 1000;  // Minimum 1 second between mode switches
unsigned long lastAssetNavigation = 0;  // Track last single asset navigation
bool touchProcessed = false;  // Flag to ensure one touch = one action
bool touchCurrentlyPressed = false;  // Track if touch is currently active
unsigned long touchReleaseTime = 0;  // When touch was last released
const unsigned long TOUCH_RELEASE_DELAY = 5;    // Ultra-ultra-responsive for production use
bool navigationPerformed = false;  // Flag to prevent multiple navigation per touch
unsigned long globalTouchLockout = 0;  // Global lockout after navigation
const unsigned long GLOBAL_LOCKOUT_DURATION = 100;   // Minimal lockout for maximum responsiveness
// Stuck touch detection
int lastTouchX = -1;
int lastTouchY = -1;
unsigned long sameCoordinateCount = 0;
const unsigned long MAX_SAME_COORDINATE_COUNT = 3;  // Max consecutive same coordinate detections

// Selected network and password
String selectedSSID = "";
String enteredPassword = "";
int selectedNetwork = -1;

// Keyboard layout (includes numbers now)
const char* keyboardKeys[] = {
  "1", "2", "3", "4", "5", "6", "7", "8", "9", "0",
  "q", "w", "e", "r", "t", "y", "u", "i", "o", "p",
  "a", "s", "d", "f", "g", "h", "j", "k", "l",
  "z", "x", "c", "v", "b", "n", "m", "@", ".",
  "Space", "Delete", "Done"
};

const int keyboardRows = 5;
const int keyboardCols[] = {10, 10, 9, 9, 3};
int keyboardPage = 0;

// Provisioning variables
String enteredProvisionKey = "";
bool provisioningInProgress = false;
String provisioningError = "";
unsigned long provisioningStartTime = 0;

// Keyboard debouncing variables
unsigned long lastKeyPressTime = 0;
const unsigned long KEYBOARD_DEBOUNCE_DELAY = 150; // Reduced to 150ms between key presses
const unsigned long SAME_KEY_DEBOUNCE_DELAY = 300; // 300ms for same key to prevent repeats
bool keyCurrentlyPressed = false;
String lastPressedKey = "";
unsigned long keyPressStartTime = 0;

// Touch context for debouncing
enum TouchContext {
  TOUCH_NAVIGATION,  // Fast response for navigation (10ms)
  TOUCH_KEYBOARD,    // Slower response for keyboard input (50ms)
  TOUCH_GENERAL      // Default response (25ms)
};
TouchContext currentTouchContext = TOUCH_GENERAL;

// Device settings dialog states
enum DeviceDialogState {
  DIALOG_NONE,
  DIALOG_REPROVISION,
  DIALOG_CLEAR_DATA,
  DIALOG_FINAL_ERASE
};
DeviceDialogState currentDialogState = DIALOG_NONE;

// Auto/Manual mode for ticker
bool autoMode = true;
bool autoModePaused = false;  // Temporarily pause auto cycling when viewing single ticker
unsigned long lastAutoUpdate = 0;
int autoInterval = 5000; // 5 seconds default, adjustable in settings

// Calibration variables
int currentCalibPoint = 0;
int touchSamples[6][100][2]; // Store 100 samples per calibration point
int sampleCount = 0;
bool collectingSamples = false;
unsigned long lastDataUpdate = 0;
const unsigned long DATA_UPDATE_INTERVAL = 300000; // 5 minutes
int currentAssetPage = 0;
int totalPages = 0;
int currentSingleAsset = 0; // For single asset mode

// Pagination
const int ASSETS_PER_PAGE = 9;

// Tickertronix logo bitmap array (200x86)
const unsigned char tickertronix_logo[] PROGMEM = {
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x1f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x1f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00
};

// Forward declarations
void setupTouch();
uint16_t readTouchRaw(uint8_t command);
bool getTouchPoint(int &x, int &y);
bool getTouchPoint(int &x, int &y, TouchContext context);
void scanNetworks();
void showNetworkList();
void showPasswordEntry();
void showConnectionStatus(bool isConnecting);
void connectToNetwork();
void drawKey(int row, int col, const char* label, bool pressed = false);
void handleNetworkListTouch();
void handlePasswordEntryTouch();
void loadWiFiCredentials();
void saveWiFiCredentials();
void clearWiFiCredentials();
void handleWiFiConfig();
void handleWiFiConnection();
void showTickerApp();
void drawAssetGrid();
void updateGridOnly();  // Efficient grid update without redrawing top bar
void drawAssetCell(int x, int y, int width, int height, int index);
void fetchTickerDataLegacy();
void handleTickerApp();
void updateLocalData(String jsonData);
void showBootScreen();
void drawSingleAsset();
void drawSettingsMenu();
void handleSettingsTouch();
String formatPrice(float price, String assetType);
String formatForexPair(String symbol);

// Calibration functions
void startTouchCalibration();
void showCalibrationPoint();
void handleCalibrationTouch();
void calculateCalibrationCoefficients();
void saveCalibration();
void loadCalibration();
int applyCalibratedTouch(int rawX, int rawY, int &screenX, int &screenY);

// Touch coordinate transform
void getTouchCoordinates(int &x, int &y) {
  // Fix the coordinate transform - Y was inverted
  int temp = x;
  x = y;
  y = temp;  // Don't invert, just swap
}

// Touch raw SPI read function
uint16_t readTouchRaw(uint8_t command) {
  touchSPI.beginTransaction(SPISettings(2500000, MSBFIRST, SPI_MODE0));
  digitalWrite(XPT2046_CS, LOW);
  delayMicroseconds(10);
  
  touchSPI.transfer(command);
  uint16_t data = touchSPI.transfer16(0);
  
  digitalWrite(XPT2046_CS, HIGH);
  touchSPI.endTransaction();
  
  return data >> 3;  // Remove the 3 lowest bits
}

bool getTouchPoint(int &x, int &y) {
  // Check IRQ pin first - it should be LOW when touched
  bool irqActive = (digitalRead(XPT2046_IRQ) == LOW);
  
  // Track IRQ stuck state and low pressure count
  static unsigned long irqStuckStartTime = 0;
  static bool irqWasLow = false;
  static int consecutiveLowPressureCount = 0;
  
  if (!irqActive) {
    // IRQ is HIGH - normal release
    if (touchCurrentlyPressed) {
      touchCurrentlyPressed = false;
      touchProcessed = false;
      navigationPerformed = false;
      touchReleaseTime = millis();
      sameCoordinateCount = 0;
      lastTouchX = -1;
      lastTouchY = -1;
      // CRITICAL: Invalidate cached touch coordinates to prevent stale navigation
      touchX = -1;
      touchY = -1;
      Serial.println("Touch released (IRQ HIGH)");
    }
    irqStuckStartTime = 0;  // Reset stuck timer
    irqWasLow = false;
    consecutiveLowPressureCount = 0;
    return false;
  }
  
  // IRQ is LOW - read pressure first to check if it's stuck
  uint16_t rawZ1 = readTouchRaw(0xB0);  // Read Z1 pressure
  uint16_t rawZ2 = readTouchRaw(0xC0);  // Read Z2 pressure
  
  // Check if pressure indicates real touch - RELAXED thresholds for better detection
  // Your readings show Z1=146-161, Z2=2240-2752 which should be valid
  bool pressureIndicatesRealTouch = (rawZ1 > 100 && rawZ2 > 300 && rawZ1 < 4000 && rawZ2 < 4000);
  
  if (!pressureIndicatesRealTouch) {
    consecutiveLowPressureCount++;
    // STILL try to read coordinates for marginal touches - your Z1=146-161 should work
    Serial.print("Marginal pressure but reading coordinates anyway: Z1=");
    Serial.print(rawZ1); Serial.print(" Z2="); Serial.println(rawZ2);
  } else {
    consecutiveLowPressureCount = 0;  // Reset counter for good pressure
    Serial.print("Good pressure detected: Z1=");
    Serial.print(rawZ1); Serial.print(" Z2="); Serial.println(rawZ2);
  }
  
  // IRQ stuck detection - only trigger when we have consistently low pressure
  if (!irqWasLow) {
    irqStuckStartTime = millis();  // Start timing this LOW period
    irqWasLow = true;
    consecutiveLowPressureCount = 0;
  } else if (consecutiveLowPressureCount > 10 && millis() - irqStuckStartTime > 500) {
    // IRQ has been stuck LOW with bad pressure for too long - force reset
    static int resetCount = 0;
    resetCount++;
    Serial.print("*** IRQ STUCK LOW - HARDWARE RESET #");
    Serial.print(resetCount);
    Serial.println(" ***");
    
    // Comprehensive touch controller reset
    digitalWrite(XPT2046_CS, HIGH);  // Deselect
    delay(10);
    touchSPI.end();                  // End SPI
    delay(50);                       // Reduced delay
    
    // Reinitialize SPI and pins
    touchSPI.begin(XPT2046_CLK, XPT2046_MISO, XPT2046_MOSI, XPT2046_CS);
    pinMode(XPT2046_IRQ, INPUT);     // Reinit IRQ pin
    pinMode(XPT2046_CS, OUTPUT);
    digitalWrite(XPT2046_CS, HIGH);
    
    // Try to clear any stuck commands by sending dummy reads
    delay(10);
    readTouchRaw(0x80);  // Dummy read to clear controller state
    readTouchRaw(0x80);  // Second dummy read
    delay(10);
    
    // Reset all touch state
    touchCurrentlyPressed = false;
    touchProcessed = false;
    navigationPerformed = false;
    touchReleaseTime = millis();
    sameCoordinateCount = 0;
    lastTouchX = -1;
    lastTouchY = -1;
    // CRITICAL: Invalidate cached touch coordinates
    touchX = -1;
    touchY = -1;
    irqStuckStartTime = 0;
    irqWasLow = false;
    consecutiveLowPressureCount = 0;
    
    Serial.println("Touch controller reset complete - ready for next touch");
    // Force a small delay to let hardware settle before next touch attempt
    delay(20);
    return false;
  }
  
  // DEBUG: Only show pressure status occasionally and when values change significantly
  static unsigned long lastPressureLog = 0;
  static uint16_t lastZ1 = 0, lastZ2 = 0;
  
  if (millis() - lastPressureLog > 5000 ||  // Every 5 seconds max
      abs((int)rawZ1 - (int)lastZ1) > 100 || abs((int)rawZ2 - (int)lastZ2) > 100) {  // Or significant change
    Serial.print("IRQ=LOW for "); Serial.print(millis() - irqStuckStartTime); 
    Serial.print("ms, PRESSURE: Z1="); Serial.print(rawZ1); Serial.print(" Z2="); Serial.println(rawZ2);
    lastPressureLog = millis();
    lastZ1 = rawZ1;
    lastZ2 = rawZ2;
  }
  
  // MODIFIED: Always try to read coordinates - your Z1=146-161 readings are valid!
  // Only skip coordinate reading for EXTREMELY bad pressure (like Z1 < 50)
  bool extremelyBadPressure = (rawZ1 < 50 || rawZ2 < 100 || rawZ1 > 4000 || rawZ2 > 4000);
  
  if (extremelyBadPressure) {
    // Truly no touch detected - handle release
    if (touchCurrentlyPressed) {
      touchCurrentlyPressed = false;
      touchProcessed = false;
      navigationPerformed = false;  // Reset navigation flag on touch release
      touchReleaseTime = millis();
      // Reset stuck detection
      sameCoordinateCount = 0;
      lastTouchX = -1;
      lastTouchY = -1;
      // CRITICAL: Invalidate cached touch coordinates to prevent stale navigation
      touchX = -1;
      touchY = -1;
      Serial.println("Touch released (extremely bad pressure)");
    }
    return false;
  }
  
  // Continue with coordinate reading even with marginal pressure
  Serial.println("Proceeding with coordinate reading despite marginal pressure");
  
  // Touch is detected
  if (!touchCurrentlyPressed) {
    // This is a new touch press - MINIMAL delay for ultra responsiveness
    if (millis() - touchReleaseTime < TOUCH_RELEASE_DELAY) {
      // Very short delay for production use
      Serial.println("Touch too soon after release, ignoring");
      return false;
    }
    touchCurrentlyPressed = true;
    touchProcessed = false;
    navigationPerformed = false;  // Reset navigation flag for new touch
    Serial.println("New touch press detected");
  } else {
    // Touch is being held - ALLOW CONTINUOUS PROCESSING for ultra-responsiveness
    // No restrictions on held touches for production use
    Serial.println("Touch being held - allowing continuous processing");
  }
  
  // Now read X and Y coordinates
  uint16_t rawX = readTouchRaw(0xD0);  // Read X
  uint16_t rawY = readTouchRaw(0x90);  // Read Y
  
  // DEBUG: Always show raw coordinates when touch is detected
  Serial.print("RAW COORDS: X="); Serial.print(rawX); Serial.print(" Y="); Serial.println(rawY);
  
  // Basic bounds check
  if (rawX < 300 || rawX > 3800 || rawY < 300 || rawY > 3800) {
    Serial.println("Coordinates out of bounds");
    return false;
  }
  
  // Context-aware debouncing for different UI elements
  unsigned long debounceDelay;
  switch (currentTouchContext) {
    case TOUCH_NAVIGATION:
      debounceDelay = 10;  // Fast for navigation
      break;
    case TOUCH_KEYBOARD:
      debounceDelay = 50;  // Slower for keyboard to prevent double-entry
      break;
    case TOUCH_GENERAL:
    default:
      debounceDelay = 25;  // Balanced for general UI
      break;
  }

  if (millis() - lastTouchTime < debounceDelay) {
    return false;
  }
  
  lastTouchTime = millis();
  touchProcessed = true;  // Mark this touch as processed
  
  // Use calibrated touch if available
  if (touchCal.isCalibrated) {
    if (applyCalibratedTouch(rawX, rawY, touchX, touchY)) {
      x = touchX;
      y = touchY;
    } else {
      return false;
    }
  } else {
    // Raw coordinates for calibration mode
    x = rawX;
    y = rawY;
  }
  
  // Single unified stuck touch detection
  if (x == lastTouchX && y == lastTouchY) {
    sameCoordinateCount++;
    if (sameCoordinateCount > MAX_SAME_COORDINATE_COUNT) {
      Serial.println("STUCK TOUCH DETECTED - FULL RESET (" + String(x) + "," + String(y) + ")");
      // Complete state reset
      touchCurrentlyPressed = false;
      touchProcessed = false;
      navigationPerformed = false;
      touchReleaseTime = millis();
      globalTouchLockout = 0;
      sameCoordinateCount = 0;
      lastTouchX = -1;
      lastTouchY = -1;
      return false;
    }
  } else {
    sameCoordinateCount = 0;
    lastTouchX = x;
    lastTouchY = y;
  }
  
  return true;
}

// Overloaded version with context-aware debouncing
bool getTouchPoint(int &x, int &y, TouchContext context) {
  TouchContext previousContext = currentTouchContext;
  currentTouchContext = context;
  bool result = getTouchPoint(x, y);
  currentTouchContext = previousContext;
  return result;
}

void setupTouch() {
  Serial.println("Setting up touchscreen...");
  
  pinMode(XPT2046_IRQ, INPUT);
  pinMode(XPT2046_CS, OUTPUT);
  digitalWrite(XPT2046_CS, HIGH);
  
  touchSPI.begin(XPT2046_CLK, XPT2046_MISO, XPT2046_MOSI, XPT2046_CS);
  
  Serial.println("Touch setup complete");
}

// Price formatting function
String formatPrice(float price, String assetType) {
  if (assetType == "stock") {
    return String("$") + String(price, 2);
  } else if (assetType == "crypto") {
    if (price >= 100000) {
      return String("$") + String(price, 0);
    } else if (price >= 10000) {
      return String("$") + String(price, 0);
    } else {
      return String("$") + String(price, 2);
    }
  } else if (assetType == "forex") {
    return String(price, 2);  // Reduced from 4 to 2 decimal places
  }
  return String("$") + String(price, 2);
}

// Boot screen with logo
void showBootScreen() {
  Serial.println("Boot screen: Filling screen with background");
  tft.fillScreen(BG_COLOR);

  Serial.println("Boot screen: Setting text color");
  tft.setTextColor(TEXT_COLOR);

  Serial.println("Boot screen: Drawing title");
  tft.drawCentreString("TICKERTRONIX", 160, 80, 4);

  Serial.println("Boot screen: Drawing version");
  tft.setTextColor(BORDER_COLOR);
  tft.drawCentreString("CYD Display v2.0", 160, 140, 2);
  tft.drawCentreString("Initializing...", 160, 180, 1);

  Serial.println("Boot screen: Delaying");
  delay(3000);
  Serial.println("Boot screen: Complete");
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("=== CYD Complete System ===");

  // Load device credentials
  credentials = hmacAuth.loadCredentials();
  // Treat device as provisioned when using the local hub (no cloud auth)
  if (localHubMode) {
    if (!credentials.isProvisioned) {
      credentials.isProvisioned = true;
      credentials.deviceKey = credentials.deviceKey.length() > 0 ? credentials.deviceKey : "LOCAL-" + hmacAuth.getHardwareId();
      credentials.hmacSecret = "localhub";
      hmacAuth.saveCredentials(credentials);
      Serial.println("[LOCAL HUB] Marked device as provisioned for LAN hub");
    }
  }
  hmacAuth.setApiBaseUrl(API_BASE_URL);

  // Initialize display
  Serial.println("Initializing display...");
  tft.init();
  Serial.println("Display init complete");

  tft.setRotation(1);  // Landscape mode
  Serial.println("Display rotation set to 1");

  // Test with a simple colored rectangle to verify display is working
  tft.fillRect(10, 10, 50, 50, TFT_RED);
  tft.fillRect(270, 10, 50, 50, TFT_GREEN);
  tft.fillRect(10, 180, 50, 50, TFT_BLUE);
  tft.fillRect(270, 180, 50, 50, TFT_YELLOW);
  Serial.println("Test rectangles drawn");

  tft.fillScreen(BG_COLOR);
  Serial.println("Display filled with background color");

  // Turn on backlight - try multiple pins for different CYD variants
  pinMode(21, OUTPUT);
  digitalWrite(21, HIGH);
  pinMode(27, OUTPUT);  // Alternative backlight pin
  digitalWrite(27, HIGH);
  Serial.println("Backlight enabled on pins 21 and 27");

  // Show boot screen with logo
  Serial.println("Showing boot screen...");
  showBootScreen();
  Serial.println("Boot screen complete");
  
  // Initialize touch
  setupTouch();

  // Load calibration data
  loadCalibration();

  // Check if touch calibration exists
  if (!touchCal.isCalibrated) {
    Serial.println("No touch calibration found, starting calibration...");
    currentAppState = TOUCH_CALIBRATION;
    startTouchCalibration();
    return; // Skip the rest of setup until calibration is complete
  }

  Serial.println("Touch calibration loaded successfully");
  
  // Initialize SD card
  SPIClass sdSPI(HSPI);
  sdSPI.begin(SD_SCK, SD_MISO, SD_MOSI, SD_CS);
  if (!SD.begin(SD_CS, sdSPI)) {
    Serial.println("SD Card initialization failed!");
    sdCardAvailable = false;
  } else {
    Serial.println("SD Card initialized successfully");
    sdCardAvailable = true;
  }
  
  // Load saved WiFi credentials
  loadWiFiCredentials();

  // Try to connect with saved credentials
  if (selectedSSID.length() > 0) {
    Serial.println("Found saved WiFi credentials for: " + selectedSSID);
    // Properly stop any ongoing WiFi operations
    WiFi.disconnect(true);  // true = wifioff
    WiFi.mode(WIFI_OFF);
    delay(100);
    WiFi.mode(WIFI_STA);
    delay(100);
    WiFi.begin(selectedSSID.c_str(), enteredPassword.c_str());
    int attempts = 0;
    
    tft.fillScreen(BG_COLOR);
    tft.setTextColor(TEXT_COLOR);
    tft.drawCentreString("Connecting to WiFi...", 160, 100, 2);
    tft.drawCentreString(selectedSSID, 160, 130, 2);
    
    while (WiFi.status() != WL_CONNECTED && attempts < 30) {
      delay(500);
      attempts++;
      tft.fillRect(140, 160, 40, 20, BG_COLOR);
      tft.drawCentreString(String(attempts), 160, 160, 2);
    }

    Serial.println("WiFi connection loop complete. Status: " + String(WiFi.status()));
    Serial.println("WL_CONNECTED constant = " + String(WL_CONNECTED));

    if (WiFi.status() == WL_CONNECTED) {
      Serial.println("Connected to WiFi using saved credentials");
      Serial.print("IP Address: ");
      Serial.println(WiFi.localIP());

      Serial.println("About to check device provisioning status...");
      Serial.println("Credentials.isProvisioned = " + String(credentials.isProvisioned ? "true" : "false"));

      // Check if device is provisioned
      if (localHubMode || credentials.isProvisioned) {
        Serial.println("Device is provisioned, starting ticker app");
        currentAppState = TICKER_APP;
      } else {
        Serial.println("Device not provisioned, showing provisioning screen");
        currentAppState = PROVISIONING_CHECK;
        drawProvisioningCheck();
      }
      currentWiFiState = WIFI_SUCCESS;

      Serial.println("Setup complete, entering main loop");
      Serial.println("Current app state: " + String(currentAppState));
    } else {
      Serial.println("Failed to connect with saved credentials");
      WiFi.disconnect(true);  // true = wifioff
      clearWiFiCredentials();
      currentAppState = WIFI_SETUP;
      currentWiFiState = WIFI_SCAN;
      return; // Skip further initialization until WiFi is configured
    }
  } else {
    Serial.println("No saved WiFi credentials found, starting WiFi setup");
    currentAppState = WIFI_SETUP;
    currentWiFiState = WIFI_SCAN;
    return; // Skip further initialization until WiFi is configured
  }
}

void scanNetworks() {
  tft.fillScreen(BG_COLOR);
  tft.setTextColor(TEXT_COLOR);
  tft.drawCentreString("Scanning WiFi...", 160, 120, 2);
  
  networkCount = WiFi.scanNetworks();
  Serial.print("Networks found: ");
  Serial.println(networkCount);
  
  // Store network details
  for (int i = 0; i < networkCount && i < 20; i++) {
    ssidList[i] = WiFi.SSID(i);
    rssiList[i] = WiFi.RSSI(i);
    encryptionList[i] = WiFi.encryptionType(i);
  }
  
  currentWiFiState = NETWORK_SELECT;
  showNetworkList();
}

void showNetworkList() {
  tft.fillScreen(BG_COLOR);
  
  // Title
  tft.setTextColor(BLUE_COLOR);
  tft.drawCentreString("Select Network", 160, 10, 2);
  
  // Draw network list
  int startIdx = currentPage * networksPerPage;
  int endIdx = min(startIdx + networksPerPage, networkCount);
  
  for (int i = startIdx; i < endIdx; i++) {
    int yPos = 40 + ((i - startIdx) * 30);
    
    // Network box
    tft.drawRect(10, yPos, 300, 28, BORDER_COLOR);
    
    // Signal strength indicator
    int bars = map(rssiList[i], -90, -30, 1, 4);
    for (int b = 0; b < bars; b++) {
      int barHeight = 5 + (b * 3);
      tft.fillRect(15 + (b * 6), yPos + 14 - barHeight, 4, barHeight, GREEN_COLOR);
    }
    
    // Network name
    tft.setTextColor(TEXT_COLOR);
    tft.setCursor(50, yPos + 8);
    tft.print(ssidList[i].substring(0, 20));
    
    // Lock icon for encrypted networks
    if (encryptionList[i] != WIFI_AUTH_OPEN) {
      tft.setTextColor(YELLOW_COLOR);
      tft.setCursor(280, yPos + 8);
      tft.print("*");
    }
  }
  
  // Navigation buttons
  if (currentPage > 0) {
    tft.fillRect(10, 220, 60, 20, BLUE_COLOR);
    tft.setTextColor(WHITE);
    tft.drawCentreString("Prev", 40, 224, 1);
  }
  
  if ((currentPage + 1) * networksPerPage < networkCount) {
    tft.fillRect(250, 220, 60, 20, BLUE_COLOR);
    tft.setTextColor(WHITE);
    tft.drawCentreString("Next", 280, 224, 1);
  }
}

void showPasswordEntry() {
  tft.fillScreen(BG_COLOR);
  
  // Title
  tft.setTextColor(BLUE_COLOR);
  tft.drawCentreString("Enter Password", 160, 5, 2);
  
  // Back button
  tft.drawRoundRect(10, 5, 50, 20, 3, BORDER_COLOR);
  tft.setTextColor(TEXT_COLOR);
  tft.drawCentreString("Back", 35, 9, 1);
  
  // Network name
  tft.setTextColor(TEXT_COLOR);
  tft.setCursor(10, 25);
  tft.print("Network: ");
  tft.print(selectedSSID);
  
  // Password field
  tft.drawRect(10, 45, 300, 25, BORDER_COLOR);
  tft.setCursor(15, 52);
  
  // Show password as asterisks
  for (int i = 0; i < enteredPassword.length(); i++) {
    tft.print("*");
  }
  
  // Draw keyboard with numbers in first row
  int keyX = 10;
  int keyY = 80;
  int keyW = 28;
  int keyH = 25;
  int spacing = 3;
  
  for (int row = 0; row < keyboardRows; row++) {
    for (int col = 0; col < keyboardCols[row]; col++) {
      int keyIndex = 0;
      for (int r = 0; r < row; r++) {
        keyIndex += keyboardCols[r];
      }
      keyIndex += col;
      
      if (keyIndex < 42) {
        drawKey(row, col, keyboardKeys[keyIndex]);
      }
    }
  }
}

void drawKey(int row, int col, const char* label, bool pressed) {
  int keyW = 28;
  int keyH = 25;
  int spacing = 3;
  int keyX = 10;
  int keyY = 80;
  
  // Special handling for bottom row (wider keys)
  if (row == 4) {
    if (col == 0) { // Space
      keyX = 10;
      keyW = 100;
    } else if (col == 1) { // Delete
      keyX = 115;
      keyW = 95;
    } else if (col == 2) { // Done
      keyX = 215;
      keyW = 95;
    }
  } else {
    // Adjust starting X for centered rows
    int totalWidth = keyboardCols[row] * (keyW + spacing) - spacing;
    keyX = (320 - totalWidth) / 2;
    keyX += col * (keyW + spacing);
  }
  
  keyY += row * (keyH + spacing);
  
  // Draw key
  uint16_t keyColor = pressed ? KEY_PRESSED_COLOR : KEY_COLOR;
  tft.fillRect(keyX, keyY, keyW, keyH, keyColor);
  tft.drawRect(keyX, keyY, keyW, keyH, BORDER_COLOR);
  
  // Draw label
  tft.setTextColor(TEXT_COLOR);
  int labelX = keyX + keyW/2 - strlen(label)*3;
  int labelY = keyY + 8;
  tft.setCursor(labelX, labelY);
  tft.print(label);
}

void handleNetworkListTouch() {
  // Check network selection with enlarged touch areas
  int startIdx = currentPage * networksPerPage;
  int endIdx = min(startIdx + networksPerPage, networkCount);
  
  for (int i = startIdx; i < endIdx; i++) {
    int yPos = 40 + ((i - startIdx) * 30);
    
    // Enlarged touch area for better responsiveness
    if (touchX >= 5 && touchX <= 315 && touchY >= yPos - 2 && touchY <= yPos + 30) {
      selectedNetwork = i;
      selectedSSID = ssidList[i];
      Serial.print("Selected network: ");
      Serial.println(selectedSSID);
      
      // Highlight selection with reduced delay
      tft.drawRect(10, yPos, 300, 28, SELECTED_COLOR);
      delay(150); // Reduced delay
      
      if (encryptionList[i] == WIFI_AUTH_OPEN) {
        // Open network, connect directly
        enteredPassword = "";
        currentWiFiState = CONNECTING;
        connectToNetwork();
      } else {
        // Needs password
        enteredPassword = "";
        currentWiFiState = PASSWORD_ENTRY;
        showPasswordEntry();
      }
      return;
    }
  }
  
  // Check navigation buttons with enlarged touch areas
  if (currentPage > 0 && touchX >= 5 && touchX <= 75 && touchY >= 215 && touchY <= 245) {
    // Visual feedback for Prev button
    tft.fillRect(10, 220, 60, 20, KEY_PRESSED_COLOR);
    tft.setTextColor(TEXT_COLOR);
    tft.drawCentreString("Prev", 40, 224, 1);
    delay(100);
    
    currentPage--;
    showNetworkList();
    return;
  }
  
  if ((currentPage + 1) * networksPerPage < networkCount && 
      touchX >= 245 && touchX <= 315 && touchY >= 215 && touchY <= 245) {
    // Visual feedback for Next button
    tft.fillRect(250, 220, 60, 20, KEY_PRESSED_COLOR);
    tft.setTextColor(TEXT_COLOR);
    tft.drawCentreString("Next", 280, 224, 1);
    delay(100);
    
    currentPage++;
    showNetworkList();
    return;
  }
}

void handlePasswordEntryTouch() {
  Serial.print("Password touch at: (");
  Serial.print(touchX);
  Serial.print(",");
  Serial.print(touchY);
  Serial.println(")");
  
  // Check back button first (enlarged touch area)
  if (touchX >= 5 && touchX <= 65 && touchY >= 0 && touchY <= 30) {
    // Visual feedback for back button
    tft.fillRoundRect(10, 5, 50, 20, 3, KEY_PRESSED_COLOR);
    tft.setTextColor(TEXT_COLOR);
    tft.drawCentreString("Back", 35, 9, 1);
    delay(100); // Reduced delay
    
    // Return to network selection
    enteredPassword = "";
    selectedSSID = "";
    currentWiFiState = NETWORK_SELECT;
    showNetworkList();
    return;
  }
  
  // Simple hardcoded keyboard layout for better reliability
  
  // Row 0: Numbers 1-0 (Y: 80-105)
  if (touchY >= 80 && touchY <= 105) {
    if (touchX >= 5 && touchX < 36) { // 1
      registerKeyPress("1", 0, 0);
    } else if (touchX >= 36 && touchX < 67) { // 2  
      registerKeyPress("2", 0, 1);
    } else if (touchX >= 67 && touchX < 98) { // 3
      registerKeyPress("3", 0, 2);
    } else if (touchX >= 98 && touchX < 129) { // 4
      registerKeyPress("4", 0, 3);
    } else if (touchX >= 129 && touchX < 160) { // 5
      registerKeyPress("5", 0, 4);
    } else if (touchX >= 160 && touchX < 191) { // 6
      registerKeyPress("6", 0, 5);
    } else if (touchX >= 191 && touchX < 222) { // 7
      registerKeyPress("7", 0, 6);
    } else if (touchX >= 222 && touchX < 253) { // 8
      registerKeyPress("8", 0, 7);
    } else if (touchX >= 253 && touchX < 284) { // 9
      registerKeyPress("9", 0, 8);
    } else if (touchX >= 284 && touchX < 315) { // 0
      registerKeyPress("0", 0, 9);
    }
    return;
  }
  
  // Row 1: QWERTY (Y: 108-133)
  if (touchY >= 108 && touchY <= 133) {
    if (touchX >= 5 && touchX < 36) { // q
      registerKeyPress("q", 1, 0);
    } else if (touchX >= 36 && touchX < 67) { // w
      registerKeyPress("w", 1, 1);
    } else if (touchX >= 67 && touchX < 98) { // e
      registerKeyPress("e", 1, 2);
    } else if (touchX >= 98 && touchX < 129) { // r
      registerKeyPress("r", 1, 3);
    } else if (touchX >= 129 && touchX < 160) { // t
      registerKeyPress("t", 1, 4);
    } else if (touchX >= 160 && touchX < 191) { // y
      registerKeyPress("y", 1, 5);
    } else if (touchX >= 191 && touchX < 222) { // u
      registerKeyPress("u", 1, 6);
    } else if (touchX >= 222 && touchX < 253) { // i
      registerKeyPress("i", 1, 7);
    } else if (touchX >= 253 && touchX < 284) { // o
      registerKeyPress("o", 1, 8);
    } else if (touchX >= 284 && touchX < 315) { // p
      registerKeyPress("p", 1, 9);
    }
    return;
  }
  
  // Row 2: ASDF (Y: 136-161) - 9 keys
  if (touchY >= 136 && touchY <= 161) {
    if (touchX >= 20 && touchX < 51) { // a
      registerKeyPress("a", 2, 0);
    } else if (touchX >= 51 && touchX < 82) { // s
      registerKeyPress("s", 2, 1);
    } else if (touchX >= 82 && touchX < 113) { // d
      registerKeyPress("d", 2, 2);
    } else if (touchX >= 113 && touchX < 144) { // f
      registerKeyPress("f", 2, 3);
    } else if (touchX >= 144 && touchX < 175) { // g
      registerKeyPress("g", 2, 4);
    } else if (touchX >= 175 && touchX < 206) { // h
      registerKeyPress("h", 2, 5);
    } else if (touchX >= 206 && touchX < 237) { // j
      registerKeyPress("j", 2, 6);
    } else if (touchX >= 237 && touchX < 268) { // k
      registerKeyPress("k", 2, 7);
    } else if (touchX >= 268 && touchX < 299) { // l
      registerKeyPress("l", 2, 8);
    }
    return;
  }
  
  // Row 3: ZXCV (Y: 164-189) - 9 keys  
  if (touchY >= 164 && touchY <= 189) {
    if (touchX >= 20 && touchX < 51) { // z
      registerKeyPress("z", 3, 0);
    } else if (touchX >= 51 && touchX < 82) { // x
      registerKeyPress("x", 3, 1);
    } else if (touchX >= 82 && touchX < 113) { // c
      registerKeyPress("c", 3, 2);
    } else if (touchX >= 113 && touchX < 144) { // v
      registerKeyPress("v", 3, 3);
    } else if (touchX >= 144 && touchX < 175) { // b
      registerKeyPress("b", 3, 4);
    } else if (touchX >= 175 && touchX < 206) { // n
      registerKeyPress("n", 3, 5);
    } else if (touchX >= 206 && touchX < 237) { // m
      registerKeyPress("m", 3, 6);
    } else if (touchX >= 237 && touchX < 268) { // @
      registerKeyPress("@", 3, 7);
    } else if (touchX >= 268 && touchX < 299) { // .
      registerKeyPress(".", 3, 8);
    }
    return;
  }
  
  // Row 4: Space, Delete, Done (Y: 192-217)
  if (touchY >= 192 && touchY <= 217) {
    if (touchX >= 10 && touchX <= 110) { // Space
      registerKeyPress("Space", 4, 0);
    } else if (touchX >= 115 && touchX <= 210) { // Delete
      registerKeyPress("Delete", 4, 1);
    } else if (touchX >= 215 && touchX <= 310) { // Done
      registerKeyPress("Done", 4, 2);
    }
    return;
  }
}

void registerKeyPress(String key, int row, int col) {
  // Touch delay to prevent multiple character entry (like iPhone keyboard)
  static unsigned long lastKeyPressTime = 0;
  unsigned long currentTime = millis();

  if (currentTime - lastKeyPressTime < 200) { // 200ms minimum between key presses
    return; // Ignore too-rapid key presses
  }
  lastKeyPressTime = currentTime;

  Serial.print("Key pressed: ");
  Serial.println(key);

  // Visual feedback
  drawKey(row, col, key.c_str(), true);
  delay(80);
  drawKey(row, col, key.c_str(), false);
  
  // Handle key press
  if (key == "Space") {
    enteredPassword += " ";
  } else if (key == "Delete") {
    if (enteredPassword.length() > 0) {
      enteredPassword = enteredPassword.substring(0, enteredPassword.length() - 1);
    }
  } else if (key == "Done") {
    currentWiFiState = CONNECTING;
    connectToNetwork();
    return;
  } else {
    enteredPassword += key;
  }
  
  // Update password display
  tft.fillRect(11, 46, 298, 23, BG_COLOR);
  tft.setCursor(15, 52);
  tft.setTextColor(TEXT_COLOR);
  for (int i = 0; i < enteredPassword.length(); i++) {
    tft.print("*");
  }
  
  // Show character count
  tft.fillRect(250, 25, 60, 20, BG_COLOR);
  tft.setCursor(250, 30);
  tft.print("(" + String(enteredPassword.length()) + ")");
}

void connectToNetwork() {
  showConnectionStatus(true);

  // Properly stop any ongoing WiFi operations
  WiFi.disconnect(true);  // true = wifioff
  WiFi.mode(WIFI_OFF);
  delay(100);
  WiFi.mode(WIFI_STA);
  delay(100);
  WiFi.begin(selectedSSID.c_str(), enteredPassword.c_str());

  // Initialize non-blocking connection tracking
  wifiConnectionStart = millis();
  wifiConnectionAttempts = 0;
}

void handleWiFiConnection() {
  // Check if enough time has passed for next attempt
  if (millis() - wifiConnectionStart >= WIFI_ATTEMPT_INTERVAL) {
    wifiConnectionAttempts++;

    // Update progress display
    tft.fillRect(140, 130, 40, 20, BG_COLOR);
    tft.setTextColor(TEXT_COLOR);
    tft.drawCentreString(String(wifiConnectionAttempts), 160, 130, 2);

    // Check WiFi status
    if (WiFi.status() == WL_CONNECTED) {
      Serial.println("Connected to WiFi!");
      Serial.print("IP Address: ");
      Serial.println(WiFi.localIP());

      // Save credentials
      saveWiFiCredentials();

      currentWiFiState = WIFI_SUCCESS;
      showConnectionStatus(false);

      // Check if device is provisioned (after short delay)
      delay(1000);
      if (credentials.isProvisioned) {
        currentAppState = TICKER_APP;
      } else {
        currentAppState = PROVISIONING_CHECK;
        drawProvisioningCheck();
      }
    } else if (wifiConnectionAttempts >= MAX_WIFI_ATTEMPTS) {
      // Connection failed
      Serial.println("Failed to connect");
      currentWiFiState = WIFI_ERROR;
      WiFi.disconnect(true);  // true = wifioff

      tft.fillScreen(BG_COLOR);
      tft.setTextColor(ERROR_COLOR);
      tft.drawCentreString("Connection Failed!", 160, 100, 2);
      tft.setTextColor(TEXT_COLOR);
      tft.drawCentreString("Check password and try again", 160, 130, 2);
      tft.setTextColor(TEXT_COLOR);
      tft.drawCentreString("Touch screen to retry", 160, 160, 2);
    }

    // Reset timer for next attempt
    wifiConnectionStart = millis();
  }
}

void showConnectionStatus(bool isConnecting) {
  tft.fillScreen(BG_COLOR);
  
  if (isConnecting) {
    tft.setTextColor(BLUE_COLOR);
    tft.drawCentreString("Connecting...", 160, 80, 2);
    tft.setTextColor(TEXT_COLOR);
    tft.drawCentreString(selectedSSID, 160, 110, 2);
  } else {
    tft.setTextColor(SUCCESS_COLOR);
    tft.drawCentreString("Connected!", 160, 80, 2);
    tft.setTextColor(TEXT_COLOR);
    tft.drawCentreString("IP: " + WiFi.localIP().toString(), 160, 110, 2);
  }
}

void loadWiFiCredentials() {
  preferences.begin("wifi-config", true);  // Read-only
  selectedSSID = preferences.getString("ssid", "");
  enteredPassword = preferences.getString("password", "");
  preferences.end();
  Serial.println("Loaded credentials for: " + selectedSSID);
}

void saveWiFiCredentials() {
  preferences.begin("wifi-config", false);
  preferences.putString("ssid", selectedSSID);
  preferences.putString("password", enteredPassword);
  preferences.end();
  Serial.println("Saved credentials for: " + selectedSSID);
}

void clearWiFiCredentials() {
  preferences.begin("wifi-config", false);
  preferences.remove("ssid");
  preferences.remove("password");
  preferences.end();
  selectedSSID = "";
  enteredPassword = "";
  Serial.println("Cleared WiFi credentials");
}

void handleWiFiConfig() {
  // Handle non-blocking WiFi connection progress
  if (currentWiFiState == CONNECTING) {
    handleWiFiConnection();
  }

  if (getTouchPoint(touchX, touchY)) {
    switch (currentWiFiState) {
      case NETWORK_SELECT:
        handleNetworkListTouch();
        break;

      case PASSWORD_ENTRY:
        handlePasswordEntryTouch();
        break;

      case WIFI_SUCCESS:
        // Check provisioning status on touch
        if (localHubMode || credentials.isProvisioned) {
          currentAppState = TICKER_APP;
        } else {
          currentAppState = PROVISIONING_CHECK;
          drawProvisioningCheck();
        }
        break;

      case WIFI_ERROR:
        // Allow touch to retry WiFi setup
        currentWiFiState = NETWORK_SELECT;
        showNetworkList();
        break;
    }
  }
}

// Ticker App functions
String formatForexPair(String symbol) {
  // Convert lowercase forex ticker to uppercase currency pair format
  if (symbol.length() == 6) {
    String base = symbol.substring(0, 3);
    String quote = symbol.substring(3, 6);
    base.toUpperCase();
    quote.toUpperCase();
    return base + "/" + quote;
  }
  return symbol;
}

void showTickerApp() {
  tft.fillScreen(BG_COLOR);
  
  // Draw title bar
  tft.fillRect(0, 0, 320, 30, LIGHT_GRAY);
  tft.setTextColor(BLACK);  // Black text on light grey background
  
  if (currentTickerState == TICKER_SETTINGS) {
    tft.drawCentreString("Settings", 160, 7, 2);
  } else if (currentTickerState == TICKER_DEVICE_SETTINGS) {
    tft.drawCentreString("Device Settings", 160, 7, 2);
  } else {
    // Show navigation controls - different for each state
    if (currentTickerState == TICKER_SINGLE && isTemporarySingleView) {
      // Temporary single asset view (clicked from grid) - just back button
      tft.fillRect(10, 5, 50, 20, BUTTON_GRAY);
      tft.drawRect(10, 5, 50, 20, BLACK);
      tft.setTextColor(BLACK);
      tft.drawCentreString("Back", 35, 9, 1);
    } else if (autoMode && !autoModePaused) {
      // Auto mode in grid - show title but also need Auto/Manual buttons
      tft.drawCentreString("Tickertronix", 80, 7, 2);  // Moved left to make room for buttons
    } else {
      // Manual mode OR paused auto mode in grid: Show navigation
      if (totalPages > 1) {
        // Page navigation arrows
        if (currentAssetPage > 0) {
          tft.fillRect(10, 5, 25, 20, BUTTON_GRAY);
          tft.drawRect(10, 5, 25, 20, BLACK);
          tft.setTextColor(BLACK);
          tft.drawCentreString("<", 22, 9, 1);
        }
        
        // Page indicator
        tft.setTextColor(BLACK);
        String pageStr = String(currentAssetPage + 1) + "/" + String(totalPages);
        tft.drawCentreString(pageStr, 55, 9, 1);
        
        if (currentAssetPage < totalPages - 1) {
          tft.fillRect(75, 5, 25, 20, BUTTON_GRAY);
          tft.drawRect(75, 5, 25, 20, BLACK);
          tft.setTextColor(BLACK);
          tft.drawCentreString(">", 87, 9, 1);
        }
      }
    }
    
    // Show buttons based on state and mode - OUTSIDE the auto/manual conditional
    // Show Auto/Manual buttons for grid mode AND Single Asset Mode (not temporary single view)
    if (currentTickerState != TICKER_SINGLE || (currentTickerState == TICKER_SINGLE && !isTemporarySingleView)) {
      // In grid mode - ALWAYS show Auto/Manual buttons
      tft.fillRect(200, 5, 40, 20, BUTTON_GRAY);
      tft.drawRect(200, 5, 40, 20, WHITE);
      tft.setTextColor(WHITE);
      tft.drawCentreString("Auto", 220, 9, 1);
      
      tft.fillRect(245, 5, 45, 20, BUTTON_GRAY); 
      tft.drawRect(245, 5, 45, 20, WHITE);
      tft.setTextColor(WHITE);
      tft.drawCentreString("Manual", 267, 9, 1);
      
      // Highlight current mode
      if (autoMode) {
        tft.fillRect(201, 6, 38, 18, BUTTON_GREEN);
        tft.setTextColor(WHITE);
        tft.drawCentreString("Auto", 220, 9, 1);
      } else {
        tft.fillRect(246, 6, 43, 18, BUTTON_GREEN);
        tft.setTextColor(WHITE);
        tft.drawCentreString("Manual", 267, 9, 1);
      }
      
      // Settings button - only show in manual mode
      if (!autoMode || autoModePaused) {
        tft.fillRect(130, 5, 60, 20, BUTTON_ORANGE);
        tft.drawRect(130, 5, 60, 20, BLACK);
        tft.setTextColor(WHITE);
        tft.drawCentreString("Settings", 160, 9, 1);
      }
    }
    tft.setTextColor(WHITE);
  }
  
  // Draw content based on state
  if (currentTickerState == TICKER_SETTINGS) {
    drawSettingsMenu();
  } else if (currentTickerState == TICKER_DEVICE_SETTINGS) {
    drawDeviceSettingsMenu();
  } else if (currentTickerState == TICKER_SINGLE) {
    drawSingleAsset();
  } else {
    // Remove old navigation arrows - they're now in the top bar

    drawAssetGrid();
  }
}

void updateGridOnly() {
  // Only update the grid area without touching the top bar
  drawAssetGrid();
}

void drawAssetGrid() {
  // Calculate grid layout - adjusted to fit screen properly
  int cellWidth = 106;
  int cellHeight = 65;  // Reduced from 70 to fit 3 rows
  int startX = 1;
  int startY = 32;
  
  // Only clear screen if no data, otherwise let cells overwrite for smooth transitions
  if (assetCount == 0) {
    tft.fillRect(0, 31, 320, 209, BG_COLOR);
    tft.setTextColor(TEXT_COLOR);
    tft.drawCentreString("No data", 160, 100, 2);
    tft.drawCentreString("Device Key: " + credentials.deviceKey, 160, 120, 1);
    tft.drawCentreString("Configure via TickerApp", 160, 140, 1);
    return;
  }
  
  // Clear any unused cell areas at the bottom in case the new page has fewer assets
  if (autoMode && !autoModePaused) {
    // In auto mode, just clear the page indicator area to prevent artifacts
    tft.fillRect(0, 220, 320, 20, BG_COLOR);
  } else {
    // In manual mode, clear everything for clean display
    tft.fillRect(0, 31, 320, 209, BG_COLOR);
  }
  
  // Calculate page info
  int startIdx = currentAssetPage * ASSETS_PER_PAGE;
  int endIdx = min(startIdx + ASSETS_PER_PAGE, assetCount);
  
  // Draw assets in 3x3 grid
  for (int i = startIdx; i < endIdx; i++) {
    int gridPos = i - startIdx;
    int row = gridPos / 3;
    int col = gridPos % 3;
    
    int x = startX + (col * cellWidth);
    int y = startY + (row * cellHeight);
    
    drawAssetCell(x, y, cellWidth, cellHeight, i);
  }
  
  // Clear any unused cells on the last page
  int cellsDrawn = endIdx - startIdx;
  if (cellsDrawn < ASSETS_PER_PAGE) {
    for (int i = cellsDrawn; i < ASSETS_PER_PAGE; i++) {
      int row = i / 3;
      int col = i % 3;
      int x = startX + (col * cellWidth);
      int y = startY + (row * cellHeight);
      
      // Clear the unused cell area
      tft.fillRect(x, y, cellWidth-1, cellHeight-1, BG_COLOR);
    }
  }
  
  // Page indicator at bottom - adjusted position
  if (totalPages > 1) {
    tft.setTextColor(BORDER_COLOR);
    String pageInfo = "Page " + String(currentAssetPage + 1) + "/" + String(totalPages);
    tft.drawCentreString(pageInfo, 160, 230, 1);
  }
}

void drawAssetCell(int x, int y, int width, int height, int index) {
  if (index >= assetCount || !assets[index].isValid) return;
  
  Asset& asset = assets[index];
  
  // Fill cell background based on type and price change
  if (asset.type == "forex") {
    // Give forex a distinctive dark blue background
    tft.fillRect(x, y, width-1, height-1, tft.color565(0, 30, 60));  // Dark blue
  } else {
    // Stocks and crypto use green/red based on change
    if (asset.change > 0) {
      tft.fillRect(x, y, width-1, height-1, DARK_GREEN);
    } else if (asset.change < 0) {
      tft.fillRect(x, y, width-1, height-1, DARK_RED);
    } else {
      // No change - use very dark grey
      tft.fillRect(x, y, width-1, height-1, tft.color565(20, 20, 20));
    }
  }
  
  // Cell border
  tft.drawRect(x, y, width-1, height-1, BORDER_COLOR);
  
  // Type indicator in upper right corner
  tft.setTextColor(tft.color565(150, 150, 150));  // Light grey for subtlety
  tft.setTextSize(1);
  if (asset.type == "stock") {
    tft.drawString("S", x + width - 12, y + 3, 1);
  } else if (asset.type == "crypto") {
    tft.drawString("C", x + width - 12, y + 3, 1);
  } else if (asset.type == "forex") {
    tft.drawString("FX", x + width - 18, y + 3, 1);
  }
  
  // Symbol - white color with consistent sizing
  tft.setTextColor(WHITE);
  if (asset.type == "forex") {
    // Forex pairs use font 2 due to length (e.g., "AUD/SGD")
    tft.drawCentreString(formatForexPair(asset.symbol), x + width/2, y + 5, 2);
  } else {
    // Stocks and crypto use font 4 for all lengths up to 5 chars
    if (asset.symbol.length() <= 5) {
      tft.drawCentreString(asset.symbol, x + width/2, y + 5, 4);
    } else {
      tft.drawCentreString(asset.symbol, x + width/2, y + 5, 2);
    }
  }
  
  // Price - centered in middle of cell
  tft.setTextColor(TEXT_COLOR);
  String priceStr = formatPrice(asset.price, asset.type);
  
  // Use appropriate fonts - font 2 for most prices, font 1 for very long prices
  int priceFont = 2;
  if (priceStr.length() > 10) {
    priceFont = 1;
  }
  
  tft.drawCentreString(priceStr, x + width/2, y + 28, priceFont);
  
  // Change display - different for forex vs stocks/crypto
  if (asset.type == "forex") {
    // For forex, show exchange rate in a more compact format
    tft.setTextColor(tft.color565(180, 180, 180));  // Light grey
    String forexPair = formatForexPair(asset.symbol);
    int slashPos = forexPair.indexOf('/');
    if (slashPos != -1) {
      String baseCurrency = forexPair.substring(0, slashPos);
      String quoteCurrency = forexPair.substring(slashPos + 1);
      // More compact format without "1" prefix to save space
      String rateStr = baseCurrency + "=" + String(asset.price, 2) + quoteCurrency;  // 2 decimals
      // Use a smaller x offset to ensure it fits within cell bounds
      int textWidth = rateStr.length() * 6; // Approximate width for font 1
      if (textWidth > width - 10) {
        // If still too wide, just show the rate
        rateStr = String(asset.price, 2);  // 2 decimals
      }
      tft.drawCentreString(rateStr, x + width/2, y + 48, 1);
    }
  } else {
    // Stocks and crypto show change and percent
    uint16_t changeColor = (asset.change >= 0) ? GREEN_COLOR : RED_COLOR;
    tft.setTextColor(changeColor);
    
    String changeStr = (asset.change >= 0 ? "+" : "") + String(asset.change, 2);
    String percentStr = "(" + String(abs(asset.changePercent), 1) + "%)";
    
    // Draw change values side by side at bottom of cell
    int textWidth = changeStr.length() * 6;  // Approximate width
    int percentWidth = percentStr.length() * 6;
    int totalWidth = textWidth + percentWidth + 10;  // 10 pixel gap
    int startX = x + (width - totalWidth) / 2;
    
    tft.drawString(changeStr, startX, y + 48, 1);
    tft.drawString(percentStr, startX + textWidth + 10, y + 48, 1);
  }
}

void drawSingleAsset() {
  if (currentSingleAsset >= assetCount || !assets[currentSingleAsset].isValid) {
    Serial.println("WARNING: Single asset view invalid - switching to grid");
    Serial.print("currentSingleAsset: ");
    Serial.print(currentSingleAsset);
    Serial.print(", assetCount: ");
    Serial.print(assetCount);
    if (currentSingleAsset < assetCount) {
      Serial.print(", isValid: ");
      Serial.println(assets[currentSingleAsset].isValid);
    } else {
      Serial.println(", index out of bounds");
    }
    currentTickerState = TICKER_GRID;
    return;
  }
  
  Asset& asset = assets[currentSingleAsset];
  
  // Debug: Print asset type to serial
  Serial.print("Single view - Asset: ");
  Serial.print(asset.symbol);
  Serial.print(", Type: ");
  Serial.print(asset.type);
  Serial.print(", Price: ");
  Serial.println(asset.price);
  
  // Clear display area
  tft.fillRect(0, 31, 320, 209, BG_COLOR);
  
  // Use full screen dimensions similar to grid cell layout but larger
  int x = 10;
  int y = 40;
  int width = 300;
  int height = 180;
  
  // Fill background based on price change (skip for forex)
  if (asset.type != "forex") {
    if (asset.change > 0) {
      tft.fillRect(x, y, width, height, DARK_GREEN);
    } else if (asset.change < 0) {
      tft.fillRect(x, y, width, height, DARK_RED);
    }
  }
  
  // Draw border
  tft.drawRect(x, y, width, height, BORDER_COLOR);
  
  // Type indicator in upper right corner (similar to grid view)
  tft.setTextColor(tft.color565(150, 150, 150));  // Light grey
  tft.setTextSize(1);
  if (asset.type == "stock") {
    tft.drawString("S", x + width - 20, y + 5, 2);
  } else if (asset.type == "crypto") {
    tft.drawString("C", x + width - 20, y + 5, 2);
  } else if (asset.type == "forex") {
    tft.drawString("FX", x + width - 30, y + 5, 2);
  }
  
  // Symbol - very large and white
  tft.setTextColor(WHITE);
  if (asset.type == "forex") {
    // Forex pairs still use larger font size
    tft.setTextSize(2);
    tft.drawCentreString(formatForexPair(asset.symbol), 160, y + 20, 4);
    tft.setTextSize(1);
  } else {
    // Use larger font for all symbols in single view - plenty of room
    tft.setTextSize(2);
    if (asset.symbol.length() <= 5) {
      tft.drawCentreString(asset.symbol, 160, y + 20, 4);
    } else {
      // For very long symbols (6+ chars), use font 2 with size 2
      tft.drawCentreString(asset.symbol, 160, y + 20, 2);
    }
    tft.setTextSize(1);
  }
  
  // Price - very large
  tft.setTextColor(TEXT_COLOR);
  String priceStr = formatPrice(asset.price, asset.type);
  
  // Use text size multiplier with font 4 for large display
  if (priceStr.length() <= 7) {
    // Short prices - use font 4 with size 2 for very large display
    tft.setTextSize(2);
    tft.drawCentreString(priceStr, 160, y + 80, 4);
    tft.setTextSize(1);
  } else if (priceStr.length() <= 10) {
    // Medium prices - use font 4 normal size
    tft.drawCentreString(priceStr, 160, y + 80, 4);
  } else {
    // Long prices - use font 2
    tft.drawCentreString(priceStr, 160, y + 80, 2);
  }
  
  // Change and percent - only for stocks and crypto
  if (asset.type != "forex") {
    uint16_t changeColor = (asset.change >= 0) ? GREEN_COLOR : RED_COLOR;
    tft.setTextColor(changeColor);
    
    String changeStr = (asset.change >= 0 ? "+" : "") + String(asset.change, 2);
    String percentStr = "(" + String(abs(asset.changePercent), 1) + "%)";
    
    // Draw side by side at bottom, larger fonts
    int textWidth = changeStr.length() * 12;  // Approximate width for font 2
    int percentWidth = percentStr.length() * 12;
    int totalWidth = textWidth + percentWidth + 20;  // 20 pixel gap
    int startX = (320 - totalWidth) / 2;
    
    tft.setTextSize(2);
    tft.setCursor(startX, y + 140);
    tft.print(changeStr);
    tft.setCursor(startX + textWidth + 20, y + 140);
    tft.print(percentStr);
    tft.setTextSize(1);
  }
  
  // Navigation controls - Previous/Next arrows in single view
  // Show arrows in manual mode (works for both temporary single view and Single Asset Mode)
  if (!autoMode || autoModePaused) {
    tft.setTextColor(WHITE);
    
    // Previous asset
    if (currentSingleAsset > 0) {
      tft.drawString("<", 25, 120, 4);
    }
    
    // Next asset
    if (currentSingleAsset < assetCount - 1) {
      tft.drawString(">", 285, 120, 4);
    }
  }
  
  // Update timer - show how long since last data update
  unsigned long timeSinceUpdate = millis() - lastDataUpdate;
  tft.setTextColor(tft.color565(150, 150, 150));  // Light grey
  
  String updateText = "Updated: ";
  if (timeSinceUpdate < 60000) {  // Less than 1 minute
    updateText += String(timeSinceUpdate / 1000) + "s ago";
  } else if (timeSinceUpdate < 3600000) {  // Less than 1 hour
    int minutes = timeSinceUpdate / 60000;
    updateText += String(minutes) + "m ago";
  } else {  // More than 1 hour
    int hours = timeSinceUpdate / 3600000;
    int minutes = (timeSinceUpdate % 3600000) / 60000;
    updateText += String(hours) + "h " + String(minutes) + "m ago";
  }
  
  // Draw at bottom of screen
  tft.drawCentreString(updateText, 160, 225, 1);
}

void drawSettingsMenu() {
  // Clear display area
  tft.fillRect(0, 31, 320, 209, BG_COLOR);

  tft.setTextColor(TEXT_COLOR);

  // Display mode setting
  tft.drawString("Display Mode:", 20, 50, 2);

  // Grid button
  tft.drawRect(30, 80, 80, 30, BORDER_COLOR);
  if (displayMode == MODE_GRID) {
    tft.fillRect(31, 81, 78, 28, SELECTED_COLOR);
  }
  tft.drawCentreString("Grid", 70, 88, 2);

  // Single button
  tft.drawRect(130, 80, 80, 30, BORDER_COLOR);
  if (displayMode == MODE_SINGLE) {
    tft.fillRect(131, 81, 78, 28, SELECTED_COLOR);
  }
  tft.drawCentreString("Single", 170, 88, 2);
  
  // Auto cycle interval
  tft.drawString("Auto Cycle Interval:", 20, 130, 2);
  
  // Decrease button
  tft.drawRect(30, 160, 40, 30, BORDER_COLOR);
  tft.drawCentreString("-", 50, 168, 2);
  
  // Value display
  tft.drawRect(80, 160, 80, 30, BORDER_COLOR);
  tft.drawCentreString(String(autoInterval/1000) + "s", 120, 168, 2);
  
  // Increase button
  tft.drawRect(170, 160, 40, 30, BORDER_COLOR);
  tft.drawCentreString("+", 190, 168, 2);

  // Device settings button
  tft.fillRect(30, 200, 100, 30, BUTTON_GRAY);
  tft.drawRect(30, 200, 100, 30, BLACK);
  tft.setTextColor(WHITE);
  tft.drawCentreString("Device", 80, 208, 2);

  // Back button - using orange like Settings button for better visibility
  tft.fillRect(250, 200, 60, 30, BUTTON_ORANGE);
  tft.drawRect(250, 200, 60, 30, BLACK);
  tft.setTextColor(WHITE);
  tft.drawCentreString("Back", 280, 208, 2);
}

void handleSettingsTouch() {
  // Grid button
  if (touchX >= 30 && touchX <= 110 && touchY >= 80 && touchY <= 110) {
    displayMode = MODE_GRID;
    currentTickerState = TICKER_GRID;
    showTickerApp();
  }
  
  // Single button
  if (touchX >= 130 && touchX <= 210 && touchY >= 80 && touchY <= 110) {
    displayMode = MODE_SINGLE;
    currentTickerState = TICKER_SINGLE;
    isTemporarySingleView = false;  // This is permanent Single Asset Mode from settings
    currentSingleAsset = currentAssetPage * ASSETS_PER_PAGE; // Start with first asset on current page
    showTickerApp();
  }
  
  // Decrease interval
  if (touchX >= 30 && touchX <= 70 && touchY >= 160 && touchY <= 190) {
    if (autoInterval > 1000) {
      autoInterval -= 1000;
      drawSettingsMenu();
    }
  }
  
  // Increase interval
  if (touchX >= 170 && touchX <= 210 && touchY >= 160 && touchY <= 190) {
    if (autoInterval < 30000) {
      autoInterval += 1000;
      drawSettingsMenu();
    }
  }

  // Device settings button
  if (touchX >= 30 && touchX <= 130 && touchY >= 200 && touchY <= 230) {
    currentTickerState = TICKER_DEVICE_SETTINGS;
    drawDeviceSettingsMenu();
  }

  // Back button
  if (touchX >= 250 && touchX <= 310 && touchY >= 200 && touchY <= 230) {
    if (displayMode == MODE_SINGLE) {
      currentTickerState = TICKER_SINGLE;
      isTemporarySingleView = false;  // Going back to permanent Single Asset Mode
    } else {
      currentTickerState = TICKER_GRID;
    }
    showTickerApp();
  }
}

void fetchTickerDataLegacy() {
  Serial.println("=== fetchTickerData() called ===");
  Serial.print("WiFi status: ");
  Serial.println(WiFi.status());
  Serial.print("WL_CONNECTED = ");
  Serial.println(WL_CONNECTED);

  // Use new HMAC-authenticated API call if provisioned
  if (credentials.isProvisioned) {
    Serial.println("[FETCH] Using HMAC authentication");
    // This will be handled by the api_functions.ino fetchTickerData()
    return;
  }
  
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi not connected, skipping data fetch");
    return;
  }
  
  // Legacy function - should use HMAC authenticated version
  Serial.println("[LEGACY] Using old API endpoint - device should be re-provisioned");
  return;
}

void updateLocalData(String jsonData) {
  Serial.println("=== Parsing new JSON structure ===");
  Serial.println("JSON length: " + String(jsonData.length()));
  
  // Save current viewing state before update
  String currentViewedSymbol = "";
  if (currentTickerState == TICKER_SINGLE && currentSingleAsset < assetCount && assets[currentSingleAsset].isValid) {
    currentViewedSymbol = assets[currentSingleAsset].symbol;
    Serial.println("Preserving view of: " + currentViewedSymbol);
  }
  
  // Debug: Print first 500 characters of JSON
  Serial.println("JSON preview:");
  Serial.println(jsonData.substring(0, min(500, (int)jsonData.length())));
  
  // Clear existing assets array to prevent stale data and duplicates
  for (int i = 0; i < RAM_CACHE_SIZE; i++) {
    assets[i].isValid = false;
    assets[i].symbol = "";
    assets[i].name = "";
    assets[i].price = 0.0;
    assets[i].change = 0.0; 
    assets[i].changePercent = 0.0;
    assets[i].type = "";
    assets[i].lastUpdate = 0;
  }
  
  int assetIndex = 0;
  
  // Find the "data" object first (handle whitespace after colon)
  int dataStart = jsonData.indexOf("\"data\":");
  if (dataStart < 0) {
    Serial.println("Error: Could not find 'data' object in JSON");
    return;
  }
  Serial.println("Found data object at position: " + String(dataStart));
  
  // Parse stocks array (handle whitespace around brackets)
  int stocksStart = jsonData.indexOf("\"stocks\":", dataStart);
  Serial.println("Stocks search result: " + String(stocksStart));
  if (stocksStart >= 0) {
    Serial.println("Found stocks array at position " + String(stocksStart));
    int arrayStart = jsonData.indexOf("[", stocksStart) + 1;
    int arrayEnd = jsonData.indexOf("]", arrayStart);
    String stocksData = jsonData.substring(arrayStart, arrayEnd);
    
    while (stocksData.indexOf("{") >= 0 && assetIndex < RAM_CACHE_SIZE) {
      int objStart = stocksData.indexOf("{");
      
      // Find matching closing brace by counting braces
      int braceCount = 0;
      int objEnd = objStart;
      for (int i = objStart; i < stocksData.length(); i++) {
        if (stocksData.charAt(i) == '{') braceCount++;
        if (stocksData.charAt(i) == '}') braceCount--;
        if (braceCount == 0) {
          objEnd = i;
          break;
        }
      }
      
      if (objEnd > objStart) {
        String stockJson = stocksData.substring(objStart, objEnd + 1);
        Asset newAsset;
        
        // Debug: Print the stock JSON being parsed
        Serial.println("Parsing stock JSON: " + stockJson.substring(0, min(100, (int)stockJson.length())));
        
        // Extract ticker - handle whitespace
        int tickerStart = stockJson.indexOf("\"ticker\":");
        if (tickerStart >= 0) {
          // Find the quote after the colon
          int quoteStart = stockJson.indexOf("\"", tickerStart + 9);
          if (quoteStart >= 0) {
            int quoteEnd = stockJson.indexOf("\"", quoteStart + 1);
            if (quoteEnd > quoteStart) {
              newAsset.symbol = stockJson.substring(quoteStart + 1, quoteEnd);
              Serial.println("Extracted ticker: " + newAsset.symbol);
            } else {
              newAsset.symbol = "NOTICKER";
            }
          } else {
            newAsset.symbol = "NOTICKER";
          }
        } else {
          newAsset.symbol = "NOTICKER";
        }
        newAsset.name = newAsset.symbol;
        
        // Extract price (tngoLast) - handle whitespace  
        int priceStart = stockJson.indexOf("\"tngoLast\":");
        if (priceStart >= 0) {
          // Find the quote after the colon
          int quoteStart = stockJson.indexOf("\"", priceStart + 11);
          if (quoteStart >= 0) {
            int quoteEnd = stockJson.indexOf("\"", quoteStart + 1);
            if (quoteEnd > quoteStart) {
              newAsset.price = stockJson.substring(quoteStart + 1, quoteEnd).toFloat();
              Serial.println("Extracted price: " + String(newAsset.price));
            } else {
              newAsset.price = 0.0;
            }
          } else {
            newAsset.price = 0.0;
          }
        } else {
          newAsset.price = 0.0;
        }
        
        // Extract change (prcChange) - handle whitespace
        int changeStart = stockJson.indexOf("\"prcChange\":");
        if (changeStart >= 0) {
          // Find the quote after the colon
          int quoteStart = stockJson.indexOf("\"", changeStart + 12);
          if (quoteStart >= 0) {
            int quoteEnd = stockJson.indexOf("\"", quoteStart + 1);
            if (quoteEnd > quoteStart) {
              newAsset.change = stockJson.substring(quoteStart + 1, quoteEnd).toFloat();
              Serial.println("Extracted change: " + String(newAsset.change));
            } else {
              newAsset.change = 0.0;
            }
          } else {
            newAsset.change = 0.0;
          }
        } else {
          newAsset.change = 0.0;
        }
        
        // Extract changePercent (prcChangePct) - handle whitespace
        int percentStart = stockJson.indexOf("\"prcChangePct\":");
        if (percentStart >= 0) {
          // Find the quote after the colon
          int quoteStart = stockJson.indexOf("\"", percentStart + 15);
          if (quoteStart >= 0) {
            int quoteEnd = stockJson.indexOf("\"", quoteStart + 1);
            if (quoteEnd > quoteStart) {
              newAsset.changePercent = stockJson.substring(quoteStart + 1, quoteEnd).toFloat();
              Serial.println("Extracted changePercent: " + String(newAsset.changePercent));
            } else {
              newAsset.changePercent = 0.0;
            }
          } else {
            newAsset.changePercent = 0.0;
          }
        } else {
          newAsset.changePercent = 0.0;
        }
        
        newAsset.type = "stock";
        newAsset.isValid = true;
        newAsset.lastUpdate = millis();
        
        assets[assetIndex] = newAsset;
        Serial.print("Parsed stock: ");
        Serial.print(newAsset.symbol);
        Serial.print(" $");
        Serial.print(newAsset.price);
        Serial.print(" (");
        Serial.print(newAsset.changePercent);
        Serial.println("%)");
        assetIndex++;
        
        stocksData = stocksData.substring(objEnd + 1);
      } else {
        break;
      }
    }
  }
  
  // Parse cryptos array (handle whitespace around brackets)
  int cryptosStart = jsonData.indexOf("\"cryptos\":", dataStart);
  Serial.println("Cryptos search result: " + String(cryptosStart));
  if (cryptosStart >= 0) {
    Serial.println("Found cryptos array at position " + String(cryptosStart));
    int arrayStart = jsonData.indexOf("[", cryptosStart) + 1;
    int arrayEnd = jsonData.indexOf("]", arrayStart);
    String cryptosData = jsonData.substring(arrayStart, arrayEnd);
    
    while (cryptosData.indexOf("{") >= 0 && assetIndex < RAM_CACHE_SIZE) {
      int objStart = cryptosData.indexOf("{");
      
      // Find matching closing brace by counting braces
      int braceCount = 0;
      int objEnd = objStart;
      for (int i = objStart; i < cryptosData.length(); i++) {
        if (cryptosData.charAt(i) == '{') braceCount++;
        if (cryptosData.charAt(i) == '}') braceCount--;
        if (braceCount == 0) {
          objEnd = i;
          break;
        }
      }
      
      if (objEnd > objStart) {
        String cryptoJson = cryptosData.substring(objStart, objEnd + 1);
        Asset newAsset;
        
        // Debug: Print the crypto JSON being parsed
        Serial.println("Parsing crypto JSON: " + cryptoJson.substring(0, min(100, (int)cryptoJson.length())));
        
        // Extract baseCurrency as symbol - handle whitespace
        int currencyStart = cryptoJson.indexOf("\"baseCurrency\":");
        if (currencyStart >= 0) {
          // Find the quote after the colon
          int quoteStart = cryptoJson.indexOf("\"", currencyStart + 15);
          if (quoteStart >= 0) {
            int quoteEnd = cryptoJson.indexOf("\"", quoteStart + 1);
            if (quoteEnd > quoteStart) {
              String rawBaseCurrency = cryptoJson.substring(quoteStart + 1, quoteEnd);
              Serial.println("DEBUG: Raw baseCurrency from API: '" + rawBaseCurrency + "'");
              newAsset.symbol = rawBaseCurrency;
              newAsset.symbol.toUpperCase();
              Serial.println("DEBUG: Final crypto symbol after processing: '" + newAsset.symbol + "'");
            } else {
              newAsset.symbol = "UNKNOWN";
              Serial.println("DEBUG: Could not find end quote for baseCurrency");
            }
          } else {
            newAsset.symbol = "UNKNOWN";
            Serial.println("DEBUG: Could not find start quote for baseCurrency");
          }
        } else {
          newAsset.symbol = "NOCURRENCY";
          Serial.println("DEBUG: baseCurrency field not found in JSON");
        }
        newAsset.name = newAsset.symbol;
        
        // Extract price (lastPrice) - handle numeric values (no quotes)
        int priceStart = cryptoJson.indexOf("\"lastPrice\":");
        if (priceStart >= 0) {
          priceStart += 12;
          // Skip whitespace and colon, look for number start
          while (priceStart < cryptoJson.length() && (cryptoJson.charAt(priceStart) == ' ' || cryptoJson.charAt(priceStart) == ':')) {
            priceStart++;
          }
          int priceEnd = cryptoJson.indexOf(",", priceStart);
          if (priceEnd == -1) priceEnd = cryptoJson.indexOf("}", priceStart);
          if (priceEnd > priceStart) {
            newAsset.price = cryptoJson.substring(priceStart, priceEnd).toFloat();
            Serial.println("Extracted crypto price: " + String(newAsset.price));
          } else {
            newAsset.price = 0.0;
          }
        } else {
          newAsset.price = 0.0;
        }
        
        // Extract change (prcChange) - handle numeric values (no quotes)
        int changeStart = cryptoJson.indexOf("\"prcChange\":");
        if (changeStart >= 0) {
          changeStart += 12;
          // Skip whitespace and colon, look for number start
          while (changeStart < cryptoJson.length() && (cryptoJson.charAt(changeStart) == ' ' || cryptoJson.charAt(changeStart) == ':')) {
            changeStart++;
          }
          int changeEnd = cryptoJson.indexOf(",", changeStart);
          if (changeEnd == -1) changeEnd = cryptoJson.indexOf("}", changeStart);
          if (changeEnd > changeStart) {
            newAsset.change = cryptoJson.substring(changeStart, changeEnd).toFloat();
            Serial.println("Extracted crypto change: " + String(newAsset.change));
          } else {
            newAsset.change = 0.0;
          }
        } else {
          newAsset.change = 0.0;
        }
        
        // Extract changePercent (prcChangePct) - handle numeric values (no quotes)
        int percentStart = cryptoJson.indexOf("\"prcChangePct\":");
        if (percentStart >= 0) {
          percentStart += 15;
          // Skip whitespace and colon, look for number start
          while (percentStart < cryptoJson.length() && (cryptoJson.charAt(percentStart) == ' ' || cryptoJson.charAt(percentStart) == ':')) {
            percentStart++;
          }
          int percentEnd = cryptoJson.indexOf(",", percentStart);
          if (percentEnd == -1) percentEnd = cryptoJson.indexOf("}", percentStart);
          if (percentEnd > percentStart) {
            newAsset.changePercent = cryptoJson.substring(percentStart, percentEnd).toFloat();
            Serial.println("Extracted crypto changePercent: " + String(newAsset.changePercent));
          } else {
            newAsset.changePercent = 0.0;
          }
        } else {
          newAsset.changePercent = 0.0;
        }
        
        newAsset.type = "crypto";
        newAsset.isValid = true;
        newAsset.lastUpdate = millis();
        
        assets[assetIndex] = newAsset;
        Serial.print("Parsed crypto: ");
        Serial.print(newAsset.symbol);
        Serial.print(" $");
        Serial.print(newAsset.price);
        Serial.print(" (");
        Serial.print(newAsset.changePercent);
        Serial.println("%)");
        assetIndex++;
        
        cryptosData = cryptosData.substring(objEnd + 1);
      } else {
        break;
      }
    }
  }
  
  // Parse forex array (handle whitespace around brackets)
  int forexStart = jsonData.indexOf("\"forex\":", dataStart);
  Serial.println("Forex search result: " + String(forexStart));
  if (forexStart >= 0) {
    Serial.println("Found forex array at position " + String(forexStart));
    int arrayStart = jsonData.indexOf("[", forexStart) + 1;
    int arrayEnd = jsonData.indexOf("]", arrayStart);
    String forexData = jsonData.substring(arrayStart, arrayEnd);
    
    while (forexData.indexOf("{") >= 0 && assetIndex < RAM_CACHE_SIZE) {
      int objStart = forexData.indexOf("{");
      
      // Find matching closing brace by counting braces
      int braceCount = 0;
      int objEnd = objStart;
      for (int i = objStart; i < forexData.length(); i++) {
        if (forexData.charAt(i) == '{') braceCount++;
        if (forexData.charAt(i) == '}') braceCount--;
        if (braceCount == 0) {
          objEnd = i;
          break;
        }
      }
      
      if (objEnd > objStart) {
        String forexJson = forexData.substring(objStart, objEnd + 1);
        Asset newAsset;
        
        // Debug: Print the forex JSON being parsed
        Serial.println("Parsing forex JSON: " + forexJson.substring(0, min(100, (int)forexJson.length())));
        
        // Extract ticker - handle whitespace
        int tickerStart = forexJson.indexOf("\"ticker\":");
        if (tickerStart >= 0) {
          // Find the quote after the colon
          int quoteStart = forexJson.indexOf("\"", tickerStart + 9);
          if (quoteStart >= 0) {
            int quoteEnd = forexJson.indexOf("\"", quoteStart + 1);
            if (quoteEnd > quoteStart) {
              String ticker = forexJson.substring(quoteStart + 1, quoteEnd);
              newAsset.symbol = formatForexPair(ticker); // Convert "audsgd" to "AUD/SGD"
              Serial.println("Extracted forex ticker: " + ticker + " -> " + newAsset.symbol);
            } else {
              newAsset.symbol = "NOFOREX";
            }
          } else {
            newAsset.symbol = "NOFOREX";
          }
        } else {
          newAsset.symbol = "NOFOREX";
        }
        newAsset.name = newAsset.symbol;
        
        // Extract price (mid_price) - handle whitespace
        int priceStart = forexJson.indexOf("\"mid_price\":");
        if (priceStart >= 0) {
          // Find the quote after the colon
          int quoteStart = forexJson.indexOf("\"", priceStart + 12);
          if (quoteStart >= 0) {
            int quoteEnd = forexJson.indexOf("\"", quoteStart + 1);
            if (quoteEnd > quoteStart) {
              newAsset.price = forexJson.substring(quoteStart + 1, quoteEnd).toFloat();
              Serial.println("Extracted forex price: " + String(newAsset.price));
            } else {
              newAsset.price = 0.0;
            }
          } else {
            newAsset.price = 0.0;
          }
        } else {
          newAsset.price = 0.0;
        }
        
        // Forex doesn't have change data in this format, set to 0
        newAsset.change = 0.0;
        newAsset.changePercent = 0.0;
        
        newAsset.type = "forex";
        newAsset.isValid = true;
        newAsset.lastUpdate = millis();
        
        assets[assetIndex] = newAsset;
        assetIndex++;
        
        forexData = forexData.substring(objEnd + 1);
      } else {
        break;
      }
    }
  }
  
  // Update counts
  assetCount = assetIndex;
  totalPages = (assetCount + ASSETS_PER_PAGE - 1) / ASSETS_PER_PAGE;
  
  // Ensure currentAssetPage is within bounds
  if (currentAssetPage >= totalPages) {
    currentAssetPage = 0;
  }
  
  Serial.println("=== Parsing complete ===");
  Serial.println("Total assets loaded: " + String(assetCount));
  Serial.println("Assets per page: " + String(ASSETS_PER_PAGE));
  Serial.println("Total pages: " + String(totalPages));
  Serial.println("Current page: " + String(currentAssetPage + 1));
  
  // Update the last data update time on successful parse
  if (assetCount > 0) {
    lastDataUpdate = millis();
    Serial.println("Data update time recorded");
  }
  
  // Print first few assets for verification
  for (int i = 0; i < min(3, assetCount); i++) {
    Serial.print("Asset " + String(i) + ": ");
    Serial.print(assets[i].symbol + " ");
    Serial.print("$" + String(assets[i].price, 2) + " ");
    Serial.print("(" + String(assets[i].changePercent, 2) + "%) ");
    Serial.println(assets[i].type);
  }
  
  // Restore viewing state if possible
  if (currentViewedSymbol.length() > 0) {
    for (int i = 0; i < assetCount; i++) {
      if (assets[i].symbol == currentViewedSymbol) {
        currentSingleAsset = i;
        Serial.println("Restored view of " + currentViewedSymbol + " at index " + String(i));
        break;
      }
    }
  }
}

void handleTickerApp() {
  // Add simple debugging when in single view to catch unwanted changes
  static int lastSingleAsset = -1;
  if (currentTickerState == TICKER_SINGLE && currentSingleAsset != lastSingleAsset) {
    Serial.println("*** SINGLE ASSET CHANGED: " + String(lastSingleAsset) + " -> " + String(currentSingleAsset) + " ***");
    lastSingleAsset = currentSingleAsset;
  }
  
  // Check for data updates
  if (millis() - lastDataUpdate > DATA_UPDATE_INTERVAL) {
    if (credentials.isProvisioned) {
      // Call HMAC authenticated version from api_functions.ino
      fetchTickerData();
    } else {
      // Fallback to legacy version
      fetchTickerData();
    }
    // lastDataUpdate is now set in updateLocalData() or parseTickerData() after successful parsing
  }
  
  // Handle auto mode cycling - only when not paused
  if (autoMode && !autoModePaused && millis() - lastAutoUpdate > autoInterval) {
    Serial.println("*** AUTO CYCLING TRIGGERED ***");
    Serial.println("autoMode: " + String(autoMode) + ", paused: " + String(autoModePaused) + ", state: " + String(currentTickerState));
    // Cycle in grid mode AND Single Asset Mode (but not temporary single view)
    if (currentTickerState == TICKER_GRID) {
      // Grid mode page cycling - with safety checks
      if (totalPages > 1) {  // Only cycle if there are multiple pages
        currentAssetPage++;
        if (currentAssetPage >= totalPages) {
          currentAssetPage = 0;
        }
        Serial.println("Auto mode: Switched to page " + String(currentAssetPage + 1) + "/" + String(totalPages));
      } else {
        // If only one page, stay on page 0
        currentAssetPage = 0;
      }
      
      lastAutoUpdate = millis();
      // Use efficient update for auto mode to avoid flicker
      updateGridOnly();
    } else if (currentTickerState == TICKER_SINGLE && !isTemporarySingleView) {
      // Single Asset Mode auto-cycling - cycle through individual assets
      if (assetCount > 1) {  // Only cycle if there are multiple assets
        currentSingleAsset++;
        if (currentSingleAsset >= assetCount) {
          currentSingleAsset = 0;
        }
        Serial.println("Single Asset Mode: Auto cycled to asset " + String(currentSingleAsset + 1) + "/" + String(assetCount));
      }
      
      lastAutoUpdate = millis();
      showTickerApp();  // Full refresh for single asset mode
    }
  }
  
  // Global touch lockout check - EXEMPT Back button from lockout for better UX
  bool isBackButtonArea = (touchY <= 30 && touchX >= 5 && touchX <= 80 && currentTickerState == TICKER_SINGLE);
  if (!isBackButtonArea && millis() - globalTouchLockout < GLOBAL_LOCKOUT_DURATION) {
    return;  // Skip non-back-button touch processing during lockout
  }
  
  // Handle touch input - ULTRA RESPONSIVE MODE with navigation context
  if (getTouchPoint(touchX, touchY, TOUCH_NAVIGATION)) {
    Serial.println("=== TOUCH DETECTED IN MAIN LOOP ===");
    Serial.print("*** TOUCH COORDINATES: X="); Serial.print(touchX); Serial.print(" Y="); Serial.print(touchY);
    Serial.print(" State="); Serial.print(currentTickerState); Serial.print(" Auto="); Serial.print(autoMode);
    Serial.print(" Paused="); Serial.println(autoModePaused);
    // Check title bar touches
    if (touchY <= 30) {
      if (currentTickerState == TICKER_SETTINGS) {
        // Any touch in title bar goes back from settings
        if (displayMode == MODE_SINGLE) {
          currentTickerState = TICKER_SINGLE;
          isTemporarySingleView = false;  // Going back to permanent Single Asset Mode
        } else {
          currentTickerState = TICKER_GRID;
        }
        showTickerApp();
      } else if (currentTickerState == TICKER_SINGLE) {
        // Back button in single view - ULTRA RESPONSIVE - ALWAYS works
        Serial.println("=== SINGLE VIEW DETECTED ===");
        Serial.print("COORDINATES: X="); Serial.print(touchX); Serial.print(" Y="); Serial.println(touchY);
        Serial.println("PRESSURE: Available via internal touch detection");
        
        // EXPANDED BACK BUTTON AREA - more forgiving
        if (touchX >= 0 && touchX <= 85 && touchY >= 0 && touchY <= 35) {
          Serial.println("*** BACK BUTTON HIT - IMMEDIATE RETURN TO GRID ***");
          Serial.println("*** BYPASSING ALL DELAYS AND LOCKOUTS ***");
          
          // IMMEDIATE STATE CHANGE - NO DELAYS  
          if (isTemporarySingleView) {
            // Temporary single view - return to grid
            currentTickerState = TICKER_GRID;
            isTemporarySingleView = false;
          } else {
            // Single Asset Mode - should not happen as it doesn't show Back button
            currentTickerState = TICKER_SINGLE;
          }
          
          // Reset auto mode if needed
          if (autoMode && autoModePaused) {
            autoModePaused = false;
            Serial.println("Auto cycling resumed");
          }
          
          // IMMEDIATE DISPLAY UPDATE
          showTickerApp();
          
          // Reset all touch state for clean slate
          touchCurrentlyPressed = false;
          touchProcessed = false;
          navigationPerformed = false;
          touchX = -1;
          touchY = -1;
          
          Serial.println("*** BACK BUTTON PROCESSING COMPLETE ***");
          return;  // Exit immediately
        } else {
          Serial.print("Touch OUTSIDE expanded Back area (0-85, 0-35): X=");
          Serial.print(touchX); Serial.print(" Y="); Serial.println(touchY);
          
          // In Single Asset Mode (not temporary), also handle Settings/Auto/Manual buttons
          if (!isTemporarySingleView) {
            // Settings button - updated coordinates
            if (touchX >= 130 && touchX <= 190 && (!autoMode || autoModePaused)) {
              Serial.println("Settings button pressed in Single Asset Mode");
              currentTickerState = TICKER_SETTINGS;
              showTickerApp();
              return;
            }
            
            // Auto button - updated coordinates for new position
            if (touchX >= 200 && touchX <= 240) {
              if (millis() - lastModeSwitch > MODE_SWITCH_DELAY) {
                Serial.println("Auto button pressed in Single Asset Mode");
                autoMode = true;
                autoModePaused = false;
                lastAutoUpdate = millis();
                lastModeSwitch = millis();
                showTickerApp();
                return;
              }
            }
            
            // Manual button - updated coordinates for new position
            if (touchX >= 245 && touchX <= 290) {
              if (millis() - lastModeSwitch > MODE_SWITCH_DELAY) {
                Serial.println("Manual button pressed in Single Asset Mode");
                autoMode = false;
                autoModePaused = false;
                lastModeSwitch = millis();
                showTickerApp();
                return;
              }
            }
          }
        }
      } else if (!autoMode || autoModePaused) {
        // Top bar controls (works for both auto paused and manual modes)
        if (totalPages > 1) {
          // Page navigation arrows
          if (touchX >= 10 && touchX <= 35 && currentAssetPage > 0) {
            // Previous page
            currentAssetPage--;
            showTickerApp();
          } else if (touchX >= 75 && touchX <= 100 && currentAssetPage < totalPages - 1) {
            // Next page
            currentAssetPage++;
            showTickerApp();
          }
        }
        
        // Settings button - updated coordinates
        if (touchX >= 130 && touchX <= 190) {
          currentTickerState = TICKER_SETTINGS;
          showTickerApp();
        }
      }
        
        // Auto button - updated coordinates for new position
        if (touchX >= 200 && touchX <= 240 && touchY >= 5 && touchY <= 25) {
          if (millis() - lastModeSwitch > MODE_SWITCH_DELAY) {
            autoMode = true;
            autoModePaused = false;  // Ensure auto cycling is not paused
            lastAutoUpdate = millis();
            lastModeSwitch = millis();
            // Only reset page if in grid mode
            if (currentTickerState == TICKER_GRID) {
              currentAssetPage = 0;  // Reset to first page when entering auto mode
            }
            Serial.println("Switched to auto mode");
            showTickerApp();
          }
        }
        
        // Manual button - updated coordinates for new position
        if (touchX >= 245 && touchX <= 290 && touchY >= 5 && touchY <= 25) {
          if (millis() - lastModeSwitch > MODE_SWITCH_DELAY) {
            autoMode = false;
            autoModePaused = false;  // Clear any pause state
            lastModeSwitch = millis();
            Serial.println("Switched to manual mode");
            showTickerApp();
          }
        }
      }
    }
    
    // Handle content area touches based on state
    if (currentTickerState == TICKER_SETTINGS) {
      handleSettingsTouch();
    } else if (currentTickerState == TICKER_DEVICE_SETTINGS) {
      handleDeviceSettingsTouch();
      // Handle confirmation dialogs based on current state
      if (currentDialogState == DIALOG_REPROVISION) {
        handleReProvisionConfirmTouch();
      } else if (currentDialogState == DIALOG_CLEAR_DATA) {
        handleClearDataConfirmTouch();
      } else if (currentDialogState == DIALOG_FINAL_ERASE) {
        handleFinalEraseWarningTouch();
      }
    } else if (currentTickerState == TICKER_SINGLE) {
      // Single asset navigation (works in both manual mode and paused auto)
      if (!autoMode || autoModePaused) {
        // Previous asset - left side of screen (expanded touch area)
        if (touchX >= 10 && touchX <= 60 && touchY >= 90 && touchY <= 150) {
          Serial.print("PREV AREA TOUCHED: asset="); Serial.print(currentSingleAsset);
          Serial.print(" coords="); Serial.print(touchX); Serial.print(","); Serial.println(touchY);
          
          if (currentSingleAsset > 0) {
            currentSingleAsset--;
            Serial.println("*** PREVIOUS NAVIGATION: " + String(currentSingleAsset) + " ***");
            showTickerApp();
          } else {
            Serial.println("Already at first asset");
          }
          return;
        }
        
        // Next asset - right side of screen (expanded touch area)
        if (touchX >= 260 && touchX <= 310 && touchY >= 90 && touchY <= 150) {
          Serial.print("NEXT AREA TOUCHED: asset="); Serial.print(currentSingleAsset);
          Serial.print(" coords="); Serial.print(touchX); Serial.print(","); Serial.println(touchY);
          
          if (currentSingleAsset < assetCount - 1) {
            currentSingleAsset++;
            Serial.println("*** NEXT NAVIGATION: " + String(currentSingleAsset) + " ***");
            showTickerApp();
          } else {
            Serial.println("Already at last asset");
          }
          return;
        }
      }
    } else {
      // Grid mode - check for asset cell touches
      int cellWidth = 106;
      int cellHeight = 65;  // Updated to match new cell height
      int startX = 1;
      int startY = 32;
      
      for (int i = 0; i < 9; i++) {
        int row = i / 3;
        int col = i % 3;
        int x = startX + (col * cellWidth);
        int y = startY + (row * cellHeight);
        
        if (touchX >= x && touchX <= x + cellWidth && 
            touchY >= y && touchY <= y + cellHeight) {
          int assetIdx = currentAssetPage * ASSETS_PER_PAGE + i;
          if (assetIdx < assetCount) {
            currentSingleAsset = assetIdx;
            currentTickerState = TICKER_SINGLE;
            isTemporarySingleView = true;  // This is temporary single view from grid click
            
            // Pause auto cycling when viewing single ticker (keep autoMode true)
            if (autoMode) {
              autoModePaused = true;
              lastAutoUpdate = millis();  // Reset auto update timer to prevent immediate cycling
              Serial.println("Auto cycling paused - viewing single asset (resetted timer)");
            }
            
            showTickerApp();
            break;
          }
        }
      }
      
      // Navigation arrows removed - now handled in top bar
    }
  }

void loop() {
  // Touch input is now handled directly within each state handler using getTouchPoint()

  switch (currentAppState) {
    case TOUCH_CALIBRATION:
      handleCalibrationTouch();
      break;

    case WIFI_SETUP:
      if (currentWiFiState == WIFI_SCAN) {
        scanNetworks();
      } else {
        handleWiFiConfig();
      }
      break;

    case PROVISIONING_CHECK:
      Serial.println("In PROVISIONING_CHECK case, calling handleProvisioningCheckTouch()");
      handleProvisioningCheckTouch();
      break;

    case PROVISIONING_ENTRY:
      handleProvisioningEntryTouch();
      break;

    case PROVISIONING_ACTIVATE:
      // Handle provisioning activation
      if (provisioningInProgress && (millis() - provisioningStartTime > 1000)) {
        // Attempt device registration
        if (registerDevice(enteredProvisionKey)) {
          currentAppState = TICKER_APP;
          drawProvisioningSuccess();
          delay(2000);
        } else {
          provisioningInProgress = false;
          currentAppState = PROVISIONING_ERROR;
          drawProvisioningError();
        }
      } else if (provisioningInProgress) {
        drawProvisioningProgress();
      }
      break;

    case PROVISIONING_ERROR:
      handleProvisioningErrorTouch();
      break;

    case TICKER_APP:
      static bool firstRun = true;
      if (firstRun) {
        // Initialize NTP for timestamps
        timeClient.begin();
        timeClient.update();

        // Show loading message instead of "No data" flash
        tft.fillScreen(BG_COLOR);
        tft.setTextColor(TEXT_COLOR);
        tft.drawCentreString("Loading ticker data...", 160, 120, 2);

        // Reset auto-cycling timer and ensure we start on page 1
        lastAutoUpdate = millis();
        currentAssetPage = 0;

        // Fetch data first, then show the app
        if (localHubMode || credentials.isProvisioned) {
          // Call the HMAC authenticated version from api_functions.ino
          fetchTickerData();
        } else {
          // Call the legacy version (shouldn't happen with new flow)
          Serial.println("[WARNING] Device not provisioned in ticker app");
        }
        showTickerApp();
        firstRun = false;
      }
      handleTickerApp();
      break;
  }
  
  delay(10);
}

// ============ CALIBRATION FUNCTIONS ============

void startTouchCalibration() {
  Serial.println("Starting touch calibration...");
  currentCalibPoint = 0;
  sampleCount = 0;
  collectingSamples = false;
  showCalibrationPoint();
}

void showCalibrationPoint() {
  tft.fillScreen(BG_COLOR);
  
  // Title
  tft.setTextColor(TEXT_COLOR);
  tft.drawCentreString("Touch Screen Calibration", 160, 10, 2);
  
  // Instructions
  tft.drawCentreString("Tap precisely on the center", 160, 40, 1);
  tft.drawCentreString("of the crosshair", 160, 55, 1);
  
  // Progress
  String progress = "Point " + String(currentCalibPoint + 1) + " of 6";
  tft.drawCentreString(progress, 160, 80, 1);
  
  // Draw crosshair at calibration point
  int x = calibPoints[currentCalibPoint][0];
  int y = calibPoints[currentCalibPoint][1];
  
  // Draw crosshair
  tft.drawLine(x - 15, y, x + 15, y, TFT_RED);
  tft.drawLine(x, y - 15, x, y + 15, TFT_RED);
  tft.fillCircle(x, y, 3, TFT_RED);
  
  // Sample count if collecting
  if (collectingSamples) {
    String samples = "Samples: " + String(sampleCount) + "/100";
    tft.drawCentreString(samples, 160, 220, 1);
  } else {
    tft.drawCentreString("Tap to start collecting samples", 160, 220, 1);
  }
  
  Serial.print("Calibration point ");
  Serial.print(currentCalibPoint + 1);
  Serial.print(" at screen (");
  Serial.print(x);
  Serial.print(",");
  Serial.print(y);
  Serial.println(")");
}

void handleCalibrationTouch() {
  int rawX, rawY;
  
  // Debug: Always try to read raw touch values
  uint16_t testX = readTouchRaw(0xD0);
  uint16_t testY = readTouchRaw(0x90);
  
  // Show raw values if they look like valid touch
  if (testX > 200 && testX < 3900 && testY > 200 && testY < 3900) {
    Serial.print("Raw touch detected: (");
    Serial.print(testX);
    Serial.print(",");
    Serial.print(testY);
    Serial.println(")");
  }
  
  // Try getTouchPoint first, but also check for simple touch detection
  bool touchDetected = getTouchPoint(rawX, rawY);
  if (!touchDetected && testX > 200 && testX < 3900 && testY > 200 && testY < 3900) {
    // Fallback: use raw values directly
    if (millis() - lastTouchTime > 200) { // Simple debounce
      rawX = testX;
      rawY = testY;
      touchDetected = true;
      lastTouchTime = millis();
      Serial.println("Using fallback touch detection");
    }
  }
  
  if (touchDetected) {
    Serial.print("Touch processed: (");
    Serial.print(rawX);
    Serial.print(",");
    Serial.print(rawY);
    Serial.println(")");
    
    if (!collectingSamples) {
      // Start collecting samples
      collectingSamples = true;
      sampleCount = 0;
      Serial.println("Started collecting samples...");
      showCalibrationPoint();
      delay(200); // Debounce
      return;
    }
    
    // Collect sample (only need 1 sample per point for quick calibration)
    if (sampleCount < 1) {
      touchSamples[currentCalibPoint][sampleCount][0] = rawX;
      touchSamples[currentCalibPoint][sampleCount][1] = rawY;
      sampleCount++;

      Serial.print("Sample ");
      Serial.print(sampleCount);
      Serial.print(": (");
      Serial.print(rawX);
      Serial.print(",");
      Serial.print(rawY);
      Serial.println(")");
    }

    // Check if we have enough samples
    if (sampleCount >= 1) {
      collectingSamples = false;
      currentCalibPoint++;
      
      if (currentCalibPoint >= 6) {
        // All points collected, calculate calibration
        Serial.println("All calibration points collected!");
        calculateCalibrationCoefficients();
        saveCalibration();
        
        // Show completion message
        tft.fillScreen(BG_COLOR);
        tft.setTextColor(SUCCESS_COLOR);
        tft.drawCentreString("Calibration Complete!", 160, 100, 2);
        tft.setTextColor(TEXT_COLOR);
        tft.drawCentreString("Touch screen is now calibrated", 160, 130, 1);
        tft.drawCentreString("Continuing to WiFi setup...", 160, 150, 1);
        
        delay(3000);
        
        // Continue to WiFi setup
        currentAppState = WIFI_SETUP;
      } else {
        // Move to next calibration point
        delay(500);
        showCalibrationPoint();
      }
    }
    
    delay(50); // Sample rate limiting
  }
}

void calculateCalibrationCoefficients() {
  Serial.println("Calculating calibration coefficients...");
  
  // Use single sample for each calibration point (no averaging needed)
  float avgPoints[6][2];
  for (int i = 0; i < 6; i++) {
    avgPoints[i][0] = touchSamples[i][0][0];  // Just use the first (and only) sample
    avgPoints[i][1] = touchSamples[i][0][1];
    
    Serial.print("Point ");
    Serial.print(i);
    Serial.print(" avg: (");
    Serial.print(avgPoints[i][0]);
    Serial.print(",");
    Serial.print(avgPoints[i][1]);
    Serial.println(")");
  }
  
  // Use 3-point calibration with first 3 points for simplicity
  // More robust would be least squares fit with all 6 points
  
  float x1 = avgPoints[0][0], y1 = avgPoints[0][1]; // Touch coordinates
  float x2 = avgPoints[1][0], y2 = avgPoints[1][1];
  float x3 = avgPoints[2][0], y3 = avgPoints[2][1];
  
  float xd1 = calibPoints[0][0], yd1 = calibPoints[0][1]; // Display coordinates
  float xd2 = calibPoints[1][0], yd2 = calibPoints[1][1];
  float xd3 = calibPoints[2][0], yd3 = calibPoints[2][1];
  
  // Calculate denominator for the matrix solution
  float denom = (x1 - x3) * (y2 - y3) - (x2 - x3) * (y1 - y3);
  
  if (abs(denom) < 0.1) {
    Serial.println("Error: Calibration points are collinear!");
    touchCal.isCalibrated = false;
    return;
  }
  
  // Calculate X transformation coefficients
  touchCal.alphaX = ((xd1 - xd3) * (y2 - y3) - (xd2 - xd3) * (y1 - y3)) / denom;
  touchCal.betaX = ((x1 - x3) * (xd2 - xd3) - (x2 - x3) * (xd1 - xd3)) / denom;
  touchCal.deltaX = xd3 - touchCal.alphaX * x3 - touchCal.betaX * y3;
  
  // Calculate Y transformation coefficients  
  touchCal.alphaY = ((yd1 - yd3) * (y2 - y3) - (yd2 - yd3) * (y1 - y3)) / denom;
  touchCal.betaY = ((x1 - x3) * (yd2 - yd3) - (x2 - x3) * (yd1 - yd3)) / denom;
  touchCal.deltaY = yd3 - touchCal.alphaY * x3 - touchCal.betaY * y3;
  
  touchCal.isCalibrated = true;
  
  Serial.println("Calibration coefficients:");
  Serial.print("alphaX: "); Serial.println(touchCal.alphaX);
  Serial.print("betaX: "); Serial.println(touchCal.betaX);
  Serial.print("deltaX: "); Serial.println(touchCal.deltaX);
  Serial.print("alphaY: "); Serial.println(touchCal.alphaY);
  Serial.print("betaY: "); Serial.println(touchCal.betaY);
  Serial.print("deltaY: "); Serial.println(touchCal.deltaY);
}

void saveCalibration() {
  Serial.println("Saving calibration to NVS...");
  preferences.begin("cyd_ticker", false);
  preferences.putFloat("alphaX", touchCal.alphaX);
  preferences.putFloat("betaX", touchCal.betaX);
  preferences.putFloat("deltaX", touchCal.deltaX);
  preferences.putFloat("alphaY", touchCal.alphaY);
  preferences.putFloat("betaY", touchCal.betaY);
  preferences.putFloat("deltaY", touchCal.deltaY);
  preferences.putBool("calibrated", true);
  preferences.end();
  Serial.println("Calibration saved!");
}

void loadCalibration() {
  preferences.begin("cyd_ticker", true);  // Read-only
  touchCal.isCalibrated = preferences.getBool("calibrated", false);
  if (touchCal.isCalibrated) {
    touchCal.alphaX = preferences.getFloat("alphaX", 0);
    touchCal.betaX = preferences.getFloat("betaX", 0);
    touchCal.deltaX = preferences.getFloat("deltaX", 0);
    touchCal.alphaY = preferences.getFloat("alphaY", 0);
    touchCal.betaY = preferences.getFloat("betaY", 0);
    touchCal.deltaY = preferences.getFloat("deltaY", 0);
    
    Serial.println("Loaded calibration from NVS:");
    Serial.print("alphaX: "); Serial.println(touchCal.alphaX);
    Serial.print("betaX: "); Serial.println(touchCal.betaX);  
    Serial.print("deltaX: "); Serial.println(touchCal.deltaX);
    Serial.print("alphaY: "); Serial.println(touchCal.alphaY);
    Serial.print("betaY: "); Serial.println(touchCal.betaY);
    Serial.print("deltaY: "); Serial.println(touchCal.deltaY);
  } else {
    Serial.println("No calibration data found in NVS");
  }
  preferences.end();
}

int applyCalibratedTouch(int rawX, int rawY, int &screenX, int &screenY) {
  if (!touchCal.isCalibrated) {
    return false;
  }
  
  // Apply calibration transformation
  float x = touchCal.alphaX * rawX + touchCal.betaX * rawY + touchCal.deltaX;
  float y = touchCal.alphaY * rawX + touchCal.betaY * rawY + touchCal.deltaY;
  
  // Convert to integers and constrain to screen bounds
  screenX = constrain((int)x, 0, 319);
  screenY = constrain((int)y, 0, 239);
  
  return true;
}
