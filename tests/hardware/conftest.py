"""Keep physical-device tests opt-in.

Running the ordinary regression suite must not open GPIO/I2C/serial interfaces,
move a servo, or issue motor frames.  A conscious operator can opt in with
``JARVIS_RUN_HARDWARE_TESTS=1`` during a cleared, supervised maintenance test.
"""

from __future__ import annotations

import os

import pytest


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    if os.environ.get("JARVIS_RUN_HARDWARE_TESTS") == "1":
        return

    reason = "Physical hardware tests require JARVIS_RUN_HARDWARE_TESTS=1."
    marker = pytest.mark.skip(reason=reason)
    for item in items:
        if "tests/hardware" in str(item.fspath) or "tests/hardware" in str(getattr(item, "path", "")):
            item.add_marker("hardware")
            item.add_marker(marker)
