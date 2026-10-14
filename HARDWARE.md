# JARVIS Hardware Setup
DO NOT connect 12V directly to Pi GPIO. Use TB6612 for motors, PCA9685 for servos.

## Sensors Setup
- **BME280** (Temperature, Humidity, Pressure): I2C Address `0x76` or `0x77` (SDA -> GPIO 2, SCL -> GPIO 3, 3.3V).
- **BH1750** (Ambient Light Lux): I2C Address `0x23` (SDA -> GPIO 2, SCL -> GPIO 3, 3.3V).
- **VL53L0X** (ToF Distance): I2C Address `0x29` (SDA -> GPIO 2, SCL -> GPIO 3, 3.3V).
- **HC-SR501** (PIR Motion): GPIO 4 (VCC -> 5V, OUT -> GPIO 4, GND -> GND).
- **HC-SR04** (Ultrasonic Distance): TRIG -> GPIO 23, ECHO -> Voltage Divider (1kΩ/2kΩ) -> GPIO 24.
  - **CRITICAL**: HC-SR04 ECHO outputs 5V. NEVER connect directly to Raspberry Pi 3.3V GPIO without a voltage divider.

