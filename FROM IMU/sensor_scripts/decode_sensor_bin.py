import struct
import subprocess
import argparse
from argparse import RawTextHelpFormatter
import csv
import sys
import re
from datetime import datetime
import sensor_bin2_to_bin
import sensor_pb_to_bin
import decode_targeted_data
import decode_hr_sensor_data
import decode_baro_sensor_data
import swim_analysis_message_pb2 as swim_pb
from google.protobuf.internal import decoder
import swim_analysis_message_pb2 as proto

TIMESTAMP_SCALE = 25 #  us/LSB
GYRO_SCALE = 35      #  mdps/LSB
ACCEL_SCALE = 0.122  #  0.122mg/LSB
MAG_SCALE = 1.5      #  mgauss/LSB

FIFO_SAMPLE_SIZE = 156
ONE_SAMPLE_BYTES = 24
FIFO_BYTES = ONE_SAMPLE_BYTES * FIFO_SAMPLE_SIZE
FIFO_INTERVAL_MS = 1500

# Time format argument
MS_FROM_ZERO = "0"
MS_EPOCH = "1"
TICK_TIME = "2"

def get_tick_time_diff(former, latter):
    if (former <= latter):
        return latter - former
    else:
        # ticktime overflow occured
        return int('0xffffff',16) + latter - former

def getSensorBinPBSensorTypes(filename):
    sensor_types = {'test'}
    with open(filename, "rb") as bin_pb_file:
        buf = bin_pb_file.read()
        pos = 0
        print("Sensor file = {}".format(len(buf)))
        while len(buf) > 0:
            msg_len, new_pos = decoder._DecodeVarint (buf, 0)
            n = new_pos
            msg_buf = buf[n:n+msg_len]
            buf = buf[n+msg_len:]
            input_msg = proto.SwimAnalysisMessage()
            input_msg.ParseFromString(msg_buf)
            if input_msg.message_type != proto.SwimAnalysisMessage.MessageType.SENSOR_DATA:
                if input_msg.message_type == proto.SwimAnalysisMessage.MessageType.ACTIVITY_INFO:
                    print("Swim activity type = {}".format(input_msg.activity_info.swim_type))
                    print("Pool length = {}".format(input_msg.activity_info.pool_length))
                    print("Orientation = {}".format(input_msg.activity_info.goggles_orientation))
                # else:
                #     print("input event = {}".format(input_msg.message_type))
            elif input_msg.sensor_data.type == proto.SensorData.Type.GYR_ACC_MAG or \
                input_msg.sensor_data.type == proto.SensorData.Type.GYR_ACC or \
                input_msg.sensor_data.type == proto.SensorData.Type.GYR_GYR_ACC_MAG_13_SAMPLES or \
                input_msg.sensor_data.type == proto.SensorData.Type.GYR_ACC_13_SAMPLES:
                sensor_types.add("RAW_SENSOR")
            elif input_msg.sensor_data.type == proto.SensorData.Type.DIFF_ROLL_10_HZ or \
                input_msg.sensor_data.type == proto.SensorData.Type.VERT_ACC_10_HZ:
                sensor_types.add("TARGETED_SR")
            elif input_msg.sensor_data.type == proto.SensorData.Type.GYR_ACC_MAG_26HZ:
                sensor_types.add("TDL")
            elif input_msg.sensor_data.type == proto.SensorData.Type.HR_LED_GREEN:
                sensor_types.add("HR")
            elif input_msg.sensor_data.type == proto.SensorData.Type.HR_LED_GREEN_IR or \
                input_msg.sensor_data.type == proto.SensorData.Type.HR_LED_GREEN_IR_CYCLE:
                sensor_types.add("HR2")
            elif input_msg.sensor_data.type == proto.SensorData.Type.HR_LED_GREEN_IR_RED:
                sensor_types.add("HR3")
            elif input_msg.sensor_data.type == proto.SensorData.Type.BAROMETER_TEMPERATURE:
                sensor_types.add("BARO")
    return sensor_types


parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter)
parser.add_argument("-f", "--file", help="Sensor file to decode from binary format", required=True)
time_argument_help_str = "[{}] millisec from zero (default)\n[{}] epoch millisec\n[{}] tick time".format(MS_FROM_ZERO, MS_EPOCH, TICK_TIME)
parser.add_argument("--time", help=time_argument_help_str, default="0", required=False)
parser.add_argument("--tsv", help="Output tsv instead of csv (default)", action='store_true')

sensor_bin_filename = parser.parse_args().file
ext = sensor_bin_filename.rsplit(".", 1)[1]

filename = sensor_bin_filename.rsplit(".", 1)[0]

# If it's sensor.bin2 (without mag and timestamp), convert it first
if ext == 'bin2':
    if not sensor_bin2_to_bin.convert(sensor_bin_filename):
        sys.exit("Failed to convert .bin2 file")
    sensor_bin_filename = filename + '.bin'
elif ext == 'bin_pb':
    sensor_types = getSensorBinPBSensorTypes(sensor_bin_filename)

    if "HR" in sensor_types:
        print("\nDetected HR, decoding HR...")
        decode_hr_sensor_data.convert_HR(sensor_bin_filename)
    if "HR2" in sensor_types:
        print("\nDetected HR2, decoding HR2...")
        decode_hr_sensor_data.convert_HR2(sensor_bin_filename)
    elif "HR3" in sensor_types:
        print("\nDetected HR3, decoding HR3...")
        decode_hr_sensor_data.convert_HR3(sensor_bin_filename)
    if "BARO" in sensor_types:
        decode_baro_sensor_data.convert(sensor_bin_filename)
        print("\nDetected Barometer, decoding Barometer...")

    # These are mutually exclusive
    if "RAW_SENSOR" in sensor_types:
        print("Detected raw sensor, decoding raw sensor...")
        sensor_pb_to_bin.convert(sensor_bin_filename)
        sensor_bin_filename = filename + '.bin'
    elif "TDL" in sensor_types:
        decode_targeted_data.convert_26HZ(sensor_bin_filename)
        sys.exit("Done")
    elif "TARGETED_SR" in sensor_types:
        decode_targeted_data.convert_SR(sensor_bin_filename)
        sys.exit("Done")

fin = open(sensor_bin_filename, "rb")

use_tsv = parser.parse_args().tsv
if use_tsv:
    csv_filename = filename + '.tsv'
else:
    csv_filename = filename + '.csv'

time_format = parser.parse_args().time

timestamp = 0
if time_format == MS_EPOCH:
    print("matching filename time")
    # Get time from filename
    matches = re.match("sensor_data-([0-9]{4})([0-9]{2})([0-9]{2})-([0-9]{2})([0-9]{2})([0-9]{2})", filename)
    if matches:
        year = int(matches.group(1))
        month = int(matches.group(2))
        day = int(matches.group(3))
        hour = int(matches.group(4))
        minute = int(matches.group(5))
        seconds = int(matches.group(6))
        print("Sensor timestamp starts on {}-{}-{} at {}:{}:{}".format(year, month, day, hour, minute, seconds))
        start_time = datetime(year,month,day,hour,minute,seconds)
        epoch = datetime(1970,1,1)
        timestamp = long((start_time - epoch).total_seconds() * 1000)
    else:
        print("NOTE: Can't find timestamp from filename. Startime from zero")
        timestamp = 0


row_read = 0
last_FIFO_timestamp = 0
with open(csv_filename, 'w') as csvfile:
    if use_tsv:
        writer = csv.writer(csvfile, delimiter='\t', lineterminator='\n')
    else:
        writer = csv.writer(csvfile, delimiter=',', lineterminator='\n')
    if time_format == TICK_TIME:
        writer.writerow(["ticktime", "acc_x_mg", "acc_y_mg", "acc_z_mg", "gyro_x_mdps", "gyro_y_mdps", "gyro_z_mdps", "mag_x_mgauss", "mag_y_mgauss", "mag_z_mgauss"])
    else:
        writer.writerow(["time_ms", "acc_x_mg", "acc_y_mg", "acc_z_mg", "gyro_x_mdps", "gyro_y_mdps", "gyro_z_mdps", "mag_x_mgauss", "mag_y_mgauss", "mag_z_mgauss"])

    #  Format: Little endian: G_X G_Y G_Z A_X A_Y A_Z M_X M_Y M_Z,
    #        Followed by: Time midbyte, Time MSB, 0, Time LSB, 0, 0
    # So, 24 bytes per sample

    try:

        # Read 1 FIFO window at a time, 24 bytes * 156
        FIFO_byte = fin.read(FIFO_BYTES)

        last_tick_time = -1
        while len(FIFO_byte) == FIFO_BYTES:
            FIFO_byte = bytearray(FIFO_byte)
            # print("FIFO_byte size = " + str(len(FIFO_byte)))
            row_read = row_read + FIFO_SAMPLE_SIZE

            row_str_list = []

            if time_format != TICK_TIME:
                # Find the tick time of the last sample
                last_FIFO_sample_byte = FIFO_byte[(FIFO_SAMPLE_SIZE - 1) * ONE_SAMPLE_BYTES : FIFO_SAMPLE_SIZE * ONE_SAMPLE_BYTES]
                last_FIFO_sample_data = struct.unpack("<hhhhhhhhhBBxBxx", last_FIFO_sample_byte)
                last_FIFO_tick_time = 0
                last_FIFO_tick_time |= int(last_FIFO_sample_data[9] << 8)
                last_FIFO_tick_time |= int(last_FIFO_sample_data[10] << 16)
                last_FIFO_tick_time |= int(last_FIFO_sample_data[11])

                last_FIFO_timestamp = last_FIFO_timestamp + FIFO_INTERVAL_MS


            for n in range(0, FIFO_SAMPLE_SIZE):
                byte = FIFO_byte[n * ONE_SAMPLE_BYTES : (n+1) * ONE_SAMPLE_BYTES]

                row = struct.unpack("<hhhhhhhhhBBxBxx", byte)

                gyro_f = [0, 0 ,0]
                gyro_f[0] = int(row[0] * GYRO_SCALE)
                gyro_f[1] = int(row[1] * GYRO_SCALE)
                gyro_f[2] = int(row[2] * GYRO_SCALE)

                acc_f = [0, 0 ,0]
                acc_f[0] = int(row[3] * ACCEL_SCALE)
                acc_f[1] = int(row[4] * ACCEL_SCALE)
                acc_f[2] = int(row[5] * ACCEL_SCALE)

                mag_f = [0, 0, 0]
                mag_f[0] = int(row[6] * MAG_SCALE)
                mag_f[1] = int(row[7] * MAG_SCALE)
                mag_f[2] = int(row[8] * MAG_SCALE)

                tick_time = 0

                tick_time |= int(row[9] << 8)
                tick_time |= int(row[10] << 16)
                tick_time |= int(row[11])


                if time_format == TICK_TIME:
                    timestamp = tick_time
                else:
                    diff_tick_time = get_tick_time_diff(tick_time, last_FIFO_tick_time)

                    timestamp = last_FIFO_timestamp - ((155 - n) * FIFO_INTERVAL_MS / 156)

                row_str = [int(round(timestamp)), acc_f[0], acc_f[1], acc_f[2], gyro_f[0], gyro_f[1], gyro_f[2], mag_f[0], mag_f[1], mag_f[2]]

                row_str_list.append(row_str)

            for row_str in row_str_list:
                writer.writerow(row_str)

            FIFO_byte = fin.read(FIFO_BYTES)
    finally:
        fin.close()

print("Finished decoding {} samples ({}s).".format(row_read, timestamp/1000))
print("{} -> {}\n".format(sensor_bin_filename, csv_filename))
