int ldrPins[] = {A0, A1, A2};
int ledPins[] = {6, 5, 4};
int ldrValues[3] = {0, 0, 0};
int thresholds[3] = {120, 180, 140};  // default threshold values
bool ledStates[3] = {LOW, LOW, LOW};

// LED control
unsigned long ledTurnOnTimes[3] = {0, 0, 0};
int ledDurations[3] = {0, 0, 0};
bool forceOff[3] = {false, false, false};  // new variable to track whether each LED should be forced off

void setup() {
  Serial.begin(9600);
  for (int i = 0; i < 3; i++) {
    pinMode(ledPins[i], OUTPUT);
  }
}

void loop() {
  // Read command from Raspberry Pi
  while (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    if (command.startsWith("setThreshold")) {  // Change threshold
        int index = command.substring(13, 14).toInt();
        int newThreshold = command.substring(15).toInt();
        thresholds[index] = newThreshold;
    } else if (command.startsWith("led_on")) {  // Turn on LED
        int index = command.substring(7, 8).toInt();
        int duration = command.substring(9).toInt();
        digitalWrite(ledPins[index], HIGH);
        ledStates[index] = HIGH;
        ledTurnOnTimes[index] = millis();
        ledDurations[index] = duration;
        forceOff[index] = false;  // reset the force off flag when turning on the LED
    } else if (command.startsWith("led_off")) {  // Turn off LED
        int index = command.substring(8, 9).toInt();
        digitalWrite(ledPins[index], LOW);
        ledStates[index] = LOW;
        forceOff[index] = true;  // set the force off flag when turning off the LED
    } else if (command == "getStatus") {
      for (int i = 0; i < 3; i++) {
        Serial.print(ledStates[i]);
        Serial.print(",");
        Serial.print(thresholds[i]);
        if (i < 2) Serial.print(",");
      }
      Serial.println();
    }
  }
  
  // Control LEDs based on LDR values and LED control commands
  for (int i = 0; i < 3; i++) {
    ldrValues[i] = analogRead(ldrPins[i]);
    Serial.print(ldrValues[i]);
    Serial.print(",");
    
    // Check if LED control command is active
    if (millis() - ledTurnOnTimes[i] <= ledDurations[i]*1000) {
      digitalWrite(ledPins[i], HIGH);
      ledStates[i] = HIGH;
    } else {
      if (ldrValues[i] > thresholds[i] && !forceOff[i]) {
        digitalWrite(ledPins[i], LOW);
        ledStates[i] = LOW;
      } else if (!forceOff[i]) {
        digitalWrite(ledPins[i], HIGH);
        ledStates[i] = HIGH;
      }
    }
  }

  Serial.println();
  
  // Wait for a second
  delay(1000);
}