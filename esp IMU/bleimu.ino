#include <Wire.h>
#include <MPU6050.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>
#include "esp_system.h"  // ESP32 Reset Function

MPU6050 mpu;

// BLE UUIDs
#define SERVICE_UUID        "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"  // Custom Service UUID
#define CHARACTERISTIC_UUID "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"  // Custom Characteristic UUID

BLECharacteristic imuCharacteristic(CHARACTERISTIC_UUID, BLECharacteristic::PROPERTY_NOTIFY);

void setup() {
    Serial.begin(115200);
    delay(2000);  // Ensure ESP32 is fully booted before sending data

    // **Ensure Serial is clean (disable logs)**
    esp_log_level_set("*", ESP_LOG_NONE); 

    Wire.begin();
    mpu.initialize();

    if (!mpu.testConnection()) {
        while (1);  // Stop if MPU6050 fails (no serial message)
    }

    // BLE setup
    BLEDevice::init("ESP32_IMU");  
    BLEServer *pServer = BLEDevice::createServer();
    BLEService *pService = pServer->createService(SERVICE_UUID);
    
    pService->addCharacteristic(&imuCharacteristic);
    pService->start();
    pServer->getAdvertising()->start();
}

void loop() {
    static unsigned long last_time = 0;
    if (millis() - last_time < (1000 / 60)) return; // Only run at 60Hz
    last_time = millis(); // Update timestamp

    int16_t ax, ay, az, gx, gy, gz;
    mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);

    Serial.printf("%d,%d,%d,%d,%d,%d\n", ax, ay, az, gx, gy, gz);
    imuCharacteristic.setValue(String(ax) + "," + String(ay) + "," + String(az) + "," + 
                               String(gx) + "," + String(gy) + "," + String(gz));
    imuCharacteristic.notify();

    // Check for reset signal from Python
    if (Serial.available()) {
        String command = Serial.readStringUntil('\n');
        command.trim();
        if (command == "RESET") {
            delay(500);
            esp_restart();
        }
    }
}

