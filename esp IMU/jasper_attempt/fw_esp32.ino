#include <Wire.h>
#include <MPU6050.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

MPU6050 mpu;

// BLE UUIDs
#define SERVICE_UUID        "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"  // Custom Service UUID
#define CHARACTERISTIC_UUID "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"  // Custom Characteristic UUID

BLECharacteristic imuCharacteristic(CHARACTERISTIC_UUID, BLECharacteristic::PROPERTY_NOTIFY);

void setup() {
    Serial.begin(115200);

    // Initialize MPU6050
    Wire.begin();
    mpu.initialize();

    if (!mpu.testConnection()) {
        Serial.println("MPU6050 connection failed!");
        while (1);
    }
    Serial.println("MPU6050 connection successful");

    // BLE setup
    BLEDevice::init("ESP32_IMU");  // Name of the Bluetooth device
    BLEServer *pServer = BLEDevice::createServer();
    BLEService *pService = pServer->createService(SERVICE_UUID);

    // Add Characteristic to the Service
    pService->addCharacteristic(&imuCharacteristic);
    imuCharacteristic.addDescriptor(new BLE2902());  // Optional: enables client notifications

    // Start the service
    pService->start();

    // Start advertising
    pServer->getAdvertising()->start();
    Serial.println("Bluetooth device is now advertising...");
}

void loop() {
    int16_t ax, ay, az, gx, gy, gz;
    mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);

    // Format the IMU data into a string
    String data = String(ax) + "," + String(ay) + "," + String(az) + "," + String(gx) + "," + String(gy) + "," + String(gz);

    // Send IMU data as a notification to the Bluetooth client
    imuCharacteristic.setValue(data.c_str());
    imuCharacteristic.notify();

    delay(1);  // 1000Hz
}
