"""BH1750 Ambient Light (Lux) Sensor driver for JARVIS OS."""

import time
from typing import Dict, Any, Optional
from hardware.sensors.base_sensor import BaseSensor


class BH1750Sensor(BaseSensor):
    """
    BH1750 Ambient Light (Lux) Sensor.
    Communicates over I2C (default address 0x23) using smbus2.
    One-shot H-resolution mode command: 0x20.
    """

    # Operating commands
    CMD_POWER_DOWN = 0x00
    CMD_POWER_ON = 0x01
    CMD_RESET = 0x07
    CMD_ONE_TIME_H_RES = 0x20  # 1 lx resolution, measurement time ~120-180ms

    def __init__(
        self,
        name: str = "bh1750",
        i2c_bus: int = 1,
        address: int = 0x23,
        simulation_mode: Optional[bool] = None,
    ) -> None:
        super().__init__(name=name, simulation_mode=simulation_mode)
        self.bus_num = i2c_bus
        self.address = address
        self.bus = None

        if not self.simulation_mode:
            self._init_hardware()

    def _init_hardware(self) -> None:
        """Initialize I2C bus connection to BH1750."""
        try:
            import smbus2

            self.bus = smbus2.SMBus(self.bus_num)
            # Test connectivity by powering on
            self.bus.write_byte(self.address, self.CMD_POWER_ON)
            self._initialized = True
            self.logger.info(f"BH1750 light sensor initialized at I2C address {hex(self.address)}")
        except ImportError:
            self.logger.warning("smbus2 library not available. Falling back to simulation mode.")
            self.simulation_mode = True
        except Exception as e:
            self.logger.error(f"Failed to initialize BH1750 on I2C address {hex(self.address)}: {e}")
            self._initialized = False

    def _read_raw_hardware(self) -> float:
        """Trigger one-shot H-resolution mode (0x20) and read 2 bytes of light data."""
        if not self.bus:
            raise RuntimeError("I2C bus not initialized")

        import smbus2

        # Send command 0x20: One-shot H-resolution mode
        self.bus.write_byte(self.address, self.CMD_ONE_TIME_H_RES)
        # Datasheet specifies max 180ms measurement time for H-resolution
        time.sleep(0.18)

        # Read 2 bytes
        try:
            msg = smbus2.i2c_msg.read(self.address, 2)
            self.bus.i2c_rdwr(msg)
            data = list(msg)
        except Exception:
            # Fallback to block read
            data = self.bus.read_i2c_block_data(self.address, self.CMD_ONE_TIME_H_RES, 2)

        if len(data) < 2:
            raise RuntimeError(f"Unexpected data length from BH1750: {len(data)}")

        raw_val = (data[0] << 8) | data[1]
        lux = round(raw_val / 1.2, 2)
        return lux

    def read(self) -> Dict[str, Any]:
        """
        Read ambient light in lux.
        In simulation returns {'lux': 350.0, 'timestamp': ...}.
        """
        self.last_update = time.time()

        if self.simulation_mode:
            return {
                "lux": 350.0,
                "timestamp": self.last_update,
            }

        try:
            lux = self._read_raw_hardware()
            return {
                "lux": lux,
                "timestamp": self.last_update,
            }
        except Exception as e:
            self.logger.error(f"Error reading BH1750 sensor: {e}")
            return {
                "lux": None,
                "error": str(e),
                "timestamp": self.last_update,
            }
