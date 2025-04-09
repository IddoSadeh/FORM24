const int buttonPin = 12;  // GPIO pin for the button
int buttonState = HIGH;    // Default state (not pressed)
int lastButtonState = HIGH;
unsigned long lastDebounceTime = 0;
const unsigned long debounceDelay = 50; // Debounce time in milliseconds
int count = 0;

void setup() {
    pinMode(buttonPin, INPUT_PULLUP); // Enable internal pull-up resistor
    Serial.begin(115200);
}

void loop() {
    int reading = digitalRead(buttonPin); // Read the button state

    // If the button state has changed, reset the debounce timer
    if (reading != lastButtonState) {
        lastDebounceTime = millis();
    }

    // If the stable state persists beyond the debounce delay, register the press
    if ((millis() - lastDebounceTime) > debounceDelay) {
        if (reading == LOW && buttonState == HIGH) { // Button was released, now pressed
            Serial.println("Button Pressed!");
            count++;
            Serial.println(count);
        }
        buttonState = reading; // Update button state
    }

    lastButtonState = reading; // Save last reading for comparison
}
