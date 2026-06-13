#include <Servo.h>
//(z- Step) on the arduino CNC shield v3 
#define SERVO_ROTATION_PIN 11
Servo servo_rotation; 

/* Choosing the factor for rotate(int angle). 
Why rotate() takes angle between 0 and 90, and it doubles 
it before writing it to the servo ?
    The answer has to do with the mechanical setup of the servo for rotation.
    When we tried servo_rotation.write(180), we noticed the resulting rotation was 90 degrees. 
    And since the maximum parameter of servo_rotation.write() should be 180, so : 
            parameter   ====>    resulting rotation
            180         ====>    90
            ??          ====>    angle
            ?? = angle*180/90  = angle * 2.

            thus the parameter 'angle' will refer the resulting angle we are expecting.
                
    If you choose to do a different mechanical setup for the rotation, you should repeat the above process
*/
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
