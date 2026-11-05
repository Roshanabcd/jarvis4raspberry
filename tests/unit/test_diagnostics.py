"""
Unit Tests for System Diagnostics and Hardware Metric Reporting.
"""

import pytest
from hardware.raspberry_pi.rpi_info import get_system_status, get_cpu_temp
from hardware.raspberry_pi.diagnostics import Diagnostics


class TestSystemDiagnostics:
    def test_system_status_metric_aliases(self):
        stat = get_system_status()
        # Verify both canonical and backward-compatible alias keys are present
        assert "temp_c" in stat
        assert "cpu_temp_c" in stat
        assert stat["temp_c"] == stat["cpu_temp_c"]

        assert "ram_used_mb" in stat
        assert "memory_used_mb" in stat
        assert stat["ram_used_mb"] == stat["memory_used_mb"]
        assert stat["ram_used_mb"] > 0

        assert "ram_total_mb" in stat
        assert "memory_total_mb" in stat
        assert stat["ram_total_mb"] == stat["memory_total_mb"]
        assert stat["ram_total_mb"] > 0

        assert "disk_pct" in stat
        assert "disk_used_percent" in stat
        assert stat["disk_pct"] == stat["disk_used_percent"]
        assert stat["disk_pct"] > 0

    def test_cpu_temp_positive(self):
        temp = get_cpu_temp()
        assert temp is not None
        assert 10.0 <= temp <= 100.0  # Realistic thermal range for Pi 5

    def test_full_diagnostics_suite(self):
        diag = Diagnostics()
        report = diag.run_full_diagnostics()
        assert report["all_passed"] is True
        checks = report["checks"]
        assert checks["python_version"]["passed"] is True
        assert checks["storage"]["passed"] is True
        assert checks["network"]["passed"] is True
        assert checks["db_accessible"]["passed"] is True
