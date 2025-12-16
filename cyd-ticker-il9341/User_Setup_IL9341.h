  // User_Setup_ILI9341.h
  // TFT_eSPI setup for ESP32-2432S028R CYD using ILI9341 driver
  //
  // INSTRUCTIONS:
  // 1. Backup your current User_Setup.h
  // 2. Copy this file to: Arduino/libraries/TFT_eSPI/User_Setup.h
  // 3. Restart Arduino IDE and upload test code

  #define USER_SETUP_INFO "User_Setup_ILI9341_ESP32_CYD"

  // Use ILI9341 driver (NOT ST7789)
  #define ILI9341_DRIVER

  // Display resolution for ILI9341
  #define TFT_WIDTH  320
  #define TFT_HEIGHT 240

  // ESP32-2432S028R pin assignments
  #define TFT_MISO 12
  #define TFT_MOSI 13
  #define TFT_SCLK 14
  #define TFT_CS   15  // Chip select control pin
  #define TFT_DC    2  // Data Command control pin
  #define TFT_RST   4  // Reset pin

  // Backlight control
  #define TFT_BL   21

  // SPI frequency
  #define SPI_FREQUENCY  40000000
  #define SPI_READ_FREQUENCY  20000000

  // Color order
  #define TFT_RGB_ORDER TFT_BGR

  // Display inversion - commented out for ILI9341
  // #define TFT_INVERSION_OFF

  // Load fonts
  #define LOAD_GLCD
  #define LOAD_FONT2
  #define LOAD_FONT4
  #define LOAD_FONT6
  #define LOAD_FONT7
  #define LOAD_FONT8
  #define LOAD_GFXFF

  #define SMOOTH_FONT