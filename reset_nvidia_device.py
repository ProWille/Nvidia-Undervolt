#!/usr/bin/env python
from pynvml import *

DEVICE_INDEX = 0

nvmlInit()
device = nvmlDeviceGetHandleByIndex(index=DEVICE_INDEX)

# Reset locked clocks to default values
nvmlDeviceResetGpuLockedClocks(handle=device)
nvmlDeviceResetMemoryLockedClocks(handle=device)

# Reset power limit to the default value
default_power_limit = nvmlDeviceGetPowerManagementDefaultLimit(handle=device)
nvmlDeviceSetPowerManagementLimit(handle=device, limit=default_power_limit)

gpu_clock_info = c_nvmlClockOffset_t()
gpu_clock_info.version = nvmlClockOffset_v1
gpu_clock_info.type = NVML_CLOCK_GRAPHICS
gpu_clock_info.pstate = NVML_PSTATE_0
gpu_clock_info.clockOffsetMHz = 0

# Offsets the curve back to default
status_code = nvmlDeviceSetClockOffsets(device=device, info=byref(gpu_clock_info))

if status_code != NVML_SUCCESS:
    print("Error setting GPU clock offset:", nvmlErrorString(status_code).decode())
    raise Exception("Failed to set GPU clock offset")

mem_clock_info = c_nvmlClockOffset_t()
mem_clock_info.version = nvmlClockOffset_v1
mem_clock_info.type = NVML_CLOCK_MEM
mem_clock_info.pstate = NVML_PSTATE_0
mem_clock_info.clockOffsetMHz = 0

# Offsets the memory clock back to default
status_code = nvmlDeviceSetClockOffsets(device=device, info=byref(mem_clock_info))

if status_code != NVML_SUCCESS:
    print("Error setting memory clock offset:", nvmlErrorString(status_code).decode())
    raise Exception("Failed to set memory clock offset")

nvmlShutdown()
print("NVIDIA device reset to default settings successfully.")
