void setup() {
  Serial.begin(9600);  // Start Serial communication
  Serial.println("Time (ms),Sensor Value,Voltage");  // CSV header
}

void loop() {
  unsigned long time = millis();  // Time in milliseconds
  int sensorValue = analogRead(A0);  // Read sensor value from A0
  double voltage = sensorValue * (5.0 / 1023.0);  // Convert to voltage
  double normalizedVoltage = 5 - voltage; //flips graph across time axis

  // Output data in CSV format
  Serial.print(time);
  Serial.print(",");
  Serial.print(sensorValue);
  Serial.print(",");
  Serial.println(normalizedVoltage);

  delay(1000);  // Log data every second
}