#!/usr/bin/env python
from pynvml import *

DEVICE_INDEX = 0

# Reset gpu locked clocks to default values.
def reset_gpu_locked_clocks(device) -> None:
    nvmlDeviceResetGpuLockedClocks(handle=device)

# Reset power limit to the default value.
def reset_power_limit(device) -> None:
    default_power_limit = nvmlDeviceGetPowerManagementDefaultLimit(handle=device)
    nvmlDeviceSetPowerManagementLimit(handle=device, limit=default_power_limit)

# Offsets the curve back to default.
def reset_gpu_clock_offset(device) -> None:
    gpu_clock_info = c_nvmlClockOffset_t()
    gpu_clock_info.version = nvmlClockOffset_v1
    gpu_clock_info.type = NVML_CLOCK_GRAPHICS
    gpu_clock_info.pstate = NVML_PSTATE_0
    gpu_clock_info.clockOffsetMHz = 0

    status_code = nvmlDeviceSetClockOffsets(device=device, info=byref(gpu_clock_info))

    if status_code != NVML_SUCCESS:
        print("Error setting GPU clock offset:", nvmlErrorString(status_code).decode())
        raise Exception("Failed to set GPU clock offset")

# Offsets the memory clock back to default.
def reset_memory_clock_offset(device) -> None:
    mem_clock_info = c_nvmlClockOffset_t()
    mem_clock_info.version = nvmlClockOffset_v1
    mem_clock_info.type = NVML_CLOCK_MEM
    mem_clock_info.pstate = NVML_PSTATE_0
    mem_clock_info.clockOffsetMHz = 0

    status_code = nvmlDeviceSetClockOffsets(device=device, info=byref(mem_clock_info))

    if status_code != NVML_SUCCESS:
        print("Error setting memory clock offset:", nvmlErrorString(status_code).decode())
        raise Exception("Failed to set memory clock offset")

def main():
    try:
        nvmlInit()
        device = nvmlDeviceGetHandleByIndex(index=DEVICE_INDEX)
        reset_gpu_locked_clocks(device=device)
        reset_power_limit(device=device)
        reset_gpu_clock_offset(device=device)
        reset_memory_clock_offset(device=device)
        print("NVIDIA device reset to default settings successfully.")
    except NVMLError as err:
        print("Failed to initialize NVML or get device handle:", err)
    except Exception as e:
        print("An error occurred:", e)
    finally:
        nvmlShutdown()

if __name__ == "__main__":
    main()
