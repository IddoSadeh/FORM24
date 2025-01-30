from bleak import BleakClient
import asyncio

ESP32_MAC_ADDRESS = "14:2b:2f:af:65:2a"  # Replace with your ESP32 MAC Address
CHARACTERISTIC_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"

async def read_imu_data():
    async with BleakClient(ESP32_MAC_ADDRESS) as client:
        print("Connected to ESP32")

        def notification_handler(sender, data):
            print(f"IMU Data: {data.decode('utf-8')}")

        await client.start_notify(CHARACTERISTIC_UUID, notification_handler)

        while True:
            await asyncio.sleep(1)  # Keep the script running to receive data

asyncio.run(read_imu_data())
