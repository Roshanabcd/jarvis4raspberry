"""
JARVIS OS Robot Control API
Provides endpoints for motor control, servo positions, and emergency stops.
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional
from tools.robotics.controller import robot

robot_router = APIRouter(prefix="/robot", tags=["Robotics"])


class ServoRequest(BaseModel):
    channel: int = Field(..., ge=0, le=15, description="PCA9685 servo channel 0-15")
    angle: int = Field(..., ge=0, le=180, description="Angle in degrees (0-180)")


class MoveRequest(BaseModel):
    speed: int = Field(100, ge=0, le=100, description="Speed percentage 0-100")


@robot_router.get("/state")
def get_state():
    return {
        "status": "ok",
        "state": robot.state,
        "simulated": getattr(robot, "simulated", True),
    }


@robot_router.post("/forward")
def forward(speed: int = 100):
    robot.forward(speed)
    return {"status": "moving", "direction": "forward", "speed": speed}


@robot_router.post("/backward")
def backward(speed: int = 100):
    robot.backward(speed)
    return {"status": "moving", "direction": "backward", "speed": speed}


@robot_router.post("/left")
def turn_left(speed: int = 100):
    robot.turn_left(speed)
    return {"status": "turning", "direction": "left", "speed": speed}


@robot_router.post("/right")
def turn_right(speed: int = 100):
    robot.turn_right(speed)
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
def set_servo(req: Optional[ServoRequest] = None, channel: Optional[int] = None, angle: Optional[int] = None):
    # Support both JSON body and query parameters for flexibility
    ch = req.channel if req else (channel if channel is not None else 0)
    deg = req.angle if req else (angle if angle is not None else 90)
    robot.set_servo(ch, deg)
    return {"status": "ok", "channel": ch, "angle": deg}
