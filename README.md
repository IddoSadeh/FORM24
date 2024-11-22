# How the code works

`ML_run.m` will run take a file in the `data` folder and send it to be processed by `decode_sensor_bin.py`

`decode_sensor_bin.py` will call the rest of the python files, do some magic and output a csv file to the `data` folder.

if you want to run the python code without MATLAB i believe you need to manually set `ext` to the file extension and `filename` to the file name, and the press run:
![alt text](image.png)

# OCTAVE/MATLAB files

files have been changed to work in MATLAB