from typing import Dict, List, Optional
from dataclasses import dataclass, field
import math

@dataclass
class Page:
    """Represents a virtual memory page."""
    page_number: int
    frame_number: Optional[int] = None
    is_valid: bool = False  # True if mapped to a physical frame

@dataclass
class Frame:
    """Represents a physical memory frame."""
    frame_number: int
    is_allocated: bool = False
    process_id: Optional[str] = None
    page_number: Optional[int] = None

@dataclass
class PageTable:
    """Represents a process's page table mapping logical pages to physical frames."""
    process_id: str
    process_size: int
    # Maps page_number -> Page object
    pages: Dict[int, Page] = field(default_factory=dict)

class PagingManager:
    def __init__(self, total_physical_memory: int, page_size: int):
        self.total_memory = total_physical_memory
        self.page_size = page_size
        self.num_frames = total_physical_memory // page_size
        
        # Initialize physical frames
        self.frames: List[Frame] = [Frame(frame_number=i) for i in range(self.num_frames)]
        
        # Maps process_id -> PageTable
        self.page_tables: Dict[str, PageTable] = {}

    def get_free_frames(self) -> List[Frame]:
        return [f for f in self.frames if not f.is_allocated]

    def allocate_process(self, process_id: str, process_size: int) -> bool:
        """
        Allocates frames for a process and builds its page table using Page objects.
        Returns True if successful, False if out of memory.
        """
        if process_size <= 0 or process_id in self.page_tables:
            return False

        # Calculate how many pages this process needs
        pages_needed = math.ceil(process_size / self.page_size)
        free_frames = self.get_free_frames()

        if pages_needed > len(free_frames):
            return False  # Insufficient memory

        # Create the page table
        page_table = PageTable(process_id=process_id, process_size=process_size)

        # Allocate the exact number of frames needed
        frames_to_allocate = free_frames[:pages_needed]
        for page_num, frame in enumerate(frames_to_allocate):
            # Update physical frame
            frame.is_allocated = True
            frame.process_id = process_id
            frame.page_number = page_num
            
            # Create the virtual Page and map it
            page = Page(page_number=page_num, frame_number=frame.frame_number, is_valid=True)
            page_table.pages[page_num] = page

        self.page_tables[process_id] = page_table
        return True

    def deallocate_process(self, process_id: str) -> None:
        """Frees all frames owned by a process and removes its page table."""
        if process_id not in self.page_tables:
            return

        page_table = self.page_tables[process_id]
        
        # Free the physical frames
        for page in page_table.pages.values():
            if page.is_valid and page.frame_number is not None:
                frame = self.frames[page.frame_number]
                frame.is_allocated = False
                frame.process_id = None
                frame.page_number = None

        # Delete the page table
        del self.page_tables[process_id]

    def translate_address(self, process_id: str, virtual_address: int) -> int:
        """
        Translates a virtual address to a physical address.
        Raises ValueError on invalid access or page fault.
        """
        if process_id not in self.page_tables:
            raise ValueError(f"Process {process_id} is not mapped in memory.")

        page_table = self.page_tables[process_id]

        # 1. Check if the address is within the process's allocated memory space
        if virtual_address < 0 or virtual_address >= page_table.process_size:
            raise ValueError(f"Segmentation Fault: Virtual address {virtual_address} is out of bounds for {process_id}.")

        # 2. Calculate Page Number and Offset
        page_number = virtual_address // self.page_size
        offset = virtual_address % self.page_size

        # 3. Lookup Page
        page = page_table.pages.get(page_number)
        
        if not page or not page.is_valid or page.frame_number is None:
            raise ValueError(f"Page Fault: Page {page_number} is not mapped to a valid frame.")

        # 4. Calculate and return Physical Address
        physical_address = (page.frame_number * self.page_size) + offset
        return physical_address