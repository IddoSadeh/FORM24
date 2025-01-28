import argparse;
import datetime;

parser = argparse.ArgumentParser();
parser.add_argument("-f", "--file", help="Sensor tsv to repair timestamps", required=True);

input_file_name = parser.parse_args().file;
tsv_index = input_file_name.find(".tsv");
if tsv_index == -1:
    print("This is not a tsv file!  Give me a tsv file!");
    exit(1);
output_file_name = input_file_name[:tsv_index] + "_Fixed-Timestamps" + input_file_name[tsv_index:];
with open(input_file_name, "r") as input_file, open(output_file_name, "w") as output_file:
    prev_line = "";
    prev_datetime = datetime.datetime(2000, 1, 1);
    line_list = input_file.readlines();
    for line in line_list:

        # Parse line to determine timestamp information, skip if headers or first line
        parse_str = line.split();
        if (parse_str[0] == "Timestamp"):
            output_file.write(line);
            continue;

        datestamp = parse_str[0];
        timestamp = parse_str[1];
        line_datetime = datetime.datetime.strptime(datestamp+" "+timestamp, "%y-%m-%d %H:%M:%S.%f");

        if (prev_line == ""):
            prev_line = line;
            prev_datetime = line_datetime;
            continue;

        # Compare last line to current line.  If Previous line is behind by more than a second, repair it and write, otherwise just write.
        if (line_datetime - prev_datetime > datetime.timedelta(0, 1)):
            repaired_datetime = prev_datetime + datetime.timedelta(0, 1);
            prev_parse_str = prev_line.split();
            prev_parse_str[0] = repaired_datetime.strftime("%y-%m-%d");
            prev_parse_str[1] = repaired_datetime.strftime("%H:%M:%S.%f");
            output_file.write(" ".join(prev_parse_str[0:2]) + "\t" + "\t".join(prev_parse_str[2:]) + "\t\r\n");
        else:
            output_file.write(prev_line);

        prev_line = line;
        prev_datetime = line_datetime;

    # Handle last line
    second_last_line = line_list[-2];
    last_line = line_list[-1];

    second_last_line_datestamp = second_last_line.split()[0];
    second_last_line_timestamp = second_last_line.split()[1];
    second_last_line_datetime = datetime.datetime.strptime(second_last_line_datestamp+" "+second_last_line_timestamp, "%y-%m-%d %H:%M:%S.%f");

    last_line_split = last_line.split();
    last_line_datestamp = last_line_split[0];
    last_line_timestamp = last_line_split[1];
    last_line_datetime = datetime.datetime.strptime(last_line_datestamp+" "+last_line_timestamp, "%y-%m-%d %H:%M:%S.%f");

    if (last_line_datetime < second_last_line_datetime):
        repaired_datetime = last_line_datetime + datetime.timedelta(0, 1);
        repaired_date = repaired_datetime.strftime("%y-%m-%d");
        repaired_time = repaired_datetime.strftime("%H:%M:%S.%f");
        output_file.write(repaired_date + " " + repaired_time + "\t" + "\t".join(last_line_split[2:]) + "\t\r\n");
    else:
        output_file.write(last_line);
