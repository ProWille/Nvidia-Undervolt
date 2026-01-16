#!/home/william/Scripts/Nvidia-Undervolt/.venv/bin/python
from pynvml import *

DEVICE_INDEX = 0

# Reset gpu locked clocks to default values.
def reset_gpu_locked_clocks(device) -> None:
    nvmlDeviceResetGpuLockedClocks(handle=device)

# Reset power limit to the default value.
def reset_power_limit(device) -> None:
    power_limit_default = nvmlDeviceGetPowerManagementDefaultLimit(handle=device)

    status_code = nvmlDeviceSetPowerManagementLimit_v2(device=device, powerScope=NVML_POWER_SCOPE_GPU, powerLimit=power_limit_default)
    if status_code != NVML_SUCCESS:
        print("Error resetting power limit:", nvmlErrorString(status_code).decode())
        raise Exception("Failed to reset power limit.")

# Offsets the curve back to default.
def reset_gpu_clock_offset(device) -> None:
    gpu_clock_info = c_nvmlClockOffset_t()
    gpu_clock_info.version = nvmlClockOffset_v1
    gpu_clock_info.type = NVML_CLOCK_GRAPHICS
    gpu_clock_info.pstate = NVML_PSTATE_0
    gpu_clock_info.clockOffsetMHz = 0

    status_code = nvmlDeviceSetClockOffsets(device=device, info=byref(gpu_clock_info))
    if status_code != NVML_SUCCESS:
        print("Error resetting GPU clock offset:", nvmlErrorString(status_code).decode())
        raise Exception("Failed to reset GPU clock offset.")

# Offsets the memory clock back to default.
def reset_memory_clock_offset(device) -> None:
    mem_clock_info = c_nvmlClockOffset_t()
    mem_clock_info.version = nvmlClockOffset_v1
    mem_clock_info.type = NVML_CLOCK_MEM
    mem_clock_info.pstate = NVML_PSTATE_0
    mem_clock_info.clockOffsetMHz = 0

    status_code = nvmlDeviceSetClockOffsets(device=device, info=byref(mem_clock_info))
    if status_code != NVML_SUCCESS:
        print("Error resetting memory clock offset:", nvmlErrorString(status_code).decode())
        raise Exception("Failed to reset memory clock offset.")

def main() -> None:
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
