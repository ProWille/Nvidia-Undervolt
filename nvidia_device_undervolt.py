#!/usr/bin/env python3
import sys
import argparse
from pynvml import *
from ctypes import byref

DEFAULT_DEVICE_INDEX = 0
DEFAULT_MIN_GPU_LOCKED_CLOCK = 210
DEFAULT_MAX_GPU_LOCKED_CLOCK = 1995
DEFAULT_POWER_LIMIT = 230
DEFAULT_GPU_CLOCK_OFFSET = 165
DEFAULT_MEM_CLOCK_OFFSET = 550

# Sets minimum and maximum GPU clocks, You can find valid clock values with command: nvidia-smi -q -d SUPPORTED_CLOCKS.
# If you're happy with the maximum clock value of your GPU, you can omit this function.
def set_gpu_locked_clocks(device, min_locked_clock: int, max_locked_clock: int) -> None:
    nvmlDeviceSetGpuLockedClocks(handle=device, minGpuClockMHz=min_locked_clock, maxGpuClockMHz=max_locked_clock)

# Sets the power limit which has nothing to do with undervolting and can be omitted.
# The GPU will throttle itself (reduce clocks) to stay within this value.
def set_power_limit(device, power_limit: int) -> None:
    power_limit_range = nvmlDeviceGetPowerManagementLimitConstraints(handle=device)
    power_limit *= 1000
    if power_limit < power_limit_range[0] or power_limit > power_limit_range[1]:
        raise ValueError(f"Power limit {power_limit} is out of range ({power_limit_range[0]} - {power_limit_range[1]}).")

    status_code = nvmlDeviceSetPowerManagementLimit_v2(device=device, powerScope=NVML_POWER_SCOPE_GPU, powerLimit=power_limit)
    if status_code != NVML_SUCCESS:
        raise Exception("Failed to set power limit with error code:", nvmlErrorString(status_code).decode())

# Offsets the curve, this is the actual undervolt. However, it doesn't mean the card will run at a maximum of (MAX_LOCKED_CLOCK + CLOCK_OFFSET) MHz.
# It means that at MAX_LOCKED_CLOCK MHz, it will use the voltage that it would've used at (MAX_LOCKED_CLOCK - CLOCK_OFFSET) MHz before the offset.
def set_gpu_clock_offset(device, clock_offset: int) -> None:
    gpu_clock_info = c_nvmlClockOffset_t()
    gpu_clock_info.version = nvmlClockOffset_v1
    gpu_clock_info.type = NVML_CLOCK_GRAPHICS
    gpu_clock_info.pstate = NVML_PSTATE_0
    gpu_clock_info.clockOffsetMHz = clock_offset

    status_code = nvmlDeviceSetClockOffsets(device=device, info=byref(gpu_clock_info))
    if status_code != NVML_SUCCESS:
        raise Exception("Failed to set GPU clock offset with error code:", nvmlErrorString(status_code).decode())

# Offsets the memory clock as well, which can help with stability on some cards.
def set_memory_clock_offset(device, clock_offset: int) -> None:
    mem_clock_info = c_nvmlClockOffset_t()
    mem_clock_info.version = nvmlClockOffset_v1
    mem_clock_info.type = NVML_CLOCK_MEM
    mem_clock_info.pstate = NVML_PSTATE_0
    mem_clock_info.clockOffsetMHz = clock_offset * 2

    status_code = nvmlDeviceSetClockOffsets(device=device, info=byref(mem_clock_info))
    if status_code != NVML_SUCCESS:
        raise Exception("Failed to set memory clock offset with error code:", nvmlErrorString(status_code).decode())

def main() -> None:
    parser = argparse.ArgumentParser(description="NVIDIA GPU Undervolt")
    parser.add_argument("--gpu-index", type=int, default=DEFAULT_DEVICE_INDEX, help="GPU device index (default: %(default)s)")
    parser.add_argument("--min-clock", type=int, default=DEFAULT_MIN_GPU_LOCKED_CLOCK, help="Minimum GPU clock in MHz (default: %(default)s)")
    parser.add_argument("--max-clock", type=int, default=DEFAULT_MAX_GPU_LOCKED_CLOCK, help="Maximum GPU clock in MHz (default: %(default)s)")
    parser.add_argument("--power-limit", type=int, default=DEFAULT_POWER_LIMIT, help="Power limit in Watts (default: %(default)s)")
    parser.add_argument("--gpu-offset", type=int, default=DEFAULT_GPU_CLOCK_OFFSET, help="GPU clock offset in MHz (default: %(default)s)")
    parser.add_argument("--mem-offset", type=int, default=DEFAULT_MEM_CLOCK_OFFSET, help="Memory clock offset in MHz (default: %(default)s)")
    args = parser.parse_args()

    try:
        nvmlInit()
        device = nvmlDeviceGetHandleByIndex(index=args.gpu_index)
        set_gpu_locked_clocks(device=device, min_locked_clock=args.min_clock, max_locked_clock=args.max_clock)
        set_power_limit(device=device, power_limit=args.power_limit)
        set_gpu_clock_offset(device=device, clock_offset=args.gpu_offset)
        set_memory_clock_offset(device=device, clock_offset=args.mem_offset)
        device_name = nvmlDeviceGetName(handle=device)
        print(f"Undervolt applied to {device_name}:\
              \nGPU Locked Clocks : {args.min_clock}-{args.max_clock} MHz\
              \nPower Limit       : {args.power_limit} W\
              \nGPU Clock Offset  : {args.gpu_offset} MHz\
              \nMem Clock Offset  : {args.mem_offset} MHz")
    except NVMLError as err:
        print("NVMLError:", err, file=sys.stderr)
        sys.exit(1)
    except ValueError as ve:
        print("ValueError:", ve, file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print("Exception:", e, file=sys.stderr)
        sys.exit(1)
    finally:
        nvmlShutdown()

if __name__ == "__main__":
    main()
