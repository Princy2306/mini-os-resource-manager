import unittest
from io_sim.io_request import IODevice, IORequest

class TestIORequest(unittest.TestCase):

    def test_device_enum_values(self):
        """Verify the IODevice enum contains the required devices."""
        self.assertTrue(hasattr(IODevice, "DISK"))
        self.assertTrue(hasattr(IODevice, "KEYBOARD"))
        self.assertTrue(hasattr(IODevice, "NETWORK"))
        self.assertTrue(hasattr(IODevice, "PRINTER"))
        
        self.assertEqual(IODevice.DISK.value, "DISK")

    def test_valid_request_creation(self):
        """Verify an I/O request is initialized correctly with valid data."""
        req = IORequest(process_id=1, device=IODevice.DISK, duration=5)
        
        self.assertEqual(req.process_id, 1)
        self.assertEqual(req.device, IODevice.DISK)
        self.assertEqual(req.duration, 5)
        self.assertEqual(req.remaining_time, 5)  # Should equal duration initially
        self.assertIsNone(req.start_time)
        self.assertIsNone(req.completion_time)
        self.assertFalse(req.is_complete)

    def test_invalid_duration(self):
        """Verify that zero or negative durations raise a ValueError."""
        with self.assertRaises(ValueError):
            IORequest(process_id=2, device=IODevice.KEYBOARD, duration=0)
            
        with self.assertRaises(ValueError):
            IORequest(process_id=3, device=IODevice.NETWORK, duration=-3)

    def test_advancing_request(self):
        """Verify that advancing the request decreases remaining time."""
        req = IORequest(process_id=4, device=IODevice.PRINTER, duration=3)
        
        req.advance()
        self.assertEqual(req.remaining_time, 2)
        self.assertFalse(req.is_complete)
        
        req.advance()
        self.assertEqual(req.remaining_time, 1)
        self.assertFalse(req.is_complete)

    def test_request_completion(self):
        """Verify the is_complete property transitions to True when remaining_time hits 0."""
        req = IORequest(process_id=5, device=IODevice.DISK, duration=1)
        
        self.assertFalse(req.is_complete)
        req.advance()
        self.assertEqual(req.remaining_time, 0)
        self.assertTrue(req.is_complete)

    def test_prevent_negative_remaining_time(self):
        """Verify advancing a completed request does not drop remaining_time below zero."""
        req = IORequest(process_id=6, device=IODevice.KEYBOARD, duration=1)
        
        req.advance()  # Goes to 0
        self.assertTrue(req.is_complete)
        
        req.advance()  # Should stay at 0
        self.assertEqual(req.remaining_time, 0)
        self.assertTrue(req.is_complete)

if __name__ == '__main__':
    unittest.main()