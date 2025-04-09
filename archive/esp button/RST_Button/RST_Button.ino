/*
 * Checks that microcontroller will reset when button connected to reset pin is pressed
 * When ESP32 is reset, it will start setup again, so "ESP32 is running will print"
 * Otherwise, will print "Still running..."
 */


void setup() {
    Serial.begin(115200);
    Serial.println("ESP32 is running...");
}

void loop() {
    Serial.println("Still running...");
    delay(1000);
}
