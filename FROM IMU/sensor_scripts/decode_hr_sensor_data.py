import swim_analysis_message_pb2 as proto
from google.protobuf.internal import decoder
import struct
import argparse
from argparse import RawTextHelpFormatter
import sys
import re
import os
import csv

HR_SAMPLES_BYTES = (4)
HR2_SAMPLES_BYTES = (4 + 4)
HR3_SAMPLES_BYTES = (4 + 4 + 4)

def convert_HR3(bin_pb_filename):
    filename = bin_pb_filename.rsplit(".", 1)[0]
    ext = bin_pb_filename.rsplit(".", 1)[1]

    if ext != 'bin_pb':
        print("File is not .bin_pb!")
        return False, False

    csv_filename = filename + '_hr.csv'

    last_FIFO_timestamp = 0

    bin_pb_file = open(bin_pb_filename, "rb");

    with open(csv_filename, 'w') as csv_file:

        writer = csv.writer(csv_file, delimiter=',', lineterminator='\n')
        writer.writerow(["epoch_time_ms", "GREEN_LED", "IR_LED", "RED_LED"])

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
                # if input_msg.message_type == proto.SwimAnalysisMessage.MessageType.ACTIVITY_INFO:
                #     print("Swim activity type = {}".format(input_msg.activity_info.swim_type))
                #     print("Pool length = {}".format(input_msg.activity_info.pool_length))
                #     print("Orientation = {}".format(input_msg.activity_info.goggles_orientation))
                # elif input_msg.message_type == proto.SwimAnalysisMessage.MessageType.HR_INFO:
                if input_msg.message_type == proto.SwimAnalysisMessage.MessageType.HR_INFO:
                    print("HR sampling freq = {}".format(input_msg.hr_led_info.sampling_rate))
                    print("LED current Green, IR, Red = {}, {}, {}".format(input_msg.hr_led_info.led_current_green,
                        input_msg.hr_led_info.led_current_ir, input_msg.hr_led_info.led_current_red))
                    if input_msg.hr_led_info.led_current_green == 7:
                        row_str = [0, 0, 0]
                        writer.writerow(row_str)
                    elif input_msg.hr_led_info.led_current_green == 15:
                        row_str = [0, 1, 1]
                        writer.writerow(row_str)
                    elif input_msg.hr_led_info.led_current_green == 30:
                        row_str = [0, 2, 2]
                        writer.writerow(row_str)
                    elif input_msg.hr_led_info.led_current_green == 40:
                        row_str = [0, 3, 3]
                        writer.writerow(row_str)
                    elif input_msg.hr_led_info.led_current_green == 50:
                        row_str = [0, 4, 4]
                        writer.writerow(row_str)
                    elif input_msg.hr_led_info.led_current_green == 60:
                        row_str = [0, 5, 5]
                        writer.writerow(row_str)
                # else:
                #     print("input event = {}".format(input_msg.message_type))
            elif input_msg.sensor_data.type == proto.SensorData.Type.HR_LED_GREEN_IR_RED:

                timestamp = input_msg.timestamp
                FIFO_byte = input_msg.sensor_data.buffer

                # print("sample_count = {}, {}".format(input_msg.timestamp, input_msg.sensor_data.sample_count))
                for n in range(0, input_msg.sensor_data.sample_count):
                    byte = FIFO_byte[n * HR3_SAMPLES_BYTES : (n+1) * HR3_SAMPLES_BYTES]
                    row = struct.unpack("<III", byte)

                    green_led = row[0]
                    ir_led = row[1]
                    red_led = row[2]

                    row_str = [int(round(timestamp)), green_led, ir_led, red_led]
                    writer.writerow(row_str)

        bin_pb_file.close()
        csv_file.close()

    print("Finished converting .bin_pb to .csv ")
    print("{} -> {}\n".format(bin_pb_filename, csv_filename))

def convert_HR2(bin_pb_filename):
    filename = bin_pb_filename.rsplit(".", 1)[0]
    ext = bin_pb_filename.rsplit(".", 1)[1]

    if ext != 'bin_pb':
        print("File is not .bin_pb!")
        return False, False

    csv_filename = filename + '_hr.csv'

    last_FIFO_timestamp = 0

    bin_pb_file = open(bin_pb_filename, "rb");

    with open(csv_filename, 'w') as csv_file:

        writer = csv.writer(csv_file, delimiter=',', lineterminator='\n')
        writer.writerow(["epoch_time_ms", "GREEN_LED", "IR_LED"])

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
                # if input_msg.message_type == proto.SwimAnalysisMessage.MessageType.ACTIVITY_INFO:
                #     print("Swim activity type = {}".format(input_msg.activity_info.swim_type))
                #     print("Pool length = {}".format(input_msg.activity_info.pool_length))
                #     print("Orientation = {}".format(input_msg.activity_info.goggles_orientation))
                # elif input_msg.message_type == proto.SwimAnalysisMessage.MessageType.HR_INFO:
                if input_msg.message_type == proto.SwimAnalysisMessage.MessageType.HR_INFO:
                    print("HR sampling freq = {}".format(input_msg.hr_led_info.sampling_rate))
                    print("LED current Green, IR, Red = {}, {}, {}".format(input_msg.hr_led_info.led_current_green,
                        input_msg.hr_led_info.led_current_ir, input_msg.hr_led_info.led_current_red))
                    if input_msg.hr_led_info.led_current_green == 7:
                        row_str = [0, 0, 0]
                        writer.writerow(row_str)
                    elif input_msg.hr_led_info.led_current_green == 15:
                        row_str = [0, 1, 1]
                        writer.writerow(row_str)
                    elif input_msg.hr_led_info.led_current_green == 30:
                        row_str = [0, 2, 2]
                        writer.writerow(row_str)
                    elif input_msg.hr_led_info.led_current_green == 40:
                        row_str = [0, 3, 3]
                        writer.writerow(row_str)
                    elif input_msg.hr_led_info.led_current_green == 50:
                        row_str = [0, 4, 4]
                        writer.writerow(row_str)
                    elif input_msg.hr_led_info.led_current_green == 60:
                        row_str = [0, 5, 5]
                        writer.writerow(row_str)
                # else:
                #     print("input event = {}".format(input_msg.message_type))
            elif input_msg.sensor_data.type == proto.SensorData.Type.HR_LED_GREEN_IR:

                timestamp = input_msg.timestamp
                FIFO_byte = input_msg.sensor_data.buffer

                # print("sample_count = {}, {}".format(input_msg.timestamp, input_msg.sensor_data.sample_count))
                for n in range(0, input_msg.sensor_data.sample_count):
                    byte = FIFO_byte[n * HR2_SAMPLES_BYTES : (n+1) * HR2_SAMPLES_BYTES]
                    row = struct.unpack("<II", byte)

                    green_led = row[0]
                    ir_led = row[1]

                    row_str = [int(round(timestamp)), green_led, ir_led]
                    writer.writerow(row_str)

        bin_pb_file.close()
        csv_file.close()

    print("Finished converting .bin_pb to .csv ")
    print("{} -> {}\n".format(bin_pb_filename, csv_filename))

def convert_HR(bin_pb_filename):
    filename = bin_pb_filename.rsplit(".", 1)[0]
    ext = bin_pb_filename.rsplit(".", 1)[1]

    if ext != 'bin_pb':
        print("File is not .bin_pb!")
        return False, False

    csv_filename = filename + '_hr.csv'

    last_FIFO_timestamp = 0

    bin_pb_file = open(bin_pb_filename, "rb");

    with open(csv_filename, 'w') as csv_file:

        writer = csv.writer(csv_file, delimiter=',', lineterminator='\n')
        writer.writerow(["epoch_time_ms", "GREEN_LED"])

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
                # if input_msg.message_type == proto.SwimAnalysisMessage.MessageType.ACTIVITY_INFO:
                #     print("Swim activity type = {}".format(input_msg.activity_info.swim_type))
                #     print("Pool length = {}".format(input_msg.activity_info.pool_length))
                #     print("Orientation = {}".format(input_msg.activity_info.goggles_orientation))
                # elif input_msg.message_type == proto.SwimAnalysisMessage.MessageType.HR_INFO:
                if input_msg.message_type == proto.SwimAnalysisMessage.MessageType.HR_INFO:
                    print("HR sampling freq = {}".format(input_msg.hr_led_info.sampling_rate))
                    print("LED current Green, IR, Red = {}, {}, {}".format(input_msg.hr_led_info.led_current_green,
                        input_msg.hr_led_info.led_current_ir, input_msg.hr_led_info.led_current_red))
                    if input_msg.hr_led_info.led_current_green == 7:
                        row_str = [0, 0, 0]
                        writer.writerow(row_str)
                    elif input_msg.hr_led_info.led_current_green == 15:
                        row_str = [0, 1, 1]
                        writer.writerow(row_str)
                    elif input_msg.hr_led_info.led_current_green == 30:
                        row_str = [0, 2, 2]
                        writer.writerow(row_str)
                    elif input_msg.hr_led_info.led_current_green == 40:
                        row_str = [0, 3, 3]
                        writer.writerow(row_str)
                    elif input_msg.hr_led_info.led_current_green == 50:
                        row_str = [0, 4, 4]
                        writer.writerow(row_str)
                    elif input_msg.hr_led_info.led_current_green == 60:
                        row_str = [0, 5, 5]
                        writer.writerow(row_str)
                # else:
                #     print("input event = {}".format(input_msg.message_type))
            elif input_msg.sensor_data.type == proto.SensorData.Type.HR_LED_GREEN:

                timestamp = input_msg.timestamp
                FIFO_byte = input_msg.sensor_data.buffer

                # print("sample_count = {}, {}".format(input_msg.timestamp, input_msg.sensor_data.sample_count))
                for n in range(0, input_msg.sensor_data.sample_count):
                    byte = FIFO_byte[n * HR_SAMPLES_BYTES : (n+1) * HR_SAMPLES_BYTES]
                    row = struct.unpack("<I", byte)

                    green_led = row[0]

                    row_str = [int(round(timestamp)), green_led]
                    writer.writerow(row_str)

        bin_pb_file.close()
        csv_file.close()

    print("Finished converting .bin_pb to .csv ")
    print("{} -> {}\n".format(bin_pb_filename, csv_filename))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter)
    parser.add_argument("-f", "--file", help="Sensor file to decode from binary format", required=True)

    fbin_filename  = parser.parse_args().file
    convert_HR2(fbin_filename)
