import unittest

from models.pcb import PCB, ProcessState, TimelineEvent
from scheduler.schedulers import (
    FCFSScheduler,
    SJFScheduler,
    PriorityScheduler,
    RoundRobinScheduler,
)
class TestIncrementalSchedulers(unittest.TestCase):
    """Verifies that the new select_next_process interface behaves correctly."""

    def get_processes(self):
        return [
            PCB(pid=1, arrival_time=0, cpu_burst_time=4, priority=2),
            PCB(pid=2, arrival_time=1, cpu_burst_time=2, priority=1),
            PCB(pid=3, arrival_time=2, cpu_burst_time=6, priority=3),
        ]

    def test_fcfs_incremental(self):
        processes = self.get_processes()
        scheduler = FCFSScheduler([])
        
        # At t=0, only P1 arrived
        selected = scheduler.select_next_process([processes[0]], 0)
        self.assertEqual(selected.pid, 1)

        # At t=2, P1, P2, P3 are all eligible. P1 should still be chosen (earliest arrival)
        selected = scheduler.select_next_process(processes, 2)
        self.assertEqual(selected.pid, 1)

    def test_sjf_incremental(self):
        processes = self.get_processes()
        scheduler = SJFScheduler([])
        
        # P2 has shortest burst (2). 
        selected = scheduler.select_next_process(processes, 2)
        self.assertEqual(selected.pid, 2)

    def test_priority_incremental(self):
        processes = self.get_processes()
        scheduler = PriorityScheduler([])
        
        # P2 has highest priority (1)
        selected = scheduler.select_next_process(processes, 2)
        self.assertEqual(selected.pid, 2)

    def test_round_robin_incremental_state(self):
        """Verifies RR maintains its queue and respects quantum across multiple calls."""
        processes = self.get_processes()
        # Quantum = 2
        scheduler = RoundRobinScheduler([], quantum=2)
        
        # Tick 1: Only P1 is ready
        p1 = scheduler.select_next_process([processes[0]], 0)
        self.assertEqual(p1.pid, 1)
        
        # Tick 2: P1 and P2 are ready. P1 should continue (quantum not exhausted)
        p1_again = scheduler.select_next_process([processes[0], processes[1]], 1)
        self.assertEqual(p1_again.pid, 1)
        
        # Tick 3: Quantum reached! RR should rotate to P2. P3 arrived.
        p2 = scheduler.select_next_process(processes, 2)
        self.assertEqual(p2.pid, 2)
        
        # Tick 4: P2 continues
        p2_again = scheduler.select_next_process(processes, 3)
        self.assertEqual(p2_again.pid, 2)
        
        # Tick 5: P2 exhausted quantum. Next in internal queue is P3.
        p3 = scheduler.select_next_process(processes, 4)
        self.assertEqual(p3.pid, 3)