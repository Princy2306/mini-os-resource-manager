import unittest
from memory.memory_manager import ContiguousMemoryManager, FirstFit, BestFit, WorstFit

class TestContiguousMemoryManager(unittest.TestCase):

    def setUp(self):
        # Reset memory state before each test
        self.total_mem = 1000

    def test_first_fit_allocation(self):
        manager = ContiguousMemoryManager(self.total_mem, FirstFit())
        
        # Allocate: [P1:200] [P2:400] [P3:200] [Free:200]
        self.assertTrue(manager.allocate("P1", 200))
        self.assertTrue(manager.allocate("P2", 400))
        self.assertTrue(manager.allocate("P3", 200))
        
        # Deallocate P2 -> [P1:200] [Free:400] [P3:200] [Free:200]
        manager.deallocate("P2")
        
        # First fit for 150 should pick the very first available hole (the 400 block)
        self.assertTrue(manager.allocate("P4", 150))
        
        blocks = manager.get_memory_snapshot()
        # Layout should be: [P1:200] [P4:150] [Free:250] [P3:200] [Free:200]
        self.assertEqual(blocks[1]["pid"], "P4")
        self.assertEqual(blocks[1]["size"], 150)
        self.assertEqual(blocks[2]["allocated"], False)
        self.assertEqual(blocks[2]["size"], 250)

    def test_best_fit_allocation(self):
        manager = ContiguousMemoryManager(self.total_mem, BestFit())
        
        # Allocate: [P1:200] [P2:200] [P3:200] [P4:200] [Free:200]
        manager.allocate("P1", 200)
        manager.allocate("P2", 200)
        manager.allocate("P3", 200)
        manager.allocate("P4", 200)
        
        # Deallocate P2 & P4 
        # -> [P1:200] [Free:200] [P3:200] [Free:400 (P4's 200 merges with end 200)]
        manager.deallocate("P2")
        manager.deallocate("P4")
        
        # Best Fit for 150 should pick the tighter 200 hole over the 400 hole.
        self.assertTrue(manager.allocate("P5", 150))
        
        blocks = manager.get_memory_snapshot()
        # Layout: [P1:200] [P5:150] [Free:50] [P3:200] [Free:400]
        self.assertEqual(blocks[1]["pid"], "P5")
        self.assertEqual(blocks[1]["size"], 150)
        self.assertEqual(blocks[2]["size"], 50)
        
        # Best Fit for 250 should now pick the 400 hole (since 50 is too small)
        self.assertTrue(manager.allocate("P6", 250))
        
        blocks2 = manager.get_memory_snapshot()
        # Layout: [P1:200] [P5:150] [Free:50] [P3:200] [P6:250] [Free:150]
        self.assertEqual(blocks2[4]["pid"], "P6")
        self.assertEqual(blocks2[4]["size"], 250)
        self.assertEqual(blocks2[5]["size"], 150)

    def test_worst_fit_allocation(self):
        manager = ContiguousMemoryManager(self.total_mem, WorstFit())
        
        # Allocate: [P1:200] [P2:200] [P3:200] [Free:400]
        manager.allocate("P1", 200)
        manager.allocate("P2", 200)
        manager.allocate("P3", 200)
        
        # Deallocate P2 -> [P1:200] [Free:200] [P3:200] [Free:400]
        manager.deallocate("P2")
        
        # Worst fit for 150 should pick the LARGEST hole (the 400 block), NOT the 200 block
        self.assertTrue(manager.allocate("P4", 150))
        
        blocks = manager.get_memory_snapshot()
        # Layout: [P1:200] [Free:200] [P3:200] [P4:150] [Free:250]
        self.assertEqual(blocks[1]["allocated"], False)
        self.assertEqual(blocks[1]["size"], 200) # 200 hole untouched
        self.assertEqual(blocks[3]["pid"], "P4")
        self.assertEqual(blocks[3]["size"], 150)

    def test_allocation_failure(self):
        manager = ContiguousMemoryManager(self.total_mem, FirstFit())
        
        self.assertTrue(manager.allocate("P1", 600))
        # 400 remaining. Asking for 500 should fail gracefully.
        self.assertFalse(manager.allocate("P2", 500)) 
        
        blocks = manager.get_memory_snapshot()
        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[1]["allocated"], False)
        self.assertEqual(blocks[1]["size"], 400)

    def test_deallocation_and_merging(self):
        manager = ContiguousMemoryManager(self.total_mem, FirstFit())
        
        manager.allocate("P1", 100)
        manager.allocate("P2", 100)
        manager.allocate("P3", 100)
        manager.allocate("P4", 100)
        
        # Free adjacent blocks P2 and P3
        manager.deallocate("P2")
        manager.deallocate("P3")
        
        blocks = manager.get_memory_snapshot()
        # Layout should be: [P1:100] [Free:200] [P4:100] [Free:600]
        self.assertEqual(len(blocks), 4)
        self.assertEqual(blocks[1]["size"], 200)
        self.assertEqual(blocks[1]["allocated"], False)
        
        # Ensure the perfectly-sized merged block is reusable without splitting
        self.assertTrue(manager.allocate("P5", 200))
        blocks2 = manager.get_memory_snapshot()
        
        # Layout should be: [P1:100] [P5:200] [P4:100] [Free:600]
        self.assertEqual(len(blocks2), 4) # Did not split, length remains 4
        self.assertEqual(blocks2[1]["pid"], "P5")
        self.assertEqual(blocks2[1]["size"], 200)

if __name__ == "__main__":
    unittest.main()