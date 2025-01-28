import serial
import time
import csv
import sys
import os
from datetime import datetime

def collect_data(duration):
    # Cap duration at 30 seconds
    if duration > 30:
        print("Capping duration to 30 seconds.")
        duration = 30

    # Configure the serial port
    port = 'COM5'  # Replace with your ESP32's COM port
    baud_rate = 115200
    ser = serial.Serial(port, baud_rate, timeout=1)
    
    # Create a "data" folder if it doesn't exist
    folder_name = "data"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    
    # Generate a timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # Format: YYYYMMDD_HHMMSS
    filename = os.path.join(folder_name, f"imu_data_{timestamp}.csv")
    
    with open(filename, mode='w', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(['Timestamp', 'Accel_X', 'Accel_Y', 'Accel_Z', 'Gyro_X', 'Gyro_Y', 'Gyro_Z'])
        
        print(f"Collecting data for {duration} seconds at 60Hz...")
        start_time = time.time()
        
        while time.time() - start_time < duration:
            # Read data from the serial port
            try:
                line = ser.readline().decode('utf-8').strip()
                
                # Parse the line if it contains valid IMU data
                if line.startswith("Accel"):
                    # Example: "Accel X: 0.12 m/s^2, Y: -0.05 m/s^2, Z: 9.81 m/s^2"
                    accel_line = line.split(", ")
                    gyro_line = ser.readline().decode('utf-8').strip().split(", ")
                    
                    # Extract accelerometer values
                    ax = float(accel_line[0].split(": ")[1].split(" ")[0])
                    ay = float(accel_line[1].split(": ")[1].split(" ")[0])
                    az = float(accel_line[2].split(": ")[1].split(" ")[0])
                    
                    # Extract gyroscope values
                    gx = float(gyro_line[0].split(": ")[1].split(" ")[0])
                    gy = float(gyro_line[1].split(": ")[1].split(" ")[0])
                    gz = float(gyro_line[2].split(": ")[1].split(" ")[0])
                    
                    # Add a timestamp
                    timestamp = time.time()
                    
                    # Save to CSV
                    csv_writer.writerow([timestamp, ax, ay, az, gx, gy, gz])
                    
                    # Print the data to the console
                    print(f"Accel: [{ax}, {ay}, {az}], Gyro: [{gx}, {gy}, {gz}]")
                    
                    # Sleep to maintain 60Hz
                    time.sleep(1 / 60.0)
            
            except Exception as e:
                print(f"Error reading data: {e}")
                break
    
    print(f"Data collection complete. Saved to {filename}.")
    ser.close()

if __name__ == "__main__":
    # Validate and parse input
    if len(sys.argv) != 2:
        print("Usage: python imuCollect.py <seconds>")
        sys.exit(1)
    
    try:
        duration = int(sys.argv[1])
        if duration <= 0:
            raise ValueError("Duration must be greater than 0.")
        collect_data(duration)
    except ValueError as e:
        print(f"Invalid input: {e}")
        sys.exit(1)
