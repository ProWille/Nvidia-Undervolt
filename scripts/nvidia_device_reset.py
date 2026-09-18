#!/usr/bin/env python3
import sys
import argparse
from pynvml import *
from ctypes import byref

from nvidia_device_config import load_config, get_int, DEFAULT_CONFIG_PATH

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
    parser.add_argument("--gpu-index", type=int, default=None, help=f"GPU device index (default: {DEFAULT_DEVICE_INDEX})")
    parser.add_argument("--config", default=None, help=f"Config file path (default: {DEFAULT_CONFIG_PATH})")
    args = parser.parse_args()

    try:
        nvmlInit()
        config = load_config(args.config or DEFAULT_CONFIG_PATH)
        gpu_index = args.gpu_index if args.gpu_index is not None else get_int(config, "gpu-index", DEFAULT_DEVICE_INDEX)
        device = nvmlDeviceGetHandleByIndex(index=gpu_index)
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
