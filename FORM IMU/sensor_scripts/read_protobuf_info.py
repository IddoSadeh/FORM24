import argparse
import csv
from google.protobuf.internal import decoder
import swim_analysis_message_pb2 as proto

parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument("-f", "--file", help="Sensor file to decode from binary format", required=True)
parser.add_argument("-i", "--inpath", help="Input file data path", required=True)
parser.add_argument("-o", "--outpath", help="Output file data path", required=True)

sensor_bin_filename = parser.parse_args().file
input_data_path = parser.parse_args().inpath
output_data_path = parser.parse_args().outpath
ext = sensor_bin_filename.rsplit(".", 1)[1]
no_ext = sensor_bin_filename.rsplit(".", 1)[0]
csvfile = open(output_data_path + no_ext + "_protobuf_info.csv", "w");


def getSensorBinPBInfo(filename):
    sensor_types = {''}
    with open(input_data_path + filename, "rb") as bin_pb_file:
            buf = bin_pb_file.read()
            pos = 0
            # print("Sensor file = {}".format(len(buf)))
            csv_writer = csv.writer(csvfile, delimiter=',', lineterminator='\n')
            csv_writer.writerow(["epoch_time_ms", "protobuf_event"])
            row_str_list = []
            while len(buf) > 0:
                msg_len, new_pos = decoder._DecodeVarint (buf, 0)
                n = new_pos
                msg_buf = buf[n:n+msg_len]
                buf = buf[n+msg_len:]
                input_msg = proto.SwimAnalysisMessage()
                input_msg.ParseFromString(msg_buf)

                if input_msg.message_type != proto.SwimAnalysisMessage.MessageType.SENSOR_DATA:
                    if input_msg.message_type == proto.SwimAnalysisMessage.MessageType.ACTIVITY_INFO:
                        # print("Pool length = {}".format(input_msg.activity_info.pool_length))
                        # print("Orientation = {}".format(input_msg.activity_info.goggles_orientation))
                        # print("Swim activity type = {}".format(input_msg.activity_info.swim_type))
                        # print("Board Type = {}".format(input_msg.activity_info.board_type))
                        row_str = [input_msg.timestamp, input_msg.activity_info.pool_length]
                        row_str_list.append(row_str)
                        row_str = [input_msg.timestamp, input_msg.activity_info.goggles_orientation]
                        row_str_list.append(row_str)
                        row_str = [input_msg.timestamp, input_msg.activity_info.swim_type]
                        row_str_list.append(row_str)
                        row_str = [input_msg.timestamp, input_msg.activity_info.board_type]
                        row_str_list.append(row_str)
                    else:
                        print("input event = {}".format(str(input_msg.message_type) + ', timestamp = ' + str(input_msg.timestamp)))
                        row_str = [input_msg.timestamp, input_msg.message_type]
                        row_str_list.append(row_str)
                elif input_msg.sensor_data.type == proto.SensorData.Type.GYR_ACC_MAG or \
                    input_msg.sensor_data.type == proto.SensorData.Type.GYR_ACC:
                    sensor_types.add("RAW_SENSOR")
                elif input_msg.sensor_data.type == proto.SensorData.Type.DIFF_ROLL_10_HZ or \
                    input_msg.sensor_data.type == proto.SensorData.Type.VERT_ACC_10_HZ:
                    sensor_types.add("TARGETED_SR")
                elif input_msg.sensor_data.type == proto.SensorData.Type.GYR_ACC_MAG_26HZ:
                    sensor_types.add("TDL")
                elif input_msg.sensor_data.type == proto.SensorData.Type.HR_LED_GREEN_IR or \
                    input_msg.sensor_data.type == proto.SensorData.Type.HR_LED_GREEN_IR_CYCLE:
                    sensor_types.add("HR")
                elif input_msg.sensor_data.type == proto.SensorData.Type.HR_LED_GREEN_IR_RED:
                    sensor_types.add("HR3")
                elif input_msg.sensor_data.type == proto.SensorData.Type.BAROMETER_TEMPERATURE:
                    sensor_types.add("BARO")
            row_str = [input_msg.timestamp, sensor_types]
            row_str_list.append(row_str)
            for row_str in row_str_list:
                    csv_writer.writerow(row_str)

    print(sensor_types)
    return sensor_types

getSensorBinPBInfo(sensor_bin_filename)