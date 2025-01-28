# Table of Contents
- [Table of Contents](#table-of-contents)
- [Circuit](#circuit)
  - [Circuit Designer Link](#circuit-designer-link)
  - [Circuit Image](#circuit-image)
  - [Datasheets](#datasheets)
- [IMU Form Code](#imu-form-code)
  - [Folders Overview](#folders-overview)
  - [How Data is Processed](#how-data-is-processed)
  - [Running Python Code Without MATLAB](#running-python-code-without-matlab)
- [Force Sensor Files](#force-sensor-files)
- [ESP IMUs](#esp-imus)
  - [How We Fixed ESP Issues](#how-we-fixed-esp-issues)

---

# Circuit

## Circuit Designer Link
https://app.cirkitdesigner.com/project/71fc41e8-6a78-4813-9acc-cf6826728f7b

## Circuit Image
![image](circuit_image.png)

## Datasheets
Datasheets for both our boards:
![image](ESP32DEVKITV1.png)
![image](ESP32FEATHERV2.png)

---

# IMU Form Code

## Folders Overview
- Data in `data` folder. 
- MATLAB scripts in `analysis_scripts` folder. 
- Python in `sensor_scripts` folder.

## How Data is Processed
`ML_run.m` will take a file in the `data` folder and send it to be processed by `decode_sensor_bin.py`.

`decode_sensor_bin.py` will call the rest of the Python files, do some magic, and output a CSV file to the `data` folder.

`read_data.m` is called by `ML_run.m` to turn the CSV into a MATLAB dataframe.

## Running Python Code Without MATLAB
If you want to run the Python code without MATLAB, you need to manually set `ext` to the file extension and `filename` to the file name, then press run:
![alt text](image.png)

---

# Force Sensor Files
Files are located in the folder called `force_sensor`.

---

# ESP IMUs


## How We Fixed ESP Issues
Making the Adafruit work requires specific drivers. Steps:

```
Physically Connect the Adafruit ESP32. Open the Arduino IDE. Go to File > Preferences (or Arduino > Preferences on macOS). Add this URL in the Additional Board Manager URLs field: https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json (Separate it with a comma if other URLs were already present.)

Go to Tools > Board > Boards Manager. Search for ESP32. Click Install next to the "esp32 by Espressif Systems" package (v3.1.1). Go to Tools > Board and select Adafruit Feather ESP32 V2 from the list. Go to Tools > Port and select the correct COM port (you can check device manager to see which COM port you’re using for the ESP32).

After this, go to the top tab and click: “Tools,” then go to Sketch > Include Library > Manage Libraries. Search for MPU6050 in the Library Manager. If first time set up, install the Adafruit MPU6050 library (It will prompt you to install the dependencies; make sure you do that too). Ask ChatGPT how to install an Arduino library if you forgot—it’ll tell you exactly what to click.

You can do a simple code to make sure I2C is connected (assuming the MPU6050 is already physically connected to the Adafruit ESP32).

Go to the Git repo we have for FORM. Then under esp IMU, copy the code in the .ino file (there should be only one .ino file) into Arduino IDE, then upload the code onto your ESP32.

You can double-check in Serial Monitor (baud rate MUST be 115200) to see the output, but this step, in my opinion, you should skip. You can just go straight to the Python part.

Now, in PowerShell, cd into the same analysis_scripts folder. Now, run python imucollect.py <seconds to sample> here.

It SHOULD now store all six axes into the /analysis_scripts/data folder, but I found that I need to click the reset button on the ESP32 sometimes while the script is running, which is annoying. But click that button and then start doing some circles (you should see some numbers changing, hopefully).

Now you have the timestamped data in $STEM/analysis_scripts/data. From here, you can run the Python notebook.

```