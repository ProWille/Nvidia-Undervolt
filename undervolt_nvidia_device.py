#!/home/william/Scripts/Nvidia-Undervolt/.venv/bin/python
from pynvml import *
from ctypes import byref

# Run command to find the correct index: nvidia-smi --list-gpus.
DEVICE_INDEX = 0
MIN_GPU_LOCKED_CLOCK = 210
MAX_GPU_LOCKED_CLOCK = 1995
POWER_LIMIT = 230_000
GPU_CLOCK_OFFSET = 165
MEM_CLOCK_OFFSET = 550

# Sets minimum and maximum GPU clocks, You can find valid clock values with command: nvidia-smi -q -d SUPPORTED_CLOCKS.
# If you're happy with the maximum clock value of your GPU, you can omit this function.
def set_gpu_locked_clocks(device, min_locked_clock: int, max_locked_clock: int) -> None:
    nvmlDeviceSetGpuLockedClocks(handle=device, minGpuClockMHz=min_locked_clock, maxGpuClockMHz=max_locked_clock)

# Sets the power limit which has nothing to do with undervolting and can be omitted.
# The GPU will throttle itself (reduce clocks) to stay within this value.
def set_power_limit(device, power_limit: int) -> None:
    power_limit_range = nvmlDeviceGetPowerManagementLimitConstraints(handle=device)
    if power_limit < power_limit_range[0] or power_limit > power_limit_range[1]:
        raise ValueError(f"Power limit {power_limit} is out of range ({power_limit_range[0]} - {power_limit_range[1]}).")

    status_code = nvmlDeviceSetPowerManagementLimit_v2(device=device, powerScope=NVML_POWER_SCOPE_GPU, powerLimit=power_limit)
    if status_code != NVML_SUCCESS:
        print("Error setting power limit:", nvmlErrorString(status_code).decode())
        raise Exception("Failed to set power limit.")

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
        print("Error setting GPU clock offset:", nvmlErrorString(status_code).decode())
        raise Exception("Failed to set GPU clock offset.")

# Offsets the memory clock as well, which can help with stability on some cards.
def set_memory_clock_offset(device, clock_offset: int) -> None:
    mem_clock_info = c_nvmlClockOffset_t()
    mem_clock_info.version = nvmlClockOffset_v1
    mem_clock_info.type = NVML_CLOCK_MEM
    mem_clock_info.pstate = NVML_PSTATE_0
    mem_clock_info.clockOffsetMHz = clock_offset * 2

    status_code = nvmlDeviceSetClockOffsets(device=device, info=byref(mem_clock_info))
    if status_code != NVML_SUCCESS:
        print("Error setting memory clock offset:", nvmlErrorString(status_code).decode())
        raise Exception("Failed to set memory clock offset.")

def main() -> None:
    try:
        nvmlInit()
        device = nvmlDeviceGetHandleByIndex(index=DEVICE_INDEX)
        set_gpu_locked_clocks(device=device, min_locked_clock=MIN_GPU_LOCKED_CLOCK, max_locked_clock=MAX_GPU_LOCKED_CLOCK)
        set_power_limit(device=device, power_limit=POWER_LIMIT)
        set_gpu_clock_offset(device=device, clock_offset=GPU_CLOCK_OFFSET)
        set_memory_clock_offset(device=device, clock_offset=MEM_CLOCK_OFFSET)
        print("NVIDIA device undervolt applied successfully.")
    except NVMLError as err:
        print("Failed to initialize NVML or get device handle:", err)
    except ValueError as ve:
        print("Value error:", ve)
    except Exception as e:
        print("An error occurred:", e)
    finally:
        nvmlShutdown()

if __name__ == "__main__":
    main()
