
function flt_data = read_data(data)

  %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
  % TDL File
  %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
  raw_data = data;
  raw_data(:,1) = raw_data(:,1)*0.001; %account for milli sec

   if raw_data(2,1) > 100 % Epoch time will be greater than 100
      window_epoch_time = unique(raw_data(:,1));
      relative_time = [];
      window_start_time = 0;
      for i = 1:size(window_epoch_time,1)
        num_samples_in_window = length(find(raw_data(:,1) == window_epoch_time(i)));
        if (i == 1)
          window_duration = 1.5;
        else
          window_duration = (window_epoch_time(i) - window_epoch_time(i-1));
        end
        relative_time = [relative_time;
                         linspace(window_start_time,window_duration+window_start_time,num_samples_in_window)'];
        window_start_time = window_start_time + window_duration;
      end
      raw_data(:,1) = relative_time;
    end
    time_stamp_all = raw_data(:,1);
    fprintf(['Finished processing SensorData' '\n']);

    flt_data = raw_data; % LPF done on the device already

end
