#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

#define BATTERY_PIN 35  // ADC pin for battery voltage measurement
#define MIN_VOLTAGE 3.0  // Min battery voltage (0%)
#define MAX_VOLTAGE 4.2  // Max battery voltage (100%)

BLEServer *pServer = NULL;
BLECharacteristic *pCharacteristic = NULL;
bool deviceConnected = false;

#define SERVICE_UUID "0000180F-0000-1000-8000-00805F9B34FB"  // Battery Service
#define CHARACTERISTIC_UUID "00002A19-0000-1000-8000-00805F9B34FB"  // Battery Level Characteristic

class MyServerCallbacks : public BLEServerCallbacks {
    void onConnect(BLEServer* pServer) {
        deviceConnected = true;
    }

    void onDisconnect(BLEServer* pServer) {
        deviceConnected = false;
        pServer->getAdvertising()->start();  // Restart advertising after disconnect
    }
};

void setup() {
    Serial.begin(115200);
    BLEDevice::init("ESP32_BatteryMonitor");

    pServer = BLEDevice::createServer();
    pServer->setCallbacks(new MyServerCallbacks());

    BLEService *pService = pServer->createService(SERVICE_UUID);

    pCharacteristic = pService->createCharacteristic(
                        CHARACTERISTIC_UUID,
                        BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY);

    pCharacteristic->addDescriptor(new BLE2902());

    pService->start();
    pServer->getAdvertising()->start();  // Start advertising
}

void loop() {
    int rawADC = analogRead(BATTERY_PIN);
    float batteryVoltage = (rawADC / 4095.0) * 3.3 * 2;
    float batteryPercentage = ((batteryVoltage - MIN_VOLTAGE) / (MAX_VOLTAGE - MIN_VOLTAGE)) * 100;
    batteryPercentage = constrain(batteryPercentage, 0, 100); 

    Serial.print("Battery: ");
    Serial.print(batteryPercentage);
    Serial.println("%");

    if (deviceConnected) {
        uint8_t batteryLevel = (uint8_t)batteryPercentage;  // Convert to uint8_t (0-100%)
        pCharacteristic->setValue(&batteryLevel, 1);
        pCharacteristic->notify();  // Send notification to connected device
    }

    delay(2000);
}
