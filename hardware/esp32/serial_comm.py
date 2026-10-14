import serial
import threading
import time
import logging
from config.config_manager import config

logger = logging.getLogger("JARVIS-ESP32")

class ESP32Controller:
    def __init__(self, port='/dev/ttyUSB0', baudrate=115200):
        self.simulated = config.get("simulation_mode", True)
        self.running = False
        self.serial = None
        
        if not self.simulated:
            try:
                self.serial = serial.Serial(port, baudrate, timeout=1)
                self.running = True
                self.read_thread = threading.Thread(target=self._read_loop, daemon=True)
                self.read_thread.start()
                logger.info(f"Connected to ESP32 on {port}")
            except Exception as e:
                logger.error(f"Failed to connect to ESP32: {e}")
                self.simulated = True
        else:
            logger.info("ESP32 running in SIMULATION mode.")

    def _read_loop(self):
        while self.running and self.serial:
            try:
                if self.serial.in_waiting > 0:
                    line = self.serial.readline().decode('utf-8').strip()
                    logger.debug(f"[ESP32 IN] {line}")
            except Exception as e:
                logger.error(f"ESP32 Read Error: {e}")
                time.sleep(1)

    def send_command(self, command: str):
        if self.simulated:
            logger.info(f"[SIM-ESP32 OUT] {command}")
            return
        if self.serial and self.serial.is_open:
            self.serial.write(f"{command}\n".encode('utf-8'))
            logger.debug(f"[ESP32 OUT] {command}")
            
    def shutdown(self):
        self.running = False
        if self.serial:
            self.serial.close()
