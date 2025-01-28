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
