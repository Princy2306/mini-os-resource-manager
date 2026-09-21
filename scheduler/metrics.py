from typing import List
from models.pcb import PCB, ProcessState, TimelineEvent

class SchedulingMetrics:
    """Calculates standard OS scheduling metrics from simulation results."""
    
    def __init__(self, processes: List[PCB], timeline: List[TimelineEvent]):
        # Only consider processes that have completed their execution
        self.completed_processes = [p for p in processes if p.state == ProcessState.TERMINATED]
        self.timeline = timeline

    @property
    def num_completed(self) -> int:
        return len(self.completed_processes)

    @property
    def total_elapsed_time(self) -> int:
        """Total time from t=0 to the end of the last timeline event."""
        if not self.timeline:
            return 0
        return max(event.end_time for event in self.timeline)

    @property
    def avg_waiting_time(self) -> float:
        if self.num_completed == 0:
            return 0.0
        total_wait = sum(p.waiting_time for p in self.completed_processes if p.waiting_time is not None)
        return total_wait / self.num_completed

    @property
    def avg_turnaround_time(self) -> float:
        if self.num_completed == 0:
            return 0.0
        total_turnaround = sum(p.turnaround_time for p in self.completed_processes if p.turnaround_time is not None)
        return total_turnaround / self.num_completed

    @property
    def avg_response_time(self) -> float:
        if self.num_completed == 0:
            return 0.0
        total_response = sum(p.response_time for p in self.completed_processes if p.response_time is not None)
        return total_response / self.num_completed

    @property
    def cpu_utilization(self) -> float:
        """Percentage of time the CPU was busy executing processes."""
        elapsed = self.total_elapsed_time
        if elapsed == 0:
            return 0.0
            
        total_busy_time = sum(event.end_time - event.start_time for event in self.timeline)
        return (total_busy_time / elapsed) * 100.0

    @property
    def throughput(self) -> float:
        """Number of processes completed per unit of time."""
        elapsed = self.total_elapsed_time
        if elapsed == 0:
            return 0.0
        return self.num_completed / elapsed