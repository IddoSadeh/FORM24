#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>

Adafruit_MPU6050 mpu;

void setup() {
  Serial.begin(115200);  // Start Serial Monitor
  while (!Serial) delay(10);  // Wait for Serial Monitor to connect

  Serial.println("Initializing MPU6050...");

  if (!mpu.begin()) {
    Serial.println("Could not find a valid MPU6050 sensor. Check connections!");
    while (1);  // Halt if the MPU6050 isn't found
  }

  Serial.println("MPU6050 initialized successfully.");
}

void loop() {
  sensors_event_t accel, gyro, temp;
  mpu.getEvent(&accel, &gyro, &temp);

  // Print accelerometer data
  Serial.print("Accel X: "); Serial.print(accel.acceleration.x); Serial.print(" m/s^2, ");
  Serial.print("Y: "); Serial.print(accel.acceleration.y); Serial.print(" m/s^2, ");
  Serial.print("Z: "); Serial.print(accel.acceleration.z); Serial.print(" m/s^2, ");

  // Print gyroscope data
  Serial.print("Gyro X: "); Serial.print(gyro.gyro.x); Serial.print(" rad/s, ");
  Serial.print("Y: "); Serial.print(gyro.gyro.y); Serial.print(" rad/s, ");
  Serial.println(gyro.gyro.z);  // rad/s

  delay(17);  // Delay to maintain ~60Hz (1000ms / 60 = 16.67ms) (adjust this as needed if we want to increase sampling rate)
}
