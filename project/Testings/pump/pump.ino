const int PIN_VALVE    = 4;   // pin4 is Zstep  on arduino CNC Shield v3 
const int PIN_POMPE = 7;      // pin7 is Zdir on arduino CNC Shield v3

void pompeON() {
  digitalWrite(PIN_POMPE, HIGH);
  digitalWrite(PIN_VALVE, LOW);
}

void pompeOFF() {
  digitalWrite(PIN_VALVE, HIGH);
  digitalWrite(PIN_POMPE, LOW);
}

void setup() {
  pinMode(PIN_POMPE, OUTPUT);
  pinMode(PIN_VALVE, OUTPUT);
}

void loop() {
  pompeON();
  delay(2000);  // Active for 2 seconds
  pompeOFF();
  delay(2000);  // Pause 2 seconds
}
