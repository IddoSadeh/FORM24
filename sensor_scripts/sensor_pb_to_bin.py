import swim_analysis_message_pb2 as proto
from google.protobuf.internal import decoder
import struct
import argparse
from argparse import RawTextHelpFormatter
import sys
import re
import os
import csv

FIFO_SAMPLE_SIZE = 156
REAL_REAL_TIME_FIFO_SAMPLE_SIZE = 13
ONE_GYR_ACC_SAMPLE_BYTES = 12
ONE_GYR_ACC_MAG_SAMPLE_BYTES = 18

def convert(bin_pb_filename):
    filename = bin_pb_filename.rsplit(".", 1)[0]
    ext = bin_pb_filename.rsplit(".", 1)[1]

    csv_filename = filename + '_epoch.csv'

    if ext != 'bin_pb':
        print("File is not .bin_pb!")
        return False, False

    bin_filename = filename + '.bin'

    last_FIFO_timestamp = 0

    bin_pb_file = open(bin_pb_filename, "rb");

    csvfile = open(csv_filename, "w");

    has_hr = False

    FIFO_INTERVAL_MS = 1500

    with open(bin_filename, 'wb') as bin_file:

        csv_writer = csv.writer(csvfile, delimiter=',', lineterminator='\n')
        csv_writer.writerow(["epoch_time_ms", "acc_x_mg", "acc_y_mg", "acc_z_mg", "gyro_x_mdps", "gyro_y_mdps", "gyro_z_mdps", "mag_x_mgauss", "mag_y_mgauss", "mag_z_mgauss"])

        buf = bin_pb_file.read()
        pos = 0
        while pos < len(buf):
            msg_len, new_pos = decoder._DecodeVarint (buf, 0)
            n = new_pos
            msg_buf = buf[n:n+msg_len]
            buf = buf[n+msg_len:]
            input_msg = proto.SwimAnalysisMessage()
            input_msg.ParseFromString(msg_buf)
            if input_msg.message_type != proto.SwimAnalysisMessage.MessageType.SENSOR_DATA:
                continue
                # if input_msg.message_type == proto.SwimAnalysisMessage.MessageType.ACTIVITY_INFO:
                #     print("Swim activity type = {}".format(input_msg.activity_info.swim_type))
                #     print("Pool length = {}".format(input_msg.activity_info.pool_length))
                #     print("Orientation = {}".format(input_msg.activity_info.goggles_orientation))
                # else:
                #     print("input event = {}".format(input_msg.message_type))
            elif input_msg.sensor_data.type == proto.SensorData.Type.DIFF_ROLL_10_HZ or \
                input_msg.sensor_data.type == proto.SensorData.Type.VERT_ACC_10_HZ or \
                input_msg.sensor_data.type == proto.SensorData.Type.GYR_ACC_MAG_26HZ:
                return False, True, input_msg.sensor_data.type
            elif input_msg.sensor_data.type == proto.SensorData.Type.HR_LED_GREEN_IR or \
                input_msg.sensor_data.type == proto.SensorData.Type.HR_LED_GREEN or \
                input_msg.sensor_data.type == proto.SensorData.Type.HR_LED_GREEN_IR_CYCLE or \
                input_msg.sensor_data.type == proto.SensorData.Type.HR_LED_GREEN_IR_RED:
                has_hr = True
                continue
            elif input_msg.sensor_data.type == proto.SensorData.Type.BAROMETER_TEMPERATURE:
                has_hr = True
                continue
            else:
                row_str_list = []
                sample_size = 0
                if input_msg.sensor_data.type == proto.SensorData.Type.GYR_ACC_MAG:
                    FIFO_byte = input_msg.sensor_data.buffer
                    sample_size = FIFO_SAMPLE_SIZE
                elif input_msg.sensor_data.type == proto.SensorData.Type.GYR_ACC:
                    FIFO_byte = input_msg.sensor_data.buffer
                    sample_size = FIFO_SAMPLE_SIZE
                elif input_msg.sensor_data.type == proto.SensorData.Type.GYR_GYR_ACC_MAG_13_SAMPLES:
                    FIFO_byte = input_msg.sensor_data.buffer
                    sample_size = REAL_REAL_TIME_FIFO_SAMPLE_SIZE
                elif input_msg.sensor_data.type == proto.SensorData.Type.GYR_ACC_13_SAMPLES:
                    FIFO_byte = input_msg.sensor_data.buffer
                    sample_size = REAL_REAL_TIME_FIFO_SAMPLE_SIZE
                    
                if last_FIFO_timestamp != 0:
                    FIFO_INTERVAL_MS = input_msg.timestamp - last_FIFO_timestamp

                last_FIFO_timestamp = input_msg.timestamp

                for n in range(0, sample_size):
                    if input_msg.sensor_data.type == proto.SensorData.Type.GYR_ACC_MAG or \
                        input_msg.sensor_data.type == proto.SensorData.Type.GYR_GYR_ACC_MAG_13_SAMPLES:
                      byte = FIFO_byte[n * ONE_GYR_ACC_MAG_SAMPLE_BYTES : (n+1) * ONE_GYR_ACC_MAG_SAMPLE_BYTES]
                      row = struct.unpack("<hhhhhhhhh", byte)
                      mag_x = row[6]
                      mag_y = row[7]
                      mag_z = row[8]
                    elif input_msg.sensor_data.type == proto.SensorData.Type.GYR_ACC or \
                        input_msg.sensor_data.type == proto.SensorData.Type.GYR_ACC_13_SAMPLES:
                      byte = FIFO_byte[n * ONE_GYR_ACC_SAMPLE_BYTES : (n+1) * ONE_GYR_ACC_SAMPLE_BYTES]
                      row = struct.unpack("<hhhhhh", byte)
                      mag_x = 0
                      mag_y = 0
                      mag_z = 0

                    gyr_x = row[0]
                    gyr_y = row[1]
                    gyr_z = row[2]

                    acc_x = row[3]
                    acc_y = row[4]
                    acc_z = row[5]

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

                    timestamp = int(last_FIFO_timestamp - (((sample_size - 1) - n) * FIFO_INTERVAL_MS / sample_size))
                    row_str = [timestamp, acc_x, acc_y, acc_z, gyr_x, gyr_y, gyr_z, mag_x, mag_y, mag_z]
                    row_str_list.append(row_str)

                for row_str in row_str_list:
                    csv_writer.writerow(row_str)
            
        bin_pb_file.close()
        bin_file.close()
        csvfile.close()

    print("Finished converting .bin_pb to .bin ")
    print("{} -> {}\n".format(bin_pb_filename, bin_filename))

    if has_hr:
        return True, True, proto.SensorData.Type.HR_LED_GREEN_IR
    else:
        return True, False, input_msg.sensor_data.type

if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter)
    parser.add_argument("-f", "--file", help="Sensor file to decode from binary format", required=True)

    fbin_filename  = parser.parse_args().file
    convert(fbin_filename)
