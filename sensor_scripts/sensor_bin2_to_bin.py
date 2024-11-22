import struct
import argparse
from argparse import RawTextHelpFormatter
import sys
import re

FIFO_SAMPLE_SIZE = 156
ONE_SAMPLE_BYTES = 12
FIFO_BYTES = ONE_SAMPLE_BYTES * FIFO_SAMPLE_SIZE
FIFO_INTERVAL_MS = 1500


def convert(bin2_filename):
    filename = bin2_filename.rsplit(".", 1)[0]
    ext = bin2_filename.rsplit(".", 1)[1]

    if ext != 'bin2':
        print("File is not .bin2!")
        return False

    bin_filename = filename + '.bin'

    last_FIFO_timestamp = 0

    bin2_file = open(bin2_filename, "rb");

    with open(bin_filename, 'wb') as bin_file:
        #  Format: Little endian: G_X G_Y G_Z A_X A_Y A_Z ,
        # So, 12 bytes per sample

        try:
            # Read 1 FIFO window at a time, 12 bytes * 156
            FIFO_byte = bin2_file.read(FIFO_BYTES)

            last_tick_time = -1 
            while len(FIFO_byte) == FIFO_BYTES:
                FIFO_byte = bytearray(FIFO_byte)

                for n in range(0, FIFO_SAMPLE_SIZE):
                    byte = FIFO_byte[n * ONE_SAMPLE_BYTES : (n+1) * ONE_SAMPLE_BYTES]

                    row = struct.unpack("<hhhhhh", byte)

                    gyr_x = row[0]
                    gyr_y = row[1]
                    gyr_z = row[2]

                    acc_x = row[3]
                    acc_y = row[4]
                    acc_z = row[5]

                    #  Format: Little endian: G_X G_Y G_Z A_X A_Y A_Z M_X M_Y M_Z,
                    #        Followed by: Time midbyte, Time MSB, 0, Time LSB, 0, 0
                    bin_file.write(struct.pack("<hhhhhhxxxxxxxxxxxx",
                                                gyr_x,
                                                gyr_y,
                                                gyr_z,
                                                acc_x,
                                                acc_y,
                                                acc_z))

                FIFO_byte = bin2_file.read(FIFO_BYTES)
        except:
            return False
        finally:
            bin2_file.close()
            bin_file.close()

    print("Finished converting .bin2 to .bin ")
    print("{} -> {}\n".format(bin2_filename, bin_filename))

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter)
    parser.add_argument("-f", "--file", help="Sensor file to decode from binary format", required=True)

    bin2_filename  = parser.parse_args().file
    convert(bin2_filename)
