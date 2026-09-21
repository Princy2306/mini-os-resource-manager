import unittest
from models.pcb import PCB, ProcessState
from io_sim.io_request import IODevice
from io_sim.io_manager import IOManager
from io_sim.process_io import ProcessIOManager

class TestIOSubsystemIntegration(unittest.TestCase):

    def setUp(self):
        # Create a shared IOManager and ProcessIOManager for each test
        self.io_manager = IOManager()
        self.process_io = ProcessIOManager(self.io_manager)

    def test_io_subsystem_integration_same_device(self):
        """
        Integration scenario: Two processes request the same device. 
        Verifies queueing, sequential execution, and correct state transitions.
        """
        # 1. Create two PCBs and put both into RUNNING state
        p1 = PCB(pid=1, arrival_time=0, cpu_burst_time=10)
        p2 = PCB(pid=2, arrival_time=0, cpu_burst_time=10)
        p1.state = ProcessState.RUNNING
        p2.state = ProcessState.RUNNING

        # 2. Process 1 requests DISK I/O with duration 2
        req1 = self.process_io.request_io(p1, IODevice.DISK, 2)
        
        # Verify P1 is WAITING and request starts at time 0
        self.assertEqual(p1.state, ProcessState.WAITING)
        self.assertEqual(req1.start_time, 0)

        # 3. Process 2 requests DISK I/O with duration 3
        req2 = self.process_io.request_io(p2, IODevice.DISK, 3)
        
        # Verify P2 is WAITING and its request is queued (no start_time yet)
        self.assertEqual(p2.state, ProcessState.WAITING)
        self.assertIsNone(req2.start_time)

        # 4. Advance the I/O manager for two time units
        self.io_manager.advance_time()
        self.io_manager.advance_time()

        # Verify P1's I/O completes at time 2
        self.assertTrue(req1.is_complete)
        self.assertEqual(req1.completion_time, 2)
        
        # Verify P2's request automatically starts at time 2
        self.assertEqual(req2.start_time, 2)
        self.assertFalse(req2.is_complete)

        # 5. Call ProcessIOManager.update_processes()
        self.process_io.update_processes()
        
        # Verify P1 becomes READY, while P2 remains WAITING
        self.assertEqual(p1.state, ProcessState.READY)
        self.assertEqual(p2.state, ProcessState.WAITING)

        # 6. Advance the I/O manager for three more time units
        self.io_manager.advance_time()
        self.io_manager.advance_time()
        self.io_manager.advance_time()

        # Verify P2's I/O completes at time 5 (started at 2, duration 3)
        self.assertTrue(req2.is_complete)
        self.assertEqual(req2.completion_time, 5)

        # 7. Call update_processes() again
        self.process_io.update_processes()
        
        # Verify P2 becomes READY
        self.assertEqual(p2.state, ProcessState.READY)

        # 8. Neither process should ever be automatically changed back to RUNNING
        self.assertNotEqual(p1.state, ProcessState.RUNNING)
        self.assertNotEqual(p2.state, ProcessState.RUNNING)

    def test_io_subsystem_concurrent_different_devices(self):
        """
        Integration scenario: Two processes request different devices.
        Verifies that devices operate independently and concurrently.
        """
        p3 = PCB(pid=3, arrival_time=0, cpu_burst_time=10)
        p4 = PCB(pid=4, arrival_time=0, cpu_burst_time=10)
        p3.state = ProcessState.RUNNING
        p4.state = ProcessState.RUNNING

        # Process 3 requests DISK (duration 2)
        req3 = self.process_io.request_io(p3, IODevice.DISK, 2)
        # Process 4 requests NETWORK (duration 3)
        req4 = self.process_io.request_io(p4, IODevice.NETWORK, 3)

        # Both requests should start immediately at time 0
        self.assertEqual(req3.start_time, 0)
        self.assertEqual(req4.start_time, 0)
        self.assertEqual(p3.state, ProcessState.WAITING)
        self.assertEqual(p4.state, ProcessState.WAITING)

        # Advance 2 time units
        self.io_manager.advance_time()
        self.io_manager.advance_time()

        # req3 should be done, req4 should have 1 time unit remaining
        self.assertTrue(req3.is_complete)
        self.assertEqual(req3.completion_time, 2)
        self.assertFalse(req4.is_complete)

        # Update processes
        self.process_io.update_processes()
        
        # P3 should be READY, P4 should still be WAITING
        self.assertEqual(p3.state, ProcessState.READY)
        self.assertEqual(p4.state, ProcessState.WAITING)

        # Advance 1 final time unit
        self.io_manager.advance_time()
        
        # req4 should now be done
        self.assertTrue(req4.is_complete)
        self.assertEqual(req4.completion_time, 3)

        # Final update
        self.process_io.update_processes()
        
        self.assertEqual(p4.state, ProcessState.READY)

if __name__ == '__main__':
    unittest.main()