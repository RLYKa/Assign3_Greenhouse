int ldrPins[] = {A0, A1, A2};
int ledPins[] = {6, 5, 4};
int ldrValues[3] = {0, 0, 0};
int thresholds[3] = {100, 100, 100};  // default threshold values
bool ledStates[3] = {LOW, LOW, LOW};

// LED control
unsigned long ledTurnOnTimes[3] = {0, 0, 0};
int ledDurations[3] = {0, 0, 0};

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
    if (command.substring(0, 1) == "T") {  // Change threshold
      int index = command.substring(1, 2).toInt();
      int newThreshold = command.substring(3).toInt();
      thresholds[index] = newThreshold;
    } else if (command.substring(0, 1) == "L") {  // Control LED
      int index = command.substring(1, 2).toInt();
      ledDurations[index] = command.substring(3).toInt();
      ledTurnOnTimes[index] = millis();
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
      if (ldrValues[i] > thresholds[i]) {
        digitalWrite(ledPins[i], LOW);
        ledStates[i] = LOW;
      } else {
        digitalWrite(ledPins[i], HIGH);
        ledStates[i] = HIGH;
      }
    }
  }

  Serial.println();
  
  // Wait for a second
  delay(1000);
}
