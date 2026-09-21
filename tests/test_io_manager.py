import unittest
from io_sim.io_request import IODevice, IORequest
from io_sim.io_manager import IOManager

class TestIOManager(unittest.TestCase):

    def setUp(self):
        self.manager = IOManager()

    def test_submit_first_request_starts_immediately(self):
        """Verify the first request on a device gets an immediate start time."""
        req = IORequest(process_id=1, device=IODevice.DISK, duration=3)
        self.manager.submit_request(req)
        
        self.assertEqual(req.start_time, 0)
        self.assertIn(req, self.manager.get_active_requests())
        self.assertTrue(self.manager.has_active_io(1))

    def test_queue_progression_and_timing(self):
        """Verify second request queues, has no start time, and starts exactly when first finishes."""
        req_a = IORequest(process_id=1, device=IODevice.DISK, duration=2)
        req_b = IORequest(process_id=2, device=IODevice.DISK, duration=1)
        
        self.manager.submit_request(req_a) # t=0
        self.manager.submit_request(req_b) # t=0
        
        self.assertEqual(req_a.start_time, 0)
        self.assertIsNone(req_b.start_time) # Queued requests shouldn't have a start time yet
        
        self.manager.advance_time() # t=1, A remaining=1
        self.assertIsNone(req_b.start_time)
        self.assertIn(req_a, self.manager.get_active_requests())
        self.assertNotIn(req_b, self.manager.get_active_requests())
        
        self.manager.advance_time() # t=2, A completes, B starts automatically
        
        self.assertTrue(req_a.is_complete)
        self.assertEqual(req_a.completion_time, 2)
        
        self.assertEqual(req_b.start_time, 2) # B must start at exactly t=2
        self.assertIn(req_b, self.manager.get_active_requests())
        
        self.manager.advance_time() # t=3, B completes
        self.assertTrue(req_b.is_complete)
        self.assertEqual(req_b.completion_time, 3)

    def test_fifo_ordering(self):
        """Verify requests on the same device execute strictly in FIFO order."""
        r1 = IORequest(process_id=1, device=IODevice.KEYBOARD, duration=1)
        r2 = IORequest(process_id=2, device=IODevice.KEYBOARD, duration=1)
        r3 = IORequest(process_id=3, device=IODevice.KEYBOARD, duration=1)
        
        self.manager.submit_request(r1)
        self.manager.submit_request(r2)
        self.manager.submit_request(r3)
        
        self.manager.advance_time() # t=1
        self.assertTrue(r1.is_complete)
        self.assertEqual(r2.start_time, 1)
        self.assertIsNone(r3.start_time)
        
        self.manager.advance_time() # t=2
        self.assertTrue(r2.is_complete)
        self.assertEqual(r3.start_time, 2)

    def test_independent_devices(self):
        """Verify requests on different devices execute concurrently."""
        disk_req = IORequest(process_id=1, device=IODevice.DISK, duration=2)
        net_req = IORequest(process_id=2, device=IODevice.NETWORK, duration=1)
        
        self.manager.submit_request(disk_req)
        self.manager.submit_request(net_req)
        
        # Both start immediately because they request different devices
        self.assertEqual(disk_req.start_time, 0)
        self.assertEqual(net_req.start_time, 0)
        
        self.assertTrue(self.manager.has_active_io(1))
        self.assertTrue(self.manager.has_active_io(2))
        
        self.manager.advance_time() # t=1
        self.assertTrue(net_req.is_complete)
        self.assertFalse(disk_req.is_complete)
        
        self.manager.advance_time() # t=2
        self.assertTrue(disk_req.is_complete)

    def test_pending_vs_active_io(self):
        """Verify has_pending_io correctly identifies both queued and active requests."""
        req_a = IORequest(process_id=10, device=IODevice.PRINTER, duration=2)
        req_b = IORequest(process_id=20, device=IODevice.PRINTER, duration=2)
        
        self.manager.submit_request(req_a)
        self.manager.submit_request(req_b)
        
        # A is active (executing), B is pending (queued)
        self.assertTrue(self.manager.has_active_io(10))
        self.assertTrue(self.manager.has_pending_io(10))
        
        self.assertFalse(self.manager.has_active_io(20)) # Not executing yet
        self.assertTrue(self.manager.has_pending_io(20)) # But is waiting in queue
        
        self.manager.advance_time() # t=1
        self.manager.advance_time() # t=2, A finishes, B starts
        
        self.assertFalse(self.manager.has_active_io(10))
        self.assertFalse(self.manager.has_pending_io(10))
        
        self.assertTrue(self.manager.has_active_io(20))
        self.assertTrue(self.manager.has_pending_io(20))

if __name__ == '__main__':
    unittest.main()