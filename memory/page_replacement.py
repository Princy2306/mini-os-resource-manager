from typing import List, Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class PageReplacementResult:
    page_faults: int
    page_hits: int
    replacements: int
    hit_ratio: float
    final_frames: List[Optional[int]]

class PageReplacementStrategy(ABC):
    @abstractmethod
    def find_victim(
        self, 
        frames: List[int], 
        ref_string: List[int], 
        current_idx: int, 
        load_times: List[int], 
        access_times: List[int]
    ) -> int:
        """Returns the index of the frame to be replaced."""
        pass

class FIFO(PageReplacementStrategy):
    def find_victim(
        self, frames: List[int], ref_string: List[int], current_idx: int, 
        load_times: List[int], access_times: List[int]
    ) -> int:
        # Victim is the frame with the oldest load time
        return load_times.index(min(load_times))

class LRU(PageReplacementStrategy):
    def find_victim(
        self, frames: List[int], ref_string: List[int], current_idx: int, 
        load_times: List[int], access_times: List[int]
    ) -> int:
        # Victim is the frame with the oldest access time
        return access_times.index(min(access_times))

class Optimal(PageReplacementStrategy):
    def find_victim(
        self, frames: List[int], ref_string: List[int], current_idx: int, 
        load_times: List[int], access_times: List[int]
    ) -> int:
        farthest_idx = -1
        victim = -1
        
        future_refs = ref_string[current_idx + 1:]
        
        for i, frame_page in enumerate(frames):
            if frame_page not in future_refs:
                # If a page is never used again, it is the perfect victim
                return i
            
            # Find when this page is next used
            next_use = future_refs.index(frame_page)
            if next_use > farthest_idx:
                farthest_idx = next_use
                victim = i
                
        return victim

class PageReplacementSimulator:
    def __init__(self, num_frames: int, strategy: PageReplacementStrategy):
        if num_frames <= 0:
            raise ValueError("Number of frames must be strictly positive.")
        self.num_frames = num_frames
        self.strategy = strategy

    def run(self, reference_string: List[int]) -> PageReplacementResult:
        frames: List[int] = []
        # Parallel arrays to track metadata for each frame index
        load_times: List[int] = [-1] * self.num_frames
        access_times: List[int] = [-1] * self.num_frames
        
        faults = 0
        hits = 0
        replacements = 0
        
        for i, page in enumerate(reference_string):
            if page in frames:
                # Page Hit
                hits += 1
                idx = frames.index(page)
                access_times[idx] = i
            else:
                # Page Fault
                faults += 1
                if len(frames) < self.num_frames:
                    # Space available
                    frames.append(page)
                    idx = len(frames) - 1
                    load_times[idx] = i
                    access_times[idx] = i
                else:
                    # Frames full -> Replacement required
                    replacements += 1
                    idx = self.strategy.find_victim(
                        frames, reference_string, i, load_times, access_times
                    )
                    
                    frames[idx] = page
                    load_times[idx] = i
                    access_times[idx] = i
                    
        hit_ratio = (hits / len(reference_string)) if reference_string else 0.0
        
        # Pad the final frames list with None if it wasn't completely filled
        final_frames = frames + [None] * (self.num_frames - len(frames))
        
        return PageReplacementResult(
            page_faults=faults,
            page_hits=hits,
            replacements=replacements,
            hit_ratio=hit_ratio,
            final_frames=final_frames
        )