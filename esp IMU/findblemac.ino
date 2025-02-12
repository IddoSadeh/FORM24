#include <BLEDevice.h>

void setup() {
    Serial.begin(115200);
    BLEDevice::init("ESP32_IMU");  
    Serial.println("BLE initialized!");
    Serial.print("ESP32 BLE MAC Address: ");
    Serial.println(BLEDevice::getAddress().toString().c_str());
}

void loop() {
    delay(1000);
}
