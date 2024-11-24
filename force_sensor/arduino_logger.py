import serial
import csv
import time
import os
import argparse

# Ensure the data folder exists
if not os.path.exists("data"):
    os.makedirs("data")

# Define the COM port for your Arduino
COM_PORT = "COM5"  # Replace with your Arduino's port (e.g., COM3, /dev/ttyUSB0)

def read_arduino_data(duration):
    max_duration = 20  # Maximum allowed duration in seconds

    # Validate duration
    if duration > max_duration:
        print(f"Duration of {duration} seconds exceeds the maximum limit of {max_duration} seconds. Truncating to {max_duration} seconds.")
        duration = max_duration

    # Open serial connection
    try:
        ser = serial.Serial(COM_PORT, 9600)  # Use the predefined COM port
        print(f"Connected to {ser.port}. Starting data collection for {duration} seconds...")
    except serial.SerialException:
        print(f"Failed to connect to the specified port {COM_PORT}. Ensure the Arduino is connected.")
        return

    # Prepare CSV file with timestamp
    timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"data/arduino_data_{timestamp}.csv"

    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Time (s)", "Data"])  # Write header

        start_time = time.time()
        elapsed_time = 0
        count = 0

        try:
            while elapsed_time < duration:
                line = ser.readline().decode('utf-8').strip()  # Read and decode serial data
                elapsed_time = time.time() - start_time
                writer.writerow([round(elapsed_time, 3), line])  # Write time and data
                print(f"{round(elapsed_time, 3)} s: {line}")
                count += 1
                time.sleep(0.01)  # Wait ~10 ms (100 Hz)

        except KeyboardInterrupt:
            print("\nData collection interrupted by user.")

        finally:
            ser.close()
            print(f"Data collection complete. {count} entries saved to {filename}.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Read Arduino data and save to CSV.")
    parser.add_argument("duration", type=int, nargs='?', default=20, help="Duration in seconds (max: 20)")
    args = parser.parse_args()

    read_arduino_data(args.duration)
