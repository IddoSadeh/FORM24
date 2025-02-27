#include <Wire.h>
#include <MPU6050.h>
#include <SD.h>
#include <SPI.h>
#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEServer.h>
#include <BLE2902.h>

// Define pins
#define SD_CS 33  // SD card chip select pin - UPDATED to match your hardware (CS to 33/A9)
#define SPI_MISO 21  // MISO pin - UPDATED to match your hardware
#define SPI_MOSI 19  // MOSI pin - UPDATED to match your hardware
#define SPI_SCK  5   // SCK pin - UPDATED to match your hardware

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

// BLE objects
BLEServer *pServer = nullptr;
BLECharacteristic *pCommandCharacteristic = nullptr;
BLECharacteristic *pDataCharacteristic = nullptr;
bool deviceConnected = false;

// MPU6050 sensor
MPU6050 imu;

// SD Card status
bool sdCardAvailable = false;

// Logging state
bool isLogging = false;
File dataFile;
String currentFileName = "";
unsigned long fileCounter = 0;
const int CHUNK_SIZE = 512; // Size of data chunks for file transfer

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

// BLE Server Callbacks
class ServerCallbacks: public BLEServerCallbacks {
    void onConnect(BLEServer* pServer) {
        deviceConnected = true;
        Serial.println("Device connected");
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
    Wire.begin();
    
    // Initialize MPU6050
    Serial.println("Initializing MPU6050...");
    imu.initialize();
    if (!imu.testConnection()) {
        Serial.println("MPU6050 connection failed!");
        while (1);
    }
    Serial.println("MPU6050 connected!");
    
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
    } else {
        Serial.println("SD card initialized!");
        sdCardAvailable = true;
    }
    
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

void startLogging() {
    // Create a new filename with timestamp or counter
    fileCounter++;
    currentFileName = "/IMU_" + String(fileCounter) + ".csv";
    
    // Open the file for writing
    dataFile = SD.open(currentFileName, FILE_WRITE);
    
    if (dataFile) {
        // Write CSV header
        dataFile.println("Time,AccelX,AccelY,AccelZ,GyroX,GyroY,GyroZ");
        isLogging = true;
        
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
    }
}

void stopLogging() {
    if (isLogging) {
        // Close the file
        dataFile.close();
        isLogging = false;
        
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

// Replace these functions in your ESP32 Arduino code

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
        return;
    }
    
    // Open the file for reading
    transferFile = SD.open(filename);
    
    if (!transferFile) {
        String error = "Error: Couldn't open file " + filename;
        pDataCharacteristic->setValue(error.c_str());
        pDataCharacteristic->notify();
        
        Serial.println(error);
        return;
    }
    
    // Get file size
    fileSize = transferFile.size();
    bytesTransferred = 0;
    
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
    }
}