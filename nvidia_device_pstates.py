#!/home/william/Scripts/Nvidia-Undervolt/.venv/bin/python
from pynvml import *

DEVICE_INDEX = 0
CLOCK_TYPES = {
    "CLOCK_GRAPHICS": NVML_CLOCK_GRAPHICS,
    "CLOCK_SM": NVML_CLOCK_SM,
    "CLOCK_MEM": NVML_CLOCK_MEM,
    "CLOCK_VIDEO": NVML_CLOCK_VIDEO
}

def get_min_max_clock_of_pstate(device, pstate, clock_types: dict) -> None:
    lines = []
    lines.append(f"PSTATE_{pstate}:\n")
    for name, clock_type in clock_types.items():
        clock = nvmlDeviceGetMinMaxClockOfPState(device=device, clockType=clock_type, pstate=pstate)
        lines.append(f"  {name}: {clock}\n")
    print(''.join(lines))

def main() -> None:
    try:
        nvmlInit()
        device = nvmlDeviceGetHandleByIndex(index=DEVICE_INDEX)
        supported_pstates = nvmlDeviceGetSupportedPerformanceStates(device=device)
        for pstate in supported_pstates:
            get_min_max_clock_of_pstate(device=device, pstate=pstate, clock_types=CLOCK_TYPES)
    except NVMLError as err:
        print("NVMLError:", err)
    except Exception as e:
        print("Exception:", e)
    finally:
        nvmlShutdown()

if __name__ == "__main__":
    main()
