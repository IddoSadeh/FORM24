#  Script to create a binary file in LSM6DSL FIFO format from Machine Learning's TSV files.
import argparse;
import datetime;
import struct;
import time;

SHRT_MIN = -32768;
SHRT_MAX = 32767;

SECOND_TO_MICROSECOND = 1000000

TIMESTAMP_SCALE = 25 #  us/LSB

GYRO_SCALE = 35      #  mdps/LSB
ACCEL_SCALE = 0.122  #  0.122mg/LSB
MAG_SCALE = 1.5      #  mgauss/LSB

#  Clamp a value between a minimum and maximum
def clamp(n, nmin, nmax):
    return min(nmax, max(nmin, n));

parser = argparse.ArgumentParser();
parser.add_argument("-f", "--file", help="Sensor file to convert to binary format", required=True);

first_timestamp = 0;

output_file = open("sensor.bin", "w");

with open(parser.parse_args().file, "r") as input_file:
    for line in input_file:
        str = line.split();
        #  Ignore the first line if it has column headers
        if (str[0] == "Timestamp"):
            continue;
        #  Timestamp LSB = 25us/LSB
        date_part_stamp = str[0];
        time_part_stamp = str[1];
        timestamp = datetime.datetime.strptime(date_part_stamp+" "+time_part_stamp, "%y-%m-%d %H:%M:%S.%f");
        full_timestamp = int(time.mktime(timestamp.timetuple())) * SECOND_TO_MICROSECOND;
        full_timestamp += timestamp.microsecond;
        lsm6dsm_timestamp = full_timestamp / TIMESTAMP_SCALE;
        #  Time is relative to the first timestamp
        if (first_timestamp == 0):
            first_timestamp = lsm6dsm_timestamp;

        data_timestamp = lsm6dsm_timestamp - first_timestamp;

        #  Gyro each bit is worth 35mdps, so scale
        raw_gyr_x = clamp(int(str[5]) / GYRO_SCALE, SHRT_MIN, SHRT_MAX);
        raw_gyr_y = clamp(int(str[6]) / GYRO_SCALE, SHRT_MIN, SHRT_MAX);
        raw_gyr_z = clamp(int(str[7]) / GYRO_SCALE, SHRT_MIN, SHRT_MAX);
        #  Acc each bit is worth 0.122mg, so scale
        raw_acc_x = clamp(int(str[2]) / ACCEL_SCALE, SHRT_MIN, SHRT_MAX);
        raw_acc_y = clamp(int(str[3]) / ACCEL_SCALE, SHRT_MIN, SHRT_MAX);
        raw_acc_z = clamp(int(str[4]) / ACCEL_SCALE, SHRT_MIN, SHRT_MAX);
        #  Mag each bit is worth 1.5mgauss, so scale
        raw_mag_x = clamp(int(str[8]) / MAG_SCALE, SHRT_MIN, SHRT_MAX);
        raw_mag_y = clamp(int(str[9]) / MAG_SCALE, SHRT_MIN, SHRT_MAX);
        raw_mag_z = clamp(int(str[10]) / MAG_SCALE, SHRT_MIN, SHRT_MAX);

        #  Correctly orient sensor data
        #  Orientation matrix:
        #  [ 0  1  0 ]
        #  [ 1  0  0 ]
        #  [ 0  0 -1 ]
        #  Gyro
        gyr_x = raw_gyr_y;
        gyr_y = raw_gyr_x;
        gyr_z = -raw_gyr_z;
        #  Acc
        acc_x = raw_acc_y;
        acc_y = raw_acc_x;
        acc_z = -raw_acc_z;
        #  Mag
        mag_x = raw_mag_y;
        mag_y = raw_mag_x;
        mag_z = -raw_mag_z;
        #  Format: Little endian: G_X G_Y G_Z A_X A_Y A_Z M_X M_Y M_Z,
        #        Followed by: Time midbyte, Time MSB, 0, Time LSB, 0, 0
        output_file.write(struct.pack("<hhhhhhhhhBBxBxx",
                                      gyr_x,
                                      gyr_y,
                                      gyr_z,
                                      acc_x,
                                      acc_y,
                                      acc_z,
                                      mag_x,
                                      mag_y,
                                      mag_z,
                                      (data_timestamp >> 8) & 0xFF,
                                      (data_timestamp >> 16) & 0xFF,
                                      (data_timestamp >> 0) & 0xFF));
    input_file.close();
output_file.close();
