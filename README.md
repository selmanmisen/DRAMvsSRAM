# DRAMvsSRAM

Basically this is a simulation of the "difference between DRAM and SRAM" explanation.

At the top, users enter some data (each character means one data).

Then the simulation starts with "Başlat" button.

For each data, SRAM is first checked. If the data is not there, the system checks DRAM. We call this situation "cache miss".
If it isn't there either,firstly the simulation writes the data to DRAM. Then the system writes to SRAM before selecting the next data.
Thus, if system needs to use this data again, it can easily access data via SRAM.

Or system can find the data in SRAM, we call this situation "cache hit".

In another case, SRAM cells may be full. In this case system can delete the least used cell. Then the system writes new data in deleted cell. We call this algorithm 
 "LRU algortihm".

At the bottom simulation gives a live chart. This chart can show the energy and latency for DRAM and SRAM step by step. 

For running the system:
pip install -r requirements.txt
python sramvsdrm.py
