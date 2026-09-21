import unittest
from models.pcb import PCB, ProcessState
from io_sim.io_request import IODevice
from io_sim.io_manager import IOManager
from io_sim.process_io import ProcessIOManager

class TestProcessIOManager(unittest.TestCase):

    def setUp(self):
        self.io_manager = IOManager()
        self.process_io = ProcessIOManager(self.io_manager)

    def test_running_process_can_request_io(self):
        """Verify a RUNNING process can request I/O and changes state to WAITING."""
        pcb = PCB(pid=1, arrival_time=0, cpu_burst_time=5)
        pcb.state = ProcessState.RUNNING
        
        req = self.process_io.request_io(pcb, IODevice.DISK, 3)
        
        self.assertEqual(req.process_id, 1)
        self.assertEqual(pcb.state, ProcessState.WAITING)
        self.assertIn(req, self.io_manager.get_active_requests())

    def test_non_running_process_rejected(self):
        """Verify processes not currently on the CPU cannot issue I/O requests."""
        pcb = PCB(pid=2, arrival_time=0, cpu_burst_time=5)
        pcb.state = ProcessState.READY
        
        with self.assertRaises(ValueError):
            self.process_io.request_io(pcb, IODevice.KEYBOARD, 2)
            
        # State should remain unchanged
        self.assertEqual(pcb.state, ProcessState.READY)

    def test_io_completion_updates_process_to_ready(self):
        """Verify that a finished I/O request transitions a WAITING process to READY (not RUNNING)."""
        pcb = PCB(pid=3, arrival_time=0, cpu_burst_time=5)
        pcb.state = ProcessState.RUNNING
        
        self.process_io.request_io(pcb, IODevice.NETWORK, 1)
        
        # Advance simulation to finish the I/O
        self.io_manager.advance_time()
        
        # System hasn't updated processes yet, should still be WAITING
        self.assertEqual(pcb.state, ProcessState.WAITING)
        
        # Update process states based on IO completions
        self.process_io.update_processes()
        
        # Should be strictly READY, the scheduler must decide when it runs again
        self.assertEqual(pcb.state, ProcessState.READY)

    def test_multiple_independent_process_io(self):
        """Verify the manager correctly maps multiple processes finishing I/O at different times."""
        p1 = PCB(pid=10, arrival_time=0, cpu_burst_time=5)
        p2 = PCB(pid=20, arrival_time=0, cpu_burst_time=5)
        
        p1.state = ProcessState.RUNNING
        p2.state = ProcessState.RUNNING
        
        self.process_io.request_io(p1, IODevice.DISK, 2)
        self.process_io.request_io(p2, IODevice.PRINTER, 4)
        
        self.assertEqual(p1.state, ProcessState.WAITING)
        self.assertEqual(p2.state, ProcessState.WAITING)
        
        # Advance 2 units: p1 finishes, p2 still has 2 remaining
        self.io_manager.advance_time()
        self.io_manager.advance_time()
        
        self.process_io.update_processes()
        
        self.assertEqual(p1.state, ProcessState.READY)
        self.assertEqual(p2.state, ProcessState.WAITING)
        
        # Advance 2 more units: p2 finishes
        self.io_manager.advance_time()
        self.io_manager.advance_time()
        
        self.process_io.update_processes()
        self.assertEqual(p2.state, ProcessState.READY)
        
        # Ensure redundant calls to update don't break states
        self.process_io.update_processes()
        self.assertEqual(p1.state, ProcessState.READY)
        self.assertEqual(p2.state, ProcessState.READY)

if __name__ == '__main__':
    unittest.main()