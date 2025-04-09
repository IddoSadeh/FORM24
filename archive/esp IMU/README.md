## Files Overview

### Current Core Project Files

- *imuLoggerAndTransfer.ino*: Main Arduino sketch for the ESP32 that handles IMU data collection, SD card logging, and Bluetooth communication. This code allows the ESP32 to:
  - Record IMU (accelerometer/gyroscope) data to CSV files on an SD card
  - Receive commands via Bluetooth to start/stop logging
  - Transfer files from the SD card to a connected device
  - List and delete files on the SD card
  
- *bleClientGUI.py*: Python desktop application that provides a graphical interface to control the ESP32 logger. Features include:
  - Device scanning and connection management
  - Starting and stopping data logging
  - Viewing, downloading, and managing files on the ESP32's SD card
  - Live status updates and connection logs

- *imuProcess.ipynb*: Jupyter notebook for processing and analyzing collected IMU data.
  - Preprocess data (savitsky-golay filtering)
  - Peak finding (Scipy - find peaks)
  - Continuous Stroke Rate derivation

- *batteryfw.ino (needs testing and revision)*: Arduino sketch that measures battery life (only works for esp32 with BAT or related pin)
  - Advertises a BLE service to broadcast the battery level.
  - Measures battery voltage using an analog pin and converts it to a percentage.
  - Sends the battery percentage to a connected BLE client via notifications.

- *battery.py (needs testing and revision)*: Python script for battery checking (Needs Testing)
  - Simple script to fetch arduino serial output


### Old Core Project Files

- *IMUCollect.py*: Python script for collecting and processing IMU data received from the ESP32.

- *bleClient.py*: Simple Python Bluetooth Low Energy client for connecting to the ESP32 without the graphical interface.

- *bleimu.ino*: Arduino sketch for basic Bluetooth IMU data transmission from ESP32.


### Other Project Files

- *find_imu_bus.ino*: Utility sketch to detect and identify IMU devices on the I2C bus.

- *findblesmac.ino*: Utility sketch to find and display Bluetooth MAC addresses.



