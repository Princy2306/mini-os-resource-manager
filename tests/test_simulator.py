import unittest
from models.pcb import PCB, ProcessState
from simulation.simulator import OSSimulator

class TestOSSimulator(unittest.TestCase):

    def setUp(self):
        self.simulator = OSSimulator()

    def test_initialization(self):
        """Verify the simulator starts at time 0 with an empty registry."""
        self.assertEqual(self.simulator.current_time, 0)
        self.assertEqual(self.simulator.get_all_processes(), [])

    def test_add_and_get_process(self):
        """Verify adding a process works and its state is completely retained."""
        pcb = PCB(pid=1, arrival_time=0, cpu_burst_time=5)
        pcb.state = ProcessState.READY
        pcb.priority = 2
        
        self.simulator.add_process(pcb)
        
        retrieved = self.simulator.get_process(1)
        self.assertIs(retrieved, pcb)  # Must be the exact same object
        self.assertEqual(retrieved.state, ProcessState.READY)
        self.assertEqual(retrieved.priority, 2)

    def test_duplicate_pid_rejection(self):
        """Verify that attempting to add a process with an existing PID raises ValueError."""
        pcb1 = PCB(pid=10, arrival_time=0, cpu_burst_time=5)
        pcb2 = PCB(pid=10, arrival_time=2, cpu_burst_time=3)
        
        self.simulator.add_process(pcb1)
        
        with self.assertRaises(ValueError):
            self.simulator.add_process(pcb2)

    def test_missing_pid_behavior(self):
        """Verify retrieving a non-existent PID raises KeyError."""
        with self.assertRaises(KeyError):
            self.simulator.get_process(99)

    def test_deterministic_pid_ordering(self):
        """Verify get_all_processes returns PCBs strictly ordered by PID, regardless of insertion order."""
        p3 = PCB(pid=3, arrival_time=1, cpu_burst_time=1)
        p1 = PCB(pid=1, arrival_time=2, cpu_burst_time=2)
        p2 = PCB(pid=2, arrival_time=3, cpu_burst_time=3)
        
        # Add out of order
        self.simulator.add_process(p3)
        self.simulator.add_process(p1)
        self.simulator.add_process(p2)
        
        all_processes = self.simulator.get_all_processes()
        
        self.assertEqual(len(all_processes), 3)
        self.assertEqual(all_processes[0].pid, 1)
        self.assertEqual(all_processes[1].pid, 2)
        self.assertEqual(all_processes[2].pid, 3)

    def test_registering_multiple_processes(self):
        """Verify multiple distinct processes are correctly registered and managed."""
        for i in range(5):
            self.simulator.add_process(PCB(pid=i, arrival_time=i, cpu_burst_time=5))
            
        self.assertEqual(len(self.simulator.get_all_processes()), 5)
        for i in range(5):
            # Assert no KeyError is raised and correct PID is returned
            self.assertEqual(self.simulator.get_process(i).pid, i)

    def test_advancing_simulation_time(self):
        """Verify advancing the simulation increments the time by exactly 1 unit."""
        self.assertEqual(self.simulator.current_time, 0)
        
        self.simulator.advance_time()
        self.assertEqual(self.simulator.current_time, 1)
        
        self.simulator.advance_time()
        self.assertEqual(self.simulator.current_time, 2)

if __name__ == '__main__':
    unittest.main()