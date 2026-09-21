import unittest
from models.pcb import PCB, ProcessState, TimelineEvent
from scheduler.metrics import SchedulingMetrics

class TestSchedulingMetrics(unittest.TestCase):

    def setUp(self):
        # Create a deterministic completed state manually to test the math
        # P1: arrived 0, burst 5, started 0, completed 5 (wait 0, turnaround 5, response 0)
        p1 = PCB(pid=1, arrival_time=0, cpu_burst_time=5)
        p1.start_time = 0
        p1.completion_time = 5
        p1.state = ProcessState.TERMINATED

        # P2: arrived 1, burst 3, started 5, completed 8 (wait 4, turnaround 7, response 4)
        p2 = PCB(pid=2, arrival_time=1, cpu_burst_time=3)
        p2.start_time = 5
        p2.completion_time = 8
        p2.state = ProcessState.TERMINATED

        self.processes = [p1, p2]
        
        # CPU was busy from 0-5, then 5-8. Total elapsed = 8. Busy = 8. (100% utilization)
        self.timeline = [
            TimelineEvent(start_time=0, end_time=5, pid=1),
            TimelineEvent(start_time=5, end_time=8, pid=2)
        ]

    def test_standard_metrics(self):
        metrics = SchedulingMetrics(self.processes, self.timeline)

        # Wait: (0 + 4) / 2 = 2.0
        self.assertEqual(metrics.avg_waiting_time, 2.0)
        
        # Turnaround: (5 + 7) / 2 = 6.0
        self.assertEqual(metrics.avg_turnaround_time, 6.0)
        
        # Response: (0 + 4) / 2 = 2.0
        self.assertEqual(metrics.avg_response_time, 2.0)
        
        # Utilization: 8 busy / 8 elapsed = 100%
        self.assertEqual(metrics.cpu_utilization, 100.0)
        
        # Throughput: 2 processes / 8 time units = 0.25
        self.assertEqual(metrics.throughput, 0.25)

    def test_cpu_idle_time(self):
        """Test metrics when there is a gap (idle time) in the timeline."""
        # P1 runs 0-5. CPU idles 5-10. P2 runs 10-13.
        # Total elapsed = 13. Busy = 5 + 3 = 8.
        timeline_with_idle = [
            TimelineEvent(start_time=0, end_time=5, pid=1),
            TimelineEvent(start_time=10, end_time=13, pid=2)
        ]
        metrics = SchedulingMetrics(self.processes, timeline_with_idle)
        
        self.assertEqual(metrics.total_elapsed_time, 13)
        self.assertAlmostEqual(metrics.cpu_utilization, (8 / 13) * 100.0)
        self.assertEqual(metrics.throughput, 2 / 13)

    def test_empty_inputs_safety(self):
        """Ensure the module does not crash with division by zero on empty inputs."""
        metrics = SchedulingMetrics([], [])
        
        self.assertEqual(metrics.avg_waiting_time, 0.0)
        self.assertEqual(metrics.avg_turnaround_time, 0.0)
        self.assertEqual(metrics.avg_response_time, 0.0)
        self.assertEqual(metrics.cpu_utilization, 0.0)
        self.assertEqual(metrics.throughput, 0.0)

    def test_ignores_uncompleted_processes(self):
        """Ensure processes not in TERMINATED state are ignored for averages."""
        p3 = PCB(pid=3, arrival_time=0, cpu_burst_time=10)
        p3.state = ProcessState.RUNNING # Not terminated
        
        processes_mixed = self.processes + [p3]
        metrics = SchedulingMetrics(processes_mixed, self.timeline)
        
        # Metrics should remain exactly the same as test_standard_metrics
        self.assertEqual(metrics.num_completed, 2)
        self.assertEqual(metrics.avg_waiting_time, 2.0)

if __name__ == '__main__':
    unittest.main()