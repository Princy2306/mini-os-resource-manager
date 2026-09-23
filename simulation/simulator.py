from typing import List, Dict, Optional, Any
from models.pcb import PCB, ProcessState

# --- Step 4 Additions ---
from io_sim.io_manager import IOManager
from io_sim.process_io import ProcessIOManager

class OSSimulator:
    """Central OS Simulation Engine Core and Process Registry."""
    
    def __init__(self):
        # Deterministic simulation clock
        self.current_time: int = 0
        
        # Registry mapping process ID to PCB object
        self._registry: Dict[int, PCB] = {}
        
        # Configured CPU Scheduler
        self.scheduler: Optional[Any] = None
        
        # I/O Subsystem
        self.io_manager = IOManager()
        self.process_io = ProcessIOManager(self.io_manager)

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
        Also advances the I/O subsystem and updates any processes waiting on I/O.
        """
        self.current_time += 1
        self.io_manager.advance_time()
        self.process_io.update_processes()

    def set_scheduler(self, scheduler: Any) -> None:
        """
        Attaches a CPU scheduling algorithm to the simulator.
        """
        self.scheduler = scheduler

    def get_next_process(self) -> Optional[PCB]:
        """
        Asks the configured scheduler to select the next runnable process.
        Filters for eligible processes (READY, arrived, not waiting/terminated).
        """
        if self.scheduler is None:
            raise RuntimeError("Cannot get next process: No CPU scheduler is configured.")

        # Filter for processes that are actively eligible to run
        eligible_processes = [
            pcb for pcb in self._registry.values()
            if pcb.state == ProcessState.READY
            and pcb.arrival_time <= self.current_time
        ]

        if not eligible_processes:
            return None

        # Prefer the incremental interface from recent scheduler modifications
        if hasattr(self.scheduler, 'select_next_process'):
            return self.scheduler.select_next_process(eligible_processes, self.current_time)
            
        # Fallback for older monolithic get_next_process if it exists
        if hasattr(self.scheduler, 'get_next_process'):
            return self.scheduler.get_next_process(eligible_processes, self.current_time)

        # Adapter for original monolithic schedulers
        scheduler_name = self.scheduler.__class__.__name__
        if "SJF" in scheduler_name:
            return min(eligible_processes, key=lambda p: (p.cpu_burst_time, p.arrival_time))
        elif "Priority" in scheduler_name:
            return min(eligible_processes, key=lambda p: (p.priority, p.arrival_time))
        else:
            # FCFS fallback
            return min(eligible_processes, key=lambda p: (p.arrival_time, p.pid))

    def tick(self) -> None:
        """
        Executes exactly 1 CPU time unit per tick.
        Handles process admission, scheduling, execution, and termination.
        """
        # 1. Admit new arrivals
        for pcb in self._registry.values():
            if pcb.state == ProcessState.NEW and pcb.arrival_time <= self.current_time:
                pcb.state = ProcessState.READY
                
        # 2. To allow schedulers to make decisions (including preemption), 
        # if a process is RUNNING, we temporarily mark it READY so it appears in the eligible list.
        # Note: If a process transitioned to WAITING (via I/O request), it will safely be ignored here.
        active_process = None
        for pcb in self._registry.values():
            if pcb.state == ProcessState.RUNNING:
                active_process = pcb
                pcb.state = ProcessState.READY
                
        # 3. Ask scheduler for the next process
        next_process = self.get_next_process()
        
        # 4. Handle CPU idle
        if next_process is None:
            # Restore the active process state if it wasn't preempted but get_next_process returned None
            if active_process is not None and active_process.remaining_cpu_time > 0 and active_process.state == ProcessState.READY:
                active_process.state = ProcessState.RUNNING
            self.advance_time()
            return
            
        # 5. Execute the selected process
        if next_process.start_time is None:
            next_process.start_time = self.current_time
            
        next_process.state = ProcessState.RUNNING
        next_process.remaining_cpu_time -= 1
        
        # 6. Advance simulation clock (this also advances I/O)
        self.advance_time()
        
        # 7. Check for termination
        if next_process.remaining_cpu_time == 0:
            next_process.state = ProcessState.TERMINATED
            next_process.completion_time = self.current_time