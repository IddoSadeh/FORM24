#include <Wire.h>
#include <MPU6050.h>
#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEServer.h>
#include <BLE2902.h>


MPU6050 imu;  // Initialize MPU6050

#define SERVICE_UUID        "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
#define CHARACTERISTIC_UUID "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"

BLEServer *pServer = nullptr;
BLECharacteristic *pCharacteristic = nullptr;
BLEAdvertising *pAdvertising = nullptr;
bool deviceConnected = false;

// BLE Callbacks
class MyServerCallbacks: public BLEServerCallbacks {
    void onConnect(BLEServer* pServer) {
        deviceConnected = true;
    }

    void onDisconnect(BLEServer* pServer) {
        deviceConnected = false;
        Serial.println("Device disconnected, restarting advertising...");
        pServer->getAdvertising()->start();  // Restart BLE advertising
    }
};

void setup() {
    Serial.begin(115200);
    Wire.begin();

    // Initialize IMU Sensor
    imu.initialize();
    if (!imu.testConnection()) {
        Serial.println("MPU6050 connection failed!");
        while (1);
    }
    Serial.println("MPU6050 connected!");

    // Initialize BLE
    BLEDevice::init("FeatherESP32_IMU");
    pServer = BLEDevice::createServer();
    pServer->setCallbacks(new MyServerCallbacks());

    BLEService *pService = pServer->createService(SERVICE_UUID);
    pCharacteristic = pService->createCharacteristic(
        CHARACTERISTIC_UUID,
        BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY
    );

    pCharacteristic->addDescriptor(new BLE2902());

    pService->start();
    pAdvertising = BLEDevice::getAdvertising();
    pAdvertising->addServiceUUID(SERVICE_UUID);
    pServer->getAdvertising()->start();

    Serial.println("BLE Server Started");
}

void loop() {
    if (deviceConnected) {
        int16_t ax, ay, az, gx, gy, gz;
        imu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);

        char buffer[50];
        snprintf(buffer, sizeof(buffer), "AX:%d AY:%d AZ:%d GX:%d GY:%d GZ:%d", ax, ay, az, gx, gy, gz);

        pCharacteristic->setValue(buffer);
        pCharacteristic->notify();
        Serial.println(buffer);  // Debugging output

        delay(100);  // Send data every 100ms
    }
}
