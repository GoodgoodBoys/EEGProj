#include "BluetoothSerial.h"

#define NULLACTION 'N'
#define ADVANCE '0'
#define BACKWARD '1'
#define STOP '2'

BluetoothSerial SerialBT;

int Relay_1_IO = 2;
int Relay_2_IO = 4;

bool moving = false;
int directionCount = -1;
char preAction = NULLACTION;

void setup() {
  pinMode(Relay_1_IO, OUTPUT);
  pinMode(Relay_2_IO, OUTPUT);

  Serial.begin(115200);                         // COM Baud rate
  SerialBT.begin("ESP32_BT_Team8_ModelCar");    // Bluetooth name
  Serial.println("ESP32 setup finished\n");
}

void loop() {
  if (SerialBT.available()) {
    char BTMessage = SerialBT.read();
    // Serial.write(BTMessage);
    if(BTMessage != '\r' && BTMessage != '\n') {
      Serial.print("[Serial] Receive: ");
      Serial.println(BTMessage);
      if(BTMessage == ADVANCE && moving == true) {
        if(preAction == ADVANCE) {
          directionCount += 1;
          if(directionCount >= 5) {
            Advance();
            directionCount = 0;
          }
        } else {
          preAction = ADVANCE;
          directionCount = 0;
        }
      } else if(BTMessage == BACKWARD && moving == true) {
        if(preAction == BACKWARD) {
          directionCount += 1;
          if(directionCount >= 5) {
            Backward();
            directionCount = 0;
          }
        } else {
          preAction = BACKWARD;
          directionCount = 0;
        }
      } else if(BTMessage == STOP) {
        if(moving == 0) {
          moving = !moving;
        } else {
          moving = !moving;
          Stop();
        }
      }
    } else {
      Serial.println("[Serial] Carriage return received");
    }
  }
  if (Serial.available()) {
    char SerialMessage = Serial.read();

    if(SerialMessage != '\r' && SerialMessage != '\n') {
      Serial.print("[Serial] Receive: ");
      Serial.println(SerialMessage);
      if(SerialMessage == ADVANCE) {
        Advance();
      } else if(SerialMessage == BACKWARD) {
        Backward();
      } else if(SerialMessage == STOP) {
        Stop();
      }
    } else {
      Serial.println("[Serial] Carriage return received");
    }
  }
}

void Advance() {
  digitalWrite(Relay_1_IO, HIGH);
  digitalWrite(Relay_2_IO, LOW);
  Serial.println("Advance");
}

void Backward() {
  digitalWrite(Relay_1_IO, LOW);
  digitalWrite(Relay_2_IO, HIGH);
  Serial.println("Backward");
}

void Stop() {
  digitalWrite(Relay_1_IO, LOW);
  digitalWrite(Relay_2_IO, LOW);
  Serial.println("Stop");
}
