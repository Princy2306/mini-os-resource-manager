from typing import List
from models.pcb import PCB, ProcessState, TimelineEvent

class BaseScheduler:
    def __init__(self, processes: List[PCB]):
        self.processes = processes
        self.timeline: List[TimelineEvent] = []
        self.current_time = 0

    def _mark_start(self, process: PCB):
        """Records start time if this is the first time the process runs."""
        if process.start_time is None:
            process.start_time = self.current_time

    def _mark_completion(self, process: PCB):
        """Records completion and sets state to TERMINATED."""
        process.completion_time = self.current_time
        process.state = ProcessState.TERMINATED

    def run(self) -> List[TimelineEvent]:
        raise NotImplementedError("Subclasses must implement run()")


class FCFSScheduler(BaseScheduler):
    def run(self) -> List[TimelineEvent]:
        queue = sorted(self.processes, key=lambda p: p.arrival_time)
        
        for p in queue:
            if self.current_time < p.arrival_time:
                self.current_time = p.arrival_time
            
            p.state = ProcessState.RUNNING
            self._mark_start(p)
            start = self.current_time
            
            # Execute
            self.current_time += p.cpu_burst_time
            p.remaining_cpu_time = 0
            
            self._mark_completion(p)
            self.timeline.append(TimelineEvent(start, self.current_time, p.pid))
            
        return self.timeline


class SJFScheduler(BaseScheduler):
    def run(self) -> List[TimelineEvent]:
        unstarted = sorted(self.processes, key=lambda p: p.arrival_time)
        ready_queue: List[PCB] = []
        completed = 0
        n = len(self.processes)
        
        while completed < n:
            while unstarted and unstarted[0].arrival_time <= self.current_time:
                ready_queue.append(unstarted.pop(0))
                
            if not ready_queue:
                self.current_time = unstarted[0].arrival_time
                continue
                
            # Non-preemptive SJF: sort by burst time, then arrival time
            ready_queue.sort(key=lambda p: (p.cpu_burst_time, p.arrival_time))
            p = ready_queue.pop(0)
            
            p.state = ProcessState.RUNNING
            self._mark_start(p)
            start = self.current_time
            
            # Execute
            self.current_time += p.cpu_burst_time
            p.remaining_cpu_time = 0
            
            self._mark_completion(p)
            self.timeline.append(TimelineEvent(start, self.current_time, p.pid))
            completed += 1
            
        return self.timeline


class PriorityScheduler(BaseScheduler):
    def run(self) -> List[TimelineEvent]:
        unstarted = sorted(self.processes, key=lambda p: p.arrival_time)
        ready_queue: List[PCB] = []
        completed = 0
        n = len(self.processes)
        
        while completed < n:
            while unstarted and unstarted[0].arrival_time <= self.current_time:
                ready_queue.append(unstarted.pop(0))
                
            if not ready_queue:
                self.current_time = unstarted[0].arrival_time
                continue
                
            # Lower integer = higher priority
            ready_queue.sort(key=lambda p: (p.priority, p.arrival_time))
            p = ready_queue.pop(0)
            
            p.state = ProcessState.RUNNING
            self._mark_start(p)
            start = self.current_time
            
            # Execute
            self.current_time += p.cpu_burst_time
            p.remaining_cpu_time = 0
            
            self._mark_completion(p)
            self.timeline.append(TimelineEvent(start, self.current_time, p.pid))
            completed += 1
            
        return self.timeline


class RoundRobinScheduler(BaseScheduler):
    def __init__(self, processes: List[PCB], quantum: int):
        super().__init__(processes)
        self.quantum = quantum

    def run(self) -> List[TimelineEvent]:
        unstarted = sorted(self.processes, key=lambda p: p.arrival_time)
        ready_queue: List[PCB] = []
        completed = 0
        n = len(self.processes)
        
        if unstarted:
            self.current_time = unstarted[0].arrival_time
            while unstarted and unstarted[0].arrival_time <= self.current_time:
                ready_queue.append(unstarted.pop(0))

        while completed < n:
            if not ready_queue:
                self.current_time = unstarted[0].arrival_time
                while unstarted and unstarted[0].arrival_time <= self.current_time:
                    ready_queue.append(unstarted.pop(0))
                
            p = ready_queue.pop(0)
            p.state = ProcessState.RUNNING
            self._mark_start(p)
            start = self.current_time
            
            # Execute up to quantum
            execute_time = min(self.quantum, p.remaining_cpu_time)
            self.current_time += execute_time
            p.remaining_cpu_time -= execute_time
            
            self.timeline.append(TimelineEvent(start, self.current_time, p.pid))
            
            # Any newly arrived processes are queued BEFORE current process is re-added
            while unstarted and unstarted[0].arrival_time <= self.current_time:
                ready_queue.append(unstarted.pop(0))
                
            if p.remaining_cpu_time > 0:
                p.state = ProcessState.READY
                ready_queue.append(p)
            else:
                self._mark_completion(p)
                completed += 1
                
        return self.timeline