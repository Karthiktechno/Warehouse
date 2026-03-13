//LEFT Motor
#define ENA 15
#define IN1 2
#define IN2 4

#define ENCODER_A_PIN 17
#define ENCODER_B_PIN 16

//RIGHT Motor
// #define ENA 19
// #define IN1 5
// #define IN2 18

// #define ENCODER_A_PIN 23
// #define ENCODER_B_PIN 22

volatile long encoder_ticks = 0;

long target_ticks = 370;
int speed = 50;

void setup() {

  Serial.begin(115200);

  pinMode(ENA, OUTPUT);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);

  pinMode(ENCODER_A_PIN, INPUT_PULLUP);
  pinMode(ENCODER_B_PIN, INPUT_PULLUP);

  attachInterrupt(digitalPinToInterrupt(ENCODER_A_PIN), encoderISR, RISING);

  // Motor forward
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);

  analogWrite(ENA, speed);
}

void loop() {

  Serial.println(encoder_ticks);

  if (abs(encoder_ticks) >= target_ticks) {

    analogWrite(ENA, 0); // stop motor

    while (1); // halt
  }

  delay(10);
}

void encoderISR() {

  if (digitalRead(ENCODER_A_PIN) == digitalRead(ENCODER_B_PIN))
    encoder_ticks++;
  else
    encoder_ticks--;
}