import unittest
from memory.paging import Page, PagingManager

class TestPagingManager(unittest.TestCase):

    def setUp(self):
        # 100 bytes of total RAM, page size is 10 bytes -> exactly 10 frames available.
        self.manager = PagingManager(total_physical_memory=100, page_size=10)

    def test_page_creation(self):
        """Verify the Page class initializes correctly."""
        p = Page(page_number=2)
        self.assertEqual(p.page_number, 2)
        self.assertIsNone(p.frame_number)
        self.assertFalse(p.is_valid)

        p2 = Page(page_number=3, frame_number=5, is_valid=True)
        self.assertEqual(p2.page_number, 3)
        self.assertEqual(p2.frame_number, 5)
        self.assertTrue(p2.is_valid)

    def test_initialization(self):
        self.assertEqual(self.manager.num_frames, 10)
        self.assertEqual(len(self.manager.frames), 10)
        self.assertEqual(len(self.manager.get_free_frames()), 10)

    def test_allocate_process_success(self):
        # P1 needs 25 bytes. 25 / 10 = 2.5 -> needs 3 pages (30 bytes allocated).
        success = self.manager.allocate_process("P1", 25)
        
        self.assertTrue(success)
        self.assertEqual(len(self.manager.get_free_frames()), 7)
        self.assertIn("P1", self.manager.page_tables)
        
        # Check mapping (Pages 0, 1, 2 should map to Frames 0, 1, 2)
        pt = self.manager.page_tables["P1"]
        self.assertEqual(len(pt.pages), 3)
        
        self.assertEqual(pt.pages[0].page_number, 0)
        self.assertEqual(pt.pages[0].frame_number, 0)
        self.assertTrue(pt.pages[0].is_valid)
        
        self.assertEqual(pt.pages[2].page_number, 2)
        self.assertEqual(pt.pages[2].frame_number, 2)
        self.assertTrue(pt.pages[2].is_valid)

    def test_allocate_insufficient_frames(self):
        # Requires 12 pages, but only 10 frames exist.
        success = self.manager.allocate_process("P2", 120)
        
        self.assertFalse(success)
        self.assertEqual(len(self.manager.get_free_frames()), 10) # No frames leaked
        self.assertNotIn("P2", self.manager.page_tables)

    def test_address_translation_success(self):
        self.manager.allocate_process("P1", 25)
        
        # VA 14 -> Page 1, Offset 4. Page 1 is in Frame 1. PA = (1 * 10) + 4 = 14
        pa = self.manager.translate_address("P1", 14)
        self.assertEqual(pa, 14)
        
        # P2 needs 1 page (10 bytes). Gets Frame 3.
        self.manager.allocate_process("P2", 8)
        
        # VA 5 for P2 -> Page 0, Offset 5. Page 0 in Frame 3. PA = (3 * 10) + 5 = 35
        pa_p2 = self.manager.translate_address("P2", 5)
        self.assertEqual(pa_p2, 35)

    def test_translation_out_of_bounds(self):
        self.manager.allocate_process("P1", 25)
        
        # VA 25 is out of bounds (valid indices are 0 to 24)
        with self.assertRaises(ValueError) as context:
            self.manager.translate_address("P1", 25)
            
        self.assertIn("Segmentation Fault", str(context.exception))
        
    def test_translation_page_fault(self):
        self.manager.allocate_process("P1", 20) # 2 pages
        pt = self.manager.page_tables["P1"]
        
        # Manually invalidate Page 1 to simulate a page swapped to disk
        pt.pages[1].is_valid = False
        pt.pages[1].frame_number = None
        
        # Accessing VA 15 falls into Page 1, which is now invalid
        with self.assertRaises(ValueError) as context:
            self.manager.translate_address("P1", 15)
            
        self.assertIn("Page Fault", str(context.exception))

    def test_deallocation(self):
        self.manager.allocate_process("P1", 40) # Uses 4 frames
        self.assertEqual(len(self.manager.get_free_frames()), 6)
        
        self.manager.deallocate_process("P1")
        
        # Verify completely restored
        self.assertEqual(len(self.manager.get_free_frames()), 10)
        self.assertNotIn("P1", self.manager.page_tables)
        
        # Frames should be wiped
        for frame in self.manager.frames:
            self.assertFalse(frame.is_allocated)
            self.assertIsNone(frame.process_id)

if __name__ == '__main__':
    unittest.main()