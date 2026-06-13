#define SERVO_PIN  A5
#define POS_UP     500   
#define POS_DOWN   2500   

/* Calibrating the up-down servo.
    The values of POS_DOWN and POS_UP were chosen through experimentation. The process : 
    - run loop(){servo_up();};
    - remove the horn and manually place on the desired position
    - run loop(){servo_down();}; and verify if the position is acceptable :
         - if (very big rotation): try widening the gap between POS_DOWN and POS_UP by increase the one or decresing the other, 
         and repeat the process until both positions are acceptable.
         - else if (small rotation):  try shortening the gap between POS_DOWN and POS_UP by increase the one or decresing the other, 
         and repeat the process until both positions are acceptable.
         - else (if good enough) : stop
*/

// POS_UP : microseconds pulse for UP
// POS_DOWN : microseconds pulse for DOWN
// A5 = SCL 
void sendPulse(int microseconds) {
    for (int i = 0; i < 50; i++) {  // send 50 pulses to lock position
        digitalWrite(SERVO_PIN, HIGH);
        delayMicroseconds(microseconds);
        digitalWrite(SERVO_PIN, LOW);
        delayMicroseconds(20000 - microseconds);  // 20ms period
    }
}

void setup() {
    pinMode(SERVO_PIN, OUTPUT);
}

void servo_up() {
    sendPulse(POS_UP);    
}

void servo_down() {
    sendPulse(POS_DOWN);  
}

void loop () {
  servo_down(); 
  delay(500);
  servo_up(); 
  delay(1000);
}
