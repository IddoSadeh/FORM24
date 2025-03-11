import asyncio
from bleak import BleakClient, BleakScanner

BATTERY_SERVICE_UUID = "0000180F-0000-1000-8000-00805F9B34FB"
BATTERY_CHARACTERISTIC_UUID = "00002A19-0000-1000-8000-00805F9B34FB"

async def find_esp32():
    print("Scanning for ESP32 Battery Monitor...")
    devices = await BleakScanner.discover()

    for device in devices:
        if "ESP32_BatteryMonitor" in device.name:
            print(f"Found ESP32: {device.address}")
            return device.address

    print("ESP32 not found. Make sure it's powered on and advertising.")
    return None

async def read_battery():
    address = await find_esp32()
    if not address:
        return

    async with BleakClient(address) as client:
        print("Connected to ESP32 BLE!")
        while True:
            battery_data = await client.read_gatt_char(BATTERY_CHARACTERISTIC_UUID)
            battery_percentage = int.from_bytes(battery_data, byteorder='little')
            print(f"Battery Level: {battery_percentage}%")
            
            if battery_percentage <= 20:
                print("Warning: Low Battery!")
            
            await asyncio.sleep(2)

asyncio.run(read_battery())
