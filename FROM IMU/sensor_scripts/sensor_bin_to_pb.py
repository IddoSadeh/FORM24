import swim_analysis_message_pb2 as proto
from google.protobuf.internal import encoder
import struct
import argparse
from argparse import RawTextHelpFormatter
import sys
import re
import os

FIFO_SAMPLE_SIZE = 156
ONE_GYR_ACC_SAMPLE_BYTES = 12
ONE_GYR_ACC_MAG_SAMPLE_BYTES = 18
ONE_SAMPLE_BYTES = 24
FIFO_BYTES = ONE_SAMPLE_BYTES * FIFO_SAMPLE_SIZE

def convert(bin_filename, is_ows):
    filename = bin_filename.rsplit(".", 1)[0]
    ext = bin_filename.rsplit(".", 1)[1]

    if ext != 'bin':
        print("File is not .bin!")
        return False

    bin_pb_filename = filename + '.bin_pb'

    last_FIFO_timestamp = 0

    bin_file = open(bin_filename, "rb");

    with open(bin_pb_filename, 'wb') as bin_pb_file:

        swim_analysis_msg = proto.SwimAnalysisMessage()
        swim_analysis_msg.message_type = proto.SwimAnalysisMessage.MessageType.START_ACTIVITY
        swim_analysis_msg.timestamp = last_FIFO_timestamp
        encoded_buffer = swim_analysis_msg.SerializeToString()
        # print("len = {}".format(len(encoded_buffer)))

        if is_ows:
            last_FIFO_timestamp = last_FIFO_timestamp + 1000
            swim_analysis_msg = proto.SwimAnalysisMessage()
            swim_analysis_msg.message_type = proto.SwimAnalysisMessage.MessageType.START_OWS
            swim_analysis_msg.timestamp = last_FIFO_timestamp
            encoded_buffer = swim_analysis_msg.SerializeToString()
        
        bin_pb_file.write(encoder._VarintBytes(len(encoded_buffer)))
        bin_pb_file.write(encoded_buffer)

        buf = bin_file.read(FIFO_BYTES )
        pos = 0
        while len(buf) == FIFO_BYTES:
            fifo_buf = bytearray()
            for n in range(0, FIFO_SAMPLE_SIZE):
                byte = buf[n * ONE_SAMPLE_BYTES : (n+1) * ONE_SAMPLE_BYTES]
                row = struct.unpack("<hhhhhhhhhBBxBxx", byte)
                gyr_x = row[0]
                gyr_y = row[1]
                gyr_z = row[2]

                acc_x = row[3]
                acc_y = row[4]
                acc_z = row[5]

                mag_x = row[6]
                mag_y = row[7]
                mag_z = row[8]


                #  Format: Little endian: G_X G_Y G_Z A_X A_Y A_Z M_X M_Y M_Z,
                #        Followed by: Time midbyte, Time MSB, 0, Time LSB, 0, 0
                row_buf = struct.pack("<hhhhhhhhh",
                                  gyr_x,
                                  gyr_y,
                                  gyr_z,
                                  acc_x,
                                  acc_y,
                                  acc_z,
                                  mag_x,
                                  mag_y,
                                  mag_z)
                fifo_buf = fifo_buf + row_buf
            
            last_FIFO_timestamp = last_FIFO_timestamp + 1500
            swim_analysis_msg = proto.SwimAnalysisMessage()
            swim_analysis_msg.message_type =proto.SwimAnalysisMessage.MessageType.SENSOR_DATA 
            swim_analysis_msg.timestamp = last_FIFO_timestamp
            swim_analysis_msg.sensor_data.type = proto.SensorData.Type.GYR_ACC_MAG
            swim_analysis_msg.sensor_data.buffer = bytes(fifo_buf)
            encoded_buffer = swim_analysis_msg.SerializeToString()
            # print("len = {}".format(len(encoded_buffer)))
            bin_pb_file.write(encoder._VarintBytes(len(encoded_buffer)))
            bin_pb_file.write(encoded_buffer)

            buf = bin_file.read(FIFO_BYTES )

        # Save the last FIFO data
        last_FIFO_data = encoded_buffer 
        
        swim_analysis_msg = proto.SwimAnalysisMessage()
        if is_ows:
            swim_analysis_msg.message_type = proto.SwimAnalysisMessage.MessageType.STOP_OWS
        else:
            swim_analysis_msg.message_type = proto.SwimAnalysisMessage.MessageType.PAUSE
        swim_analysis_msg.timestamp = last_FIFO_timestamp
        encoded_buffer = swim_analysis_msg.SerializeToString()
        bin_pb_file.write(encoder._VarintBytes(len(encoded_buffer)))
        bin_pb_file.write(encoded_buffer)
        # print("len = {}".format(len(encoded_buffer)))

        # Write the last FIFO data
        bin_pb_file.write(encoder._VarintBytes(len(last_FIFO_data)))
        bin_pb_file.write(last_FIFO_data)
            
        bin_pb_file.close()
        bin_file.close()

    print("Finished converting .bin_pb to .bin ")
    print("{} -> {}\n".format(bin_filename, bin_pb_filename))

    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter)
    parser.add_argument("-f", "--file", help="Sensor file to decode from binary format")
    parser.add_argument("-a", "--all", help="All .bin file in directory", action="store_true")
    parser.add_argument("--ows", help="OWS file", action="store_true")

    if parser.parse_args().file is not None:
        fbin_filename  = parser.parse_args().file
        convert(fbin_filename, parser.parse_args().ows)
    
    elif parser.parse_args().all:
        print("Converting all .bin files in directory.")
        for root, dirs, files in os.walk("."):
            for file in files:
                if file.endswith('.bin'):
                    convert(file, parser.parse_args().ows)


