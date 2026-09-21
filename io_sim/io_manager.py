from typing import List
from io_sim.io_request import IORequest

class IOManager:
    """Manages the simulation of I/O operations over time."""
    
    def __init__(self):
        self.current_time: int = 0
        self.active_requests: List[IORequest] = []
        self.completed_requests: List[IORequest] = []

    def submit_request(self, request: IORequest) -> None:
        """Submits an I/O request to be processed, setting its start time."""
        request.start_time = self.current_time
        self.active_requests.append(request)

    def advance_time(self) -> None:
        """
        Advances the simulation by one time unit.
        Updates all active I/O requests and moves completed ones to the tracking list.
        """
        self.current_time += 1
        
        still_active = []
        for req in self.active_requests:
            req.advance()
            
            if req.is_complete:
                req.completion_time = self.current_time
                self.completed_requests.append(req)
            else:
                still_active.append(req)
                
        # Keep only the requests that haven't finished yet
        self.active_requests = still_active

    def get_active_requests(self) -> List[IORequest]:
        """Returns a list of all currently running I/O requests."""
        return self.active_requests

    def get_completed_requests(self) -> List[IORequest]:
        """Returns a list of all finished I/O requests."""
        return self.completed_requests

    def has_active_io(self, process_id: int) -> bool:
        """Checks if a specific process is currently waiting on an active I/O request."""
        for req in self.active_requests:
            if req.process_id == process_id:
                return True
        return False