/*
 * Connects to IMU databus and prints IMU data to console
 * **This is specifically for the ESP32 DevKit**
 */
#include <Wire.h>

#define IMU_ADDRESS 0x68 // Replace with your IMU's I2C address
#define PWR_MGMT_1 0x6B
#define ACCEL_XOUT_H 0x3B


void setup() {
  Serial.begin(115200);
  Wire.begin();


  // Wake up the IMU
  Wire.beginTransmission(IMU_ADDRESS);
  Wire.write(PWR_MGMT_1);
  Wire.write(0);
  Wire.endTransmission();


  delay(100);
}


void loop() {
  int16_t accelX, accelY, accelZ;


  // Request accelerometer data
  Wire.beginTransmission(IMU_ADDRESS);
  Wire.write(ACCEL_XOUT_H);
  Wire.endTransmission(false);
  Wire.requestFrom(IMU_ADDRESS, 6, true);


  accelX = (Wire.read() << 8 | Wire.read());
  accelY = (Wire.read() << 8 | Wire.read());
  accelZ = (Wire.read() << 8 | Wire.read());


  // Print only numeric data separated by tabs
  Serial.print(accelX);
  Serial.print("\t");
  Serial.print(accelY);
  Serial.print("\t");
  Serial.println(accelZ);


  delay(100); // Adjust as needed
}


