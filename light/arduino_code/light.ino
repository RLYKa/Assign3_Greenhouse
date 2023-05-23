int ldr1Pin = A0;
int ldr2Pin = A1;
int ldr3Pin = A2;

int led1Pin = 6;
int led2Pin = 5;
int led3Pin = 4;

int ldr1Threshold = 100;
int ldr2Threshold = 100;
int ldr3Threshold = 100;

bool led1ForcedOn = false;
bool led2ForcedOn = false;
bool led3ForcedOn = false;
unsigned long led1ForcedOnStartTime = 0;
unsigned long led2ForcedOnStartTime = 0;
unsigned long led3ForcedOnStartTime = 0;
unsigned long forcedOnDuration = 5000; // Default duration of 5 seconds

void setup() {
  Serial.begin(9600);

  pinMode(ldr1Pin, INPUT);
  pinMode(ldr2Pin, INPUT);
  pinMode(ldr3Pin, INPUT);
  pinMode(led1Pin, OUTPUT);
  pinMode(led2Pin, OUTPUT);
  pinMode(led3Pin, OUTPUT);
}

void loop() {
  int ldr1Val = analogRead(ldr1Pin);
  int ldr2Val = analogRead(ldr2Pin);
  int ldr3Val = analogRead(ldr3Pin);

  // Check if LDR values are below the respective thresholds
  if (ldr1Val < ldr1Threshold || led1ForcedOn) {
    digitalWrite(led1Pin, HIGH); // Turn on LED1
    if (led1ForcedOn && millis() - led1ForcedOnStartTime >= forcedOnDuration) {
      digitalWrite(led1Pin, LOW); // Turn off LED1 after the forced on duration
      led1ForcedOn = false;
    }
  } else {
    digitalWrite(led1Pin, LOW); // Turn off LED1
  }

  if (ldr2Val < ldr2Threshold || led2ForcedOn) {
    digitalWrite(led2Pin, HIGH); // Turn on LED2
    if (led2ForcedOn && millis() - led2ForcedOnStartTime >= forcedOnDuration) {
      digitalWrite(led2Pin, LOW); // Turn off LED2 after the forced on duration
      led2ForcedOn = false;
    }
  } else {
    digitalWrite(led2Pin, LOW); // Turn off LED2
  }

  if (ldr3Val < ldr3Threshold || led3ForcedOn) {
    digitalWrite(led3Pin, HIGH); // Turn on LED3
    if (led3ForcedOn && millis() - led3ForcedOnStartTime >= forcedOnDuration) {
      digitalWrite(led3Pin, LOW); // Turn off LED3 after the forced on duration
      led3ForcedOn = false;
    }
  } else {
    digitalWrite(led3Pin, LOW); // Turn off LED3
  }

  if (Serial.available()) {
    String message = Serial.readStringUntil('\n');
    message.trim();
    if (message.startsWith("LED1:ON")) {
      digitalWrite(led1Pin, HIGH); // Turn on LED1
      led1ForcedOn = true;
      led1ForcedOnStartTime = millis();
    } else if (message.startsWith("LED2:ON")) {
      digitalWrite(led2Pin, HIGH); // Turn on LED2
      led2ForcedOn = true;
      led2ForcedOnStartTime = millis();
    } else if (message.startsWith("LED3:ON")) {
      digitalWrite(led3Pin, HIGH); // Turn on LED3
      led3ForcedOn = true;
      led3ForcedOnStartTime = millis();
    } else if (message.startsWith("DURATION:")) {
      forcedOnDuration = message.substring(9).toInt();
    }
  }

  delay(100);
}
