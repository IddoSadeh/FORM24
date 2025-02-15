from bleak import BleakClient
import asyncio
import sys
import time
import csv
import os

ESP32_MAC_ADDRESS = "14:2b:2f:af:65:2a"  # Replace with your ESP32 MAC Address
CHARACTERISTIC_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"

delay_seconds = 0.033  # Delay in seconds (0.033 delay = 30Hz)

# Create a timestamped CSV filename in the 'data' folder
def get_timestamped_filename():
    timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")  # Format timestamp as Year-Month-Day_Hour-Minute-Second
    folder = "data"
    if not os.path.exists(folder):
        os.makedirs(folder)  # Create 'data' folder if it doesn't exist
    return os.path.join(folder, f"imu_data_{timestamp}.csv")

# Write the header row if the CSV file doesn't exist
def write_header(csv_filename):
    with open(csv_filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "Accel_X", "Accel_Y", "Accel_Z", "Gyro_X", "Gyro_Y", "Gyro_Z"])

async def read_imu_data(run_time):
    client = BleakClient(ESP32_MAC_ADDRESS)
    csv_filename = get_timestamped_filename()  # Generate the timestamped filename
    
    try:
        await client.connect()
        print("Connected to ESP32")

        # Open the CSV file in append mode to save data continuously
        with open(csv_filename, mode='a', newline='') as file:
            writer = csv.writer(file)
            print(f"Saving data to: {csv_filename}")
            
            def notification_handler(sender, data):
                try:
                    # Decode the data received and split it into IMU values
                    data_str = data.decode('utf-8')
                    imu_values = data_str.split(',')
                    if len(imu_values) == 6:
                        # Get current timestamp
                        timestamp = time.time()
                        
                        # Write timestamp and IMU values to the CSV
                        writer.writerow([timestamp] + imu_values)
                        print(f"Timestamp: {timestamp}, IMU Data: {imu_values}")
                except Exception as e:
                    print(f"Error in notification handler: {e}")

            # Start receiving notifications
            await client.start_notify(CHARACTERISTIC_UUID, notification_handler)

            # Collect data at around 50 Hz (20 ms delay)
            start_time = time.time()
            while time.time() - start_time < run_time:
                await asyncio.sleep(delay_seconds)  # 50Hz = 20ms delay

            print(f"Data collection completed. Script ran for {run_time} seconds.")
    
    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally:
        # Disconnect from ESP32 to allow subsequent connections
        if client.is_connected:
            await client.disconnect()
        print("Disconnected from ESP32")

if __name__ == "__main__":
    # Default run time (20 seconds)
    run_time = 20

    # Check if --<seconds> argument is passed
    if len(sys.argv) > 1 and sys.argv[1].startswith("--"):
        try:
            custom_time = int(sys.argv[1][2:])  # Get number after --
            if custom_time <= 120: 
                run_time = custom_time
            else:
                print("Warning: Maximum time limit is 120 seconds. Using default (20 seconds).")
        except ValueError:
            print("Error: Invalid time format. Using default (20 seconds).")

    # Generate the CSV filename and write the header
    write_header(get_timestamped_filename())

    # Run the IMU data collection
    asyncio.run(read_imu_data(run_time))
