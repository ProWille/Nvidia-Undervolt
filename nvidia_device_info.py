#!/usr/bin/env python3
import sys
import argparse
from pynvml import *
from ctypes import byref

DEFAULT_DEVICE_INDEX = 0

def get_device_info(device) -> None:
    device_name = nvmlDeviceGetName(handle=device)
    performance_state = nvmlDeviceGetPerformanceState(handle=device)
    temperature = nvmlDeviceGetTemperature(handle=device, sensor=NVML_TEMPERATURE_GPU)

    print(f"Device Name\t\t\tDevice P-State\tTemperature")
    print(f"{device_name}\tP{performance_state}\t\t{temperature:<3} °C\n")

def get_device_usage(device) -> None:
    power_usage = nvmlDeviceGetPowerUsage(handle=device) // 1000
    fan_speed = nvmlDeviceGetFanSpeed(handle=device)
    device_usage = nvmlDeviceGetUtilizationRates(handle=device).gpu
    memory_info = nvmlDeviceGetMemoryInfo(handle=device)
    memory_usage = int((memory_info.used / memory_info.total) * 100)

    print("Power Usage\tFan Speed\tGPU Usage\tMemory Usage")
    print(f"{power_usage:<3} W\t\t{fan_speed:<3} %\t\t{device_usage:<3} %\t\t{memory_usage:<3} %\n")

def get_gpu_clock_info(device) -> None:
    gpu_clock_info = c_nvmlClockOffset_t()
    gpu_clock_info.version = nvmlClockOffset_v1
    gpu_clock_info.type = NVML_CLOCK_GRAPHICS
    gpu_clock_info.pstate = NVML_PSTATE_0

    status_code = nvmlDeviceGetClockOffsets(device=device, info=byref(gpu_clock_info))
    if status_code != NVML_SUCCESS:
        raise Exception("Failed to get GPU clock offset with error code:", nvmlErrorString(result=status_code))

    current_gpu_clock = nvmlDeviceGetClockInfo(handle=device, type=NVML_CLOCK_GRAPHICS)
    offset_gpu_clock = gpu_clock_info.clockOffsetMHz
    max_gpu_clock = nvmlDeviceGetMaxClockInfo(handle=device, type=NVML_CLOCK_GRAPHICS)

    print("GPU Clock Current\tGPU Clock Offset\tGPU Clock Max")
    print(f"{current_gpu_clock:<5} MHz\t\t{offset_gpu_clock:<5} MHz\t\t{max_gpu_clock:<5} MHz\n")

def get_mem_clock_info(device) -> None:
    current_mem_clock = nvmlDeviceGetClockInfo(handle=device, type=NVML_CLOCK_MEM)
    offset_mem_clock = nvmlDeviceGetMemClkVfOffset(device=device) // 2
    max_mem_clock = nvmlDeviceGetMaxClockInfo(handle=device, type=NVML_CLOCK_MEM)

    print("Mem Clock Current\tMem Clock Offset\tMem Clock Max")
    print(f"{current_mem_clock:<5} MHz\t\t{offset_mem_clock:<5} MHz\t\t{max_mem_clock:<5} MHz\n")

def get_power_limit_info(device) -> None:
    current_power_limit = nvmlDeviceGetPowerManagementLimit(handle=device) // 1000
    default_power_limit = nvmlDeviceGetPowerManagementDefaultLimit(handle=device) // 1000
    range_power_limit = [i // 1000 for i in nvmlDeviceGetPowerManagementLimitConstraints(handle=device)]

    print("Power Limit Current\tPower Limit Default\tPower Limit Range")
    print(f"{current_power_limit:<5} W\t\t\t{default_power_limit:<5} W\t\t\t{range_power_limit[0]} - {range_power_limit[1]} W\n")

def main() -> None:
    parser = argparse.ArgumentParser(description="NVIDIA GPU Info")
    parser.add_argument("--gpu-index", type=int, default=DEFAULT_DEVICE_INDEX, help="GPU device index (default: %(default)s)")
    args = parser.parse_args()

    try:
        nvmlInit()
        device = nvmlDeviceGetHandleByIndex(index=args.gpu_index)
        get_device_info(device=device)
        get_device_usage(device=device)
        get_gpu_clock_info(device=device)
        get_mem_clock_info(device=device)
        get_power_limit_info(device=device)
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
