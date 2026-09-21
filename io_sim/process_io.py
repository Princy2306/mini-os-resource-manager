from typing import Dict
from models.pcb import PCB, ProcessState
from io_sim.io_request import IODevice, IORequest
from io_sim.io_manager import IOManager

class ProcessIOManager:
    """Bridges OS processes (PCBs) with the I/O simulation subsystem."""
    
    def __init__(self, io_manager: IOManager):
        self.io_manager = io_manager
        
        # Maps process IDs to their PCB objects for state updates
        self.process_map: Dict[int, PCB] = {}
        
        # Tracks how many completed requests we have already processed
        # to avoid transitioning a process multiple times for the same I/O.
        self._last_processed_idx: int = 0

    def request_io(self, pcb: PCB, device: IODevice, duration: int) -> IORequest:
        """
        Submits an I/O request for a running process and transitions it to a WAITING state.
        """
        if pcb.state != ProcessState.RUNNING:
            raise ValueError(f"Process {pcb.pid} must be in RUNNING state to request I/O. Currently: {pcb.state.name}")
            
        # Create and submit the request to the IO subsystem
        request = IORequest(process_id=pcb.pid, device=device, duration=duration)
        self.io_manager.submit_request(request)
        
        # Track the PCB and update its state
        self.process_map[pcb.pid] = pcb
        pcb.state = ProcessState.WAITING
        
        return request

    def update_processes(self) -> None:
        """
        Inspects recently completed I/O requests and transitions their 
        corresponding waiting processes back to the READY state.
        """
        completed_requests = self.io_manager.get_completed_requests()
        
        # Process only the newly completed requests since our last check
        for i in range(self._last_processed_idx, len(completed_requests)):
            req = completed_requests[i]
            pcb = self.process_map.get(req.process_id)
            
            if pcb is not None and pcb.state == ProcessState.WAITING:
                pcb.state = ProcessState.READY
                
        self._last_processed_idx = len(completed_requests)