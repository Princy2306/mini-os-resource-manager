from typing import List, Dict
from io_sim.io_request import IORequest, IODevice

class IOManager:
    """Manages the simulation of I/O operations and device queues over time."""
    
    def __init__(self):
        self.current_time: int = 0
        
        # Maps a device to the currently executing request
        self.active_requests: Dict[IODevice, IORequest] = {}
        
        # Maps a device to a FIFO list of waiting requests
        self.device_queues: Dict[IODevice, List[IORequest]] = {}
        
        # Tracks finished requests
        self.completed_requests: List[IORequest] = []

    def submit_request(self, request: IORequest) -> None:
        """
        Submits an I/O request. Starts immediately if the device is idle,
        otherwise places it in the device's FIFO queue.
        """
        device = request.device
        
        if device not in self.device_queues:
            self.device_queues[device] = []
            
        if device not in self.active_requests:
            # Device is free; start immediately
            request.start_time = self.current_time
            self.active_requests[device] = request
        else:
            # Device is busy; queue the request
            self.device_queues[device].append(request)

    def advance_time(self) -> None:
        """
        Advances the simulation by one time unit.
        Updates active requests, completes them if finished, and pulls 
        the next queued request onto the device if available.
        """
        self.current_time += 1
        
        # Iterate over a list of keys since we might mutate the dictionary
        for device in list(self.active_requests.keys()):
            req = self.active_requests[device]
            req.advance()
            
            if req.is_complete:
                req.completion_time = self.current_time
                self.completed_requests.append(req)
                del self.active_requests[device]
                
                # Check if there are queued requests waiting for this device
                if self.device_queues[device]:
                    next_req = self.device_queues[device].pop(0)
                    next_req.start_time = self.current_time
                    self.active_requests[device] = next_req

    def get_active_requests(self) -> List[IORequest]:
        """Returns a list of all currently executing I/O requests."""
        return list(self.active_requests.values())

    def get_completed_requests(self) -> List[IORequest]:
        """Returns a list of all finished I/O requests."""
        return self.completed_requests

    def has_active_io(self, process_id: int) -> bool:
        """Checks if a process is currently EXECUTING an I/O request."""
        return any(req.process_id == process_id for req in self.active_requests.values())

    def has_pending_io(self, process_id: int) -> bool:
        """Checks if a process is EXECUTING or QUEUED for an I/O request."""
        if self.has_active_io(process_id):
            return True
            
        for queue in self.device_queues.values():
            if any(req.process_id == process_id for req in queue):
                return True
                
        return False