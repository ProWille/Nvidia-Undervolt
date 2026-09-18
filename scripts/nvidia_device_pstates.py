#!/usr/bin/env python3
import sys
import argparse
from pynvml import *

from nvidia_device_config import load_config, get_int, DEFAULT_CONFIG_PATH

DEFAULT_DEVICE_INDEX = 0
CLOCK_TYPES = {
    "CLOCK_GRAPHICS": NVML_CLOCK_GRAPHICS,
    "CLOCK_SM": NVML_CLOCK_SM,
    "CLOCK_MEM": NVML_CLOCK_MEM,
    "CLOCK_VIDEO": NVML_CLOCK_VIDEO
}

def get_min_max_clock_of_pstate(device, pstate, clock_types: dict) -> None:
    lines = []
    lines.append(f"PSTATE_{pstate}:")
    lines.append(f"  Clock Type\t\tMin\t\tMax")
    for name, clock_type in clock_types.items():
        min_clock, max_clock = nvmlDeviceGetMinMaxClockOfPState(device=device, clockType=clock_type, pstate=pstate)
        lines.append(f"  {name:<20}{min_clock:<8}{max_clock:<8}")
    print('\n'.join(lines))

def main() -> None:
    parser = argparse.ArgumentParser(description="NVIDIA GPU Performance States")
    parser.add_argument("--gpu-index", type=int, default=None, help=f"GPU device index (default: {DEFAULT_DEVICE_INDEX})")
    parser.add_argument("--config", default=None, help=f"Config file path (default: {DEFAULT_CONFIG_PATH})")
    args = parser.parse_args()

    try:
        nvmlInit()
        config = load_config(args.config or DEFAULT_CONFIG_PATH)
        gpu_index = args.gpu_index if args.gpu_index is not None else get_int(config, "gpu-index", DEFAULT_DEVICE_INDEX)
        device = nvmlDeviceGetHandleByIndex(index=gpu_index)
        supported_pstates = nvmlDeviceGetSupportedPerformanceStates(device=device)
        for pstate in supported_pstates:
            get_min_max_clock_of_pstate(device=device, pstate=pstate, clock_types=CLOCK_TYPES)
    except NVMLError as err:
        print("NVMLError:", err)
        sys.exit(1)
    except Exception as e:
        print("Exception:", e)
        sys.exit(1)
    finally:
        nvmlShutdown()

if __name__ == "__main__":
    main()
