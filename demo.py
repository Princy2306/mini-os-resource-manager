from models.pcb import PCB
from scheduler.schedulers import FCFSScheduler
from io_sim.io_request import IODevice
from simulation.simulator import OSSimulator


def show(sim, label):
    print(f"\n{label}")
    print(f"Simulation time: {sim.current_time}")

    for p in sim.get_all_processes():
        print(
            f"P{p.pid}: {p.state.name:<10} "
            f"remaining_cpu={p.remaining_cpu_time}"
        )


def main():
    sim = OSSimulator()
    sim.set_scheduler(FCFSScheduler([]))

    # Two processes arrive at time 0
    p1 = PCB(pid=1, arrival_time=0, cpu_burst_time=4)
    p2 = PCB(pid=2, arrival_time=0, cpu_burst_time=3)

    sim.add_process(p1)
    sim.add_process(p2)

    print("=" * 55)
    print("MINI OS RESOURCE MANAGER - LIVE DEMO")
    print("=" * 55)

    # P1 gets the CPU under FCFS
    sim.tick()
    show(sim, "After tick 1: P1 is executing")

    # P1 blocks for disk I/O
    sim.process_io.request_io(p1, IODevice.DISK, duration=2)
    show(sim, "P1 requests DISK I/O -> WAITING")

    # CPU continues with P2 while P1 waits
    sim.tick()
    show(sim, "After tick 2: P2 runs while P1 waits for I/O")

    # P1's I/O completes
    sim.tick()
    show(sim, "After tick 3: P1 I/O completes -> READY")

    # Scheduler can select P1 again
    sim.tick()
    show(sim, "After tick 4: P1 resumes CPU execution")

    print("\n" + "=" * 55)
    print("DEMO COMPLETE")
    print("=" * 55)


if __name__ == "__main__":
    main()