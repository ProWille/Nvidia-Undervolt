#!/usr/bin/env python
from pynvml import *
from ctypes import byref

DEVICE_INDEX = 0

def get_device_usage(device) -> None:
    device_power_usage = nvmlDeviceGetPowerUsage(handle=device) // 1000
    device_temperature = nvmlDeviceGetTemperature(handle=device, sensor=NVML_TEMPERATURE_GPU)
    device_usage = nvmlDeviceGetUtilizationRates(handle=device).gpu
    device_mem_info = nvmlDeviceGetMemoryInfo(handle=device)
    device_mem_usage = (device_mem_info.used / device_mem_info.total) * 100

    print("Power Usage\tTemperature\tGPU Usage\tMemory Usage")
    print(f"{device_power_usage} W\t\t{device_temperature} °C\t\t{device_usage} %\t\t{device_mem_usage:.0f} %\n")

def get_gpu_clock_info(device) -> None:
    gpu_clock_info = c_nvmlClockOffset_t()
    gpu_clock_info.version = nvmlClockOffset_v1
    gpu_clock_info.type = NVML_CLOCK_GRAPHICS
    gpu_clock_info.pstate = NVML_PSTATE_0

    status_code = nvmlDeviceGetClockOffsets(device=device, info=byref(gpu_clock_info))

    if status_code != NVML_SUCCESS:
        print("Error getting GPU clock offset:", nvmlErrorString(result=status_code).decode())
        raise Exception("Failed to get GPU clock offset.")

    current_gpu_clock = nvmlDeviceGetClockInfo(handle=device, type=NVML_CLOCK_GRAPHICS)
    gpu_clock_offset = gpu_clock_info.clockOffsetMHz
    max_gpu_clock = nvmlDeviceGetMaxClockInfo(handle=device, type=NVML_CLOCK_GRAPHICS)

    print("GPU Current Clock\tGPU Clock Offset\tGPU Max Clock")
    print(f"{current_gpu_clock} MHz\t\t{gpu_clock_offset} MHz\t\t\t{max_gpu_clock} MHz\n")

def get_mem_clock_info(device) -> None:
    current_mem_clock = nvmlDeviceGetClockInfo(handle=device, type=NVML_CLOCK_MEM)
    mem_clock_offset = nvmlDeviceGetMemClkVfOffset(device=device) // 2
    max_mem_clock = nvmlDeviceGetMaxClockInfo(handle=device, type=NVML_CLOCK_MEM)

    print("Mem Current Clock\tMem Clock Offset\tMem Max Clock")
    print(f"{current_mem_clock} MHz\t\t{mem_clock_offset} MHz\t\t\t{max_mem_clock} MHz\n")

def get_power_limit_info(device) -> None:
    default_power_limit = nvmlDeviceGetPowerManagementDefaultLimit(handle=device) // 1000
    current_power_limit = nvmlDeviceGetPowerManagementLimit(handle=device) // 1000
    range_power_limit = [i // 1000 for i in nvmlDeviceGetPowerManagementLimitConstraints(handle=device)]

    print("Power Limit Default\tPower Limit Current\tPower Limit Range")
    print(f"{default_power_limit} W\t\t\t{current_power_limit} W\t\t\t{range_power_limit[0]} - {range_power_limit[1]} W\n")

def main() -> None:
    try:
        nvmlInit()
        device = nvmlDeviceGetHandleByIndex(index=DEVICE_INDEX)
        print(f"Device Name\n{nvmlDeviceGetName(handle=device)}\n")
        get_device_usage(device=device)
        get_gpu_clock_info(device=device)
        get_mem_clock_info(device=device)
        get_power_limit_info(device=device)
    except NVMLError as err:
        print("Failed to initialize NVML or get device handle:", err)
    except Exception as e:
        print("An error occurred:", e)
    finally:
        nvmlShutdown()

if __name__ == "__main__":
    main()
