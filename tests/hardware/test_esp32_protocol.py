"""
Tests for ESP32-S3 Protocol Framing, Telemetry Parsing, and Serial Communications.
"""

import pytest
from hardware.esp32.serial_comm import ESP32Controller, calculate_crc8


class TestESP32Protocol:
    def test_crc8_calculation(self):
        crc1 = calculate_crc8("1:PING")
        assert len(crc1) == 2
        # Deterministic
        assert calculate_crc8("1:PING") == crc1
        # Different data produces different crc
        assert calculate_crc8("2:PING") != crc1

    def test_message_framing(self):
        esp = ESP32Controller(simulation_mode=True)
        seq, framed = esp._frame_message("ROBOT_FWD 50")
        assert framed.startswith(f"$CMD:{seq}:ROBOT_FWD 50*")
        assert framed.endswith("\n")

    def test_simulated_command_telemetry(self):
        esp = ESP32Controller(simulation_mode=True)
        initial_tel = esp.get_telemetry()
        assert initial_tel["left_encoder"] == 0

        esp.send_command("ROBOT_FWD 50")
        fwd_tel = esp.get_telemetry()
        assert fwd_tel["left_encoder"] == 50
        assert fwd_tel["right_encoder"] == 50

        esp.send_command("ROBOT_REV 50")
        rev_tel = esp.get_telemetry()
        assert rev_tel["left_encoder"] == 0
        assert rev_tel["right_encoder"] == 0

    def test_telemetry_line_parsing(self):
        esp = ESP32Controller(simulation_mode=True)
        received_snapshots = []
        esp.register_telemetry_callback(lambda tel: received_snapshots.append(dict(tel)))

        # Simulate receiving incoming telemetry frame from ESP32
        esp._parse_incoming_line("$TEL:240:245:12.4*FF")
        tel = esp.get_telemetry()
        assert tel["left_encoder"] == 240
        assert tel["right_encoder"] == 245
        assert tel["battery_v"] == 12.4
        assert len(received_snapshots) == 1

    def test_ack_line_parsing(self):
        esp = ESP32Controller(simulation_mode=True)
        # Register a pending ack event
        import threading
        evt = threading.Event()
        esp._pending_acks[42] = evt

        esp._parse_incoming_line("$ACK:42:OK*A5")
        assert evt.is_set()
        assert esp._ack_results.get(42) == "OK"

    def test_version_line_parsing(self):
        esp = ESP32Controller(simulation_mode=True)
        esp._parse_incoming_line("$VER:JARVIS-ESP32-v1.2.0*00")
        assert esp.firmware_version == "JARVIS-ESP32-v1.2.0"

    def test_malformed_lines_ignored(self):
        esp = ESP32Controller(simulation_mode=True)
        # Should not raise exception
        esp._parse_incoming_line("")
        esp._parse_incoming_line("garbage\x00\xff")
        esp._parse_incoming_line("$TEL:bad:packet*00")
        esp._parse_incoming_line("$ACK:invalid*00")

    def test_shutdown_simulation(self):
        esp = ESP32Controller(simulation_mode=True)
        esp.shutdown()
        assert esp.running is False
