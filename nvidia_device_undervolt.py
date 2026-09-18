#!/usr/bin/env python3
import sys
import argparse
from pynvml import *
from ctypes import byref

from nvidia_device_config import load_config, get_int, DEFAULT_CONFIG_PATH

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
        raise Exception("Failed to set power limit with error code:", nvmlErrorString(status_code))


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
        raise Exception("Failed to set GPU clock offset with error code:", nvmlErrorString(status_code))


# Offsets the memory clock as well, which can help with stability on some cards.
def set_memory_clock_offset(device, clock_offset: int) -> None:
    mem_clock_info = c_nvmlClockOffset_t()
    mem_clock_info.version = nvmlClockOffset_v1
    mem_clock_info.type = NVML_CLOCK_MEM
    mem_clock_info.pstate = NVML_PSTATE_0
    mem_clock_info.clockOffsetMHz = clock_offset * 2

    status_code = nvmlDeviceSetClockOffsets(device=device, info=byref(mem_clock_info))
    if status_code != NVML_SUCCESS:
        raise Exception("Failed to set memory clock offset with error code:", nvmlErrorString(status_code))


def emit_config(device) -> None:
    """Print a complete config file pre-filled with this GPU's limits."""
    power_range = nvmlDeviceGetPowerManagementLimitConstraints(handle=device)
    power_min = power_range[0] // 1000
    power_max = power_range[1] // 1000
    device_name = nvmlDeviceGetName(handle=device)

    print(f"# NVIDIA Undervolt configuration — generated from {device_name}")
    print(f"# Path: {DEFAULT_CONFIG_PATH}")
    print(f"#")
    print(f"# Setting any value beyond its valid range will produce an error")
    print(f"# when the undervolt is applied.  Run this script with --emit-config")
    print(f"# again after hardware changes to regenerate valid limits.\n")

    print(f"gpu-index   = {DEFAULT_DEVICE_INDEX}")
    print(f"min-clock   = {DEFAULT_MIN_GPU_LOCKED_CLOCK}   # valid: see `nvidia-smi -q -d SUPPORTED_CLOCKS`")
    print(f"max-clock   = {DEFAULT_MAX_GPU_LOCKED_CLOCK}   # valid: see `nvidia-smi -q -d SUPPORTED_CLOCKS`")
    print(f"power-limit = {DEFAULT_POWER_LIMIT}   # valid range for this GPU: {power_min} – {power_max} W")
    print(f"gpu-offset  = {DEFAULT_GPU_CLOCK_OFFSET}   # MHz (the V–F curve offset)")
    print(f"mem-offset  = {DEFAULT_MEM_CLOCK_OFFSET}   # MHz (displayed half, doubled internally)")


def main() -> None:
    parser = argparse.ArgumentParser(description="NVIDIA GPU Undervolt")
    parser.add_argument("--gpu-index", type=int, default=None, help=f"GPU device index (default: {DEFAULT_DEVICE_INDEX})")
    parser.add_argument("--min-clock", type=int, default=None, help=f"Minimum GPU clock in MHz (default: {DEFAULT_MIN_GPU_LOCKED_CLOCK})")
    parser.add_argument("--max-clock", type=int, default=None, help=f"Maximum GPU clock in MHz (default: {DEFAULT_MAX_GPU_LOCKED_CLOCK})")
    parser.add_argument("--power-limit", type=int, default=None, help=f"Power limit in Watts (default: {DEFAULT_POWER_LIMIT})")
    parser.add_argument("--gpu-offset", type=int, default=None, help=f"GPU clock offset in MHz (default: {DEFAULT_GPU_CLOCK_OFFSET})")
    parser.add_argument("--mem-offset", type=int, default=None, help=f"Memory clock offset in MHz (default: {DEFAULT_MEM_CLOCK_OFFSET})")
    parser.add_argument("--config", default=None, help=f"Config file path (default: {DEFAULT_CONFIG_PATH})")
    parser.add_argument("--emit-config", action="store_true", help="Print a default config file to stdout and exit")
    args = parser.parse_args()

    try:
        nvmlInit()

        device = nvmlDeviceGetHandleByIndex(index=0)
        if args.emit_config:
            emit_config(device)
            return

        config = load_config(args.config or DEFAULT_CONFIG_PATH)
        gpu_index   = args.gpu_index   if args.gpu_index   is not None else get_int(config, "gpu-index",   DEFAULT_DEVICE_INDEX)
        min_clock   = args.min_clock   if args.min_clock   is not None else get_int(config, "min-clock",   DEFAULT_MIN_GPU_LOCKED_CLOCK)
        max_clock   = args.max_clock   if args.max_clock   is not None else get_int(config, "max-clock",   DEFAULT_MAX_GPU_LOCKED_CLOCK)
        power_limit = args.power_limit if args.power_limit is not None else get_int(config, "power-limit", DEFAULT_POWER_LIMIT)
        gpu_offset  = args.gpu_offset  if args.gpu_offset  is not None else get_int(config, "gpu-offset",  DEFAULT_GPU_CLOCK_OFFSET)
        mem_offset  = args.mem_offset  if args.mem_offset  is not None else get_int(config, "mem-offset",  DEFAULT_MEM_CLOCK_OFFSET)

        device = nvmlDeviceGetHandleByIndex(index=gpu_index)
        set_gpu_locked_clocks(device=device, min_locked_clock=min_clock, max_locked_clock=max_clock)
        set_power_limit(device=device, power_limit=power_limit)
        set_gpu_clock_offset(device=device, clock_offset=gpu_offset)
        set_memory_clock_offset(device=device, clock_offset=mem_offset)
        device_name = nvmlDeviceGetName(handle=device)
        print(
            f"Undervolt applied to {device_name}:"
            f"\nGPU Locked Clocks : {min_clock}-{max_clock} MHz"
            f"\nPower Limit       : {power_limit} W"
            f"\nGPU Clock Offset  : {gpu_offset} MHz"
            f"\nMem Clock Offset  : {mem_offset} MHz"
        )
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
