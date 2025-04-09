%% Set up data
column_headers = {'time_new', 'acc_x_mg', 'acc_y_mg', 'acc_z_mg', ...
                  'gyro_x_mdps', 'gyro_y_mdps', 'gyro_z_mdps', ...
                  'mag_x_mgauss', 'mag_y_mgauss', 'mag_z_mgaus'};

% Filter out the first and last 800 data points
filtered_data = flt_data;

% Replace the time column with equal increments spanning 104 seconds
num_samples = size(filtered_data, 1);
time = linspace(0, 104, num_samples)'; % Time vector from 0 to 104 seconds
filtered_data(:, 1) = time; % Replace the first column with the new time

% Plot each column against the new time
num_columns = size(filtered_data, 2);

%% Plot data against time
for i = 2:(num_columns-6) % Skip the first column since it's time
    figure;
    plot(time, filtered_data(:, i)); % Plot points only
    xlabel('Time (s)');
    ylabel(column_headers{i});
    title([column_headers{i}, ' vs Time']);
    grid on;
end

%% Kalman Filter for Position Estimation
% Extract accelerometer and gyroscope data
acc_data = filtered_data(:, 2:4); % Columns: acc_x_mg, acc_y_mg, acc_z_mg
gyro_data = filtered_data(:, 5:7); % Columns: gyro_x_mdps, gyro_y_mdps, gyro_z_mdps

% Calculate refined dt using the new time
dt = time(2) - time(1); % Calculate sampling interval
num_samples = size(filtered_data, 1);

% Initialize state (position, velocity, orientation) and covariance
state = [0; 0; 0; 0; 0; 0]; % [x, y, z, vx, vy, vz]
P = eye(6); % Initial covariance matrix

% Define process noise and measurement noise
Q = 0.01 * eye(6); % Process noise covariance
R = 0.1 * eye(3); % Measurement noise covariance

% Kalman Filter matrices
A = [eye(3), dt * eye(3); zeros(3, 3), eye(3)]; % State transition matrix
B = [0.5 * dt^2 * eye(3); dt * eye(3)]; % Control input matrix
C = [eye(3), zeros(3, 3)]; % Measurement matrix

% Initialize arrays to store results
positions = zeros(num_samples, 3);

% Kalman Filter loop
for i = 1:num_samples
    % Measurement: Use accelerometer data (converted to m/s^2 from mg)
    z = acc_data(i, :)' * 9.81 / 1000; 
    
    % Predict step
    state = A * state;
    P = A * P * A' + Q;
    
    % Update step
    K = P * C' / (C * P * C' + R); % Kalman gain
    state = state + K * (z - C * state); % Update state
    P = (eye(6) - K * C) * P; % Update covariance

    % Store position for visualization
    positions(i, :) = state(1:3)';
end

% Plot 3D trajectory
figure;
plot3(positions(:, 1), positions(:, 2), positions(:, 3));
xlabel('X Position (m)');
ylabel('Y Position (m)');
zlabel('Z Position (m)');
title('3D Trajectory of IMU');
grid on;

% Plot positions over new time
figure;
subplot(3, 1, 1);
plot(time, positions(:, 1)); % Plot data against time
xlabel('Time (s)');
ylabel('X Position (m)');
title('X Position over Time');
grid on;

subplot(3, 1, 2);
plot(time, positions(:, 2)); % Plot data against time
xlabel('Time (s)');
ylabel('Y Position (m)');
title('Y Position over Time');
grid on;

subplot(3, 1, 3);
plot(time, positions(:, 3)); % Plot data against time
xlabel('Time (s)');
ylabel('Z Position (m)');
title('Z Position over Time');
grid on;
