
## Files Overview

### Current Core Project Files

- **RST_Button.ino**: Arduino sketch to check if microcontroller resets when button connected to reset pin is pressed. Hope to see the setup() message upon pressed.
  
- **GPIO12_Button.ino**: Arduino sketch to read a button input with debounce handling to avoid false triggers from mechanical noise. Continuously monitors and updates button states using digitalRead() and timing logic.