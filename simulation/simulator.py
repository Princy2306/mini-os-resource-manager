from typing import List, Dict
from models.pcb import PCB

class OSSimulator:
    """Central OS Simulation Engine Core and Process Registry."""
    
    def __init__(self):
        # Deterministic simulation clock
        self.current_time: int = 0
        
        # Registry mapping process ID to PCB object
        self._registry: Dict[int, PCB] = {}

    def add_process(self, pcb: PCB) -> None:
        """
        Registers a new process in the simulation.
        Retains the current state of the provided PCB.
        Raises ValueError if the PID already exists.
        """
        if pcb.pid in self._registry:
            raise ValueError(f"Process with PID {pcb.pid} already exists.")
        
        self._registry[pcb.pid] = pcb

    def get_process(self, pid: int) -> PCB:
        """
        Retrieves a registered process by its PID.
        Raises KeyError if the PID is not found in the registry.
        """
        if pid not in self._registry:
            raise KeyError(f"Process with PID {pid} not found in the registry.")
            
        return self._registry[pid]

    def get_all_processes(self) -> List[PCB]:
        """
        Returns all registered processes in deterministic PID order.
        """
        # Sort by PID to ensure deterministic behavior across simulations
        sorted_pids = sorted(self._registry.keys())
        return [self._registry[pid] for pid in sorted_pids]

    def advance_time(self) -> None:
        """
        Advances the simulation clock by exactly one unit.
        """
        self.current_time += 1