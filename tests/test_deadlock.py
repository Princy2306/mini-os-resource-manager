import unittest
from deadlock.manager import DeadlockManager

class TestDeadlockManager(unittest.TestCase):

    def setUp(self):
        # Textbook safe state (Galvin)
        # Total resources: 10 A, 5 B, 7 C
        self.manager = DeadlockManager(total_resources=[10, 5, 7])
        
        # Max Demand | Allocation -> Need is automatically computed
        self.manager.add_process("P0", [7, 5, 3], [0, 1, 0])
        self.manager.add_process("P1", [3, 2, 2], [2, 0, 0])
        self.manager.add_process("P2", [9, 0, 2], [3, 0, 2])
        self.manager.add_process("P3", [2, 2, 2], [2, 1, 1])
        self.manager.add_process("P4", [4, 3, 3], [0, 0, 2])
        
        # Initial available should be [3, 3, 2]

    def test_safe_state(self):
        is_safe, sequence = self.manager.is_safe_state()
        self.assertTrue(is_safe)
        
        # In this state, P1 or P3 could run first. 
        # Based on dict ordering, P1 usually resolves early.
        self.assertEqual(len(sequence), 5)
        # Verify the sequence is valid mathematically
        self.assertIn(sequence[0], ["P1", "P3"]) 

    def test_resource_request_granted(self):
        # P1 requests [1, 0, 2]. 
        # Need[P1] is [1, 2, 2]. Fits max claim. Fits available [3, 3, 2].
        granted = self.manager.request_resources("P1", [1, 0, 2])
        
        self.assertTrue(granted)
        self.assertEqual(self.manager.available, [2, 3, 0])
        self.assertEqual(self.manager.allocation["P1"], [3, 0, 2])
        self.assertEqual(self.manager.need["P1"], [0, 2, 0])
        
        # System must still be safe
        is_safe, _ = self.manager.is_safe_state()
        self.assertTrue(is_safe)

    def test_resource_request_denied_unsafe(self):
        # P4 requests [3, 3, 0]. 
        # Need[P4] is [4, 3, 1]. Fits max claim. Fits available [3, 3, 2].
        # BUT granting this leaves available as [0, 0, 2], which is UNSAFE.
        granted = self.manager.request_resources("P4", [3, 3, 0])
        
        self.assertFalse(granted)
        # Verify rollback occurred
        self.assertEqual(self.manager.available, [3, 3, 2])
        self.assertEqual(self.manager.allocation["P4"], [0, 0, 2])

    def test_unsafe_state_detection(self):
        # We manually force an unsafe state. 
        # P0 gets [3, 2, 2] more, leaving Available at [0, 1, 0]
        self.manager.available = [0, 1, 0]
        self.manager.allocation["P0"] = [3, 3, 2]
        
        is_safe, seq = self.manager.is_safe_state()
        self.assertFalse(is_safe)
        self.assertEqual(seq, [])

    def test_deadlock_detection(self):
        # Total resources: [4, 4, 4]
        dm = DeadlockManager(total_resources=[4, 4, 4])
        
        # Max demand is irrelevant for detection, so we just pass dummy values [4,4,4]
        dm.add_process("P0", [4, 4, 4], [2, 0, 0])
        dm.add_process("P1", [4, 4, 4], [0, 2, 0])
        dm.add_process("P2", [4, 4, 4], [0, 0, 2])
        dm.add_process("P3", [4, 4, 4], [1, 1, 1])
        
        # Verify Available is mathematically correct: [4,4,4] - [3,3,3] = [1,1,1]
        self.assertEqual(dm.available, [1, 1, 1])
        
        # P3 needs nothing, P0/1/2 are in a circular wait requiring 3 of the next resource
        current_requests = {
            "P0": [0, 3, 0],
            "P1": [0, 0, 3],
            "P2": [3, 0, 0],
            "P3": [0, 0, 0]
        }
        
        deadlocked = dm.detect_deadlock(current_requests)
        
        # P3 finishes (releasing [1, 1, 1]), making Available [2, 2, 2].
        # P0, P1, and P2 all need 3 of a resource, so they remain blocked.
        self.assertEqual(set(deadlocked), {"P0", "P1", "P2"})
        self.assertNotIn("P3", deadlocked)

if __name__ == '__main__':
    unittest.main()