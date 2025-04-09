import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import asyncio
import threading
import os
import time
from bleak import BleakClient, BleakScanner
from datetime import datetime

# BLE UUIDs - Match these with your Arduino code
SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
COMMAND_CHAR_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"  # For sending commands
DATA_CHAR_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"  # For receiving data

# Commands - Match these with your Arduino code
CMD_START_LOGGING = 'S'
CMD_STOP_LOGGING = 'E'
CMD_LIST_FILES = 'L'
CMD_GET_FILE = 'G'
CMD_DELETE_FILE = 'D'

# Create directory for downloaded files
DOWNLOAD_DIR = "downloaded_files"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Global variables
connected_device = None
ble_loop = None
file_transfer_in_progress = False
current_file_data = bytearray()
current_file_name = ""
file_size = 0
bytes_received = 0
is_logging = False

class ESP32LoggerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ESP32 IMU Logger")
        self.root.geometry("800x600")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Create a notebook (tabbed interface)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Connection tab
        self.conn_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.conn_frame, text="Connection")
        
        # Logging tab
        self.logging_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.logging_frame, text="Logging")
        
        # File Management tab
        self.file_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.file_frame, text="File Management")
        
        # Setup each tab
        self.setup_connection_tab()
        self.setup_logging_tab()
        self.setup_file_management_tab()
        
        # Status bar at the bottom
        self.status_var = tk.StringVar()
        self.status_var.set("Disconnected")
        self.status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Create the device info frame
        self.device_info_frame = ttk.Frame(root)
        self.device_info_frame.pack(side=tk.BOTTOM, fill=tk.X, before=self.status_bar)
        
        # Add device state indicator
        self.state_label = ttk.Label(self.device_info_frame, text="Device State:")
        self.state_label.pack(side=tk.LEFT, padx=(10, 5))
        
        self.state_value = ttk.Label(self.device_info_frame, text="Unknown", font=("Arial", 9, "bold"))
        self.state_value.pack(side=tk.LEFT, padx=(0, 20))
        
        # Start the background tasks
        self.start_async_loop()

    def setup_connection_tab(self):
        # Device scanning and connection
        scan_frame = ttk.LabelFrame(self.conn_frame, text="Device Discovery")
        scan_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.device_list = ttk.Combobox(scan_frame, width=40)
        self.device_list.pack(side=tk.LEFT, padx=5, pady=10, expand=True, fill=tk.X)
        
        scan_button = ttk.Button(scan_frame, text="Scan", command=self.scan_for_devices)
        scan_button.pack(side=tk.LEFT, padx=5, pady=10)
        
        connect_button = ttk.Button(scan_frame, text="Connect", command=self.connect_to_device)
        connect_button.pack(side=tk.LEFT, padx=5, pady=10)
        
        disconnect_button = ttk.Button(scan_frame, text="Disconnect", command=self.disconnect_device)
        disconnect_button.pack(side=tk.LEFT, padx=5, pady=10)
        
        # Device log
        log_frame = ttk.LabelFrame(self.conn_frame, text="Connection Log")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.conn_log = scrolledtext.ScrolledText(log_frame, height=10)
        self.conn_log.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.conn_log.config(state=tk.DISABLED)

    def setup_logging_tab(self):
        # Logging controls
        control_frame = ttk.Frame(self.logging_frame)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.start_logging_btn = ttk.Button(control_frame, text="Start Logging", 
                                           command=self.start_logging, state=tk.DISABLED)
        self.start_logging_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.stop_logging_btn = ttk.Button(control_frame, text="Stop Logging", 
                                          command=self.stop_logging, state=tk.DISABLED)
        self.stop_logging_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Logging status
        status_frame = ttk.LabelFrame(self.logging_frame, text="Logging Status")
        status_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.logging_status_var = tk.StringVar()
        self.logging_status_var.set("Not logging")
        status_label = ttk.Label(status_frame, textvariable=self.logging_status_var, font=("Arial", 12, "bold"))
        status_label.pack(padx=10, pady=10)
        
        # Log messages
        log_frame = ttk.LabelFrame(self.logging_frame, text="Log Messages")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.logging_log = scrolledtext.ScrolledText(log_frame)
        self.logging_log.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.logging_log.config(state=tk.DISABLED)

    def setup_file_management_tab(self):
        # File list
        list_frame = ttk.LabelFrame(self.file_frame, text="Files on SD Card")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.file_list = tk.Listbox(list_frame, height=10, width=60)
        self.file_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollbar for file list
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.file_list.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_list.config(yscrollcommand=scrollbar.set)
        
        # Buttons for file operations
        button_frame = ttk.Frame(self.file_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.refresh_btn = ttk.Button(button_frame, text="Refresh List", 
                                     command=self.refresh_file_list, state=tk.DISABLED)
        self.refresh_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.download_btn = ttk.Button(button_frame, text="Download Selected", 
                                      command=self.download_selected_file, state=tk.DISABLED)
        self.download_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.delete_btn = ttk.Button(button_frame, text="Delete Selected", 
                                    command=self.delete_selected_file, state=tk.DISABLED)
        self.delete_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Transfer progress
        progress_frame = ttk.LabelFrame(self.file_frame, text="Transfer Progress")
        progress_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, padx=5, pady=5)
        
        self.progress_label = ttk.Label(progress_frame, text="No transfer in progress")
        self.progress_label.pack(padx=5, pady=5)
        
        # Downloaded files
        downloads_frame = ttk.LabelFrame(self.file_frame, text="Downloaded Files")
        downloads_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.downloads_list = tk.Listbox(downloads_frame, height=5)
        self.downloads_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollbar for downloads list
        dl_scrollbar = ttk.Scrollbar(downloads_frame, orient="vertical", command=self.downloads_list.yview)
        dl_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.downloads_list.config(yscrollcommand=dl_scrollbar.set)
        
        # Populate downloads list
        self.update_downloads_list()
        
    def update_device_state(self, state):
        """Update the device state display in the UI"""
        state_colors = {
            "Idle": "#0000FF",       # Blue
            "Connected": "#00FFFF",  # Cyan
            "Logging": "#00FF00",    # Green
            "Error": "#FF0000",      # Red
            "Transferring": "#FF00FF" # Purple
        }
        
        self.state_value.config(text=state)
        if state in state_colors:
            self.state_value.config(foreground=state_colors[state])
        else:
            self.state_value.config(foreground="black")

    def update_downloads_list(self):
        """Update the list of downloaded files"""
        # Clear the list
        self.downloads_list.delete(0, tk.END)
        
        # Get all files in the downloads directory
        try:
            files = os.listdir(DOWNLOAD_DIR)
            for file in sorted(files):
                if os.path.isfile(os.path.join(DOWNLOAD_DIR, file)):
                    size = os.path.getsize(os.path.join(DOWNLOAD_DIR, file))
                    self.downloads_list.insert(tk.END, f"{file} ({size} bytes)")
        except Exception as e:
            self.log_to_connection(f"Error updating downloads list: {str(e)}")

    def log_to_connection(self, message):
        """Add a message to the connection log with timestamp"""
        self.conn_log.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.conn_log.insert(tk.END, f"[{timestamp}] {message}\n")
        self.conn_log.see(tk.END)
        self.conn_log.config(state=tk.DISABLED)

    def log_to_logging(self, message):
        """Add a message to the logging tab with timestamp"""
        self.logging_log.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logging_log.insert(tk.END, f"[{timestamp}] {message}\n")
        self.logging_log.see(tk.END)
        self.logging_log.config(state=tk.DISABLED)

    def scan_for_devices(self):
        self.device_list.set("Scanning...")
        self.log_to_connection("Scanning for BLE devices...")
        
        # Run the BLE scanner in the asyncio event loop
        if ble_loop:
            asyncio.run_coroutine_threadsafe(self._scan_devices(), ble_loop)

    async def _scan_devices(self):
        try:
            devices = await BleakScanner.discover()
            device_dict = {}
            
            for device in devices:
                if device.name:
                    device_dict[f"{device.name} ({device.address})"] = device.address
                    self.log_to_connection(f"Found: {device.name} ({device.address})")
            
            # Update the UI from the main thread
            self.root.after(0, lambda: self._update_device_list(device_dict))
            
        except Exception as e:
            self.root.after(0, lambda: self.log_to_connection(f"Scan error: {str(e)}"))

    def _update_device_list(self, device_dict):
        self.device_list['values'] = list(device_dict.keys())
        if device_dict:
            self.device_list.current(0)
            self.log_to_connection(f"Found {len(device_dict)} devices")
        else:
            self.device_list.set("No devices found")
            self.log_to_connection("No devices found")

    def connect_to_device(self):
        global connected_device
        
        if not self.device_list.get():
            messagebox.showwarning("Warning", "Please select a device first")
            return
        
        try:
            # Extract the MAC address from the selection
            selection = self.device_list.get()
            if "(" in selection and ")" in selection:
                mac_address = selection.split("(")[1].split(")")[0]
                self.log_to_connection(f"Connecting to {mac_address}...")
                
                # Connect in the asyncio event loop
                if ble_loop:
                    asyncio.run_coroutine_threadsafe(self._connect_to_device(mac_address), ble_loop)
            else:
                messagebox.showwarning("Warning", "Invalid device selection")
        except Exception as e:
            self.log_to_connection(f"Connection error: {str(e)}")

    async def _connect_to_device(self, address):
        global connected_device
        
        try:
            client = BleakClient(address)
            await client.connect()
            
            if client.is_connected:
                connected_device = client
                
                # Update UI in the main thread
                self.root.after(0, lambda: self._update_ui_on_connect())
                
                # Set up notification handler
                await client.start_notify(DATA_CHAR_UUID, self._notification_handler)
                self.root.after(0, lambda: self.log_to_connection("Connected and listening for notifications"))
            else:
                self.root.after(0, lambda: self.log_to_connection("Failed to connect"))
                
        except Exception as e:
            self.root.after(0, lambda: self.log_to_connection(f"Connection error: {str(e)}"))

    def _notification_handler(self, sender, data):
        # Process incoming notifications in the main thread
        try:
            message = data.decode('utf-8')
            self.root.after(0, lambda: self._process_notification(message))
        except UnicodeDecodeError:
            # Handle binary data (file transfer)
            self.root.after(0, lambda: self._process_binary_data(data))

    def _process_notification(self, message):
        global file_transfer_in_progress, current_file_name, current_file_data
        global file_size, bytes_received, is_logging
        
        self.log_to_connection(f"Received: {message[:50]}{'...' if len(message) > 50 else ''}")
        
        # Handle different message types
        if message.startswith("Logging started:"):
            filename = message.split(":", 1)[1].strip()
            self.logging_status_var.set(f"Logging to {filename}")
            self.log_to_logging(f"Started logging to {filename}")
            is_logging = True
            self.update_device_state("Logging")
            
        elif message.startswith("Logging stopped:"):
            filename = message.split(":", 1)[1].strip()
            self.logging_status_var.set("Not logging")
            self.log_to_logging(f"Stopped logging to {filename}")
            is_logging = False
            self.update_device_state("Connected")
            
        elif message.startswith("Files on SD card:"):
            # Clear the file list
            self.file_list.delete(0, tk.END)
            
            # Add files to the list
            lines = message.split("\n")
            for line in lines[1:]:  # Skip the header
                if line.strip():
                    file_info = line.strip()
                    self.file_list.insert(tk.END, file_info)
            
        elif message.startswith("Transfer starting:"):
            # Extract filename and size
            parts = message.split("(")
            current_file_name = parts[0].split(":", 1)[1].strip()
            try:
                file_size = int(parts[1].split(" ")[0])
            except ValueError:
                # Handle potential formatting issues
                self.log_to_connection(f"Warning: Could not parse file size from '{parts[1]}'")
                file_size = 0
            
            # Reset transfer state
            current_file_data = bytearray()
            bytes_received = 0
            file_transfer_in_progress = True
            
            # Update device state
            self.update_device_state("Transferring")
            
            # Update progress UI
            self.progress_var.set(0)
            self.progress_label.config(text=f"Receiving {current_file_name} (0%)")
            self.log_to_connection(f"Starting file transfer for {current_file_name} ({file_size} bytes)")
            
        elif message == "Transfer complete":
            # Save the received file
            if current_file_name and len(current_file_data) > 0:
                self._save_received_file()
                self.log_to_connection(f"Transfer complete, received {bytes_received} bytes")
            else:
                self.log_to_connection(f"Transfer complete, but no data received")
                
            # Reset transfer state
            file_transfer_in_progress = False
            current_file_name = ""
            self.progress_label.config(text="Transfer complete")
            
            # Update device state
            self.update_device_state("Connected")
            
        elif file_transfer_in_progress:
            # This is file data
            current_file_data.extend(message.encode('utf-8'))
            bytes_received += len(message)
            
            # Update progress
            if file_size > 0:
                progress = (bytes_received * 100) / file_size
                self.progress_var.set(progress)
                self.progress_label.config(text=f"Receiving {current_file_name} ({int(progress)}%)")
                
                # Log progress every 20%
                if int(progress) % 20 == 0:
                    self.log_to_connection(f"Download progress: {int(progress)}%")

    def _process_binary_data(self, data):
        global current_file_data, bytes_received, file_size, file_transfer_in_progress
        
        if file_transfer_in_progress:
            # Add the binary data to our buffer
            current_file_data.extend(data)
            bytes_received += len(data)
            
            # Update progress
            if file_size > 0:
                progress = (bytes_received * 100) / file_size
                self.progress_var.set(progress)
                self.progress_label.config(text=f"Receiving {current_file_name} ({int(progress)}%)")
                
                # Log progress every 20%
                if int(progress) % 20 == 0 and int(progress) > 0:
                    self.log_to_connection(f"Download binary progress: {int(progress)}%")
    
    def _save_received_file(self):
        global current_file_name, current_file_data
        
        if not current_file_name:
            self.log_to_connection("Error: No filename for received data")
            return
        
        if len(current_file_data) == 0:
            self.log_to_connection("Error: No data received to save")
            return
        
        # Make sure the filename doesn't have any leading slashes
        clean_filename = current_file_name.lstrip('/')
        file_path = os.path.join(DOWNLOAD_DIR, clean_filename)
        
        try:
            self.log_to_connection(f"Saving file: {file_path} ({len(current_file_data)} bytes)")
            
            # Create the directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            with open(file_path, "wb") as f:
                f.write(current_file_data)
                
            self.log_to_connection(f"File saved successfully: {file_path}")
            self.update_downloads_list()
            
        except Exception as e:
            self.log_to_connection(f"Error saving file: {str(e)}")
            import traceback
            self.log_to_connection(traceback.format_exc())

    def _update_ui_on_connect(self):
        self.status_var.set("Connected")
        self.log_to_connection("Connected successfully")
        self.update_device_state("Connected")
        
        # Enable buttons that require connection
        self.start_logging_btn.config(state=tk.NORMAL)
        self.stop_logging_btn.config(state=tk.NORMAL)
        self.refresh_btn.config(state=tk.NORMAL)
        self.download_btn.config(state=tk.NORMAL)
        self.delete_btn.config(state=tk.NORMAL)
        
        # Refresh the file list
        self.refresh_file_list()

    def disconnect_device(self):
        global connected_device
        
        if connected_device and ble_loop:
            asyncio.run_coroutine_threadsafe(self._disconnect_device(), ble_loop)

    async def _disconnect_device(self):
        global connected_device, is_logging
        
        if connected_device:
            # If logging, stop it first
            if is_logging:
                await self._stop_logging()
            
            try:
                await connected_device.disconnect()
            except Exception as e:
                pass
                
            connected_device = None
            
            # Update UI in the main thread
            self.root.after(0, lambda: self._update_ui_on_disconnect())

    def _update_ui_on_disconnect(self):
        self.status_var.set("Disconnected")
        self.log_to_connection("Disconnected")
        self.update_device_state("Idle")
        
        # Disable buttons that require connection
        self.start_logging_btn.config(state=tk.DISABLED)
        self.stop_logging_btn.config(state=tk.DISABLED)
        self.refresh_btn.config(state=tk.DISABLED)
        self.download_btn.config(state=tk.DISABLED)
        self.delete_btn.config(state=tk.DISABLED)
        
        # Update logging status
        self.logging_status_var.set("Not logging")
        is_logging = False

    def start_logging(self):
        if connected_device and ble_loop:
            asyncio.run_coroutine_threadsafe(self._start_logging(), ble_loop)

    async def _start_logging(self):
        if connected_device:
            try:
                # Send the start logging command
                await connected_device.write_gatt_char(COMMAND_CHAR_UUID, CMD_START_LOGGING.encode())
                self.root.after(0, lambda: self.log_to_logging("Sent start logging command"))
            except Exception as e:
                self.root.after(0, lambda: self.log_to_logging(f"Error starting logging: {str(e)}"))

    def stop_logging(self):
        if connected_device and ble_loop:
            asyncio.run_coroutine_threadsafe(self._stop_logging(), ble_loop)

    async def _stop_logging(self):
        if connected_device:
            try:
                # Send the stop logging command
                await connected_device.write_gatt_char(COMMAND_CHAR_UUID, CMD_STOP_LOGGING.encode())
                self.root.after(0, lambda: self.log_to_logging("Sent stop logging command"))
            except Exception as e:
                self.root.after(0, lambda: self.log_to_logging(f"Error stopping logging: {str(e)}"))

    def refresh_file_list(self):
        if connected_device and ble_loop:
            asyncio.run_coroutine_threadsafe(self._refresh_file_list(), ble_loop)

    async def _refresh_file_list(self):
        if connected_device:
            try:
                # Clear the file list
                self.root.after(0, lambda: self.file_list.delete(0, tk.END))
                
                # Send the list files command
                await connected_device.write_gatt_char(COMMAND_CHAR_UUID, CMD_LIST_FILES.encode())
                self.root.after(0, lambda: self.log_to_connection("Requested file list"))
            except Exception as e:
                self.root.after(0, lambda: self.log_to_connection(f"Error refreshing file list: {str(e)}"))

    def download_selected_file(self):
        if not connected_device:
            messagebox.showwarning("Warning", "Not connected to a device")
            return
            
        selected = self.file_list.curselection()
        if not selected:
            messagebox.showwarning("Warning", "No file selected")
            return
            
        file_info = self.file_list.get(selected[0])
        
        # Extract just the filename (before the size in parentheses)
        if " (" in file_info:
            filename = file_info.split(" (")[0]
        else:
            filename = file_info
            
        if ble_loop:
            asyncio.run_coroutine_threadsafe(self._download_file(filename), ble_loop)

    async def _download_file(self, filename):
        global file_transfer_in_progress, current_file_data, bytes_received
        
        if connected_device:
            try:
                # Reset any existing transfer state
                file_transfer_in_progress = False
                current_file_data = bytearray()
                bytes_received = 0
                
                # Send the get file command
                command = f"{CMD_GET_FILE}{filename}"
                self.log_to_connection(f"Sending download command: {command}")
                await connected_device.write_gatt_char(COMMAND_CHAR_UUID, command.encode())
                self.root.after(0, lambda: self.log_to_connection(f"Requested download of {filename}"))
            except Exception as e:
                self.root.after(0, lambda: self.log_to_connection(f"Error downloading file: {str(e)}"))

    def delete_selected_file(self):
        if not connected_device:
            messagebox.showwarning("Warning", "Not connected to a device")
            return
            
        selected = self.file_list.curselection()
        if not selected:
            messagebox.showwarning("Warning", "No file selected")
            return
            
        file_info = self.file_list.get(selected[0])
        
        # Extract just the filename
        if " (" in file_info:
            filename = file_info.split(" (")[0]
        else:
            filename = file_info
            
        # Confirm deletion
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {filename}?"):
            if ble_loop:
                asyncio.run_coroutine_threadsafe(self._delete_file(filename), ble_loop)

    async def _delete_file(self, filename):
        if connected_device:
            try:
                # Send the delete file command
                command = f"{CMD_DELETE_FILE}{filename}"
                await connected_device.write_gatt_char(COMMAND_CHAR_UUID, command.encode())
                self.root.after(0, lambda: self.log_to_connection(f"Requested deletion of {filename}"))
                
                # Refresh the file list after a short delay
                await asyncio.sleep(1)
                await self._refresh_file_list()
                
            except Exception as e:
                self.root.after(0, lambda: self.log_to_connection(f"Error deleting file: {str(e)}"))

    def start_async_loop(self):
        global ble_loop
        
        # Create a new event loop
        loop = asyncio.new_event_loop()
        ble_loop = loop
        
        # Define a function to run the loop
        def run_event_loop():
            asyncio.set_event_loop(loop)
            loop.run_forever()
        
        # Start the event loop in a separate thread
        threading.Thread(target=run_event_loop, daemon=True).start()

    def on_closing(self):
        global ble_loop, connected_device
        
        # Disconnect if connected
        if connected_device and ble_loop:
            # We need to use a different approach since the main loop is about to exit
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                loop.run_until_complete(connected_device.disconnect())
            except:
                pass
        
        # Stop the event loop
        if ble_loop:
            ble_loop.call_soon_threadsafe(ble_loop.stop)
        
        # Destroy the window
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ESP32LoggerGUI(root)
    root.mainloop()