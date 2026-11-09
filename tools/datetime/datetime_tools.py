"""
JARVIS Date and Time Tools
Query real local clock, system timezone, date differences, and timestamp formatting.
"""
from datetime import datetime, timezone, date
import time
from typing import Any, Dict, Optional


class DateTimeTools:
    """Deterministic date and time querying using local system clock."""

    @staticmethod
    def get_current_time() -> Dict[str, Any]:
        """Retrieve current local time with timezone information."""
        now = datetime.now().astimezone()
        return {
            "iso": now.isoformat(),
            "time": now.strftime("%H:%M:%S"),
            "formatted": now.strftime("%I:%M:%S %p"),
            "timezone": str(now.tzname()),
            "timestamp": now.timestamp(),
        }

    @staticmethod
    def get_current_date() -> Dict[str, Any]:
        """Retrieve current local date and day of week."""
        now = datetime.now().astimezone()
        return {
            "date": now.strftime("%Y-%m-%d"),
            "formatted": now.strftime("%A, %B %d, %Y"),
            "day_of_week": now.strftime("%A"),
            "day": now.day,
            "month": now.month,
            "year": now.year,
            "iso": now.date().isoformat(),
        }

    @staticmethod
    def get_timezone() -> Dict[str, Any]:
        """Retrieve system local timezone details."""
        now = datetime.now().astimezone()
        offset_sec = now.utcoffset().total_seconds() if now.utcoffset() else 0
        hours = int(offset_sec // 3600)
        minutes = int((offset_sec % 3600) // 60)
        offset_str = f"UTC{hours:+03d}:{minutes:02d}"
        return {
            "timezone": str(now.tzname()),
            "utc_offset": offset_str,
            "offset_seconds": offset_sec,
            "is_dst": bool(time.localtime().tm_isdst > 0),
        }

    @staticmethod
    def calculate_date_difference(start_date: str, end_date: str) -> Dict[str, Any]:
        """Calculate difference between two dates formatted as YYYY-MM-DD."""
        try:
            d1 = date.fromisoformat(start_date.strip())
            d2 = date.fromisoformat(end_date.strip())
            diff = d2 - d1
            return {
                "start_date": str(d1),
                "end_date": str(d2),
                "days": diff.days,
                "weeks": round(diff.days / 7.0, 1),
                "success": True,
            }
        except Exception as e:
            return {
                "start_date": start_date,
                "end_date": end_date,
                "error": f"Invalid date format (expected YYYY-MM-DD): {e}",
                "success": False,
            }

    @staticmethod
    def format_timestamp(ts: Optional[float] = None, fmt: str = "%Y-%m-%d %H:%M:%S") -> Dict[str, Any]:
        """Format an epoch timestamp into a string."""
        epoch = ts if ts is not None else time.time()
        dt = datetime.fromtimestamp(epoch).astimezone()
        try:
            formatted = dt.strftime(fmt)
            return {
                "timestamp": epoch,
                "formatted": formatted,
                "format": fmt,
                "timezone": str(dt.tzname()),
                "success": True,
            }
        except Exception as e:
            return {
                "timestamp": epoch,
                "error": f"Invalid format string: {e}",
                "success": False,
            }


datetime_tools = DateTimeTools()
