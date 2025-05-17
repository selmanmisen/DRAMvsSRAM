# DRAM vs SRAM

This project is a simulation that demonstrates the difference between **DRAM and SRAM**.

At the top of the interface, users can enter some data (each character represents a unit of data).

The simulation starts when the **"Başlat"** (Start) button is clicked.

For each data element:

- The system first checks **SRAM**.
- If the data is **not found** in SRAM, it checks **DRAM**. This is called a **cache miss**.
- If the data is **not in DRAM** either:
  - The system first writes the data to DRAM.
  - Then it writes the same data to SRAM.
- If the system **finds** the data in SRAM, this is called a **cache hit**.
- If **SRAM is full**, the system deletes the **least recently used** cell and writes the new data there. This process uses the **LRU (Least Recently Used) algorithm**.

At the bottom, the simulation provides a **live chart** that displays the **energy consumption** and **latency** of DRAM and SRAM step by step.

---

## How to Run the Simulation

```bash
pip install -r requirements.txt
python sramvsdrm.py
