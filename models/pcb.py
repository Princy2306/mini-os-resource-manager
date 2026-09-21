from enum import Enum
from dataclasses import dataclass
from typing import Optional

class ProcessState(Enum):
    NEW = "NEW"
    READY = "READY"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    TERMINATED = "TERMINATED"

@dataclass
class PCB:
    """Process Control Block representing an OS process."""
    pid: int
    arrival_time: int
    cpu_burst_time: int
    priority: int = 0
    
    # Dynamic state
    remaining_cpu_time: int = -1  # Initialized dynamically in __post_init__
    state: ProcessState = ProcessState.NEW
    
    # Tracking metrics
    start_time: Optional[int] = None
    completion_time: Optional[int] = None

    def __post_init__(self) -> None:
        """Set initial remaining time equal to total burst time."""
        if self.remaining_cpu_time == -1:
            self.remaining_cpu_time = self.cpu_burst_time

    @property
    def response_time(self) -> Optional[int]:
        """Time from arrival to first execution."""
        if self.start_time is None:
            return None
        return self.start_time - self.arrival_time

    @property
    def turnaround_time(self) -> Optional[int]:
        """Total time from arrival to completion."""
        if self.completion_time is None:
            return None
        return self.completion_time - self.arrival_time

    @property
    def waiting_time(self) -> Optional[int]:
        """Total time spent waiting in the ready queue."""
        if self.turnaround_time is None:
            return None
        return self.turnaround_time - self.cpu_burst_time