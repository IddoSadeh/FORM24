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
ONE_GYR_ACC_SAMPLE_BYTES = 12
ONE_GYR_ACC_MAG_SAMPLE_BYTES = 36

def convert_26HZ(bin_pb_filename):
    filename = bin_pb_filename.rsplit(".", 1)[0]
    ext = bin_pb_filename.rsplit(".", 1)[1]

    if ext != 'bin_pb':
        print("File is not .bin_pb!")
        return False, False

    csv_filename = filename + '.csv'

    last_FIFO_timestamp = 0

    bin_pb_file = open(bin_pb_filename, "rb");

    with open(csv_filename, 'w') as csv_file:

        writer = csv.writer(csv_file, delimiter=',', lineterminator='\n')
        writer.writerow(["time_ms", "acc_x_mg", "acc_y_mg", "acc_z_mg", "gyro_x_mdps", "gyro_y_mdps", "gyro_z_mdps", "mag_x_mgauss", "mag_y_mgauss", "mag_z_mgauss"])

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
                if input_msg.message_type == proto.SwimAnalysisMessage.MessageType.ACTIVITY_INFO:
                    print("Swim activity type = {}".format(input_msg.activity_info.swim_type))
                    print("Pool length = {}".format(input_msg.activity_info.pool_length))
                    print("Orientation = {}".format(input_msg.activity_info.goggles_orientation))
                else:
                    print("input event = {}".format(input_msg.message_type))
            elif input_msg.sensor_data.type == proto.SensorData.Type.GYR_ACC_MAG_26HZ:

                timestamp = input_msg.timestamp
                FIFO_byte = input_msg.sensor_data.buffer

                for n in range(0, input_msg.sensor_data.sample_count):
                    if input_msg.sensor_data.type == proto.SensorData.Type.GYR_ACC_MAG_26HZ:
                        byte = FIFO_byte[n * ONE_GYR_ACC_MAG_SAMPLE_BYTES : (n+1) * ONE_GYR_ACC_MAG_SAMPLE_BYTES]
                        row = struct.unpack("<fffffffff", byte)

                        gyr_x = row[0]
                        gyr_y = row[1]
                        gyr_z = row[2]
                        acc_x = row[3]
                        acc_y = row[4]
                        acc_z = row[5]
                        mag_x = row[6]
                        mag_y = row[7]
                        mag_z = row[8]
                        # print("buf! {}".format(input_msg.sensor_data.sample_count))

                        row_str = [int(round(timestamp)), acc_x, acc_y, acc_z, gyr_x, gyr_y, gyr_z, mag_x, mag_y, mag_z]
                        writer.writerow(row_str)

        bin_pb_file.close()
        csv_file.close()

    print("Finished converting .bin_pb to .csv ")
    print("{} -> {}\n".format(bin_pb_filename, csv_filename))

def convert_SR(bin_pb_filename):
    filename = bin_pb_filename.rsplit(".", 1)[0]
    ext = bin_pb_filename.rsplit(".", 1)[1]

    if ext != 'bin_pb':
        print("File is not .bin_pb!")
        return False, False

    csv_filename = filename + '.csv'

    last_FIFO_timestamp = 0

    bin_pb_file = open(bin_pb_filename, "rb");

    with open(csv_filename, 'w') as csvfile:

        writer = csv.writer(csvfile, delimiter=',', lineterminator='\n')
        writer.writerow(["time_ms", "diff_roll", "vert_acc"])
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
                if input_msg.message_type == proto.SwimAnalysisMessage.MessageType.ACTIVITY_INFO:
                    print("Swim activity type = {}".format(input_msg.activity_info.swim_type))
                    print("Pool length = {}".format(input_msg.activity_info.pool_length))
                    print("Orientation = {}".format(input_msg.activity_info.goggles_orientation))
                else:
                    print("input event = {}".format(input_msg.message_type))
            elif input_msg.sensor_data.type == proto.SensorData.Type.DIFF_ROLL_10_HZ or \
                 input_msg.sensor_data.type == proto.SensorData.Type.VERT_ACC_10_HZ:
                timestamp = input_msg.timestamp
                FIFO_byte = input_msg.sensor_data.buffer
                # print("Count = {}".format(input_msg.sensor_data.sample_count))
                for n in range(0, input_msg.sensor_data.sample_count):
                    byte = FIFO_byte[n * 4 : (n+1) * 4]
                    sample_f = struct.unpack("<f", byte)[0]
                    if input_msg.sensor_data.type == proto.SensorData.Type.DIFF_ROLL_10_HZ:
                        row_str = [int(round(timestamp)), sample_f, 0]
                    else:
                        row_str = [int(round(timestamp)), 0, sample_f]
                    writer.writerow(row_str)
            
        bin_pb_file.close()
        csvfile.close()

    print("Finished converting .bin_pb with targeted data to .csv ")
    print("{} -> {}\n".format(bin_pb_filename, csv_filename))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter)
    parser.add_argument("-f", "--file", help="Sensor file to decode from binary format", required=True)

    fbin_filename  = parser.parse_args().file
    convert_SR(fbin_filename)
