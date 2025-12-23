#!/usr/bin/env python
from pynvml import *
from ctypes import byref

# Run command to find the correct index: nvidia-smi --list-gpus
DEVICE_INDEX = 0
MIN_GPU_LOCKED_CLOCK = 210
MAX_GPU_LOCKED_CLOCK = 1965
MIN_MEM_LOCKED_CLOCK = 9501
MAX_MEM_LOCKED_CLOCK = 10001
GPU_CLOCK_OFFSET = 180
MEM_CLOCK_OFFSET = 500
POWER_LIMIT = 260_000

nvmlInit()
device = nvmlDeviceGetHandleByIndex(index=DEVICE_INDEX)

# Sets minimum and maximum GPU and memory clocks, You can find valid clock values with nvidia-smi -q -d SUPPORTED_CLOCKS.
# If you're happy with the maximum clock values of your GPU and memory, you can omit these lines.
nvmlDeviceSetGpuLockedClocks(handle=device, minGpuClockMHz=MIN_GPU_LOCKED_CLOCK, maxGpuClockMHz=MAX_GPU_LOCKED_CLOCK)
nvmlDeviceSetMemoryLockedClocks(handle=device, minMemClockMHz=MIN_MEM_LOCKED_CLOCK, maxMemClockMHz=MAX_MEM_LOCKED_CLOCK)

# Sets the power limit which has nothing to do with undervolting and can be omitted.
# The GPU will throttle itself (reduce clocks) to stay within this value.
nvmlDeviceSetPowerManagementLimit(handle=device, limit=POWER_LIMIT)

gpu_clock_info = c_nvmlClockOffset_t()
gpu_clock_info.version = nvmlClockOffset_v1
gpu_clock_info.type = NVML_CLOCK_GRAPHICS
gpu_clock_info.pstate = NVML_PSTATE_0
gpu_clock_info.clockOffsetMHz = GPU_CLOCK_OFFSET

# Offsets the curve, this is the actual undervolt. However, it doesn't mean the card will run at a maximum of (MAX_LOCKED_CLOCK + CLOCK_OFFSET) MHz.
# It means that at MAX_LOCKED_CLOCK MHz, it will use the voltage that it would've used at (MAX_LOCKED_CLOCK - CLOCK_OFFSET) MHz before the offset.
status_code = nvmlDeviceSetClockOffsets(device=device, info=byref(gpu_clock_info))

if status_code != NVML_SUCCESS:
    print("Error setting GPU clock offset:", nvmlErrorString(status_code).decode())
    raise Exception("Failed to set GPU clock offset")

mem_clock_info = c_nvmlClockOffset_t()
mem_clock_info.version = nvmlClockOffset_v1
mem_clock_info.type = NVML_CLOCK_MEM
mem_clock_info.pstate = NVML_PSTATE_0
mem_clock_info.clockOffsetMHz = MEM_CLOCK_OFFSET

# Offsets the memory clock as well, which can help with stability on some cards.
status_code = nvmlDeviceSetClockOffsets(device=device, info=byref(mem_clock_info))

if status_code != NVML_SUCCESS:
    print("Error setting memory clock offset:", nvmlErrorString(status_code).decode())
    raise Exception("Failed to set memory clock offset")

nvmlShutdown()
print("NVIDIA device undervolt applied successfully.")
