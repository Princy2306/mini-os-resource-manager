# Mini OS Resource Manager

A small operating system simulation project written in Python.

I built this project to understand how some basic OS components work together instead of implementing each concept separately. The main focus is process management, CPU scheduling, and I/O handling.

## What it does

The simulator supports:

- Process Control Blocks (PCB)
- Process states such as NEW, READY, RUNNING, WAITING and TERMINATED
- FCFS scheduling
- SJF scheduling
- Priority scheduling
- Round Robin scheduling
- CPU execution using a discrete time simulation
- Process arrival and termination
- I/O requests and device queues
- FIFO handling for requests on the same I/O device
- CPU and I/O running at the same time
- Integration between the scheduler, CPU simulation and I/O subsystem

## Project structure

```text
mini-os-resource-manager/
│
├── models/
│   └── pcb.py
│
├── scheduler/
│   └── schedulers.py
│
├── io_sim/
│   ├── io_request.py
│   ├── io_manager.py
│   └── process_io.py
│
├── simulation/
│   └── simulator.py
│
├── tests/
│   ├── test_pcb.py
│   ├── test_schedulers.py
│   ├── test_io_manager.py
│   ├── test_process_io.py
│   ├── test_io_integration.py
│   └── test_simulator.py
│
├── demo.py
├── requirements.txt
└── README.md
