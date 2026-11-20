"""Unit and integration tests for JARVIS OS sensor suite."""

import time
import pytest

from hardware.sensors.base_sensor import BaseSensor
from hardware.sensors.bme280 import BME280Sensor
from hardware.sensors.bh1750 import BH1750Sensor
from hardware.sensors.vl53l0x import VL53L0XSensor
from hardware.sensors.hcsr501 import PIRSensor, HCSR501Sensor
from hardware.sensors.hcsr04 import UltrasonicSensor, HCSR04Sensor


def _sensor_manager_class():
    """Delay manager import until an explicitly opted-in hardware test runs."""
    from hardware.sensors.sensor_manager import SensorManager

    return SensorManager


def _hardware_client():
    """Delay full-app import; collection itself must never initialize devices."""
    from fastapi.testclient import TestClient
    from apps.core.main import app

    return TestClient(app)


def test_base_sensor_abstract():
    """Verify BaseSensor behaves properly as an abstract class."""
    class DummySensor(BaseSensor):
        def read(self):
            return super().read()

    dummy = DummySensor(name="dummy", simulation_mode=True)
    assert dummy.name == "dummy"
    assert dummy.simulation_mode is True
    assert dummy.status() == "simulated"
    assert dummy.calibrate() is True

    reading = dummy.read()
    assert reading.get("error") == "Simulated"
    assert "timestamp" in reading
    assert dummy.last_update > 0


def test_bme280_sensor_simulation():
    """Verify BME280 sensor simulated readings and data structure."""
    bme = BME280Sensor(simulation_mode=True)
    assert bme.name == "bme280"
    assert bme.status() == "simulated"
    assert bme.calibrate() is True

    data = bme.read()
    assert data["temperature_c"] == 24.5
    assert data["humidity_pct"] == 58.0
    assert data["pressure_hpa"] == 1013.0
    assert "timestamp" in data
    assert isinstance(data["timestamp"], float)


def test_bh1750_sensor_simulation():
    """Verify BH1750 ambient light sensor simulated readings."""
    bh = BH1750Sensor(simulation_mode=True)
    assert bh.name == "bh1750"
    assert bh.status() == "simulated"

    data = bh.read()
    assert data["lux"] == 350.0
    assert "timestamp" in data
    assert isinstance(data["timestamp"], float)


def test_vl53l0x_sensor_simulation():
    """Verify VL53L0X ToF distance sensor simulated readings."""
    vl = VL53L0XSensor(simulation_mode=True)
    assert vl.name == "vl53l0x"
    assert vl.status() == "simulated"

    data = vl.read()
    assert data["distance_mm"] == 250
    assert "timestamp" in data
    assert isinstance(data["timestamp"], float)


def test_hcsr501_pir_sensor_simulation():
    """Verify HC-SR501 PIR motion sensor simulated readings and alias."""
    pir = PIRSensor(simulation_mode=True)
    assert pir.name == "hcsr501"
    assert pir.status() == "simulated"

    data = pir.read()
    assert data["motion_detected"] is False
    assert "timestamp" in data
    assert isinstance(data["timestamp"], float)

    # Verify alias
    pir_alias = HCSR501Sensor(simulation_mode=True)
    assert isinstance(pir_alias, PIRSensor)


def test_hcsr04_ultrasonic_sensor_simulation():
    """Verify HC-SR04 ultrasonic distance sensor simulated readings and alias."""
    sonar = UltrasonicSensor(simulation_mode=True)
    assert sonar.name == "hcsr04"
    assert sonar.status() == "simulated"

    data = sonar.read()
    assert data["distance_cm"] == 45.0
    assert "timestamp" in data
    assert isinstance(data["timestamp"], float)

    # Verify alias
    sonar_alias = HCSR04Sensor(simulation_mode=True)
    assert isinstance(sonar_alias, UltrasonicSensor)


def test_sensor_manager_initialization():
    """Verify SensorManager holds all expected sensors and handles aliases."""
    mgr = _sensor_manager_class()(simulation_mode=True)
    assert "bme280" in mgr.sensors
    assert "bh1750" in mgr.sensors
    assert "vl53l0x" in mgr.sensors
    assert "hcsr501" in mgr.sensors
    assert "hcsr04" in mgr.sensors

    # Direct retrieval
    assert mgr.get_sensor("bme280") is not None
    assert mgr.get_sensor("bh1750") is not None
    assert mgr.get_sensor("vl53l0x") is not None
    assert mgr.get_sensor("hcsr501") is not None
    assert mgr.get_sensor("hcsr04") is not None

    # Case insensitivity & Aliases
    assert mgr.get_sensor("BME280") is not None
    assert mgr.get_sensor("pir") is mgr.get_sensor("hcsr501")
    assert mgr.get_sensor("motion") is mgr.get_sensor("hcsr501")
    assert mgr.get_sensor("ultrasonic") is mgr.get_sensor("hcsr04")
    assert mgr.get_sensor("lux") is mgr.get_sensor("bh1750")
    assert mgr.get_sensor("tof") is mgr.get_sensor("vl53l0x")

    # Non-existent sensor
    assert mgr.get_sensor("non_existent_sensor") is None


def test_sensor_manager_read_all():
    """Verify SensorManager read_all returns all sensor telemetry with timestamps."""
    mgr = _sensor_manager_class()(simulation_mode=True)
    all_readings = mgr.read_all()

    for sensor_name in ["bme280", "bh1750", "vl53l0x", "hcsr501", "hcsr04"]:
        assert sensor_name in all_readings
        reading = all_readings[sensor_name]
        assert "timestamp" in reading
        assert isinstance(reading["timestamp"], float)


def test_sensor_manager_status_all():
    """Verify SensorManager status_all returns status for all sensors."""
    mgr = _sensor_manager_class()(simulation_mode=True)
    statuses = mgr.status_all()

    for sensor_name in ["bme280", "bh1750", "vl53l0x", "hcsr501", "hcsr04"]:
        assert sensor_name in statuses
        assert statuses[sensor_name] == "simulated"


def test_api_sensors_all_endpoint():
    """Test GET /sensors/all and GET /api/sensors/all."""
    with _hardware_client() as client:
        for prefix in ["/sensors", "/api/sensors"]:
            response = client.get(f"{prefix}/all")
            assert response.status_code == 200
            data = response.json()
            assert "bme280" in data
            assert "bh1750" in data
            assert "vl53l0x" in data
            assert "hcsr501" in data
            assert "hcsr04" in data
            assert data["bme280"]["temperature_c"] == 24.5
            assert data["bh1750"]["lux"] == 350.0


def test_api_sensors_status_endpoint():
    """Test GET /sensors/status and GET /api/sensors/status."""
    with _hardware_client() as client:
        for prefix in ["/sensors", "/api/sensors"]:
            response = client.get(f"{prefix}/status")
            assert response.status_code == 200
            data = response.json()
            assert "bme280" in data
            assert data["bme280"] == "simulated"


def test_api_sensors_get_by_name():
    """Test GET /sensors/{name} with valid sensors and aliases."""
    with _hardware_client() as client:
        # Direct sensor
        res = client.get("/sensors/bme280")
        assert res.status_code == 200
        assert res.json()["temperature_c"] == 24.5

        # Alias sensor
        res = client.get("/sensors/pir")
        assert res.status_code == 200
        assert res.json()["motion_detected"] is False

        # Ultrasonic
        res = client.get("/sensors/ultrasonic")
        assert res.status_code == 200
        assert res.json()["distance_cm"] == 45.0

        # 404 for unknown sensor
        res = client.get("/sensors/unknown_sensor")
        assert res.status_code == 404
