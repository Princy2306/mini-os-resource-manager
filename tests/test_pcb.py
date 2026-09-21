import unittest
from models.pcb import PCB, ProcessState

class TestProcessManagement(unittest.TestCase):
    
    def test_pcb_initialization(self):
        """Verify new process is initialized with correct default states."""
        process = PCB(pid=1, arrival_time=0, cpu_burst_time=5, priority=2)
        
        self.assertEqual(process.pid, 1)
        self.assertEqual(process.state, ProcessState.NEW)
        self.assertEqual(process.remaining_cpu_time, 5)
        self.assertIsNone(process.start_time)
        self.assertIsNone(process.completion_time)
        self.assertIsNone(process.turnaround_time)
        
    def test_pcb_metrics_calculation(self):
        """Verify turnaround, waiting, and response times follow standard OS formulas."""
        # Process arrives at t=2, needs 4 units of CPU
        process = PCB(pid=2, arrival_time=2, cpu_burst_time=4)
        
        # Simulate scheduler picking it up for the first time at t=5
        process.state = ProcessState.RUNNING
        process.start_time = 5
        
        # Verify Response Time: Start (5) - Arrival (2) = 3
        self.assertEqual(process.response_time, 3)
        
        # Simulate process finishing at t=12
        process.remaining_cpu_time = 0
        process.state = ProcessState.TERMINATED
        process.completion_time = 12
        
        # Verify Turnaround Time: Completion (12) - Arrival (2) = 10
        self.assertEqual(process.turnaround_time, 10)
        
        # Verify Waiting Time: Turnaround (10) - Burst (4) = 6
        self.assertEqual(process.waiting_time, 6)

    def test_preemption_logic_safety(self):
        """Verify remaining time tracking does not interfere with static burst time."""
        process = PCB(pid=3, arrival_time=0, cpu_burst_time=10)
        
        # Simulate preemption (ran for 3 units, then preempted)
        process.remaining_cpu_time -= 3
        process.state = ProcessState.READY
        
        self.assertEqual(process.remaining_cpu_time, 7)
        self.assertEqual(process.cpu_burst_time, 10)  # Original burst must remain intact

if __name__ == '__main__':
    unittest.main()