"""
JARVIS OS Robot Control API
Provides endpoints for motor control, servo positions, and emergency stops.
Enforces safety gates: actuators must be armed, emergency-stop must not be active.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from tools.robotics.controller import robot

robot_router = APIRouter(prefix="/robot", tags=["Robotics"])


class ServoRequest(BaseModel):
    channel: int = Field(..., ge=0, le=15, description="PCA9685 servo channel 0-15")
    angle: int = Field(..., ge=0, le=180, description="Angle in degrees (0-180)")


class MoveRequest(BaseModel):
    speed: int = Field(50, ge=0, le=100, description="Speed percentage 0-100")


@robot_router.get("/state")
def get_state():
    return {
        "status": "ok",
        "state": robot.state,
        "armed": getattr(robot, "armed", False),
        "emergency_stopped": getattr(robot, "is_emergency_stopped", False),
        "simulated": getattr(robot, "simulated", True),
    }


@robot_router.post("/arm")
def arm():
    res = robot.arm()
    if res.get("status") != "ok":
        raise HTTPException(status_code=400, detail=res.get("error", "Failed to arm robot"))
    return {"status": "ok", "armed": True}


@robot_router.post("/disarm")
def disarm():
    res = robot.disarm()
    return {"status": "ok", "armed": False}


@robot_router.post("/clear_estop")
def clear_estop():
    res = robot.clear_emergency_stop()
    return {"status": "ok", "message": "Emergency stop cleared", "armed": res.get("armed", False)}


@robot_router.post("/forward")
def forward(speed: int = Query(50, ge=0, le=100)):
    success = robot.forward(speed)
    if not success:
        reason = "Emergency stop active" if robot.is_emergency_stopped else "Actuators disarmed"
        raise HTTPException(status_code=400, detail=f"Cannot move forward: {reason}")
    return {"status": "moving", "direction": "forward", "speed": speed}


@robot_router.post("/backward")
def backward(speed: int = Query(50, ge=0, le=100)):
    success = robot.backward(speed)
    if not success:
        reason = "Emergency stop active" if robot.is_emergency_stopped else "Actuators disarmed"
        raise HTTPException(status_code=400, detail=f"Cannot move backward: {reason}")
    return {"status": "moving", "direction": "backward", "speed": speed}


@robot_router.post("/left")
def turn_left(speed: int = Query(40, ge=0, le=100)):
    success = robot.turn_left(speed)
    if not success:
        reason = "Emergency stop active" if robot.is_emergency_stopped else "Actuators disarmed"
        raise HTTPException(status_code=400, detail=f"Cannot turn left: {reason}")
    return {"status": "turning", "direction": "left", "speed": speed}


@robot_router.post("/right")
def turn_right(speed: int = Query(40, ge=0, le=100)):
    success = robot.turn_right(speed)
    if not success:
        reason = "Emergency stop active" if robot.is_emergency_stopped else "Actuators disarmed"
        raise HTTPException(status_code=400, detail=f"Cannot turn right: {reason}")
    return {"status": "turning", "direction": "right", "speed": speed}


@robot_router.post("/stop")
def stop():
    robot.stop()
    return {"status": "stopped"}


@robot_router.post("/estop")
def estop():
    robot.emergency_stop()
    return {"status": "emergency_stop_activated"}


@robot_router.post("/servo")
def set_servo(
    req: Optional[ServoRequest] = None,
    channel: Optional[int] = Query(None, ge=0, le=15),
    angle: Optional[int] = Query(None, ge=0, le=180),
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
        robot.set_servo(ch, deg)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Servo control failed: {exc}")

    return {"status": "ok", "channel": ch, "angle": deg}
