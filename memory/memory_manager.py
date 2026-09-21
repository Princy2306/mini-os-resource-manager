from typing import List, Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class MemoryBlock:
    start_address: int
    size: int
    is_allocated: bool = False
    process_id: Optional[str] = None

class AllocationStrategy(ABC):
    @abstractmethod
    def find_block(self, blocks: List[MemoryBlock], request_size: int) -> int:
        """Returns the index of the suitable memory block, or -1 if none found."""
        pass

class FirstFit(AllocationStrategy):
    def find_block(self, blocks: List[MemoryBlock], request_size: int) -> int:
        for i, block in enumerate(blocks):
            if not block.is_allocated and block.size >= request_size:
                return i
        return -1

class BestFit(AllocationStrategy):
    def find_block(self, blocks: List[MemoryBlock], request_size: int) -> int:
        best_idx = -1
        smallest_sufficient_size = float('inf')
        
        for i, block in enumerate(blocks):
            if not block.is_allocated and block.size >= request_size:
                if block.size < smallest_sufficient_size:
                    smallest_sufficient_size = block.size
                    best_idx = i
        return best_idx

class WorstFit(AllocationStrategy):
    def find_block(self, blocks: List[MemoryBlock], request_size: int) -> int:
        worst_idx = -1
        largest_size = -1
        
        for i, block in enumerate(blocks):
            if not block.is_allocated and block.size >= request_size:
                if block.size > largest_size:
                    largest_size = block.size
                    worst_idx = i
        return worst_idx

class ContiguousMemoryManager:
    def __init__(self, total_memory: int, strategy: AllocationStrategy):
        self.total_memory = total_memory
        self.strategy = strategy
        # Initialize memory as a single large free block
        self.blocks: List[MemoryBlock] = [
            MemoryBlock(start_address=0, size=total_memory, is_allocated=False, process_id=None)
        ]

    def allocate(self, process_id: str, size: int) -> bool:
        """Attempts to allocate contiguous memory for a process."""
        if size <= 0:
            return False
            
        block_idx = self.strategy.find_block(self.blocks, size)
        
        if block_idx == -1:
            return False  # Allocation failed (Out of memory / Fragmentation)
            
        target_block = self.blocks[block_idx]
        
        # Split block if there is leftover space
        if target_block.size > size:
            new_free_block = MemoryBlock(
                start_address=target_block.start_address + size,
                size=target_block.size - size,
                is_allocated=False,
                process_id=None
            )
            target_block.size = size
            self.blocks.insert(block_idx + 1, new_free_block)
            
        target_block.is_allocated = True
        target_block.process_id = process_id
        return True

    def deallocate(self, process_id: str) -> None:
        """Frees all memory blocks owned by the process and merges adjacent free blocks."""
        freed_any = False
        for block in self.blocks:
            if block.is_allocated and block.process_id == process_id:
                block.is_allocated = False
                block.process_id = None
                freed_any = True
                
        if freed_any:
            self._merge_free_blocks()

    def _merge_free_blocks(self) -> None:
        """Compacts adjacent free blocks into single larger blocks."""
        merged_blocks: List[MemoryBlock] = []
        
        for block in self.blocks:
            if not merged_blocks:
                merged_blocks.append(block)
                continue
                
            prev_block = merged_blocks[-1]
            if not prev_block.is_allocated and not block.is_allocated:
                # Merge the current block into the previous one
                prev_block.size += block.size
            else:
                merged_blocks.append(block)
                
        self.blocks = merged_blocks

    def get_memory_snapshot(self) -> List[dict]:
        """Returns a snapshot of the current memory map for testing/debugging."""
        return [
            {
                "start": b.start_address,
                "size": b.size,
                "allocated": b.is_allocated,
                "pid": b.process_id
            }
            for b in self.blocks
        ]