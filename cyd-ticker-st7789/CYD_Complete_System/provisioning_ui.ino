// ========== PROVISIONING UI FUNCTIONS ==========

// Forward declaration
void drawProvisioningKey(int row, int col, const char* label, bool pressed = false);

void drawProvisioningCheck() {
  tft.fillScreen(BG_COLOR);
  tft.setTextColor(TEXT_COLOR);

  // Title
  tft.drawCentreString("Device Setup", 160, 30, 2);

  // Status
  tft.drawCentreString("Device needs to be provisioned", 160, 70, 1);
  tft.drawCentreString("to connect to your account", 160, 90, 1);

  // Instructions
  tft.drawCentreString("1. Open Tickertronix mobile app", 160, 120, 1);
  tft.drawCentreString("2. Go to Settings > DIY Hardware", 160, 140, 1);
  tft.drawCentreString("3. Tap 'Add New Device'", 160, 160, 1);
  tft.drawCentreString("4. Select 'ESP32 Display'", 160, 180, 1);

  // Button
  tft.fillRoundRect(110, 200, 100, 30, 5, BUTTON_GRAY);
  tft.setTextColor(WHITE);
  tft.drawCentreString("Continue", 160, 210, 1);
  tft.setTextColor(TEXT_COLOR);
}

void handleProvisioningCheckTouch() {
  // Use general context for button touches
  if (getTouchPoint(touchX, touchY, TOUCH_GENERAL)) {
    Serial.println("Touch detected in PROVISIONING_CHECK: X=" + String(touchX) + " Y=" + String(touchY));

    // Check if Continue button was pressed (expanded touch area for better responsiveness)
    if (touchX >= 100 && touchX <= 220 && touchY >= 190 && touchY <= 240) {
      Serial.println("Continue button pressed! Advancing to provisioning entry...");
      currentAppState = PROVISIONING_ENTRY;
      enteredProvisionKey = "";
      provisioningError = "";
      drawProvisioningEntry(); // Draw the new screen immediately
    } else {
      Serial.println("Touch outside Continue button area. X=" + String(touchX) + " Y=" + String(touchY));
    }
  }
}

void drawProvisioningEntry() {
  tft.fillScreen(BG_COLOR);
  tft.setTextColor(TEXT_COLOR);

  // Title - adjusted for landscape 320x240
  tft.drawCentreString("Enter Provisioning Code", 160, 10, 2);

  // Input field
  drawProvisioningInput();

  // Keyboard layout for provisioning
  drawProvisioningKeyboard();

  // Instructions - moved higher for landscape
  tft.setTextColor(YELLOW_COLOR);
  tft.drawCentreString("Get code from mobile app", 160, 220, 1);
}

void drawProvisioningInput() {
  // Input field background - adjusted for landscape
  tft.fillRoundRect(20, 30, 280, 25, 3, WHITE);
  tft.drawRoundRect(20, 30, 280, 25, 3, BORDER_COLOR);

  // Format the entered key with dashes
  String displayKey = formatProvKeyForDisplay(enteredProvisionKey);

  // Display the formatted key
  tft.setTextColor(BLACK);
  tft.drawString(displayKey, 25, 38, 1);

  // Cursor
  if ((millis() / 500) % 2) {
    int cursorX = 25 + tft.textWidth(displayKey, 1);
    if (cursorX < 295) {
      tft.drawFastVLine(cursorX, 35, 12, BLACK);
    }
  }

  tft.setTextColor(TEXT_COLOR);
}

String formatProvKeyForDisplay(String input) {
  // Remove any existing dashes
  String clean = input;
  clean.replace("-", "");
  clean.toUpperCase();

  // Add PROV- prefix
  String display = "PROV-";

  // Add characters with formatting
  for (int i = 0; i < min(12, (int)clean.length()); i++) {
    if (i > 0 && i % 4 == 0) {
      display += "-";
    }
    display += clean.charAt(i);
  }

  // Add remaining placeholders for incomplete segments
  int remaining = 12 - clean.length();
  for (int i = 0; i < remaining; i++) {
    if ((clean.length() + i) > 0 && (clean.length() + i) % 4 == 0) {
      display += "-";
    }
    display += "_";
  }

  return display;
}

void handleProvisioningEntryTouch() {
  // Use keyboard context for better debouncing on keyboard input
  if (!getTouchPoint(touchX, touchY, TOUCH_KEYBOARD)) return;

  Serial.println("Touch detected in PROVISIONING_ENTRY: X=" + String(touchX) + " Y=" + String(touchY));

  // Handle keyboard input
  String key = handleKeyboardTouch();

  // Only process non-empty keys (empty means debounced/ignored)
  if (key != "") {
    if (key == "Done") {
      // Validate and format the key
      String formatted = hmacAuth.formatProvisionKey(enteredProvisionKey);
      if (hmacAuth.validateProvisionKey(formatted)) {
        enteredProvisionKey = formatted;
        currentAppState = PROVISIONING_ACTIVATE;
        provisioningInProgress = true;
        provisioningStartTime = millis();
        Serial.println("[PROV] Starting activation with key: " + enteredProvisionKey);
      } else {
        provisioningError = "Invalid format - use 12 characters";
        drawProvisioningError();
        delay(2000);
        provisioningError = "";
      }
    } else if (key == "Delete") {
      if (enteredProvisionKey.length() > 0) {
        enteredProvisionKey = enteredProvisionKey.substring(0, enteredProvisionKey.length() - 1);
        Serial.println("Deleted character | Current key: " + enteredProvisionKey);
        drawProvisioningInput();  // Redraw input field
      }
    } else if (key == "Space") {
      // Ignore spaces in provisioning keys
    } else {
      // Only allow alphanumeric characters (no @ or . for provisioning codes)
      if (key.length() == 1 && key != "@" && key != "." && (isAlphaNumeric(key.charAt(0)) || isDigit(key.charAt(0)))) {
        if (enteredProvisionKey.length() < 12) {
          key.toUpperCase();  // Modify key in place
          enteredProvisionKey += key;
          Serial.println("Added character: " + key + " | Current key: " + enteredProvisionKey);
          drawProvisioningInput();  // Redraw input field to show new character
        } else {
          Serial.println("Max length reached - ignoring key: " + key);
        }
      } else {
        Serial.println("Invalid character for provisioning code - ignoring: " + key);
      }
    }
  }
}

String handleKeyboardTouch() {
  // Use exact same touch logic as WiFi keyboard

  // Row 0: Numbers 1-0 (Y: 80-105)
  if (touchY >= 80 && touchY <= 105) {
    if (touchX >= 5 && touchX < 36) { // 1
      return registerProvisioningKeyPress("1", 0, 0);
    } else if (touchX >= 36 && touchX < 67) { // 2
      return registerProvisioningKeyPress("2", 0, 1);
    } else if (touchX >= 67 && touchX < 98) { // 3
      return registerProvisioningKeyPress("3", 0, 2);
    } else if (touchX >= 98 && touchX < 129) { // 4
      return registerProvisioningKeyPress("4", 0, 3);
    } else if (touchX >= 129 && touchX < 160) { // 5
      return registerProvisioningKeyPress("5", 0, 4);
    } else if (touchX >= 160 && touchX < 191) { // 6
      return registerProvisioningKeyPress("6", 0, 5);
    } else if (touchX >= 191 && touchX < 222) { // 7
      return registerProvisioningKeyPress("7", 0, 6);
    } else if (touchX >= 222 && touchX < 253) { // 8
      return registerProvisioningKeyPress("8", 0, 7);
    } else if (touchX >= 253 && touchX < 284) { // 9
      return registerProvisioningKeyPress("9", 0, 8);
    } else if (touchX >= 284 && touchX < 315) { // 0
      return registerProvisioningKeyPress("0", 0, 9);
    }
    return "";
  }

  // Row 1: QWERTY (Y: 108-133)
  if (touchY >= 108 && touchY <= 133) {
    if (touchX >= 5 && touchX < 36) { // q
      return registerProvisioningKeyPress("Q", 1, 0);
    } else if (touchX >= 36 && touchX < 67) { // w
      return registerProvisioningKeyPress("W", 1, 1);
    } else if (touchX >= 67 && touchX < 98) { // e
      return registerProvisioningKeyPress("E", 1, 2);
    } else if (touchX >= 98 && touchX < 129) { // r
      return registerProvisioningKeyPress("R", 1, 3);
    } else if (touchX >= 129 && touchX < 160) { // t
      return registerProvisioningKeyPress("T", 1, 4);
    } else if (touchX >= 160 && touchX < 191) { // y
      return registerProvisioningKeyPress("Y", 1, 5);
    } else if (touchX >= 191 && touchX < 222) { // u
      return registerProvisioningKeyPress("U", 1, 6);
    } else if (touchX >= 222 && touchX < 253) { // i
      return registerProvisioningKeyPress("I", 1, 7);
    } else if (touchX >= 253 && touchX < 284) { // o
      return registerProvisioningKeyPress("O", 1, 8);
    } else if (touchX >= 284 && touchX < 315) { // p
      return registerProvisioningKeyPress("P", 1, 9);
    }
    return "";
  }

  // Row 2: ASDF (Y: 136-161) - 9 keys
  if (touchY >= 136 && touchY <= 161) {
    if (touchX >= 20 && touchX < 51) { // a
      return registerProvisioningKeyPress("A", 2, 0);
    } else if (touchX >= 51 && touchX < 82) { // s
      return registerProvisioningKeyPress("S", 2, 1);
    } else if (touchX >= 82 && touchX < 113) { // d
      return registerProvisioningKeyPress("D", 2, 2);
    } else if (touchX >= 113 && touchX < 144) { // f
      return registerProvisioningKeyPress("F", 2, 3);
    } else if (touchX >= 144 && touchX < 175) { // g
      return registerProvisioningKeyPress("G", 2, 4);
    } else if (touchX >= 175 && touchX < 206) { // h
      return registerProvisioningKeyPress("H", 2, 5);
    } else if (touchX >= 206 && touchX < 237) { // j
      return registerProvisioningKeyPress("J", 2, 6);
    } else if (touchX >= 237 && touchX < 268) { // k
      return registerProvisioningKeyPress("K", 2, 7);
    } else if (touchX >= 268 && touchX < 299) { // l
      return registerProvisioningKeyPress("L", 2, 8);
    }
    return "";
  }

  // Row 3: ZXCV (Y: 164-189) - 9 keys
  if (touchY >= 164 && touchY <= 189) {
    if (touchX >= 20 && touchX < 51) { // z
      return registerProvisioningKeyPress("Z", 3, 0);
    } else if (touchX >= 51 && touchX < 82) { // x
      return registerProvisioningKeyPress("X", 3, 1);
    } else if (touchX >= 82 && touchX < 113) { // c
      return registerProvisioningKeyPress("C", 3, 2);
    } else if (touchX >= 113 && touchX < 144) { // v
      return registerProvisioningKeyPress("V", 3, 3);
    } else if (touchX >= 144 && touchX < 175) { // b
      return registerProvisioningKeyPress("B", 3, 4);
    } else if (touchX >= 175 && touchX < 206) { // n
      return registerProvisioningKeyPress("N", 3, 5);
    } else if (touchX >= 206 && touchX < 237) { // m
      return registerProvisioningKeyPress("M", 3, 6);
    } else if (touchX >= 237 && touchX < 268) { // @
      return registerProvisioningKeyPress("@", 3, 7);
    } else if (touchX >= 268 && touchX < 299) { // .
      return registerProvisioningKeyPress(".", 3, 8);
    }
    return "";
  }

  // Row 4: Space, Delete, Done (Y: 192-217)
  if (touchY >= 192 && touchY <= 217) {
    if (touchX >= 10 && touchX <= 110) { // Space
      return registerProvisioningKeyPress("Space", 4, 0);
    } else if (touchX >= 115 && touchX <= 210) { // Delete
      return registerProvisioningKeyPress("Delete", 4, 1);
    } else if (touchX >= 215 && touchX <= 310) { // Done
      return registerProvisioningKeyPress("Done", 4, 2);
    }
    return "";
  }

  return "";
}

String registerProvisioningKeyPress(String key, int row, int col) {
  unsigned long currentTime = millis();

  Serial.println("registerProvisioningKeyPress called: " + key + " at time: " + String(currentTime) + " (last: " + String(lastKeyPressTime) + ")");

  // Check if enough time has passed since last key press
  if (currentTime - lastKeyPressTime < KEYBOARD_DEBOUNCE_DELAY) {
    Serial.println("Key press ignored - too soon after last press (" + String(currentTime - lastKeyPressTime) + "ms)");
    return "";
  }

  // Check if same key is being pressed repeatedly
  if (key == lastPressedKey && currentTime - lastKeyPressTime < SAME_KEY_DEBOUNCE_DELAY) {
    Serial.println("Same key pressed too quickly - ignoring: " + key);
    return "";
  }

  Serial.print("Provisioning key accepted: ");
  Serial.println(key);

  // Update debounce tracking
  lastKeyPressTime = currentTime;
  lastPressedKey = key;

  // Visual feedback - reduced delay to prevent blocking
  drawProvisioningKey(row, col, key.c_str(), true);
  delay(50); // Reduced from 80ms
  drawProvisioningKey(row, col, key.c_str(), false);

  return key;
}

void drawProvisioningKeyboard() {
  // Use exact same keyboard layout as WiFi setup
  const char* provisioningKeys[] = {
    "1", "2", "3", "4", "5", "6", "7", "8", "9", "0",
    "Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P",
    "A", "S", "D", "F", "G", "H", "J", "K", "L",
    "Z", "X", "C", "V", "B", "N", "M", "@", ".",
    "Space", "Delete", "Done"
  };

  const int provisioningRows = 5;
  const int provisioningCols[] = {10, 10, 9, 9, 3};

  for (int row = 0; row < provisioningRows; row++) {
    for (int col = 0; col < provisioningCols[row]; col++) {
      int keyIndex = 0;
      for (int r = 0; r < row; r++) {
        keyIndex += provisioningCols[r];
      }
      keyIndex += col;

      if (keyIndex < 42) {
        drawProvisioningKey(row, col, provisioningKeys[keyIndex]);
      }
    }
  }
}

void drawProvisioningKey(int row, int col, const char* label, bool pressed) {
  int keyW = 28;
  int keyH = 25;
  int spacing = 3;
  int keyX = 10;
  int keyY = 80;

  const int provisioningCols[] = {10, 10, 9, 9, 3};

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
    int totalWidth = provisioningCols[row] * (keyW + spacing) - spacing;
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

void drawProvisioningProgress() {
  tft.fillScreen(BG_COLOR);
  tft.setTextColor(TEXT_COLOR);

  // Title
  tft.drawCentreString("Activating Device", 160, 80, 2);

  // Progress indicator
  tft.drawCentreString("Connecting to server...", 160, 120, 1);

  // Animated dots
  int dots = ((millis() - provisioningStartTime) / 500) % 4;
  String dotString = "";
  for (int i = 0; i < dots; i++) {
    dotString += ".";
  }
  tft.drawCentreString(dotString, 160, 140, 2);

  // Instructions
  tft.setTextColor(YELLOW_COLOR);
  tft.drawCentreString("Please wait...", 160, 180, 1);
  tft.setTextColor(TEXT_COLOR);
}

void drawProvisioningSuccess() {
  tft.fillScreen(BG_COLOR);
  tft.setTextColor(SUCCESS_COLOR);

  // Success message
  tft.drawCentreString("Device Activated!", 160, 110, 2);

  tft.setTextColor(TEXT_COLOR);
  tft.drawCentreString("Your device is now connected", 160, 140, 1);
  tft.drawCentreString("to your Tickertronix account", 160, 160, 1);
  tft.drawCentreString("Starting ticker display...", 160, 190, 1);
}

void drawProvisioningError() {
  tft.fillScreen(BG_COLOR);
  tft.setTextColor(ERROR_COLOR);

  // Error message
  tft.drawCentreString("Activation Failed", 160, 80, 2);

  tft.setTextColor(TEXT_COLOR);
  tft.drawCentreString(provisioningError, 160, 120, 1);

  // Retry button
  tft.fillRoundRect(110, 160, 100, 30, 5, BUTTON_GRAY);
  tft.setTextColor(WHITE);
  tft.drawCentreString("Try Again", 160, 170, 1);
  tft.setTextColor(TEXT_COLOR);
}

void handleProvisioningErrorTouch() {
  // Use general context for button touches
  if (!getTouchPoint(touchX, touchY, TOUCH_GENERAL)) return;

  Serial.println("Touch detected in PROVISIONING_ERROR: X=" + String(touchX) + " Y=" + String(touchY));

  // Check if Try Again button was pressed
  if (touchX >= 110 && touchX <= 210 && touchY >= 160 && touchY <= 190) {
    Serial.println("Try Again button pressed! Returning to provisioning entry...");
    currentAppState = PROVISIONING_ENTRY;
    provisioningError = "";
    enteredProvisionKey = ""; // Clear any previous input
    drawProvisioningEntry(); // Immediately redraw the screen
    return; // Exit immediately to prevent touch carryover
  }
}