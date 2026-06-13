/*
  This Arduino program implements a precise homing sequence for a CNC Shield V3 controlling three stepper motors (X, Y, and A).
  Each axis moves toward its corresponding endstop switch at high speed until the switch is triggered, marking the initial contact point.
  After this first hit, the motor backs away slightly and then approaches the switch again at a much slower speed. 
  This double‑approach technique—fast approach, retract, slow approach—allows the system to compensate for switch hysteresis and mechanical play, 
  ensuring a highly accurate and repeatable determination of the machine’s physical origin. 
  Once the slow approach re-triggers the switch, the axis position is reset to zero, establishing a reliable (0,0) reference for subsequent movements. 
  The X axis homes using two synchronized motors (stepper1 and stepper3), while the Y axis homes independently using stepper2.
*/

#include <AccelStepper.h>

const int endstopPinY = 10;
const int endstopPinX = 9;

AccelStepper stepper1(1, 2, 5);
AccelStepper stepper2(1, 3, 6);
AccelStepper stepper3(1, 12, 13);

const byte enablePin = 8;


void setup() {
  pinMode(endstopPinX, INPUT_PULLUP); // active la résistance interne
  pinMode(endstopPinY, INPUT_PULLUP); 
  Serial.begin(9600);
  pinMode(enablePin, OUTPUT);
  digitalWrite(enablePin, LOW);

  stepper1.setMaxSpeed(1500);    // Stepper X
  stepper2.setMaxSpeed(-1500);   // Stepper A   
  stepper3.setMaxSpeed(1500);    // Stepper Y

  stepper1.setSpeed(1500);
  stepper2.setSpeed(-1500);
  stepper3.setSpeed(1500);
}

void homingX() {
  // Aller vers le switch
  while (digitalRead(endstopPinX) == HIGH) {
    stepper1.runSpeed();
    stepper3.runSpeed();
  }

  // Stop
  stepper1.stop();
  stepper3.stop();

  delay(200);

  // Recul
  stepper1.setSpeed(-500);
  stepper3.setSpeed(-500);

  while (digitalRead(endstopPinX) == LOW) {
    stepper1.runSpeed();
    stepper3.runSpeed();
  }

  delay(200);

  // Approche lente
  stepper1.setSpeed(200);
  stepper3.setSpeed(200);

  while (digitalRead(endstopPinX) == HIGH) {
    stepper1.runSpeed();
    stepper3.runSpeed();
  }

  // Position zéro
  stepper1.setCurrentPosition(0);
  stepper3.setCurrentPosition(0);
}

void homingY() {
  while (digitalRead(endstopPinY) == HIGH) {
    stepper2.runSpeed();
  }

  stepper2.stop();
  delay(200);

  stepper2.setSpeed(500);

  while (digitalRead(endstopPinY) == LOW) {
    stepper2.runSpeed();
  }

  delay(200);

  stepper2.setSpeed(-200);

  while (digitalRead(endstopPinY) == HIGH) {
    stepper2.runSpeed();
  }

  stepper2.setCurrentPosition(0);
}
bool homing_val = false;

void loop() {
  if(homing_val == false){
    stepper1.setSpeed(1500);
    stepper2.setSpeed(-1500);
    stepper3.setSpeed(1500);
    homingX();
    homingY();
    homing_val = true;
  }

};
