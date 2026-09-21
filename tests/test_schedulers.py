import unittest
from models.pcb import PCB, ProcessState
from scheduler.schedulers import FCFSScheduler, SJFScheduler, PriorityScheduler, RoundRobinScheduler

class TestSchedulers(unittest.TestCase):
    
    def get_test_processes(self):
        """Returns a fresh set of processes for each test."""
        # P1: Arrives 0, Burst 5, Priority 2
        # P2: Arrives 1, Burst 3, Priority 1
        # P3: Arrives 2, Burst 1, Priority 3
        return [
            PCB(pid=1, arrival_time=0, cpu_burst_time=5, priority=2),
            PCB(pid=2, arrival_time=1, cpu_burst_time=3, priority=1),
            PCB(pid=3, arrival_time=2, cpu_burst_time=1, priority=3),
        ]

    def test_fcfs_scheduling(self):
        processes = self.get_test_processes()
        scheduler = FCFSScheduler(processes)
        timeline = scheduler.run()
        
        self.assertEqual([e.pid for e in timeline], [1, 2, 3])
        
        p1, p2, p3 = processes
        
        # P2 (Arrival 1, starts after P1 finishes at 5, finishes at 8)
        self.assertEqual(p2.start_time, 5)
        self.assertEqual(p2.completion_time, 8)
        self.assertEqual(p2.response_time, 4)   # 5 - 1
        self.assertEqual(p2.turnaround_time, 7) # 8 - 1
        self.assertEqual(p2.waiting_time, 4)    # 7 - 3

    def test_sjf_non_preemptive(self):
        processes = self.get_test_processes()
        scheduler = SJFScheduler(processes)
        timeline = scheduler.run()
        
        # P1 runs first (0-5). Then P3 is shortest (burst 1), then P2 (burst 3).
        self.assertEqual([e.pid for e in timeline], [1, 3, 2])
        
        p3 = processes[2]
        # P3 arrived at 2, started at 5, finished at 6
        self.assertEqual(p3.completion_time, 6)
        self.assertEqual(p3.waiting_time, 3) # (6-2) - 1

    def test_priority_non_preemptive(self):
        processes = self.get_test_processes()
        scheduler = PriorityScheduler(processes)
        timeline = scheduler.run()
        
        # P1 runs first. Then P2 (priority 1) beats P3 (priority 3).
        self.assertEqual([e.pid for e in timeline], [1, 2, 3])
        
        p2 = processes[1]
        self.assertEqual(p2.completion_time, 8)

    def test_round_robin(self):
        processes = self.get_test_processes()
        scheduler = RoundRobinScheduler(processes, quantum=2)
        timeline = scheduler.run()
        
        # Timeline Execution:
        # P1 (0-2), P2 (2-4), P3 (4-5) [completes], P1 (5-7), P2 (7-8) [completes], P1 (8-9) [completes]
        self.assertEqual([e.pid for e in timeline], [1, 2, 3, 1, 2, 1])

        p1, p2, p3 = processes
        
        self.assertEqual(p1.completion_time, 9)
        self.assertEqual(p2.completion_time, 8)
        self.assertEqual(p3.completion_time, 5)
        
        # Check P1 turnaround: arrival 0, completion 9 -> 9
        self.assertEqual(p1.turnaround_time, 9)

if __name__ == '__main__':
    unittest.main()