import time
import logging
from config.config_manager import config

logger = logging.getLogger("JARVIS-PCA9685")

class PCA9685:
    def __init__(self, busnum=1, address=0x40):
        self.address = address
        self.simulated = config.get("simulation_mode", True)
        
        if not self.simulated:
            try:
                import smbus2
                self.bus = smbus2.SMBus(busnum)
                logger.info(f"Connected to PCA9685 at I2C {hex(self.address)}")
                self._reset()
                self.set_pwm_freq(50)
            except Exception as e:
                logger.error(f"Failed to initialize PCA9685: {e}")
                self.simulated = True
        else:
            logger.info("PCA9685 running in SIMULATION mode.")

    def _reset(self):
        if not self.simulated:
            self.bus.write_byte_data(self.address, 0x00, 0x00)

    def set_pwm_freq(self, freq_hz):
        if self.simulated:
            return
        prescaleval = 25000000.0    # 25MHz
        prescaleval /= 4096.0       # 12-bit
        prescaleval /= float(freq_hz)
        prescaleval -= 1.0
        prescale = int(prescaleval + 0.5)
        oldmode = self.bus.read_byte_data(self.address, 0x00)
        newmode = (oldmode & 0x7F) | 0x10    # sleep
        self.bus.write_byte_data(self.address, 0x00, newmode) # go to sleep
        self.bus.write_byte_data(self.address, 0xFE, prescale)
        self.bus.write_byte_data(self.address, 0x00, oldmode)
        time.sleep(0.005)
        self.bus.write_byte_data(self.address, 0x00, oldmode | 0x80)

    def set_pwm(self, channel, on, off):
        if self.simulated:
            logger.debug(f"[SIM-PCA] Channel {channel} -> on: {on}, off: {off}")
            return
        self.bus.write_byte_data(self.address, 0x06 + 4*channel, on & 0xFF)
        self.bus.write_byte_data(self.address, 0x07 + 4*channel, on >> 8)
        self.bus.write_byte_data(self.address, 0x08 + 4*channel, off & 0xFF)
        self.bus.write_byte_data(self.address, 0x09 + 4*channel, off >> 8)
