// ========== DEVICE SETTINGS FUNCTIONS ==========

void drawDeviceSettingsMenu() {
  currentDialogState = DIALOG_NONE;  // Reset dialog state
  tft.fillScreen(BG_COLOR);
  tft.setTextColor(TEXT_COLOR);

  // Title
  tft.drawCentreString("Device Settings", 160, 10, 2);

  // Device info section (moved up 15 pixels)
  tft.drawString("Device Information:", 20, 35, 2);

  if (credentials.isProvisioned) {
    tft.setTextColor(SUCCESS_COLOR);
    tft.drawString("Status: Provisioned", 30, 60, 1);
    tft.setTextColor(TEXT_COLOR);
    tft.drawString("Device Key: " + credentials.deviceKey, 30, 75, 1);
    tft.drawString("Hardware ID: " + credentials.hardwareId.substring(0, 8) + "...", 30, 90, 1);
  } else {
    tft.setTextColor(ERROR_COLOR);
    tft.drawString("Status: Not Provisioned", 30, 60, 1);
    tft.setTextColor(TEXT_COLOR);
  }

  // Firmware version (moved up 15 pixels)
  tft.drawString("Firmware: v2.0.0", 30, 105, 1);
  tft.drawString("Display: ST7789 (TPM408)", 30, 120, 1);
  tft.drawString("Hub: " + API_BASE_URL, 30, 135, 1);

  // Action buttons
  int buttonY = 160;
  int buttonHeight = 25;
  int buttonSpacing = 30;

  // Re-provision device button
  tft.fillRoundRect(20, buttonY, 280, buttonHeight, 5, BUTTON_GRAY);
  tft.setTextColor(WHITE);
  tft.drawCentreString("Re-provision Device", 160, buttonY + 8, 1);

  buttonY += buttonSpacing;

  // Clear device data button
  tft.fillRoundRect(20, buttonY, 280, buttonHeight, 5, credentials.isProvisioned ? BUTTON_ORANGE : BUTTON_GRAY);
  tft.setTextColor(WHITE);
  tft.drawCentreString("Clear Device Data", 160, buttonY + 8, 1);

  // Back button (moved to avoid overlap)
  tft.fillRoundRect(250, 220, 60, 25, 5, SELECTED_COLOR);
  tft.setTextColor(WHITE);
  tft.drawCentreString("Back", 280, 228, 1);

  tft.setTextColor(TEXT_COLOR);
}

void handleDeviceSettingsTouch() {
  int x, y;
  if (!getTouchPoint(x, y, TOUCH_GENERAL)) return;

  Serial.print("Device Settings Touch: (");
  Serial.print(x);
  Serial.print(",");
  Serial.print(y);
  Serial.print(") Dialog State: ");
  Serial.println(currentDialogState);

  // Only handle main menu touches when no dialog is active
  if (currentDialogState == DIALOG_NONE) {
    // Re-provision device button
    if (x >= 20 && x <= 300 && y >= 160 && y <= 185) {
      Serial.println("Re-provision button touched!");
      showReProvisionConfirm();
      return;
    }

    // Clear device data button
    if (x >= 20 && x <= 300 && y >= 190 && y <= 215) {
      Serial.println("Clear data button touched!");
      if (credentials.isProvisioned) {
        showClearDataConfirm();
      } else {
        Serial.println("Device not provisioned - Clear data disabled");
      }
      return;
    }

    // Back button (updated coordinates)
    if (x >= 250 && x <= 310 && y >= 220 && y <= 245) {
      Serial.println("Back button touched!");
      currentTickerState = TICKER_SETTINGS;
      drawSettingsMenu();
      return;
    }

    Serial.println("Touch outside button areas");
  } else {
    Serial.println("Dialog active - ignoring main menu touch");
  }
}

void showReProvisionConfirm() {
  currentDialogState = DIALOG_REPROVISION;
  tft.fillScreen(BG_COLOR);
  tft.setTextColor(TEXT_COLOR);

  // Title
  tft.drawCentreString("Re-provision Device", 160, 30, 2);

  // Warning message
  tft.setTextColor(YELLOW_COLOR);
  tft.drawCentreString("This will disconnect the device", 160, 70, 1);
  tft.drawCentreString("from your current account and", 160, 90, 1);
  tft.drawCentreString("require a new provisioning code.", 160, 110, 1);

  tft.setTextColor(TEXT_COLOR);
  tft.drawCentreString("Are you sure you want to continue?", 160, 140, 1);

  // Confirm button
  tft.fillRoundRect(50, 170, 100, 30, 5, ERROR_COLOR);
  tft.setTextColor(WHITE);
  tft.drawCentreString("Yes, Re-provision", 100, 180, 1);

  // Cancel button
  tft.fillRoundRect(170, 170, 100, 30, 5, BUTTON_GRAY);
  tft.setTextColor(WHITE);
  tft.drawCentreString("Cancel", 220, 180, 1);

  tft.setTextColor(TEXT_COLOR);
}

void handleReProvisionConfirmTouch() {
  if (currentDialogState != DIALOG_REPROVISION) return;

  int x, y;
  if (!getTouchPoint(x, y, TOUCH_GENERAL)) return;

  Serial.print("Re-provision dialog touch: (");
  Serial.print(x);
  Serial.print(",");
  Serial.print(y);
  Serial.println(")");

  // Confirm button
  if (x >= 50 && x <= 150 && y >= 170 && y <= 200) {
    // Clear credentials and restart provisioning
    hmacAuth.clearCredentials();
    credentials = hmacAuth.loadCredentials();

    // Reset provisioning state
    enteredProvisionKey = "";
    provisioningError = "";
    provisioningInProgress = false;

    // Reset dialog state
    currentDialogState = DIALOG_NONE;

    // Go to provisioning check
    currentAppState = PROVISIONING_CHECK;
    return;
  }

  // Cancel button
  if (x >= 170 && x <= 270 && y >= 170 && y <= 200) {
    currentDialogState = DIALOG_NONE;
    drawDeviceSettingsMenu();
    return;
  }
}

void showClearDataConfirm() {
  currentDialogState = DIALOG_CLEAR_DATA;
  tft.fillScreen(BG_COLOR);
  tft.setTextColor(TEXT_COLOR);

  // Title
  tft.drawCentreString("Clear Device Data", 160, 30, 2);

  // Warning message
  tft.setTextColor(ERROR_COLOR);
  tft.drawCentreString("WARNING: This will erase", 160, 70, 1);
  tft.drawCentreString("ALL device data including:", 160, 90, 1);

  tft.setTextColor(TEXT_COLOR);
  tft.drawString("• Device credentials", 50, 110, 1);
  tft.drawString("• WiFi settings", 50, 125, 1);
  tft.drawString("• Display calibration", 50, 140, 1);
  tft.drawString("• All preferences", 50, 155, 1);

  tft.setTextColor(ERROR_COLOR);
  tft.drawCentreString("This action cannot be undone!", 160, 175, 1);

  // Confirm button
  tft.fillRoundRect(50, 200, 100, 30, 5, ERROR_COLOR);
  tft.setTextColor(WHITE);
  tft.drawCentreString("ERASE ALL", 100, 210, 1);

  // Cancel button
  tft.fillRoundRect(170, 200, 100, 30, 5, BUTTON_GRAY);
  tft.setTextColor(WHITE);
  tft.drawCentreString("Cancel", 220, 210, 1);

  tft.setTextColor(TEXT_COLOR);
}

void handleClearDataConfirmTouch() {
  if (currentDialogState != DIALOG_CLEAR_DATA) return;

  int x, y;
  if (!getTouchPoint(x, y, TOUCH_GENERAL)) return;

  // Confirm button
  if (x >= 50 && x <= 150 && y >= 200 && y <= 230) {
    // Show final warning
    showFinalEraseWarning();
    return;
  }

  // Cancel button
  if (x >= 170 && x <= 270 && y >= 200 && y <= 230) {
    currentDialogState = DIALOG_NONE;
    drawDeviceSettingsMenu();
    return;
  }
}

void showFinalEraseWarning() {
  currentDialogState = DIALOG_FINAL_ERASE;
  tft.fillScreen(ERROR_COLOR);
  tft.setTextColor(WHITE);

  // Final warning
  tft.drawCentreString("FINAL WARNING", 160, 60, 2);
  tft.drawCentreString("All data will be erased!", 160, 90, 1);
  tft.drawCentreString("Device will restart for", 160, 110, 1);
  tft.drawCentreString("initial setup.", 160, 130, 1);

  // Countdown or immediate action buttons
  tft.fillRoundRect(30, 170, 120, 30, 5, BG_COLOR);
  tft.setTextColor(ERROR_COLOR);
  tft.drawCentreString("ERASE NOW", 90, 180, 1);

  tft.fillRoundRect(170, 170, 120, 30, 5, BUTTON_GRAY);
  tft.setTextColor(WHITE);
  tft.drawCentreString("Cancel", 230, 180, 1);
}

void handleFinalEraseWarningTouch() {
  if (currentDialogState != DIALOG_FINAL_ERASE) return;

  int x, y;
  if (!getTouchPoint(x, y, TOUCH_GENERAL)) return;

  // Erase now button
  if (x >= 30 && x <= 150 && y >= 170 && y <= 200) {
    performFactoryReset();
    return;
  }

  // Cancel button
  if (x >= 170 && x <= 290 && y >= 170 && y <= 200) {
    currentDialogState = DIALOG_NONE;
    drawDeviceSettingsMenu();
    return;
  }
}

void performFactoryReset() {
  tft.fillScreen(BG_COLOR);
  tft.setTextColor(TEXT_COLOR);
  tft.drawCentreString("Erasing Device Data...", 160, 100, 2);
  tft.drawCentreString("Please wait...", 160, 130, 1);

  // Clear all preferences
  hmacAuth.clearCredentials();
  clearWiFiCredentials();

  // Clear calibration data
  preferences.begin("tickertronix", false);
  preferences.clear();
  preferences.end();

  // Show completion and restart
  tft.fillScreen(SUCCESS_COLOR);
  tft.setTextColor(WHITE);
  tft.drawCentreString("Device Reset Complete", 160, 100, 2);
  tft.drawCentreString("Restarting...", 160, 130, 1);

  delay(3000);

  // Restart the ESP32
  ESP.restart();
}
