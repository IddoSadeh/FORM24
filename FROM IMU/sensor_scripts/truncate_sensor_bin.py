import os
import subprocess
import argparse
from argparse import RawTextHelpFormatter

FIFO_SAMPLE_SIZE = 156
ONE_SAMPLE_BYTES = 24
FIFO_BYTES = ONE_SAMPLE_BYTES * FIFO_SAMPLE_SIZE

parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter)
parser.add_argument("-f", "--file", help="Original sensor.bin file", required=True)
parser.add_argument("-o", "--out", help="Truncated sensor.bin file", required=True)
parser.add_argument("-s", "--startwin", type=int, help="Start window", default="1", required=False)
parser.add_argument("-e", "--endwin", type=int, help="End window", default="0", required=False)

filename = parser.parse_args().file
out_filename = parser.parse_args().out
start_win = parser.parse_args().startwin
end_win = parser.parse_args().endwin

statinfo = os.stat(filename)
file_size = statinfo.st_size

total_win = int(file_size / FIFO_BYTES)
if end_win == 0:
    end_win = total_win

print("-------- Truncate Sensor.bin --------")
print("Input file {} contains {} FIFO windows".format(filename, total_win))

# Check inputs
if start_win <= 0:
  exit("ERROR: Start win must be >= 1!")
elif end_win > total_win:
  exit("ERROR: End win larger than total win!")
elif start_win >= end_win:
  exit("ERROR: Start win larger than end win!")

print("Truncating" , filename, "from FIFO window", start_win, "to", end_win)

count_win = int(end_win - start_win + 1)

cmd_str = "dd if={} of={} bs={} skip={} count={}".format(filename, out_filename, FIFO_BYTES, int(start_win-1), count_win)
# print(cmd_str)
subprocess.run(cmd_str, shell=True)

# Verify size
new_size = count_win * FIFO_BYTES

statinfo = os.stat(out_filename)
file_size = statinfo.st_size

if new_size == file_size:
  print("DONE. {} contains {} FIFO windows".format(out_filename, int(file_size/FIFO_BYTES)))
else:
  exit("ERROR: output file size not expected!")
