#include <SD.h>
#include <SPI.h>
#include <Wire.h>

#define IMU_ADDRESS 0x68 // Replace with your IMU's I2C address
#define PWR_MGMT_1 0x6B
#define ACCEL_XOUT_H 0x3B

#define SD_CS 5  // Pin for SD card chip select

File file;

void setup() {
  // Start serial communication for debugging
  Serial.begin(115200);
  Wire.begin();

  // Initialize SD card
  if (!SD.begin(SD_CS)) {
    Serial.println("SD card initialization failed!");
    return;
  }

    // Wake up the IMU
  Wire.beginTransmission(IMU_ADDRESS);
  Wire.write(PWR_MGMT_1);
  Wire.write(0);
  Wire.endTransmission();

  delay(5000);
  Serial.println("SD card initialized.");

  // Open the file for writing (create if doesn't exist)
  file = SD.open("/test.csv", FILE_WRITE);
  
  // Check if the file opened correctly
  if (file) {
    Serial.println("Writing to test.csv...");

    // Write some text to the file (CSV format)
    file.println("xAccel, yAccel, zAccel");

    // Close the file
    Serial.println("Write successful!");
  } else {
    // If the file doesn't open, print an error message
    Serial.println("Error opening test.csv");
  }
}

void loop() {

  static unsigned long lastWriteTime = 0;
  unsigned long currentTime = millis();
  int count = 0;

  if (currentTime - lastWriteTime >= 100) {  // Write every 2 seconds
    lastWriteTime = currentTime;
    int16_t accelX, accelY, accelZ;


    // Request accelerometer data
    Wire.beginTransmission(IMU_ADDRESS);
    Wire.write(ACCEL_XOUT_H);
    Wire.endTransmission(false);
    Wire.requestFrom(IMU_ADDRESS, 6, true);


    accelX = (Wire.read() << 8 | Wire.read());
    accelY = (Wire.read() << 8 | Wire.read());
    accelZ = (Wire.read() << 8 | Wire.read());

    // Write a new line of data to the file
    file.print(accelX);
    file.print(", ");
    file.print(accelY); 
    file.print(", ");
    file.println(accelZ);

        // Print only numeric data separated by tabs
      Serial.print(accelX);
      Serial.print("\t");
      Serial.print(accelY);
      Serial.print("\t");
      Serial.println(accelZ);
  }

  // Continue to do other tasks if necessary

  // Make sure to flush the file buffer every so often
  file.flush();
  count++;

  if(count > 100) closeFile();

}

void closeFile() {
  // Close the file when finished (can be done in loop or in setup, depending on your needs)
  if (file) {
    file.close();
    Serial.println("File closed.");
  }
}
