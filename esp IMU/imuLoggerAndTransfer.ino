#include <Wire.h>
#include <MPU6050.h>
#include <SD.h>
#include <SPI.h>
#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEServer.h>
#include <BLE2902.h>
#include <Adafruit_NeoPixel.h> // For controlling the onboard LED

// Define pins
#define SD_CS 33  // SD card chip select pin
#define SPI_MISO 21  // MISO pin
#define SPI_MOSI 19  // MOSI pin
#define SPI_SCK  5   // SCK pin
#define NEOPIXEL_PIN 0  // ESP32 Featherboard v2 NeoPixel pin
#define LOGGING_PIN 12 // Button connected to GPIO pin 12

// Define LED states/colors
#define LED_IDLE      0x0000FF  // Blue - ready but idle
#define LED_CONNECTED 0x00FFFF  // Cyan - connected via BLE
#define LED_LOGGING   0x00FF00  // Green - actively logging data
#define LED_ERROR     0xFF0000  // Red - error state
#define LED_TRANSFER  0xFF00FF  // Purple - transferring file

// BLE UUIDs
#define SERVICE_UUID        "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
#define COMMAND_CHAR_UUID   "6E400002-B5A3-F393-E0A9-E50E24DCCA9E" // For receiving commands
#define DATA_CHAR_UUID      "6E400003-B5A3-F393-E0A9-E50E24DCCA9E" // For sending data

// Function declarations
void startLogging();
void stopLogging();
void logIMUData();
void listFiles();
void startFileTransfer(String filename);
void continueFileTransfer();
void deleteFile(String filename);
void updateLED(uint32_t color);

// BLE objects
BLEServer *pServer = nullptr;
BLECharacteristic *pCommandCharacteristic = nullptr;
BLECharacteristic *pDataCharacteristic = nullptr;
bool deviceConnected = false;

// MPU6050 sensor
MPU6050 imu;

// NeoPixel for status LED
Adafruit_NeoPixel pixels(1, NEOPIXEL_PIN, NEO_GRB + NEO_KHZ800);

// SD Card status
bool sdCardAvailable = false;

// Logging state
bool isLogging = false;
File dataFile;
String currentFileName = "";
const int CHUNK_SIZE = 512; // Size of data chunks for file transfer

// Time tracking
unsigned long startupTime = 0;

// Command codes
const char CMD_START_LOGGING = 'S';
const char CMD_STOP_LOGGING = 'E';
const char CMD_LIST_FILES = 'L';
const char CMD_GET_FILE = 'G';
const char CMD_DELETE_FILE = 'D';

// File transfer state
bool isTransferring = false;
File transferFile;
size_t fileSize = 0;
size_t bytesTransferred = 0;

// Logging Button state
int buttonState = HIGH;    // Default state (not pressed)
int lastButtonState = HIGH;
unsigned long lastDebounceTime = 0;
const unsigned long debounceDelay = 50; // Debounce time in milliseconds

// BLE Server Callbacks
class ServerCallbacks: public BLEServerCallbacks {
    void onConnect(BLEServer* pServer) {
        deviceConnected = true;
        Serial.println("Device connected");
        updateLED(LED_CONNECTED);
    }

    void onDisconnect(BLEServer* pServer) {
        deviceConnected = false;
        Serial.println("Device disconnected");
        
        // If logging was in progress, close the file
        if (isLogging) {
            stopLogging();
        }
        
        // If transferring was in progress, close the file
        if (isTransferring && sdCardAvailable) {
            transferFile.close();
            isTransferring = false;
        }
        
        // Reset LED to idle state
        updateLED(LED_IDLE);
        
        // Restart advertising
        pServer->getAdvertising()->start();
    }
};

// Command Characteristic Callbacks
class CommandCallbacks: public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic *pCharacteristic) {
        String rxValue;
        // Get the data from characteristic as byte array
        uint8_t* data = pCharacteristic->getData();
        // Get the length of the data
        size_t len = pCharacteristic->getValue().length();
        
        // Convert byte array to String
        for (int i = 0; i < len; i++) {
            rxValue += (char)data[i];
        }
        
        if (rxValue.length() > 0) {
            char command = rxValue.charAt(0);
            Serial.print("Received command: ");
            Serial.println(command);
            
            switch (command) {
                case CMD_START_LOGGING:
                    if (!isLogging && sdCardAvailable) {
                        startLogging();
                    } else if (!sdCardAvailable) {
                        String error = "Error: SD card not available";
                        pDataCharacteristic->setValue(error.c_str());
                        pDataCharacteristic->notify();
                        Serial.println(error);
                        updateLED(LED_ERROR);
                    }
                    break;
                    
                case CMD_STOP_LOGGING:
                    if (isLogging) {
                        stopLogging();
                    }
                    break;
                    
                case CMD_LIST_FILES:
                    if (sdCardAvailable) {
                        listFiles();
                    } else {
                        String error = "Error: SD card not available";
                        pDataCharacteristic->setValue(error.c_str());
                        pDataCharacteristic->notify();
                        Serial.println(error);
                        updateLED(LED_ERROR);
                    }
                    break;
                    
                case CMD_GET_FILE:
                    if (sdCardAvailable) {
                        if (rxValue.length() > 1) {
                            // Extract filename from command
                            String filename = "/" + rxValue.substring(1);
                            startFileTransfer(filename);
                        }
                    } else {
                        String error = "Error: SD card not available";
                        pDataCharacteristic->setValue(error.c_str());
                        pDataCharacteristic->notify();
                        Serial.println(error);
                        updateLED(LED_ERROR);
                    }
                    break;
                    
                case CMD_DELETE_FILE:
                    if (sdCardAvailable) {
                        if (rxValue.length() > 1) {
                            // Extract filename from command
                            String filename = "/" + rxValue.substring(1);
                            deleteFile(filename);
                        }
                    } else {
                        String error = "Error: SD card not available";
                        pDataCharacteristic->setValue(error.c_str());
                        pDataCharacteristic->notify();
                        Serial.println(error);
                        updateLED(LED_ERROR);
                    }
                    break;
                    
                default:
                    Serial.println("Unknown command");
                    break;
            }
        }
    }
};

void setup() {
    Serial.begin(115200);
    
    // Record startup time
    startupTime = millis();
    
    // Initialize NeoPixel LED
    pixels.begin();
    updateLED(LED_IDLE); // Set initial blue idle state
    
    Wire.begin();
    
    // Initialize MPU6050
    Serial.println("Initializing MPU6050...");
    imu.initialize();
    if (!imu.testConnection()) {
        Serial.println("MPU6050 connection failed!");
        updateLED(LED_ERROR);
        delay(1000);
    } else {
        Serial.println("MPU6050 connected!");
    }
    
    // Initialize SPI with custom pins before SD card
    SPI.begin(SPI_SCK, SPI_MISO, SPI_MOSI);
    
    // Initialize SD card
    Serial.println("Initializing SD card...");
    Serial.println("CS pin: " + String(SD_CS) + ", MISO: " + String(SPI_MISO) + 
                   ", MOSI: " + String(SPI_MOSI) + ", SCK: " + String(SPI_SCK));
                   
    if (!SD.begin(SD_CS)) {
        Serial.println("SD card initialization failed!");
        Serial.println("Continuing without SD card functionality");
        sdCardAvailable = false;
        
        // Briefly show error state
        updateLED(LED_ERROR);
        delay(1000);
        updateLED(LED_IDLE);
    } else {
        Serial.println("SD card initialized!");
        sdCardAvailable = true;
    }

    // Initialize logging button
    pinMode(LOGGING_PIN, INPUT_PULLUP);
    Serial.println("Logging button initialized!");
    
    // Initialize BLE
    Serial.println("Initializing BLE...");
    BLEDevice::init("ESP32_IMU_Logger");
    
    // Print the MAC address
    String macAddress = BLEDevice::getAddress().toString().c_str();
    Serial.print("ESP32 Bluetooth MAC Address: ");
    Serial.println(macAddress);
    
    // Create BLE Server
    pServer = BLEDevice::createServer();
    pServer->setCallbacks(new ServerCallbacks());
    
    // Create BLE Service
    BLEService *pService = pServer->createService(SERVICE_UUID);
    
    // Create Command Characteristic (for receiving commands)
    pCommandCharacteristic = pService->createCharacteristic(
        COMMAND_CHAR_UUID,
        BLECharacteristic::PROPERTY_WRITE
    );
    pCommandCharacteristic->setCallbacks(new CommandCallbacks());
    
    // Create Data Characteristic (for sending data)
    pDataCharacteristic = pService->createCharacteristic(
        DATA_CHAR_UUID,
        BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY
    );
    pDataCharacteristic->addDescriptor(new BLE2902());
    
    // Start the service
    pService->start();
    
    // Start advertising
    BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
    pAdvertising->addServiceUUID(SERVICE_UUID);
    pAdvertising->setScanResponse(true);
    pAdvertising->setMinPreferred(0x06);  // functions that help with iPhone connections issue
    pAdvertising->setMinPreferred(0x12);
    BLEDevice::startAdvertising();
    
    Serial.println("BLE server started. Waiting for connections...");
    
    // Print connection info again for clarity
    Serial.println("\n-------------------------------------");
    Serial.println("BLUETOOTH CONNECTION INFORMATION:");
    Serial.println("Device Name: ESP32_IMU_Logger");
    Serial.print("MAC Address: ");
    Serial.println(macAddress);
    Serial.println("Service UUID: " + String(SERVICE_UUID));
    Serial.println("Command Characteristic: " + String(COMMAND_CHAR_UUID));
    Serial.println("Data Characteristic: " + String(DATA_CHAR_UUID));
    Serial.println("SD Card Status: " + String(sdCardAvailable ? "Available" : "Not Available"));
    Serial.println("-------------------------------------\n");
}

void loop() {
    static unsigned long lastDebugTime = 0;
    unsigned long currentTime = millis();
    
    // If logging is active, read IMU data and save to SD card
    if (isLogging && deviceConnected && sdCardAvailable) {
        logIMUData();
    }
    
    // If transferring a file, continue the transfer process
    if (isTransferring && deviceConnected && sdCardAvailable) {
        continueFileTransfer();
    }

    // Button state checking
    int reading = digitalRead(buttonPin); // Read the button state

    // If the button state has changed, reset the debounce timer
    if (reading != lastButtonState) {
        lastDebounceTime = millis();
    }

    // If the stable state persists beyond the debounce delay, register the press
    if ((millis() - lastDebounceTime) > debounceDelay) {
        if (reading == LOW && buttonState == HIGH) { // Button was released, now pressed
            if (!isLogging && sdCardAvailable) {
                startLogging();
            } else if (!sdCardAvailable) {
                String error = "Error: SD card not available";
                pDataCharacteristic->setValue(error.c_str());
                pDataCharacteristic->notify();
                Serial.println(error);
                updateLED(LED_ERROR);
            } else if (isLogging) {
                stopLogging();
            }
        }
        buttonState = reading; // Update button state
    }

    lastButtonState = reading; // Save last reading for comparison
    
    // Debug output every 5 seconds
    if (currentTime - lastDebugTime > 5000) {
        lastDebugTime = currentTime;
        Serial.print("Connection status: ");
        Serial.println(deviceConnected ? "Connected" : "Disconnected");
        
        if (isLogging) {
            Serial.println("Currently logging to: " + currentFileName);
        }
    }
    
    // Small delay to prevent overloading the CPU
    delay(10);
}

// Updates the onboard NeoPixel LED color
void updateLED(uint32_t color) {
    pixels.setPixelColor(0, color);
    pixels.show();
}

// Gets a timestamp string for the current system uptime
String getTimestampString() {
    // Get current uptime in milliseconds
    unsigned long now = millis();
    unsigned long uptime = now - startupTime;
    
    // Calculate hours, minutes, seconds
    unsigned long seconds = uptime / 1000;
    unsigned long minutes = seconds / 60;
    unsigned long hours = minutes / 60;
    unsigned long days = hours / 24;
    
    seconds %= 60;
    minutes %= 60;
    hours %= 24;
    
    // Format timestamp as DD_HH-MM-SS
    String timestamp = String(days) + "_";
    
    if (hours < 10) timestamp += "0";
    timestamp += String(hours) + "-";
    
    if (minutes < 10) timestamp += "0";
    timestamp += String(minutes) + "-";
    
    if (seconds < 10) timestamp += "0";
    timestamp += String(seconds);
    
    return timestamp;
}

void startLogging() {
    // Create a new filename with timestamp
    String timestamp = getTimestampString();
    currentFileName = "/IMU_" + timestamp + ".csv";
    
    // Open the file for writing
    dataFile = SD.open(currentFileName, FILE_WRITE);
    
    if (dataFile) {
        // Write CSV header
        dataFile.println("Time,AccelX,AccelY,AccelZ,GyroX,GyroY,GyroZ");
        isLogging = true;
        
        // Update LED to indicate logging
        updateLED(LED_LOGGING);
        
        // Notify client that logging has started
        String message = "Logging started: " + currentFileName;
        pDataCharacteristic->setValue(message.c_str());
        pDataCharacteristic->notify();
        
        Serial.println(message);
    } else {
        // Failed to open file
        String error = "Error: Couldn't create file " + currentFileName;
        pDataCharacteristic->setValue(error.c_str());
        pDataCharacteristic->notify();
        
        Serial.println(error);
        
        // Show error with LED
        updateLED(LED_ERROR);
        delay(1000);
        updateLED(LED_CONNECTED); // Return to connected state
    }
}

void stopLogging() {
    if (isLogging) {
        // Close the file
        dataFile.close();
        isLogging = false;
        
        // Update LED back to connected state
        updateLED(LED_CONNECTED);
        
        // Notify client that logging has stopped
        String message = "Logging stopped: " + currentFileName;
        pDataCharacteristic->setValue(message.c_str());
        pDataCharacteristic->notify();
        
        Serial.println(message);
    }
}

void logIMUData() {
    // Read raw IMU data
    int16_t ax, ay, az, gx, gy, gz;
    imu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);
    
    // Get current time in milliseconds
    unsigned long timestamp = millis();
    
    // Create data string in CSV format
    String dataString = String(timestamp) + "," + 
                        String(ax) + "," + 
                        String(ay) + "," + 
                        String(az) + "," + 
                        String(gx) + "," + 
                        String(gy) + "," + 
                        String(gz);
    
    // Write to file
    dataFile.println(dataString);
    
    // Flush every 10 records to ensure data is written to SD card
    static int counter = 0;
    counter++;
    if (counter >= 10) {
        dataFile.flush();
        counter = 0;
    }
}

void listFiles() {
    // Open the root directory
    File root = SD.open("/");
    
    // Prepare a string to hold the file list
    String fileList = "Files on SD card:\n";
    
    // Iterate through all files in the root directory
    while (true) {
        File entry = root.openNextFile();
        if (!entry) {
            // No more files
            break;
        }
        
        // Add file name and size to the list
        fileList += entry.name();
        fileList += " (";
        fileList += String(entry.size());
        fileList += " bytes)\n";
        
        entry.close();
    }
    
    // Close the root directory
    root.close();
    
    // Send the file list to the client
    pDataCharacteristic->setValue(fileList.c_str());
    pDataCharacteristic->notify();
    
    Serial.println("File list sent");
}

void startFileTransfer(String filename) {
    // Check if a transfer is already in progress
    if (isTransferring) {
        transferFile.close();
        isTransferring = false;
    }
    
    // Check if the file exists
    if (!SD.exists(filename)) {
        String error = "Error: File " + filename + " not found";
        pDataCharacteristic->setValue(error.c_str());
        pDataCharacteristic->notify();
        
        Serial.println(error);
        
        // Show error state
        updateLED(LED_ERROR);
        delay(1000);
        updateLED(LED_CONNECTED);
        return;
    }
    
    // Open the file for reading
    transferFile = SD.open(filename);
    
    if (!transferFile) {
        String error = "Error: Couldn't open file " + filename;
        pDataCharacteristic->setValue(error.c_str());
        pDataCharacteristic->notify();
        
        Serial.println(error);
        
        // Show error state
        updateLED(LED_ERROR);
        delay(1000);
        updateLED(LED_CONNECTED);
        return;
    }
    
    // Get file size
    fileSize = transferFile.size();
    bytesTransferred = 0;
    
    // Update LED to indicate transfer
    updateLED(LED_TRANSFER);
    
    // Notify client that transfer is starting
    String message = "Transfer starting: " + filename + " (" + String(fileSize) + " bytes)";
    pDataCharacteristic->setValue(message.c_str());
    pDataCharacteristic->notify();
    
    Serial.println(message);
    Serial.print("File size: ");
    Serial.print(fileSize);
    Serial.println(" bytes");
    
    // Set the transfer flag
    isTransferring = true;
    
    // Add a small delay to make sure the client is ready
    delay(500);
    
    // Start the transfer process
    continueFileTransfer();
}

void continueFileTransfer() {
    if (!isTransferring) return;
    
    // Read a chunk of data from the file
    uint8_t buffer[CHUNK_SIZE];
    size_t bytesToRead = min((size_t)CHUNK_SIZE, fileSize - bytesTransferred);
    
    // If no more bytes to read, close the file and end transfer
    if (bytesToRead == 0) {
        transferFile.close();
        isTransferring = false;
        
        // Return LED to connected state
        updateLED(LED_CONNECTED);
        
        // Notify client that transfer is complete
        String message = "Transfer complete";
        pDataCharacteristic->setValue(message.c_str());
        pDataCharacteristic->notify();
        
        Serial.println(message);
        return;
    }
    
    // Read the chunk
    size_t bytesRead = transferFile.read(buffer, bytesToRead);
    
    if (bytesRead > 0) {
        // Send the chunk to the client
        pDataCharacteristic->setValue(buffer, bytesRead);
        pDataCharacteristic->notify();
        
        // Update the counter
        bytesTransferred += bytesRead;
        
        // Print progress
        int progress = (bytesTransferred * 100) / fileSize;
        Serial.print("Transfer progress: ");
        Serial.print(progress);
        Serial.println("%");
        Serial.print("Bytes sent: ");
        Serial.print(bytesTransferred);
        Serial.print(" of ");
        Serial.println(fileSize);
    } else {
        Serial.println("Error reading file");
    }
    
    // Add a small delay to allow BLE stack to process
    delay(50);
}

void deleteFile(String filename) {
    // Check if the file exists
    if (!SD.exists(filename)) {
        String error = "Error: File " + filename + " not found";
        pDataCharacteristic->setValue(error.c_str());
        pDataCharacteristic->notify();
        
        Serial.println(error);
        
        // Show error state
        updateLED(LED_ERROR);
        delay(1000);
        updateLED(LED_CONNECTED);
        return;
    }
    
    // Delete the file
    if (SD.remove(filename)) {
        String message = "File deleted: " + filename;
        pDataCharacteristic->setValue(message.c_str());
        pDataCharacteristic->notify();
        
        Serial.println(message);
    } else {
        String error = "Error: Couldn't delete file " + filename;
        pDataCharacteristic->setValue(error.c_str());
        pDataCharacteristic->notify();
        
        Serial.println(error);
        
        // Show error state
        updateLED(LED_ERROR);
        delay(1000);
        updateLED(LED_CONNECTED);
    }
}