"""
JARVIS OS Robot Control API
Provides endpoints for motor control, servo positions, and emergency stops.
Enforces safety gates: actuators must be armed, emergency-stop must not be
active, and HTTP actuation must be deliberately enabled and authorized.
"""

from typing import Any, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field

from config.config_manager import config
from tools.identity.user_manager import user_manager

robot_router = APIRouter(prefix="/robot", tags=["Robotics"])


class ServoRequest(BaseModel):
    channel: int = Field(..., ge=0, le=15, description="PCA9685 servo channel 0-15")
    angle: int = Field(..., ge=0, le=180, description="Angle in degrees (0-180)")


class MoveRequest(BaseModel):
    speed: int = Field(50, ge=0, le=100, description="Speed percentage 0-100")


ACTUATION_CONFIRMATION_VALUE = "physical-motion"


def get_robot() -> Any:
    """Resolve the controller lazily so router import never opens hardware."""
    from tools.robotics.controller import get_robot as resolve_robot

    return resolve_robot()


def _http_actuation_enabled() -> bool:
    robot_cfg = config.get("robot", {}) if hasattr(config, "get") else {}
    return bool((robot_cfg or {}).get("http_actuation_enabled", False))


def require_http_actuation_authorization(
    x_jarvis_admin_pin: Optional[str] = Header(default=None),
    x_jarvis_actuation_confirmation: Optional[str] = Header(default=None),
) -> Any:
    """Authorize one potentially physical HTTP action.

    Arm, motion, servo, and e-stop-clear operations require all of:
    an explicit configuration opt-in, a fresh administrator PIN in a header,
    and an acknowledgement string.  Stop, e-stop, and disarm remain available
    as safety actions.  The PIN is never accepted in a query string or logged.
    """
    if not _http_actuation_enabled():
        raise HTTPException(
            status_code=403,
            detail="HTTP actuator control is disabled by configuration."
        )
    if x_jarvis_actuation_confirmation != ACTUATION_CONFIRMATION_VALUE:
        raise HTTPException(
            status_code=428,
            detail="Explicit physical-motion confirmation is required."
        )
    if not x_jarvis_admin_pin:
        raise HTTPException(status_code=401, detail="Fresh administrator PIN is required for physical actuation.")

    valid, message = user_manager.verify_admin_pin(x_jarvis_admin_pin)
    if not valid:
        raise HTTPException(status_code=401, detail=f"Administrator verification failed: {message}")
    return get_robot()


@robot_router.get("/state")
def get_state(robot: Any = Depends(get_robot)):
    return {
        "status": "ok",
        "state": robot.state,
        "armed": getattr(robot, "armed", False),
        "emergency_stopped": getattr(robot, "is_emergency_stopped", False),
        "simulated": getattr(robot, "simulated", True),
        "http_actuation_enabled": _http_actuation_enabled(),
    }


@robot_router.post("/arm")
def arm(robot: Any = Depends(require_http_actuation_authorization)):
    res = robot.arm()
    if res.get("status") != "ok":
        raise HTTPException(status_code=400, detail=res.get("error", "Failed to arm robot"))
    return {"status": "ok", "armed": True}


@robot_router.post("/disarm")
def disarm(robot: Any = Depends(get_robot)):
    res = robot.disarm()
    return {"status": "ok", "armed": False}


@robot_router.post("/clear_estop")
def clear_estop(robot: Any = Depends(require_http_actuation_authorization)):
    res = robot.clear_emergency_stop()
    return {"status": "ok", "message": "Emergency stop cleared", "armed": res.get("armed", False)}


@robot_router.post("/forward")
def forward(
    speed: int = Query(50, ge=0, le=100),
    robot: Any = Depends(require_http_actuation_authorization),
):
    success = robot.forward(speed)
    if not success:
        reason = "Emergency stop active" if robot.is_emergency_stopped else "Actuators disarmed"
        raise HTTPException(status_code=400, detail=f"Cannot move forward: {reason}")
    return {"status": "moving", "direction": "forward", "speed": speed}


@robot_router.post("/backward")
def backward(
    speed: int = Query(50, ge=0, le=100),
    robot: Any = Depends(require_http_actuation_authorization),
):
    success = robot.backward(speed)
    if not success:
        reason = "Emergency stop active" if robot.is_emergency_stopped else "Actuators disarmed"
        raise HTTPException(status_code=400, detail=f"Cannot move backward: {reason}")
    return {"status": "moving", "direction": "backward", "speed": speed}


@robot_router.post("/left")
def turn_left(
    speed: int = Query(40, ge=0, le=100),
    robot: Any = Depends(require_http_actuation_authorization),
):
    success = robot.turn_left(speed)
    if not success:
        reason = "Emergency stop active" if robot.is_emergency_stopped else "Actuators disarmed"
        raise HTTPException(status_code=400, detail=f"Cannot turn left: {reason}")
    return {"status": "turning", "direction": "left", "speed": speed}


@robot_router.post("/right")
def turn_right(
    speed: int = Query(40, ge=0, le=100),
    robot: Any = Depends(require_http_actuation_authorization),
):
    success = robot.turn_right(speed)
    if not success:
        reason = "Emergency stop active" if robot.is_emergency_stopped else "Actuators disarmed"
        raise HTTPException(status_code=400, detail=f"Cannot turn right: {reason}")
    return {"status": "turning", "direction": "right", "speed": speed}


@robot_router.post("/stop")
def stop(robot: Any = Depends(get_robot)):
    robot.stop()
    return {"status": "stopped"}


@robot_router.post("/estop")
def estop(robot: Any = Depends(get_robot)):
    robot.emergency_stop()
    return {"status": "emergency_stop_activated"}


@robot_router.post("/servo")
def set_servo(
    req: Optional[ServoRequest] = None,
    channel: Optional[int] = Query(None, ge=0, le=15),
    angle: Optional[int] = Query(None, ge=0, le=180),
    robot: Any = Depends(require_http_actuation_authorization),
):
    if req is not None:
        ch = req.channel
        deg = req.angle
    else:
        ch = channel if channel is not None else 0
        deg = angle if angle is not None else 90

    if not (0 <= ch <= 15):
        raise HTTPException(status_code=422, detail="Channel must be between 0 and 15")
    if not (0 <= deg <= 180):
        raise HTTPException(status_code=422, detail="Angle must be between 0 and 180")

    try:
        moved = robot.set_servo(ch, deg)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Servo control failed: {exc}")

    if not moved:
        reason = "Emergency stop active" if getattr(robot, "is_emergency_stopped", False) else "Actuators disarmed"
        raise HTTPException(status_code=400, detail=f"Cannot move servo: {reason}")

    return {"status": "ok", "channel": ch, "angle": deg}
