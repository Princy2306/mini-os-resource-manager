from typing import List, Dict, Tuple

class DeadlockManager:
    def __init__(self, total_resources: List[int]):
        self.total_resources = total_resources.copy()
        self.num_resources = len(total_resources)
        self.available = total_resources.copy()
        
        self.max_demand: Dict[str, List[int]] = {}
        self.allocation: Dict[str, List[int]] = {}
        self.need: Dict[str, List[int]] = {}

    # --- Helper Methods for Vector Math ---
    def _le(self, v1: List[int], v2: List[int]) -> bool:
        """Returns True if v1 <= v2 element-wise."""
        return all(x <= y for x, y in zip(v1, v2))

    def _add(self, v1: List[int], v2: List[int]) -> List[int]:
        """Adds two vectors element-wise."""
        return [x + y for x, y in zip(v1, v2)]

    def _sub(self, v1: List[int], v2: List[int]) -> List[int]:
        """Subtracts v2 from v1 element-wise."""
        return [x - y for x, y in zip(v1, v2)]

    # --- Core Operations ---
    def add_process(self, pid: str, max_demand: List[int], allocated: List[int]):
        if len(max_demand) != self.num_resources or len(allocated) != self.num_resources:
            raise ValueError("Resource vector size mismatch.")
            
        self.max_demand[pid] = max_demand.copy()
        self.allocation[pid] = allocated.copy()
        self.need[pid] = self._sub(max_demand, allocated)
        
        # Adjust available resources
        self.available = self._sub(self.available, allocated)

    def remove_process(self, pid: str):
        if pid in self.allocation:
            self.available = self._add(self.available, self.allocation[pid])
            del self.max_demand[pid]
            del self.allocation[pid]
            del self.need[pid]

    # --- Banker's Algorithm (Avoidance) ---
    def is_safe_state(self) -> Tuple[bool, List[str]]:
        """
        Determines if the system is in a SAFE state.
        Returns (is_safe, safe_sequence).
        """
        work = self.available.copy()
        finish = {pid: False for pid in self.allocation}
        safe_sequence: List[str] = []
        
        while len(safe_sequence) < len(self.allocation):
            allocated_this_round = False
            
            for pid, is_finished in finish.items():
                if not is_finished and self._le(self.need[pid], work):
                    # Pretend process finishes and releases its resources
                    work = self._add(work, self.allocation[pid])
                    finish[pid] = True
                    safe_sequence.append(pid)
                    allocated_this_round = True
                    
            if not allocated_this_round:
                # We looped through all processes but couldn't satisfy any.
                return False, []
                
        return True, safe_sequence

    def request_resources(self, pid: str, request: List[int]) -> bool:
        """
        Attempts to grant a resource request using Banker's Algorithm.
        Returns True if granted, False if denied (must wait).
        """
        if not self._le(request, self.need[pid]):
            raise ValueError(f"Request {request} exceeds maximum claim for {pid}.")
            
        if not self._le(request, self.available):
            return False # Must wait, resources not currently available
            
        # 1. Pretend to allocate (Trial)
        self.available = self._sub(self.available, request)
        self.allocation[pid] = self._add(self.allocation[pid], request)
        self.need[pid] = self._sub(self.need[pid], request)
        
        # 2. Run safety algorithm
        is_safe, _ = self.is_safe_state()
        
        if is_safe:
            return True # Commit allocation
            
        # 3. Rollback if UNSAFE
        self.available = self._add(self.available, request)
        self.allocation[pid] = self._sub(self.allocation[pid], request)
        self.need[pid] = self._add(self.need[pid], request)
        return False

    # --- Deadlock Detection ---
    def detect_deadlock(self, current_requests: Dict[str, List[int]]) -> List[str]:
        """
        Identifies processes that are currently deadlocked.
        Returns a list of deadlocked PIDs.
        """
        work = self.available.copy()
        finish = {pid: False for pid in self.allocation}
        
        # Processes with 0 allocation don't hold resources that can block others
        for pid, alloc in self.allocation.items():
            if all(x == 0 for x in alloc):
                finish[pid] = True

        while True:
            progress_made = False
            
            for pid, is_finished in finish.items():
                req = current_requests.get(pid, [0] * self.num_resources)
                if not is_finished and self._le(req, work):
                    # Process can finish
                    work = self._add(work, self.allocation[pid])
                    finish[pid] = True
                    progress_made = True
                    
            if not progress_made:
                break
                
        # Any process where Finish == False is deadlocked
        deadlocked_processes = [pid for pid, is_finished in finish.items() if not is_finished]
        return deadlocked_processes