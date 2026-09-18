#!/usr/bin/env python3
import sys
import argparse
from pynvml import *
from ctypes import byref

DEFAULT_DEVICE_INDEX = 0

# Reset gpu locked clocks to default values.
def reset_gpu_locked_clocks(device) -> None:
    nvmlDeviceResetGpuLockedClocks(handle=device)

# Reset power limit to the default value.
def reset_power_limit(device) -> None:
    power_limit_default = nvmlDeviceGetPowerManagementDefaultLimit(handle=device)

    status_code = nvmlDeviceSetPowerManagementLimit_v2(device=device, powerScope=NVML_POWER_SCOPE_GPU, powerLimit=power_limit_default)
    if status_code != NVML_SUCCESS:
        raise Exception("Failed to reset power limit with error code:", nvmlErrorString(result=status_code))

# Offsets the curve back to default.
def reset_gpu_clock_offset(device) -> None:
    gpu_clock_info = c_nvmlClockOffset_t()
    gpu_clock_info.version = nvmlClockOffset_v1
    gpu_clock_info.type = NVML_CLOCK_GRAPHICS
    gpu_clock_info.pstate = NVML_PSTATE_0
    gpu_clock_info.clockOffsetMHz = 0

    status_code = nvmlDeviceSetClockOffsets(device=device, info=byref(gpu_clock_info))
    if status_code != NVML_SUCCESS:
        raise Exception("Failed to reset GPU clock offset with error code:", nvmlErrorString(result=status_code))

# Offsets the memory clock back to default.
def reset_memory_clock_offset(device) -> None:
    mem_clock_info = c_nvmlClockOffset_t()
    mem_clock_info.version = nvmlClockOffset_v1
    mem_clock_info.type = NVML_CLOCK_MEM
    mem_clock_info.pstate = NVML_PSTATE_0
    mem_clock_info.clockOffsetMHz = 0

    status_code = nvmlDeviceSetClockOffsets(device=device, info=byref(mem_clock_info))
    if status_code != NVML_SUCCESS:
        raise Exception("Failed to reset memory clock offset with error code:", nvmlErrorString(result=status_code))

def main() -> None:
    parser = argparse.ArgumentParser(description="NVIDIA GPU Reset")
    parser.add_argument("--gpu-index", type=int, default=DEFAULT_DEVICE_INDEX, help="GPU device index (default: %(default)s)")
    args = parser.parse_args()

    try:
        nvmlInit()
        device = nvmlDeviceGetHandleByIndex(index=args.gpu_index)
        reset_gpu_locked_clocks(device=device)
        reset_power_limit(device=device)
        reset_gpu_clock_offset(device=device)
        reset_memory_clock_offset(device=device)
        device_name = nvmlDeviceGetName(handle=device)
        print(f"Device reset applied to {device_name} with default settings.")
    except NVMLError as err:
        print("NVMLError:", err, file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print("Exception:", e, file=sys.stderr)
        sys.exit(1)
    finally:
        nvmlShutdown()

if __name__ == "__main__":
    main()
