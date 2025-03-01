import serial
import time
import csv
import sys
import os
from datetime import datetime

def collect_data(duration):

    port = 'COM6'  # Replace with your ESP32's COM port
    baud_rate = 115200
    ser = serial.Serial(port, baud_rate, timeout=1)

    # **Step 1: Reset ESP32**
    print("Resetting ESP32...")
    ser.write(b'RESET\n')
    time.sleep(2)  # Wait extra time for ESP32 to fully reboot

    ser.reset_input_buffer()  # Flush garbage data

    # **Step 2: Ensure ESP32 is ready before logging**
    print("Waiting for ESP32 to send data...")
    start_time = time.time()
    while time.time() - start_time < 5:  # Wait max 5 seconds for valid IMU data
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        if line and "," in line:
            print("ESP32 is ready!")
            break
    else:
        print("ESP32 did not send valid data. Exiting.")
        ser.close()
        return

    # **Step 3: Start Logging**
    folder_name = "data"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(folder_name, f"imu_data_{timestamp}.csv")

    with open(filename, mode='w', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(['Time', 'Accel_X', 'Accel_Y', 'Accel_Z', 'Gyro_X', 'Gyro_Y', 'Gyro_Z'])

        print(f"Collecting data for {duration} seconds at 60Hz...")
        start_time = time.time()

        while time.time() - start_time < duration:
            try:
                line = ser.readline().decode('utf-8', errors='ignore').strip()

                # **Ignore lines that don’t contain 6 comma-separated values**
                values = line.split(",")
                if len(values) != 6:
                    print(f"Ignoring non-IMU line: {line}")  # Debugging print
                    continue  # Skip this line

                # **Convert values safely**
                try:
                    ax, ay, az, gx, gy, gz = map(float, values)
                except ValueError:
                    print(f"Skipping malformed IMU line: {line}")
                    continue  # Skip bad data

                timestamp = time.time()
                csv_writer.writerow([timestamp, ax, ay, az, gx, gy, gz])
                print(f"Accel: [{ax}, {ay}, {az}], Gyro: [{gx}, {gy}, {gz}]")

                time.sleep(1 / 60.0)  # Maintain 60Hz
            except Exception as e:
                print(f"Error reading data: {e}")
                break


        print("Sending reset command to ESP32 after logging...")
        ser.write(b'RESET\n')

    print(f"Data collection complete. Saved to {filename}.")
    ser.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python imu_logger.py <seconds>")
        sys.exit(1)
    
    try:
        duration = int(sys.argv[1])
        if duration <= 0:
            raise ValueError("Duration must be greater than 0.")
        collect_data(duration)
    except ValueError as e:
        print(f"Invalid input: {e}")
        sys.exit(1)
