"""BME280 Temperature, Humidity, and Pressure Sensor driver for JARVIS OS."""

import struct
import time
from typing import Dict, Any, Optional
from hardware.sensors.base_sensor import BaseSensor


class BME280Sensor(BaseSensor):
    """
    BME280 Environmental Sensor (Temperature, Humidity, Pressure).
    Supports I2C communication via smbus2 on addresses 0x76 or 0x77.
    """

    # BME280 Register addresses
    REG_DIG_T1 = 0x88
    REG_DIG_H1 = 0xA1
    REG_CHIP_ID = 0xD0
    REG_RESET = 0xE0
    REG_DIG_H2 = 0xE1
    REG_CTRL_HUM = 0xF2
    REG_STATUS = 0xF3
    REG_CTRL_MEAS = 0xF4
    REG_CONFIG = 0xF5
    REG_PRESSURE_DATA = 0xF7

    def __init__(
        self,
        name: str = "bme280",
        i2c_bus: int = 1,
        address: Optional[int] = None,
        simulation_mode: Optional[bool] = None,
    ) -> None:
        super().__init__(name=name, simulation_mode=simulation_mode)
        self.bus_num = i2c_bus
        self.bus = None
        self.address = address
        self.calib: Dict[str, Any] = {}

        if not self.simulation_mode:
            self._init_hardware()

    def _init_hardware(self) -> None:
        """Initialize I2C bus and BME280 hardware registers."""
        try:
            import smbus2

            self.bus = smbus2.SMBus(self.bus_num)
            candidate_addrs = [self.address] if self.address is not None else [0x76, 0x77]
            detected_addr = None

            for addr in candidate_addrs:
                try:
                    chip_id = self.bus.read_byte_data(addr, self.REG_CHIP_ID)
                    if chip_id in (0x60, 0x58):  # 0x60: BME280, 0x58: BMP280
                        detected_addr = addr
                        self.logger.info(
                            f"BME280 detected at I2C address {hex(addr)} (Chip ID: {hex(chip_id)})"
                        )
                        break
                except Exception:
                    continue

            if detected_addr is None:
                raise RuntimeError(
                    f"No BME280 sensor responded on I2C bus {self.bus_num} addresses: {candidate_addrs}"
                )

            self.address = detected_addr
            self._read_calibration_data()
            self._configure_sensor()
            self._initialized = True
        except ImportError:
            self.logger.warning("smbus2 library not available. Falling back to simulation mode.")
            self.simulation_mode = True
        except Exception as e:
            self.logger.error(f"Failed to initialize BME280 on I2C bus {self.bus_num}: {e}")
            self._initialized = False

    def _read_calibration_data(self) -> None:
        """Read trimming calibration parameters from sensor ROM."""
        if not self.bus or not self.address:
            return

        # Read 24 bytes from 0x88 (dig_T1 through dig_P9)
        cal1 = self.bus.read_i2c_block_data(self.address, self.REG_DIG_T1, 24)
        dig_t1, dig_t2, dig_t3 = struct.unpack("<Hhh", bytes(cal1[0:6]))
        dig_p1, dig_p2, dig_p3, dig_p4, dig_p5, dig_p6, dig_p7, dig_p8, dig_p9 = struct.unpack(
            "<Hhhhhhhhh", bytes(cal1[6:24])
        )

        # Read dig_H1 from 0xA1
        dig_h1 = self.bus.read_byte_data(self.address, self.REG_DIG_H1)

        # Read dig_H2 to dig_H6 from 0xE1
        cal2 = self.bus.read_i2c_block_data(self.address, self.REG_DIG_H2, 7)
        dig_h2 = struct.unpack("<h", bytes(cal2[0:2]))[0]
        dig_h3 = cal2[2]

        dig_h4 = (cal2[3] << 4) | (cal2[4] & 0x0F)
        if dig_h4 > 2047:
            dig_h4 -= 4096

        dig_h5 = (cal2[5] << 4) | (cal2[4] >> 4)
        if dig_h5 > 2047:
            dig_h5 -= 4096

        dig_h6 = cal2[6]
        if dig_h6 > 127:
            dig_h6 -= 256

        self.calib = {
            "dig_T1": dig_t1,
            "dig_T2": dig_t2,
            "dig_T3": dig_t3,
            "dig_P1": dig_p1,
            "dig_P2": dig_p2,
            "dig_P3": dig_p3,
            "dig_P4": dig_p4,
            "dig_P5": dig_p5,
            "dig_P6": dig_p6,
            "dig_P7": dig_p7,
            "dig_P8": dig_p8,
            "dig_P9": dig_p9,
            "dig_H1": dig_h1,
            "dig_H2": dig_h2,
            "dig_H3": dig_h3,
            "dig_H4": dig_h4,
            "dig_H5": dig_h5,
            "dig_H6": dig_h6,
        }
        self.logger.debug(f"BME280 calibration parameters loaded successfully from {hex(self.address)}")

    def _configure_sensor(self) -> None:
        """Configure sampling and operation mode."""
        if not self.bus or not self.address:
            return

        # Reset device
        self.bus.write_byte_data(self.address, self.REG_RESET, 0xB6)
        time.sleep(0.01)

        # Set humidity oversampling (1x)
        self.bus.write_byte_data(self.address, self.REG_CTRL_HUM, 0x01)

        # Set standby 1000ms, filter 4
        self.bus.write_byte_data(self.address, self.REG_CONFIG, 0xA0)

        # Set temp oversampling 1x, press oversampling 1x, normal mode (3)
        # (1 << 5) | (1 << 2) | 3 = 0x27
        self.bus.write_byte_data(self.address, self.REG_CTRL_MEAS, 0x27)
        time.sleep(0.05)

    def calibrate(self) -> bool:
        """Re-read calibration registers if connected."""
        super().calibrate()
        if self.simulation_mode:
            return True
        try:
            self._read_calibration_data()
            return True
        except Exception as e:
            self.logger.error(f"Calibration reload failed: {e}")
            return False

    def _read_raw_hardware(self) -> Dict[str, Any]:
        """Read registers and apply Bosch compensation formulas."""
        if not self.bus or not self.address:
            raise RuntimeError("Hardware bus or address not configured")

        # Read 8 bytes of burst telemetry starting at 0xF7
        data = self.bus.read_i2c_block_data(self.address, self.REG_PRESSURE_DATA, 8)

        adc_p = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
        adc_t = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
        adc_h = (data[6] << 8) | data[7]

        c = self.calib

        # Temperature compensation
        var1 = (adc_t / 16384.0 - c["dig_T1"] / 1024.0) * c["dig_T2"]
        var2 = ((adc_t / 131072.0 - c["dig_T1"] / 8192.0) ** 2) * c["dig_T3"]
        t_fine = var1 + var2
        temperature_c = round(t_fine / 5120.0, 2)

        # Pressure compensation
        p_var1 = (t_fine / 2.0) - 64000.0
        p_var2 = p_var1 * p_var1 * c["dig_P6"] / 32768.0
        p_var2 = p_var2 + p_var1 * c["dig_P5"] * 2.0
        p_var2 = (p_var2 / 4.0) + (c["dig_P4"] * 65536.0)
        p_var1 = (c["dig_P3"] * p_var1 * p_var1 / 524288.0 + c["dig_P2"] * p_var1) / 524288.0
        p_var1 = (1.0 + p_var1 / 32768.0) * c["dig_P1"]

        if p_var1 != 0:
            p = 1048576.0 - adc_p
            p = (p - (p_var2 / 4096.0)) * 6250.0 / p_var1
            p_var1 = c["dig_P9"] * p * p / 2147483648.0
            p_var2 = p * c["dig_P8"] / 32768.0
            p = p + (p_var1 + p_var2 + c["dig_P7"]) / 16.0
            pressure_hpa = round(p / 100.0, 2)
        else:
            pressure_hpa = 0.0

        # Humidity compensation
        h_var = t_fine - 76800.0
        if h_var != 0:
            h_var = (adc_h - (c["dig_H4"] * 64.0 + (c["dig_H5"] / 16384.0) * h_var)) * (
                (c["dig_H2"] / 65536.0)
                * (1.0 + (c["dig_H6"] / 67108864.0) * h_var * (1.0 + (c["dig_H3"] / 67108864.0) * h_var))
            )
            h_var = h_var * (1.0 - (c["dig_H1"] * h_var / 524288.0))
            humidity_pct = round(max(0.0, min(100.0, h_var)), 2)
        else:
            humidity_pct = 0.0

        return {
            "temperature_c": temperature_c,
            "humidity_pct": humidity_pct,
            "pressure_hpa": pressure_hpa,
        }

    def read(self) -> Dict[str, Any]:
        """
        Read temperature, humidity, and pressure.
        In simulation returns {'temperature_c': 24.5, 'humidity_pct': 58.0, 'pressure_hpa': 1013.0, 'timestamp': ...}.
        """
        self.last_update = time.time()

        if self.simulation_mode:
            return {
                "temperature_c": 24.5,
                "humidity_pct": 58.0,
                "pressure_hpa": 1013.0,
                "timestamp": self.last_update,
            }

        try:
            telemetry = self._read_raw_hardware()
            telemetry["timestamp"] = self.last_update
            return telemetry
        except Exception as e:
            self.logger.error(f"Error reading BME280 sensor: {e}")
            return {
                "temperature_c": None,
                "humidity_pct": None,
                "pressure_hpa": None,
                "error": str(e),
                "timestamp": self.last_update,
            }
