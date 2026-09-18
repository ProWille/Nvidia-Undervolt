#!/usr/bin/env python3
import sys
import argparse
from pynvml import *

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
    parser.add_argument("--gpu-index", type=int, default=DEFAULT_DEVICE_INDEX, help="GPU device index (default: %(default)s)")
    args = parser.parse_args()

    try:
        nvmlInit()
        device = nvmlDeviceGetHandleByIndex(index=args.gpu_index)
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
