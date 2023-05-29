#include <dht11.h>
#include <LiquidCrystal_I2C.h>


LiquidCrystal_I2C lcd(0x27, 16, 2);
#define DHT11PIN 4  //airCondA
#define DHT11PIN2 3 //airCondB
#define DHT11PIN3 2 //airCondC

//airCondA
#define ENA 9
#define IN1 8
#define IN2 10

//airCondB
#define ENB 11
#define IN3 13
#define IN4 12

//airCondC
#define ENC 5
#define IN5 6
#define IN6 7


dht11 DHT11;
dht11 DHT11B;
dht11 DHT11C;
int chkA;
int chkB;
int chkC;
int sensorState = 0;
int sensorStateB = 0;

int motorSpeed = 1;
int motorSpeedB = 1;
int motorSpeedC = 1;

void setup() {
  Serial.begin(9600);
  lcd.init();
  lcd.backlight();

  pinMode(ENA, OUTPUT);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, INPUT);
  
  pinMode(ENB, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, INPUT);

  pinMode(ENC, OUTPUT);
  pinMode(IN5, OUTPUT);
  pinMode(IN6, INPUT);

  analogWrite(ENA, 0);
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);

  analogWrite(ENB, 0);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);

  analogWrite(ENC, 0);
  digitalWrite(IN5, LOW);
  digitalWrite(IN6, LOW);
}

void loop() {
  chkA = DHT11.read(4);
  chkB = DHT11B.read(3);
  chkC = DHT11C.read(2);
  int chkA1 = DHT11.read(DHT11PIN);
  int chkB1 = DHT11B.read(DHT11PIN2);
  int chkC1 = DHT11C.read(DHT11PIN3);

    float temperatureA = DHT11.temperature;
    float temperatureB = DHT11B.temperature;
    float temperatureC = DHT11C.temperature;

    float humidityA = DHT11.humidity;
    float humidityB = DHT11B.humidity;
    float humidityC = DHT11C.humidity;

    Serial.println(temperatureA);
    Serial.println(humidityA);
    Serial.println(temperatureB);
    Serial.println(humidityB);
    Serial.println(temperatureC);
    Serial.println(humidityC);

    Serial.println(digitalRead(IN2));
    Serial.println(motorSpeed);

    Serial.println(digitalRead(IN4));
    Serial.println(motorSpeedB);
    
    Serial.println(digitalRead(IN6));
    Serial.println(motorSpeedC);
    delay(1000);

    lcd.setCursor(0,0);
    lcd.print("A:");
    lcd.print(DHT11.temperature);
    lcd.print(" B:");
    lcd.print(DHT11B.temperature);
    lcd.print(" C:");
    lcd.print(DHT11C.temperature);
    lcd.print((char)223);
    lcd.print("C");
    //lcd.print(digitalRead(IN2));
    //lcd.print(motorSpeed);
    lcd.setCursor(0,1);
    lcd.print("A:");
    lcd.print(DHT11.humidity);
    lcd.print(" B:");
    lcd.print(DHT11B.humidity);
    lcd.print(" C:");
    lcd.print(DHT11C.humidity);
    lcd.print("%");
    delay(500);

    SetPinMode();
    // SetPinMode2();
}

void SetPinMode(){
  if(Serial.available()){
    String data = Serial.readStringUntil('\n');

    String prefix = data.substring(0,1);

    if (prefix == "<"){
        int motor_state = data.substring(1, 2).toInt();
        motorSpeed = data.substring(2, 3).toInt();
        analogWrite(ENA, motorSpeed == 0 ? 0 : (motorSpeed == 1 ? 55 : (motorSpeed == 2 ? 155 : 240)));
        digitalWrite(IN2, motor_state == 0 ? LOW : HIGH);
    } else if (prefix == ">"){
        int motor_stateB = data.substring(1, 2).toInt();
        motorSpeedB = data.substring(2, 3).toInt();
        analogWrite(ENB, motorSpeedB == 0 ? 0 : (motorSpeedB == 1 ? 55 : (motorSpeedB == 2 ? 155 : 240)));
        digitalWrite(IN4, motor_stateB == 0 ? LOW : HIGH);
        
    } else if (prefix == "?"){
        int motor_stateC = data.substring(1, 2).toInt();
        motorSpeedC = data.substring(2, 3).toInt();
        analogWrite(ENC, motorSpeedC == 0 ? 0 : (motorSpeedC == 1 ? 55 : (motorSpeedC == 2 ? 155 : 180)));
        digitalWrite(IN6, motor_stateC == 0 ? LOW : HIGH);
    }
  }
}

void SetPinMode2(){
  if(Serial.available()){
    String dataB = Serial.readStringUntil('\n');

    String prefixB = dataB.substring(0,1);

    if (prefixB == ">"){
        int motor_stateB = dataB.substring(1, 2).toInt();
        motorSpeedB = dataB.substring(2, 3).toInt();
        analogWrite(ENB, motorSpeedB == 0 ? 0 : (motorSpeedB == 1 ? 55 : (motorSpeedB == 2 ? 155 : 240)));
        digitalWrite(IN4, motor_stateB == 0 ? LOW : HIGH);
    }
  }
}
