clear;
clc;
close all;

% data path
input_data_path = '../data/';

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%% PRE PROCESSING STEPS %%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% sensor file
sensor_bin_filename = '2024-11-25-1732560701581.bin_pb';

% sensor path
full_sensor_bin_path = [input_data_path sensor_bin_filename];

%%% running .bin extraction
command = ['cd ../sensor_scripts && python decode_sensor_bin.py -f "' full_sensor_bin_path '"'];
status = system(command);

%% STEP 1: directly reading in data
%% changed reading csv method to support matlab
data = readmatrix([full_sensor_bin_path(1:end-7), '.csv']);
data = data(2:end,:);

%% STEP 2: remove sensortile rotations, convert to relevant units and low pass filter data
flt_data = read_data(data);



