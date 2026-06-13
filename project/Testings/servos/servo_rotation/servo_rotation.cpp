#include <Servo.h>
//(z- Step) on the arduino CNC shield v3 
#define SERVO_ROTATION_PIN 11
Servo servo_rotation; 

//angle between 0 and  90 degrees
void rotate(int angle){
    servo_rotation.write(int(angle*2)); 
}

void setup() {
  servo_rotation.attach(SERVO_ROTATION_PIN);  // attaches the servo on pin 9 to the Servo object
}

void loop(){
    for (int i = 0 ; i <= 90 ; i = i + 10){
        rotate(i);
        delay(500);
    }
}
