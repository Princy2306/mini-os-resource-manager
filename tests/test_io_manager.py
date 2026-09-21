import unittest
from io_sim.io_request import IODevice, IORequest
from io_sim.io_manager import IOManager

class TestIOManager(unittest.TestCase):

    def setUp(self):
        self.manager = IOManager()

    def test_submit_request_and_start_time(self):
        """Verify submitting a request records the start time and tracks it as active."""
        req = IORequest(process_id=1, device=IODevice.DISK, duration=3)
        self.manager.submit_request(req)
        
        self.assertEqual(req.start_time, 0)
        self.assertIn(req, self.manager.get_active_requests())
        self.assertTrue(self.manager.has_active_io(1))

    def test_advancing_simulation_time(self):
        """Verify advancing time correctly updates the manager's clock and the request's remaining time."""
        req = IORequest(process_id=2, device=IODevice.KEYBOARD, duration=3)
        self.manager.submit_request(req)
        
        self.manager.advance_time()
        
        self.assertEqual(self.manager.current_time, 1)
        self.assertEqual(req.remaining_time, 2)
        self.assertFalse(req.is_complete)
        self.assertIn(req, self.manager.get_active_requests())

    def test_request_completion_and_completion_time(self):
        """Verify requests properly complete, record completion time, and move to completed tracking."""
        req = IORequest(process_id=3, device=IODevice.NETWORK, duration=2)
        self.manager.submit_request(req)
        
        self.manager.advance_time() # t=1, remaining=1
        self.assertFalse(req.is_complete)
        
        self.manager.advance_time() # t=2, remaining=0, complete!
        
        self.assertTrue(req.is_complete)
        self.assertEqual(req.completion_time, 2)
        
        # Verify it was moved out of active and into completed
        self.assertNotIn(req, self.manager.get_active_requests())
        self.assertIn(req, self.manager.get_completed_requests())
        self.assertFalse(self.manager.has_active_io(3))

    def test_multiple_simultaneous_requests(self):
        """Verify the manager can handle multiple requests progressing independently in parallel."""
        req1 = IORequest(process_id=1, device=IODevice.DISK, duration=2)
        req2 = IORequest(process_id=2, device=IODevice.PRINTER, duration=3)
        
        self.manager.submit_request(req1)
        
        self.manager.advance_time() # t=1
        self.assertEqual(req1.remaining_time, 1)
        
        # Submit second request at t=1
        self.manager.submit_request(req2)
        self.assertEqual(req2.start_time, 1)
        
        self.assertTrue(self.manager.has_active_io(1))
        self.assertTrue(self.manager.has_active_io(2))
        
        self.manager.advance_time() # t=2
        # req1 finishes, req2 has 2 left
        self.assertTrue(req1.is_complete)
        self.assertEqual(req1.completion_time, 2)
        self.assertFalse(req2.is_complete)
        
        self.assertFalse(self.manager.has_active_io(1))
        self.assertTrue(self.manager.has_active_io(2))
        
        self.manager.advance_time() # t=3, req2 remaining=1
        self.manager.advance_time() # t=4, req2 finishes
        
        self.assertTrue(req2.is_complete)
        self.assertEqual(req2.completion_time, 4)
        
        # Verify both are safely in the completed list
        completed = self.manager.get_completed_requests()
        self.assertEqual(len(completed), 2)
        self.assertIn(req1, completed)
        self.assertIn(req2, completed)

    def test_has_active_io_check(self):
        """Verify the has_active_io method correctly returns process IO status."""
        self.assertFalse(self.manager.has_active_io(5))
        
        req = IORequest(process_id=5, device=IODevice.NETWORK, duration=1)
        self.manager.submit_request(req)
        
        self.assertTrue(self.manager.has_active_io(5))
        
        self.manager.advance_time() # t=1, finishes
        self.assertFalse(self.manager.has_active_io(5))

if __name__ == '__main__':
    unittest.main()