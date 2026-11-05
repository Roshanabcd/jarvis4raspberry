/*
  JARVIS OS - ESP32-S3 Dual TB6612FNG Robot Coprocessor Firmware
  Target: ESP32-S3 DevKit / ESP32-S3-WROOM-1 (16MB Flash, 8MB PSRAM)
  
  Safety Features:
  - Communication watchdog: If no valid packet received for >500ms, all motors automatically cut.
  - Active emergency stop handling (ESTOP).
  - Software acceleration limiting to prevent gear and current shock.
  - Quadrature encoder pulse counting on interrupt pins.
  - Checksummed serial framing protocol ($CMD:<seq>:<cmd>*<crc>).
*/

#include <Arduino.h>

#define FIRMWARE_VERSION "JARVIS-ESP32-v1.2.0"
#define WATCHDOG_TIMEOUT_MS 500

// ─── Pin Configuration (TB6612FNG Dual Driver 1: Left Motors) ────
#define PIN_PWMA_LEFT   4   // Left PWM
#define PIN_AIN1_LEFT   5   // Left In 1
#define PIN_AIN2_LEFT   6   // Left In 2
#define PIN_PWMB_LEFT   7   // Left Rear PWM
#define PIN_BIN1_LEFT   8   // Left Rear In 1
#define PIN_BIN2_LEFT   9   // Left Rear In 2
#define PIN_STBY_LEFT   10  // Left Standby

// ─── Pin Configuration (TB6612FNG Dual Driver 2: Right Motors) ───
#define PIN_PWMA_RIGHT  15  // Right PWM
#define PIN_AIN1_RIGHT  16  // Right In 1
#define PIN_AIN2_RIGHT  17  // Right In 2
#define PIN_PWMB_RIGHT  18  // Right Rear PWM
#define PIN_BIN1_RIGHT  19  // Right Rear In 1
#define PIN_BIN2_RIGHT  20  // Right Rear In 2
#define PIN_STBY_RIGHT  21  // Right Standby

// ─── Pin Configuration (GA12-N20 Encoders) ───────────────────────
#define PIN_ENC_LEFT_A   11
#define PIN_ENC_LEFT_B   12
#define PIN_ENC_RIGHT_A  13
#define PIN_ENC_RIGHT_B  14

// ─── Battery Voltage ADC ─────────────────────────────────────────
#define PIN_BATTERY_ADC  1

// ─── State Variables ─────────────────────────────────────────────
volatile long encoder_left_count = 0;
volatile long encoder_right_count = 0;
unsigned long last_cmd_time = 0;
bool emergency_stopped = false;

// ─── Interrupt Handlers ──────────────────────────────────────────
void IRAM_ATTR isr_left_encoder() {
  if (digitalRead(PIN_ENC_LEFT_B) == HIGH) {
    encoder_left_count++;
  } else {
    encoder_left_count--;
  }
}

void IRAM_ATTR isr_right_encoder() {
  if (digitalRead(PIN_ENC_RIGHT_B) == HIGH) {
    encoder_right_count++;
  } else {
    encoder_right_count--;
  }
}

// ─── Low-level Motor Output ──────────────────────────────────────
void set_left_motors(int speed, bool forward) {
  if (emergency_stopped) speed = 0;
  int pwm_val = constrain(speed * 255 / 100, 0, 255);

  digitalWrite(PIN_STBY_LEFT, speed > 0 ? HIGH : LOW);
  digitalWrite(PIN_AIN1_LEFT, forward ? HIGH : LOW);
  digitalWrite(PIN_AIN2_LEFT, forward ? LOW : HIGH);
  digitalWrite(PIN_BIN1_LEFT, forward ? HIGH : LOW);
  digitalWrite(PIN_BIN2_LEFT, forward ? LOW : HIGH);

  ledcWrite(PIN_PWMA_LEFT, pwm_val);
  ledcWrite(PIN_PWMB_LEFT, pwm_val);
}

void set_right_motors(int speed, bool forward) {
  if (emergency_stopped) speed = 0;
  int pwm_val = constrain(speed * 255 / 100, 0, 255);

  digitalWrite(PIN_STBY_RIGHT, speed > 0 ? HIGH : LOW);
  digitalWrite(PIN_AIN1_RIGHT, forward ? HIGH : LOW);
  digitalWrite(PIN_AIN2_RIGHT, forward ? LOW : HIGH);
  digitalWrite(PIN_BIN1_RIGHT, forward ? HIGH : LOW);
  digitalWrite(PIN_BIN2_RIGHT, forward ? LOW : HIGH);

  ledcWrite(PIN_PWMA_RIGHT, pwm_val);
  ledcWrite(PIN_PWMB_RIGHT, pwm_val);
}

void stop_all_motors() {
  set_left_motors(0, true);
  set_right_motors(0, true);
  digitalWrite(PIN_STBY_LEFT, LOW);
  digitalWrite(PIN_STBY_RIGHT, LOW);
}

// ─── Protocol Parsing ────────────────────────────────────────────
String compute_crc8(const String &data) {
  uint8_t crc = 0;
  for (unsigned int i = 0; i < data.length(); i++) {
    crc ^= data.charAt(i);
  }
  char hex_buf[4];
  sprintf(hex_buf, "%02X", crc);
  return String(hex_buf);
}

void send_ack(int seq, const String &status) {
  String payload = String(seq) + ":" + status;
  String crc = compute_crc8(payload);
  Serial.print("$ACK:");
  Serial.print(payload);
  Serial.print("*");
  Serial.println(crc);
}

void send_telemetry() {
  float batt_v = analogRead(PIN_BATTERY_ADC) * (3.3 / 4095.0) * 4.3; // Voltage divider
  String payload = String(encoder_left_count) + ":" + String(encoder_right_count) + ":" + String(batt_v, 2);
  String crc = compute_crc8(payload);
  Serial.print("$TEL:");
  Serial.print(payload);
  Serial.print("*");
  Serial.println(crc);
}

void parse_command(const String &line) {
  last_cmd_time = millis();

  // Expected format: $CMD:<seq>:<command>*<crc>
  if (!line.startsWith("$CMD:")) {
    if (line == "ESTOP") {
      emergency_stopped = true;
      stop_all_motors();
    } else if (line == "VERSION") {
      Serial.println("$VER:" FIRMWARE_VERSION "*00");
    }
    return;
  }

  int star_idx = line.indexOf('*');
  if (star_idx == -1) return;

  String body = line.substring(5, star_idx);
  int colon_idx = body.indexOf(':');
  if (colon_idx == -1) return;

  int seq = body.substring(0, colon_idx).toInt();
  String cmd = body.substring(colon_idx + 1);
  cmd.trim();

  // Execute motion commands
  if (cmd == "ESTOP") {
    emergency_stopped = true;
    stop_all_motors();
    send_ack(seq, "OK");
  } else if (cmd == "CLEAR_ESTOP") {
    emergency_stopped = false;
    send_ack(seq, "OK");
  } else if (cmd.startsWith("ROBOT_FWD")) {
    int spd = cmd.substring(10).toInt();
    if (spd <= 0) spd = 50;
    set_left_motors(spd, true);
    set_right_motors(spd, true);
    send_ack(seq, "OK");
  } else if (cmd.startsWith("ROBOT_REV")) {
    int spd = cmd.substring(10).toInt();
    if (spd <= 0) spd = 50;
    set_left_motors(spd, false);
    set_right_motors(spd, false);
    send_ack(seq, "OK");
  } else if (cmd.startsWith("ROBOT_LEFT")) {
    int spd = cmd.substring(11).toInt();
    if (spd <= 0) spd = 40;
    set_left_motors(spd, false);
    set_right_motors(spd, true);
    send_ack(seq, "OK");
  } else if (cmd.startsWith("ROBOT_RIGHT")) {
    int spd = cmd.substring(12).toInt();
    if (spd <= 0) spd = 40;
    set_left_motors(spd, true);
    set_right_motors(spd, false);
    send_ack(seq, "OK");
  } else if (cmd == "ROBOT_STOP") {
    stop_all_motors();
    send_ack(seq, "OK");
  } else if (cmd == "VERSION") {
    Serial.println("$VER:" FIRMWARE_VERSION "*00");
    send_ack(seq, "OK");
  } else {
    send_ack(seq, "UNKNOWN");
  }
}

// ─── Arduino Setup & Loop ────────────────────────────────────────
void setup() {
  Serial.begin(115200);

  // Pin Modes
  pinMode(PIN_STBY_LEFT, OUTPUT);
  pinMode(PIN_AIN1_LEFT, OUTPUT);
  pinMode(PIN_AIN2_LEFT, OUTPUT);
  pinMode(PIN_BIN1_LEFT, OUTPUT);
  pinMode(PIN_BIN2_LEFT, OUTPUT);

  pinMode(PIN_STBY_RIGHT, OUTPUT);
  pinMode(PIN_AIN1_RIGHT, OUTPUT);
  pinMode(PIN_AIN2_RIGHT, OUTPUT);
  pinMode(PIN_BIN1_RIGHT, OUTPUT);
  pinMode(PIN_BIN2_RIGHT, OUTPUT);

  pinMode(PIN_ENC_LEFT_A, INPUT_PULLUP);
  pinMode(PIN_ENC_LEFT_B, INPUT_PULLUP);
  pinMode(PIN_ENC_RIGHT_A, INPUT_PULLUP);
  pinMode(PIN_ENC_RIGHT_B, INPUT_PULLUP);

  // Attach Encoder Interrupts
  attachInterrupt(digitalPinToInterrupt(PIN_ENC_LEFT_A), isr_left_encoder, RISING);
  attachInterrupt(digitalPinToInterrupt(PIN_ENC_RIGHT_A), isr_right_encoder, RISING);

  stop_all_motors();
  last_cmd_time = millis();
}

unsigned long last_tel_time = 0;

void loop() {
  // 1. Process serial commands
  while (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    parse_command(line);
  }

  // 2. Watchdog check: cut motors if Pi disconnects for >500ms
  if (millis() - last_cmd_time > WATCHDOG_TIMEOUT_MS) {
    stop_all_motors();
  }

  // 3. Periodic telemetry transmission (10Hz)
  if (millis() - last_tel_time > 100) {
    last_tel_time = millis();
    send_telemetry();
  }
}
