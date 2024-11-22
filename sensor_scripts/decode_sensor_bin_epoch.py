import struct
import subprocess
import argparse
from argparse import RawTextHelpFormatter
import csv
import sys
import re
from datetime import datetime 

TIMESTAMP_SCALE = 25 #  us/LSB
GYRO_SCALE = 35      #  mdps/LSB
ACCEL_SCALE = 0.122  #  0.122mg/LSB
MAG_SCALE = 1.5      #  mgauss/LSB

FIFO_SAMPLE_SIZE = 156
# 6B x 3 for IMU + 8B for time
ONE_SAMPLE_BYTES = (18 + 8)
FIFO_BYTES = ONE_SAMPLE_BYTES * FIFO_SAMPLE_SIZE

parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter)
parser.add_argument("-f", "--file", help="Sensor file to decode from binary format", required=True)

sensor_bin_filename = parser.parse_args().file
ext = sensor_bin_filename.rsplit(".", 1)[1]

if ext != "bin_epoch":
    print("Ext is {}".format(ext))
    sys.exit("This is not .bin_epoch file!")

filename = sensor_bin_filename.rsplit(".", 1)[0]

fin = open(sensor_bin_filename, "rb")

csv_filename = filename + '.csv'

row_read = 0

bin_filename = filename + '.bin'
bin_file = open(bin_filename, "wb");
print("Writing to bin file {}".format(bin_file))

with open(csv_filename, 'w') as csvfile:
    csv_writer = csv.writer(csvfile, delimiter=',', lineterminator='\n')
    csv_writer.writerow(["epoch_time_ms", "acc_x_mg", "acc_y_mg", "acc_z_mg", "gyro_x_mdps", "gyro_y_mdps", "gyro_z_mdps", "mag_x_mgauss", "mag_y_mgauss", "mag_z_mgauss"])

    try:
        # Read 1 FIFO window at a time, 24 bytes * 156
        FIFO_byte = fin.read(FIFO_BYTES)

        last_tick_time = -1 
        while len(FIFO_byte) == FIFO_BYTES:
            FIFO_byte = bytearray(FIFO_byte)
            row_read = row_read + FIFO_SAMPLE_SIZE

            row_str_list = []

            for n in range(0, FIFO_SAMPLE_SIZE):
                byte = FIFO_byte[n * ONE_SAMPLE_BYTES : (n+1) * ONE_SAMPLE_BYTES]

                row = struct.unpack("<hhhhhhhhhQ", byte)

                gyr_x = row[0]
                gyr_y = row[1]
                gyr_z = row[2]

                acc_x = row[3]
                acc_y = row[4]
                acc_z = row[5]

                mag_x = row[6]
                mag_y = row[7]
                mag_z = row[8]

                gyro_f = [0, 0 ,0] 
                gyro_f[0] = int(gyr_x * GYRO_SCALE)
                gyro_f[1] = int(gyr_y * GYRO_SCALE)
                gyro_f[2] = int(gyr_z * GYRO_SCALE)

                acc_f = [0, 0 ,0] 
                acc_f[0] = int(acc_x * ACCEL_SCALE)
                acc_f[1] = int(acc_y * ACCEL_SCALE)
                acc_f[2] = int(acc_z * ACCEL_SCALE)

                mag_f = [0, 0, 0]
                mag_f[0] = int(mag_x * MAG_SCALE)
                mag_f[1] = int(mag_y * MAG_SCALE)
                mag_f[2] = int(mag_z * MAG_SCALE)

                timestamp = int(row[9])

                row_str = [timestamp, acc_f[0], acc_f[1], acc_f[2], gyro_f[0], gyro_f[1], gyro_f[2], mag_f[0], mag_f[1], mag_f[2]]

                row_str_list.append(row_str)

                #  Format: Little endian: G_X G_Y G_Z A_X A_Y A_Z M_X M_Y M_Z,
                #        Followed by: Time midbyte, Time MSB, 0, Time LSB, 0, 0
                bin_file.write(struct.pack("<hhhhhhhhhxxxxxx",
                                            gyr_x,
                                            gyr_y,
                                            gyr_z,
                                            acc_x,
                                            acc_y,
                                            acc_z,
                                            mag_x,
                                            mag_y,
                                            mag_z))

            for row_str in row_str_list:
                csv_writer.writerow(row_str)

            FIFO_byte = fin.read(FIFO_BYTES)
    finally:
        fin.close()
        bin_file.close()

print("Finished decoding {} samples ({}s).".format(row_read, timestamp/1000))
print("{} -> {}\n".format(sensor_bin_filename, csv_filename))
