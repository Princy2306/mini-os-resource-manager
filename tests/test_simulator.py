import unittest
from models.pcb import PCB, ProcessState
from simulation.simulator import OSSimulator

# Import existing schedulers to verify compatibility
from scheduler.schedulers import FCFSScheduler, SJFScheduler, RoundRobinScheduler

class TestOSSimulator(unittest.TestCase):

    def setUp(self):
        self.simulator = OSSimulator()

    # --- STEP 1: Process Registry and Clock Tests ---

    def test_initialization(self):
        self.assertEqual(self.simulator.current_time, 0)
        self.assertEqual(self.simulator.get_all_processes(), [])

    def test_add_and_get_process(self):
        pcb = PCB(pid=1, arrival_time=0, cpu_burst_time=5)
        pcb.state = ProcessState.READY
        pcb.priority = 2
        
        self.simulator.add_process(pcb)
        
        retrieved = self.simulator.get_process(1)
        self.assertIs(retrieved, pcb)  
        self.assertEqual(retrieved.state, ProcessState.READY)
        self.assertEqual(retrieved.priority, 2)

    def test_duplicate_pid_rejection(self):
        pcb1 = PCB(pid=10, arrival_time=0, cpu_burst_time=5)
        pcb2 = PCB(pid=10, arrival_time=2, cpu_burst_time=3)
        self.simulator.add_process(pcb1)
        with self.assertRaises(ValueError):
            self.simulator.add_process(pcb2)

    def test_missing_pid_behavior(self):
        with self.assertRaises(KeyError):
            self.simulator.get_process(99)

    def test_deterministic_pid_ordering(self):
        p3 = PCB(pid=3, arrival_time=1, cpu_burst_time=1)
        p1 = PCB(pid=1, arrival_time=2, cpu_burst_time=2)
        p2 = PCB(pid=2, arrival_time=3, cpu_burst_time=3)
        
        self.simulator.add_process(p3)
        self.simulator.add_process(p1)
        self.simulator.add_process(p2)
        
        all_processes = self.simulator.get_all_processes()
        self.assertEqual([p.pid for p in all_processes], [1, 2, 3])

    def test_advancing_simulation_time(self):
        self.simulator.advance_time()
        self.assertEqual(self.simulator.current_time, 1)


    # --- STEP 2: Scheduler Integration Tests ---

    def test_error_no_scheduler_configured(self):
        pcb = PCB(pid=1, arrival_time=0, cpu_burst_time=5)
        pcb.state = ProcessState.READY
        self.simulator.add_process(pcb)
        with self.assertRaises(RuntimeError):
            self.simulator.get_next_process()

    def test_selecting_ready_process(self):
        self.simulator.set_scheduler(FCFSScheduler([]))
        
        pcb = PCB(pid=1, arrival_time=0, cpu_burst_time=5)
        pcb.state = ProcessState.READY
        self.simulator.add_process(pcb)
        
        selected = self.simulator.get_next_process()
        self.assertIsNotNone(selected)
        self.assertEqual(selected.pid, 1)
        self.assertEqual(selected.state, ProcessState.READY)

    def test_ignoring_future_arrival_times(self):
        self.simulator.set_scheduler(FCFSScheduler([]))
        
        pcb = PCB(pid=1, arrival_time=5, cpu_burst_time=5)
        pcb.state = ProcessState.READY
        self.simulator.add_process(pcb)
        
        self.assertIsNone(self.simulator.get_next_process())
        for _ in range(5):
            self.simulator.advance_time()
            
        self.assertIsNotNone(self.simulator.get_next_process())

    def test_ignoring_invalid_states(self):
        self.simulator.set_scheduler(FCFSScheduler([]))
        
        p_wait = PCB(pid=1, arrival_time=0, cpu_burst_time=5)
        p_wait.state = ProcessState.WAITING
        p_term = PCB(pid=2, arrival_time=0, cpu_burst_time=5)
        p_term.state = ProcessState.TERMINATED
        
        self.simulator.add_process(p_wait)
        self.simulator.add_process(p_term)
        self.assertIsNone(self.simulator.get_next_process())

    def test_scheduler_compatibility_sjf(self):
        self.simulator.set_scheduler(SJFScheduler([]))
        
        p_long = PCB(pid=1, arrival_time=0, cpu_burst_time=10)
        p_long.state = ProcessState.READY
        p_short = PCB(pid=2, arrival_time=0, cpu_burst_time=2)
        p_short.state = ProcessState.READY
        
        self.simulator.add_process(p_long)
        self.simulator.add_process(p_short)
        
        selected = self.simulator.get_next_process()
        self.assertEqual(selected.pid, 2)


    # --- STEP 3: Execution Engine / Tick Tests ---

    def test_tick_cpu_idle(self):
        """Verify tick advances time properly when the CPU is idle (no ready processes)."""
        self.simulator.set_scheduler(FCFSScheduler([]))
        self.simulator.tick()
        self.assertEqual(self.simulator.current_time, 1)
        
    def test_tick_executes_process(self):
        """Verify tick executes a process, decrements remaining time, and eventually completes it."""
        self.simulator.set_scheduler(FCFSScheduler([]))
        p1 = PCB(pid=1, arrival_time=0, cpu_burst_time=2)
        self.simulator.add_process(p1)
        
        # Tick 1: New -> Ready -> Running
        self.simulator.tick()
        self.assertEqual(p1.state, ProcessState.RUNNING)
        self.assertEqual(p1.start_time, 0)
        self.assertEqual(p1.remaining_cpu_time, 1)
        self.assertEqual(self.simulator.current_time, 1)
        
        # Tick 2: Running -> Terminated
        self.simulator.tick()
        self.assertEqual(p1.state, ProcessState.TERMINATED)
        self.assertEqual(p1.remaining_cpu_time, 0)
        self.assertEqual(p1.completion_time, 2)
        self.assertEqual(self.simulator.current_time, 2)

    def test_tick_round_robin_preemption(self):
        """Verify tick orchestrates context-switching with a preemptive scheduler."""
        p1 = PCB(pid=1, arrival_time=0, cpu_burst_time=2)
        p2 = PCB(pid=2, arrival_time=1, cpu_burst_time=2)
        
        scheduler = RoundRobinScheduler([], quantum=1)
        self.simulator.set_scheduler(scheduler)
        self.simulator.add_process(p1)
        self.simulator.add_process(p2)
        
        # Tick 1: (t=0) P1 is admitted and runs
        self.simulator.tick()
        self.assertEqual(p1.state, ProcessState.RUNNING)
        self.assertEqual(p1.remaining_cpu_time, 1)
        self.assertEqual(p2.state, ProcessState.NEW)
        
        # Tick 2: (t=1) P2 is admitted. P1's quantum expired, so P1 gets preempted to READY, P2 runs.
        self.simulator.tick()
        self.assertEqual(p1.state, ProcessState.READY)
        self.assertEqual(p2.state, ProcessState.RUNNING)
        self.assertEqual(p2.remaining_cpu_time, 1)
        
        # Tick 3: (t=2) P2's quantum expired. P1 runs and finishes.
        self.simulator.tick()
        self.assertEqual(p2.state, ProcessState.READY)
        self.assertEqual(p1.state, ProcessState.TERMINATED)
        self.assertEqual(p1.remaining_cpu_time, 0)
        
        # Tick 4: (t=3) P2 runs and finishes.
        self.simulator.tick()
        self.assertEqual(p2.state, ProcessState.TERMINATED)
        self.assertEqual(p2.remaining_cpu_time, 0)

from io_sim.io_request import IODevice

class TestOSSimulatorIOIntegration(unittest.TestCase):
    """Focused tests for Step 4: I/O Subsystem Integration into the Central Simulator."""

    def setUp(self):
        self.simulator = OSSimulator()
        self.simulator.set_scheduler(FCFSScheduler([]))
        
        self.p1 = PCB(pid=1, arrival_time=0, cpu_burst_time=3)
        self.p2 = PCB(pid=2, arrival_time=0, cpu_burst_time=3)
        self.simulator.add_process(self.p1)
        self.simulator.add_process(self.p2)

    def test_running_to_waiting_and_scheduler_ignores(self):
        """Verify requesting I/O puts process in WAITING, causing scheduler to pick another process."""
        # Tick 1: P1 runs
        self.simulator.tick()
        self.assertEqual(self.p1.state, ProcessState.RUNNING)
        self.assertEqual(self.p2.state, ProcessState.READY)
        
        # P1 requests I/O (Duration 2)
        self.simulator.process_io.request_io(self.p1, IODevice.DISK, 2)
        self.assertEqual(self.p1.state, ProcessState.WAITING)
        
        # Tick 2: P1 is WAITING, scheduler must pick P2
        self.simulator.tick()
        self.assertEqual(self.p1.state, ProcessState.WAITING)
        self.assertEqual(self.p2.state, ProcessState.RUNNING)

    def test_io_completion_transitions_to_ready(self):
        """Verify when I/O completes during advance_time, process transitions to READY."""
        self.simulator.tick() # P1 starts running
        
        # Request 1 tick of I/O
        self.simulator.process_io.request_io(self.p1, IODevice.NETWORK, 1)
        self.assertEqual(self.p1.state, ProcessState.WAITING)
        
        # Tick 2: P2 runs. P1's I/O progresses and finishes internally at the end of this tick
        self.simulator.tick()
        
        # Because tick() calls advance_time() which updates processes, P1 should now be READY
        self.assertEqual(self.p1.state, ProcessState.READY)

    def test_cpu_and_io_concurrent_progression(self):
        """Verify CPU bursts and I/O durations overlap and progress simultaneously."""
        self.simulator.tick() # Tick 1: (time 0->1) P1 RUNNING (remaining burst: 3 -> 2)
        
        # P1 blocks on I/O for 2 ticks
        self.simulator.process_io.request_io(self.p1, IODevice.DISK, 2)
        
        # Tick 2: (time 1->2) P2 RUNNING (remaining burst: 3 -> 2). P1 I/O active.
        self.simulator.tick() 
        self.assertEqual(self.p2.state, ProcessState.RUNNING)
        self.assertTrue(self.simulator.io_manager.has_active_io(1))
        
        # Tick 3: (time 2->3) P2 RUNNING (remaining burst: 2 -> 1). P1 I/O finishes -> READY.
        self.simulator.tick() 
        self.assertEqual(self.p2.state, ProcessState.RUNNING)
        self.assertEqual(self.p1.state, ProcessState.READY)
        self.assertFalse(self.simulator.io_manager.has_active_io(1))
        
        # Tick 4: (time 3->4) Both are READY (arrival=0). FCFS tie-breaker picks P1 (PID 1 < PID 2).
        # P1 RUNNING (remaining burst: 2 -> 1). P2 preempted to READY.
        self.simulator.tick()
        self.assertEqual(self.p1.state, ProcessState.RUNNING)
        self.assertEqual(self.p2.state, ProcessState.READY)
        
        # Tick 5: (time 4->5) P1 RUNNING (remaining burst: 1 -> 0) -> TERMINATED. P2 still READY.
        self.simulator.tick() 
        self.assertEqual(self.p1.state, ProcessState.TERMINATED)
        self.assertEqual(self.p2.state, ProcessState.READY)

        # Tick 6: (time 5->6) P2 resumes CPU (remaining burst: 1 -> 0) -> TERMINATED.
        self.simulator.tick() 
        self.assertEqual(self.p2.state, ProcessState.TERMINATED)
        
        # Verify completion times based on the simulation clock
        self.assertEqual(self.p1.completion_time, 5)
        self.assertEqual(self.p2.completion_time, 6)

if __name__ == '__main__':
    unittest.main()