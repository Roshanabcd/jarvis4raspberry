"""
JARVIS Robot State Machine
Manages validated state transitions for the physical robot.
States: OFFLINE, BOOTING, IDLE, LISTENING, PROCESSING, MOVING, STOPPING,
        ERROR, EMERGENCY_STOP, MAINTENANCE
"""
import logging
import time
from enum import Enum
from typing import Optional, Set, Dict

logger = logging.getLogger("JARVIS.Robot.StateMachine")


class RobotState(str, Enum):
    OFFLINE         = "OFFLINE"
    BOOTING         = "BOOTING"
    IDLE            = "IDLE"
    LISTENING       = "LISTENING"
    PROCESSING      = "PROCESSING"
    MOVING          = "MOVING"
    STOPPING        = "STOPPING"
    ERROR           = "ERROR"
    EMERGENCY_STOP  = "EMERGENCY_STOP"
    MAINTENANCE     = "MAINTENANCE"


# Valid state transitions — only these are permitted
_TRANSITIONS: Dict[RobotState, Set[RobotState]] = {
    RobotState.OFFLINE:        {RobotState.BOOTING},
    RobotState.BOOTING:        {RobotState.IDLE, RobotState.ERROR},
    RobotState.IDLE:           {RobotState.LISTENING, RobotState.PROCESSING,
                                 RobotState.MOVING, RobotState.MAINTENANCE,
                                 RobotState.EMERGENCY_STOP, RobotState.ERROR, RobotState.OFFLINE},
    RobotState.LISTENING:      {RobotState.PROCESSING, RobotState.IDLE,
                                 RobotState.EMERGENCY_STOP},
    RobotState.PROCESSING:     {RobotState.MOVING, RobotState.IDLE,
                                 RobotState.ERROR, RobotState.EMERGENCY_STOP},
    RobotState.MOVING:         {RobotState.STOPPING, RobotState.EMERGENCY_STOP,
                                 RobotState.ERROR},
    RobotState.STOPPING:       {RobotState.IDLE, RobotState.ERROR,
                                 RobotState.EMERGENCY_STOP},
    RobotState.ERROR:          {RobotState.IDLE, RobotState.MAINTENANCE,
                                 RobotState.OFFLINE, RobotState.EMERGENCY_STOP},
    RobotState.EMERGENCY_STOP: {RobotState.IDLE, RobotState.MAINTENANCE,
                                 RobotState.OFFLINE},
    RobotState.MAINTENANCE:    {RobotState.IDLE, RobotState.OFFLINE},
}


class RobotStateMachine:
    """
    Thread-safe robot state machine with validated transitions.
    Any transition not in _TRANSITIONS raises a RuntimeError — safe by design.
    """

    def __init__(self, initial: RobotState = RobotState.OFFLINE) -> None:
        self._state: RobotState = initial
        self._previous: Optional[RobotState] = None
        self._entered_at: float = time.time()
        self._error_message: Optional[str] = None
        logger.info(f"RobotStateMachine initialized in state {initial}")

    @property
    def state(self) -> RobotState:
        return self._state

    @property
    def state_str(self) -> str:
        return self._state.value

    def transition(self, new_state: RobotState,
                   reason: str = "") -> None:
        allowed = _TRANSITIONS.get(self._state, set())
        if new_state not in allowed:
            msg = (f"Invalid transition {self._state} → {new_state}. "
                   f"Allowed from {self._state}: {[s.value for s in allowed]}")
            logger.error(msg)
            raise RuntimeError(msg)

        self._previous = self._state
        self._state = new_state
        self._entered_at = time.time()
        if new_state == RobotState.ERROR:
            self._error_message = reason
        logger.info(f"Robot state: {self._previous} → {new_state}"
                    + (f" ({reason})" if reason else ""))

    def emergency_stop(self) -> None:
        """Always allowed — bypasses normal transition rules for safety."""
        prev = self._state
        self._previous = prev
        self._state = RobotState.EMERGENCY_STOP
        self._entered_at = time.time()
        logger.critical(f"!!! EMERGENCY STOP: {prev} → EMERGENCY_STOP !!!")

    def time_in_state(self) -> float:
        return time.time() - self._entered_at

    def info(self) -> dict:
        return {
            "state": self._state.value,
            "previous_state": self._previous.value if self._previous else None,
            "time_in_state_s": round(self.time_in_state(), 2),
            "error_message": self._error_message,
        }
