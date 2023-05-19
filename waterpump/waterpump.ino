

#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <Servo.h>
#include <TinyGPS++.h>
#include <SoftwareSerial.h>

#define PUMP1_PIN 2
#define PUMP2_PIN 4
#define PUMP3_PIN 7
#define MOISTURE1_PIN A0
#define MOISTURE2_PIN A1
#define MOISTURE3_PIN A2

SoftwareSerial gpsSerial(12, 13);  // RX, TX pins for GPS module
TinyGPSPlus gps;

int Pump1_Pause = 0;
int Pump2_Pause = 0;
int Pump3_Pause = 0; 
int thres1 = 750;
int thres2 = 750;
int thres3 = 750;
double latitude = 1.5;
double longitude = 110.35;


void setup() {
  Serial.begin(9600);
  gpsSerial.begin(9600);

 
}

void updateMoistureData() {
  int moisture1_level = analogRead(MOISTURE1_PIN);
  int moisture2_level = analogRead(MOISTURE2_PIN);
  int moisture3_level = analogRead(MOISTURE3_PIN);
  Serial.print("Moisture 1: ");
  Serial.println(moisture1_level);
  Serial.print("Moisture 2: ");
  Serial.println(moisture2_level);
  Serial.print("Moisture 3: ");
  Serial.println(moisture3_level);
}

void pumpWater(int x){
  if (x == 1) {
    digitalWrite(PUMP1_PIN, LOW);
    delay(4000);
    Serial.println("Pump 1 Activated");
    digitalWrite(PUMP1_PIN, HIGH);
  } 

  if (x == 2) {
    digitalWrite(PUMP2_PIN, HIGH);
    delay(4000);
    Serial.println("Pump 2 Activated");
    digitalWrite(PUMP2_PIN, LOW);
  } 
  if (x == 3) {
    digitalWrite(PUMP3_PIN, HIGH);
    delay(4000);
    Serial.println("Pump 3 Activated");
    digitalWrite(PUMP3_PIN, LOW);
  }
}

void readMoisture() {
  int moisture1_level = analogRead(MOISTURE1_PIN);
  int moisture2_level = analogRead(MOISTURE2_PIN);
  int moisture3_level = analogRead(MOISTURE3_PIN);
  Serial.print("Moisture 1: ");
  Serial.println(moisture1_level);
  Serial.print("Moisture 2: ");
  Serial.println(moisture2_level);
  Serial.print("Moisture 3: ");
  Serial.println(moisture3_level);

  if (moisture1_level > thres1 && Pump1_Pause == 0) {
    pumpWater(1);
  } 

  if (moisture2_level > thres2 && Pump2_Pause == 0) {
    pumpWater(2);
  } 
  if (moisture3_level > thres3 && Pump3_Pause == 0) {
    pumpWater(3);
  } 
}

void loop() {
  
  // Read data from the GPS module
  if (gpsSerial.available() > 0) {
    if (gps.encode(gpsSerial.read())) {
      // Check if valid GPS data is available
      if (gps.location.isValid()) {
        // Print latitude and longitude to the serial monitor
        latitude = gps.location.lat();
        longitude = gps.location.lng();
        Serial.print("Latitude: ");
        Serial.println(latitude, 6);
        Serial.print("Longitude: ");
        Serial.println(longitude, 6);
        
        delay(1000);
        readMoisture();
        
      }
      else {
        Serial.print("Latitude: ");
        Serial.println(latitude, 6);
        Serial.print("Longitude: ");
        Serial.println(longitude, 6);
        delay(1000);
        readMoisture();
      }
    }
  } else {
    Serial.print("Latitude: ");
    Serial.println(latitude, 6);
    Serial.print("Longitude: ");
    Serial.println(longitude, 6);
    delay(1000);
    readMoisture();
  }
  if (Serial.available()) {
    String message = Serial.readString();
    message.trim();
    Serial.println(message); 
    if (message.startsWith("thres1 = ")) {
      message.remove(0, 9);
      thres1 = message.toInt();
      Serial.print("Moisture 1 threshold set to ");
      Serial.println(thres1);
    } else if (message.startsWith("thres2 = ")) {
      message.remove(0, 9);
      thres2 = message.toInt();
      Serial.print("Moisture 2 threshold set to ");
      Serial.println(thres2);
    } else if (message.startsWith("thres3 = ")) {
      message.remove(0, 9);
      thres3 = message.toInt();
      Serial.print("Moisture 3 threshold set to ");
      Serial.println(thres3);
    } else if (message == "update") {
      readMoisture();
    } else if (message.startsWith("PumpTrigger = ")) {
      message.remove(0, 14);
      if (message == "1"){
        pumpWater(1);
      } else if (message == "2"){
        pumpWater(2);
      } else if (message == "3"){
        pumpWater(3);
      }
    } else if (message.startsWith("Pump1_Pause = ")) {
      message.remove(0, 14);
      Pump1_Pause = message.toInt();
    }  else if (message.startsWith("Pump2_Pause = ")) {
      message.remove(0, 14);
      Pump2_Pause = message.toInt();
    }  else if (message.startsWith("Pump3_Pause = ")) {
      message.remove(0, 14);
      Pump3_Pause = message.toInt();
    }
  }
}




  
  
