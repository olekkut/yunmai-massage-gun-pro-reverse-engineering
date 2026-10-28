/*
 * Yunmai Massage Gun Pro - Motor Test Prototype (v2 High Freq)
 * 
 * Hardware: Arduino Nano / Uno (ATmega328P)
 * 
 * Wiring:
 * - D9 (OC1A) -> Motor PWM (Blue Wire)
 * - D8        -> Motor FR/Direction (Yellow Wire)
 * - GND       -> Motor GND AND Battery GND
 * 
 * commands:
 * - 0-100 : Speed %
 * - s     : Stop
 * - r     : Reverse
 * - i     : Toggle Inverted Logic (Debug)
 */

const int PIN_PWM = 9;  // Uses Timer1
const int PIN_DIR = 8;
const int PIN_FG  = 2;

int currentSpeed = 0;
bool direction = false;
bool invertedLogic = false; // Set true if 0V = Max Speed

void setup() {
  Serial.begin(115200);
  
  pinMode(PIN_PWM, OUTPUT);
  pinMode(PIN_DIR, OUTPUT);
  pinMode(PIN_FG, INPUT_PULLUP);
  
  // Configure Timer1 for 25kHz PWM on Pin 9
  // Mode 14 (Fast PWM), Prescaler 1
  // ICR1 sets TOP value -> Frequency
  // F_CPU = 16MHz. Target = 25kHz.
  // TOP = 16000000 / (1 * 25000) - 1 = 639
  TCCR1A = 0;
  TCCR1B = 0;
  TCCR1A = (1 << COM1A1) | (1 << WGM11); // Non-inverting mode on Pin 9 (OC1A)
  TCCR1B = (1 << WGM13) | (1 << WGM12) | (1 << CS10); // Fast PWM, Prescaler 1
  ICR1 = 639; // Sets frequency to ~25kHz
  OCR1A = 0;  // 0% Duty Cycle initially
  
  digitalWrite(PIN_DIR, LOW);
  
  Serial.println("Yunmai Motor HF Test Ready (25kHz).");
  Serial.println("Commands: 0-100 (Speed), s (Stop), r (Rev), i (Invert Logic)");
}

void loop() {
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim();
    if (input.length() == 0) return;
    
    char cmd = input.charAt(0);
    
    if (cmd == 's' || cmd == 'S') {
      setMotorSpeed(0);
    } 
    else if (cmd == 'r' || cmd == 'R') {
      direction = !direction;
      digitalWrite(PIN_DIR, direction);
      Serial.print("Direction: "); Serial.println(direction ? "Reverse" : "Forward");
    }
    else if (cmd == 'i' || cmd == 'I') {
      invertedLogic = !invertedLogic;
      Serial.print("Logic Inverted: "); Serial.println(invertedLogic ? "YES" : "NO");
      setMotorSpeed(currentSpeed); // Re-apply
    }
    else {
      int val = input.toInt();
      val = constrain(val, 0, 100);
      setMotorSpeed(val);
    }
  }
}

void setMotorSpeed(int percent) {
  currentSpeed = percent;
  int duty = 0;
  
  if (invertedLogic) {
     duty = map(percent, 0, 100, ICR1, 0); // 100% -> 0 count (0V), 0% -> Max count (5V)
  } else {
     duty = map(percent, 0, 100, 0, ICR1); // 0% -> 0 count (0V), 100% -> Max count (5V)
  }

  OCR1A = duty; // Update Timer Compare Register directly
  
  Serial.print("Speed: "); Serial.print(percent);
  Serial.print("% (OCR1A: "); Serial.print(duty);
  Serial.print("/"); Serial.print(ICR1);
  Serial.println(")");
}
