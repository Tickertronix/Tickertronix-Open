// User_Setup_ST7789.h
// TFT_eSPI setup for CYD ST7789 displays (TPM408-2.8 and similar)
// CORRECTED VERSION - Fixes color display issues
//
// CRITICAL INSTALLATION INSTRUCTIONS:
// ====================================
// This file MUST be copied to your TFT_eSPI library folder:
//
// Windows:
//   C:\Users\[YourUsername]\Documents\Arduino\libraries\TFT_eSPI\User_Setup.h
//
// Mac/Linux:
//   ~/Arduino/libraries/TFT_eSPI/User_Setup.h
//
// STEPS:
// 1. Locate your TFT_eSPI library folder
// 2. BACKUP the existing User_Setup.h file (rename to User_Setup_backup.h)
// 3. Copy THIS file and rename it to User_Setup.h
// 4. Restart Arduino IDE
// 5. Upload the CYD_ST7789_Complete.ino firmware
//
// TROUBLESHOOTING:
// - If colors are inverted: Check TFT_INVERSION_OFF is set
// - If colors are wrong: Verify TFT_RGB_ORDER is TFT_BGR
// - If display is blank: Verify ST7789_DRIVER is defined (not ILI9341)

#define USER_SETUP_INFO "User_Setup_ST7789_CYD_CORRECTED"

// ============================================================
// CRITICAL: Use ST7789 driver (NOT ILI9341)
// ============================================================
#define ST7789_DRIVER

// Display resolution for ST7789
// Native portrait: 240x320, rotates to landscape: 320x240
#define TFT_WIDTH  240
#define TFT_HEIGHT 320

// ST7789 Column/Row offsets - CRITICAL for proper display alignment
// Remove CGRAM_OFFSET definition to allow offsets to work
// #define CGRAM_OFFSET  // COMMENTED OUT to enable offset control
// Try these offsets for proper alignment:
#define TFT_COL_OFFSET 0
#define TFT_ROW_OFFSET 0

// ============================================================
// ESP32 CYD Pin Assignments (Standard ESP32-2432S028)
// ============================================================
#define TFT_MISO 12
#define TFT_MOSI 13
#define TFT_SCLK 14
#define TFT_CS   15  // Chip select control pin
#define TFT_DC    2  // Data Command control pin
#define TFT_RST   4  // Reset pin (CRITICAL: Must be 4)

// Backlight control
#define TFT_BL   21  // Backlight PWM control

// ============================================================
// SPI Frequency Settings
// ============================================================
#define SPI_FREQUENCY  40000000   // 40MHz for write operations
#define SPI_READ_FREQUENCY  20000000  // 20MHz for read operations

// ============================================================
// CRITICAL FIX #1: Color Order
// ST7789 on TPM408-2.8 uses BGR color order (NOT RGB)
// ============================================================
#define TFT_RGB_ORDER TFT_BGR

// ============================================================
// CRITICAL FIX #2: Display Inversion
// ST7789 on TPM408-2.8 needs inversion OFF for correct colors
// ============================================================
#define TFT_INVERSION_OFF

// ============================================================
// Font Loading
// ============================================================
#define LOAD_GLCD   // Basic font
#define LOAD_FONT2  // Small 16 pixel high font
#define LOAD_FONT4  // Medium 26 pixel high font
#define LOAD_FONT6  // Large 48 pixel high font
#define LOAD_FONT7  // 7 segment 48 pixel high font
#define LOAD_FONT8  // Large 75 pixel high font
#define LOAD_GFXFF  // FreeFonts

#define SMOOTH_FONT // Enable anti-aliasing

// ============================================================
// DIFFERENCES FROM ILI9341 SETUP:
// ============================================================
// 1. Driver changed from ILI9341_DRIVER to ST7789_DRIVER
// 2. Color order changed from TFT_RGB to TFT_BGR
// 3. Inversion changed from TFT_INVERSION_ON to TFT_INVERSION_OFF
// 4. All other settings (pins, SPI frequency) remain identical
//
// NOTE: The Arduino code (CYD_Complete_System.ino) does NOT need
//       any modifications. Only this library configuration file
//       needs to be changed.
