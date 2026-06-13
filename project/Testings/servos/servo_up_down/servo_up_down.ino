#define SERVO_PIN  A5
#define POS_UP     500   
#define POS_DOWN   2500   

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
