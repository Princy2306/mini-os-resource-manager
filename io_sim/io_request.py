from enum import Enum
from dataclasses import dataclass, field
from typing import Optional

class IODevice(Enum):
    """Enumeration of available I/O devices in the simulator."""
    DISK = "DISK"
    KEYBOARD = "KEYBOARD"
    NETWORK = "NETWORK"
    PRINTER = "PRINTER"

@dataclass
class IORequest:
    """Represents a single I/O operation requested by a process."""
    process_id: int
    device: IODevice
    duration: int
    
    # Dynamic fields
    remaining_time: int = field(init=False)
    start_time: Optional[int] = None
    completion_time: Optional[int] = None

    def __post_init__(self) -> None:
        """Validates inputs and initializes the remaining time."""
        if self.duration <= 0:
            raise ValueError("I/O request duration must be a positive integer.")
        self.remaining_time = self.duration

    def advance(self) -> None:
        """Advances the I/O request by one time unit."""
        if self.remaining_time > 0:
            self.remaining_time -= 1

    @property
    def is_complete(self) -> bool:
        """Returns True if the I/O operation has finished."""
        return self.remaining_time == 0