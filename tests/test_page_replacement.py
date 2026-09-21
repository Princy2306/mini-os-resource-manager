import unittest
from memory.page_replacement import (
    PageReplacementSimulator, 
    FIFO, LRU, Optimal
)

class TestPageReplacement(unittest.TestCase):
    
    def setUp(self):
        # Classic OS textbook reference string
        self.ref_string = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1]
        self.num_frames = 3

    def test_fifo_replacement(self):
        simulator = PageReplacementSimulator(self.num_frames, FIFO())
        result = simulator.run(self.ref_string)
        
        # Textbook verification for FIFO on this string = 15 faults
        self.assertEqual(result.page_faults, 15)
        self.assertEqual(result.page_hits, 5)
        self.assertEqual(result.replacements, 12) # 15 faults - 3 initial empty frame fills
        self.assertEqual(result.final_frames, [7, 0, 1])

    def test_lru_replacement(self):
        simulator = PageReplacementSimulator(self.num_frames, LRU())
        result = simulator.run(self.ref_string)
        
        self.assertEqual(result.page_faults, 12)
        self.assertEqual(result.page_hits, 8)
        self.assertEqual(result.replacements, 9)
        # Corrected expectation based on manual trace
        self.assertEqual(result.final_frames, [1, 0, 7])

    def test_optimal_replacement(self):
        simulator = PageReplacementSimulator(self.num_frames, Optimal())
        result = simulator.run(self.ref_string)
        
        # Textbook verification for Optimal on this string = 9 faults
        self.assertEqual(result.page_faults, 9)
        self.assertEqual(result.page_hits, 11)
        self.assertEqual(result.replacements, 6)
        self.assertEqual(result.final_frames, [7, 0, 1])

    def test_invalid_frames(self):
        with self.assertRaises(ValueError):
            PageReplacementSimulator(0, FIFO())

    def test_empty_reference_string(self):
        simulator = PageReplacementSimulator(3, LRU())
        result = simulator.run([])
        
        self.assertEqual(result.page_faults, 0)
        self.assertEqual(result.page_hits, 0)
        self.assertEqual(result.hit_ratio, 0.0)
        self.assertEqual(result.replacements, 0)
        self.assertEqual(result.final_frames, [None, None, None])

    def test_fewer_references_than_frames(self):
        simulator = PageReplacementSimulator(5, FIFO())
        # 3 unique pages, 1 duplicate. 5 frames available.
        result = simulator.run([1, 2, 3, 2])
        
        self.assertEqual(result.page_faults, 3)
        self.assertEqual(result.page_hits, 1)
        self.assertEqual(result.replacements, 0) # No replacements should occur
        self.assertEqual(result.final_frames, [1, 2, 3, None, None])
        self.assertEqual(result.hit_ratio, 0.25)

if __name__ == '__main__':
    unittest.main()