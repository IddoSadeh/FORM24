import swim_analysis_message_pb2 as proto
from google.protobuf.internal import decoder
import struct
import argparse
from argparse import RawTextHelpFormatter
import sys
import re
import os
import csv

HR_SAMPLES_BYTES = (4 + 4)

def convert(bin_pb_filename):
    filename = bin_pb_filename.rsplit(".", 1)[0]
    ext = bin_pb_filename.rsplit(".", 1)[1]

    if ext != 'bin_pb':
        print("File is not .bin_pb!")
        return False, False

    csv_filename = filename + '_baro.csv'

    last_FIFO_timestamp = 0

    bin_pb_file = open(bin_pb_filename, "rb");

    with open(csv_filename, 'w') as csv_file:

        writer = csv.writer(csv_file, delimiter=',', lineterminator='\n')
        writer.writerow(["epoch_time_ms", "barometer", "temperature"])

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
            elif input_msg.sensor_data.type == proto.SensorData.Type.BAROMETER_TEMPERATURE:
                timestamp = input_msg.timestamp
                FIFO_byte = input_msg.sensor_data.buffer

                # print("sample_count = {}, {}".format(input_msg.timestamp, input_msg.sensor_data.sample_count))
                for n in range(0, input_msg.sensor_data.sample_count):
                # for n in range(0, 100):
                    byte = FIFO_byte[n * HR_SAMPLES_BYTES : (n+1) * HR_SAMPLES_BYTES]
                    row = struct.unpack("<ff", byte)

                    pressure = row[0]
                    temperature = row[1]

                    row_str = [int(round(timestamp)), pressure, temperature]
                    # print("{}".format(row_str))
                    writer.writerow(row_str)

        bin_pb_file.close()
        csv_file.close()

    print("Finished converting .bin_pb to .csv ")
    print("{} -> {}\n".format(bin_pb_filename, csv_filename))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter)
    parser.add_argument("-f", "--file", help="Sensor file to decode from binary format", required=True)

    fbin_filename  = parser.parse_args().file
    convert_HR(fbin_filename)
