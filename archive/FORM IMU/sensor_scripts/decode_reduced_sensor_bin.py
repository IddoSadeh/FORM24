import struct
import argparse
from argparse import RawTextHelpFormatter
import csv
import sys
import re
from datetime import datetime 

SIGNATURE = ['f', 's', 'a', 'b'] 
FIFO_SAMPLE_SIZE = 39
ONE_SAMPLE_BYTES = 18
FIFO_BYTES = ONE_SAMPLE_BYTES * FIFO_SAMPLE_SIZE + 8
FIFO_INTERVAL_MS = 1500

HEADER_BYTES = 4 + 2 + 8 + 2 + 4
TIMESTAMP_IDX = 0

parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter)
parser.add_argument("-f", "--file", help="ML sensor file to decode from binary format", required=True)
parser.add_argument("--tsv", help="Output tsv instead of csv (default)", action='store_true')

use_tsv = parser.parse_args().tsv

fin = open(parser.parse_args().file, "rb")

filename = parser.parse_args().file.rsplit(".", 1)[0]
if use_tsv:
    csv_filename = filename + '.tsv'
else:
    csv_filename = filename + '.csv'

timestamp = 0
first_timestamp = -1

row_read = 0
last_FIFO_timestamp = 0
with open(csv_filename, 'w') as csvfile:
    if use_tsv:
        writer = csv.writer(csvfile, delimiter='\t', lineterminator='\n')
    else:
        writer = csv.writer(csvfile, delimiter=',', lineterminator='\n')
    writer.writerow(["time_ms", "acc_x_mps2", "acc_y_mps2", "acc_z_mps2", "gyro_x_rps", "gyro_y_rps", "gyro_z_rps", "mag_x_ut", "mag_y_ut", "mag_z_ut"])

    try:
        # Read header
        header_byte = bytearray(fin.read(HEADER_BYTES))
        header = struct.unpack("<4cHQH4c", header_byte)
        if header[0] != 'F' or header[1] != 'S' or header[2] != 'A' or header[3] != 'B':
            sys.exit("File signature does not matches! Aborting program.")
        
        print("-- Form Swim Analysis Binary v{} --".format(header[4]))
        print("Start time = {}".format(header[5]))
        print("Pool length = {}\n".format(header[6]))

        FIFO_byte = fin.read(FIFO_BYTES)

        while len(FIFO_byte) == FIFO_BYTES:
            FIFO_byte = bytearray(FIFO_byte)
            # print("FIFO_byte size = " + str(len(FIFO_byte)))
            row_read = row_read + FIFO_SAMPLE_SIZE

            row_str_list = []

            byte = FIFO_byte[0 : 8]

            timestamp = struct.unpack("<Q", byte)
            # print("time = {}".format(timestamp))
            if first_timestamp == -1:
                first_timestamp = timestamp[0]

            byte = FIFO_byte[8: 8 + 39 * 6]
            acc = struct.unpack("<39h39h39h", byte)
            byte = FIFO_byte[8 + 39 * 6: 8 + (39 * 6) * 2]
            gyro = struct.unpack("<39h39h39h", byte)
            byte = FIFO_byte[8 + (39 * 6) * 2: 8 + (39 * 6) * 3]
            mag = struct.unpack("<39h39h39h", byte)

            for n in range(0, FIFO_SAMPLE_SIZE):

                gyro_f = [0, 0 ,0] 
                gyro_f[0] = float(gyro[n]) / 100
                gyro_f[1] = float(gyro[39 + n]) / 100
                gyro_f[2] = float(gyro[39 * 2 + n]) / 100

                acc_f = [0, 0 ,0] 
                acc_f[0] = float(acc[n]) / 100 
                acc_f[1] = float(acc[39 + n]) / 100 
                acc_f[2] = float(acc[39 * 2 + n]) / 100 

                mag_f = [0, 0 ,0] 
                mag_f[0] = float(mag[n]) / 100 
                mag_f[1] = float(mag[39 + n]) / 100 
                mag_f[2] = float(mag[39 * 2 + n]) / 100 

                sample_timestamp = FIFO_INTERVAL_MS + timestamp[0] - first_timestamp - FIFO_INTERVAL_MS * (39 - n) / 39

                # print("{}, {}, {}, {}, {}, {}".format(acc_f[0], acc_f[1], acc_f[2], gyro_f[0], gyro_f[1], gyro_f[2]))
                writer.writerow([sample_timestamp, acc_f[0], acc_f[1], acc_f[2], gyro_f[0], gyro_f[1], gyro_f[2], mag_f[0], mag_f[1], mag_f[2]])

            FIFO_byte = fin.read(FIFO_BYTES)
    finally:
        fin.close()

print("Finished decoding {} samples ({}s).".format(row_read, sample_timestamp/1000))
print("{} -> {}\n".format(parser.parse_args().file, csv_filename))
