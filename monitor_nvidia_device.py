#!/usr/bin/env python
from pynvml import *
from math import inf
from time import sleep

DEVICE_INDEX = 0
INTERVAL_SECONDS = 2

class NvidiaDeviceInfo:
    def __init__(self, device_index: int) -> None:
        self.min_power_usage, self.max_power_usage = inf, -inf
        self.min_temperature, self.max_temperature = inf, -inf
        self.min_device_usage, self.max_device_usage = inf, -inf
        self.min_gpu_clock, self.max_gpu_clock = inf, -inf
        self.min_memory_usage, self.max_memory_usage = inf, -inf
        self.min_memory_clock, self.max_memory_clock = inf, -inf
        self.lines = []
        self.device = nvmlDeviceGetHandleByIndex(index=device_index)

    def __print_device_info(self, measurement: str, unit: str, value: int, min_value: int, max_value: int) -> None:
        self.lines.append(f"{measurement} ({unit}):")
        self.lines.append(f"Current\t\tMin\t\tMax")
        self.lines.append(f"{value}\t\t{min_value}\t\t{max_value}\n")

    def print_device_info(self) -> None:
        print('\033c', end='')
        print('\n'.join(self.lines))
        self.lines.clear()

    def get_power_usage(self) -> None:
        current_power_usage = nvmlDeviceGetPowerUsage(handle=self.device) // 1000
        self.min_power_usage = min(current_power_usage, self.min_power_usage)
        self.max_power_usage = max(current_power_usage, self.max_power_usage)
        self.__print_device_info('Power Usage', 'W', current_power_usage, self.min_power_usage, self.max_power_usage)

    def get_temperature(self) -> None:
        current_temperature = nvmlDeviceGetTemperature(handle=self.device, sensor=NVML_TEMPERATURE_GPU)
        self.min_temperature = min(current_temperature, self.min_temperature)
        self.max_temperature = max(current_temperature, self.max_temperature)
        self.__print_device_info('Temperature', '°C', current_temperature, self.min_temperature, self.max_temperature)

    def get_device_usage(self) -> None:
        device_usage = nvmlDeviceGetUtilizationRates(handle=self.device).gpu
        self.min_device_usage = min(device_usage, self.min_device_usage)
        self.max_device_usage = max(device_usage, self.max_device_usage)
        self.__print_device_info('Device Usage', '%', device_usage, self.min_device_usage, self.max_device_usage)

    def get_device_clock(self) -> None:
        gpu_clock = nvmlDeviceGetClockInfo(handle=self.device, type=NVML_CLOCK_GRAPHICS)
        self.min_gpu_clock = min(gpu_clock, self.min_gpu_clock)
        self.max_gpu_clock = max(gpu_clock, self.max_gpu_clock)
        self.__print_device_info('GPU Clock', 'MHz', gpu_clock, self.min_gpu_clock, self.max_gpu_clock)

    def get_memory_usage(self) -> None:
        device_mem_info = nvmlDeviceGetMemoryInfo(handle=self.device)
        device_mem_usage = round((device_mem_info.used / device_mem_info.total) * 100)
        self.min_memory_usage = min(device_mem_usage, self.min_memory_usage)
        self.max_memory_usage = max(device_mem_usage, self.max_memory_usage)
        self.__print_device_info('Memory Usage', '%', device_mem_usage, self.min_memory_usage, self.max_memory_usage)

    def get_memory_clock(self) -> None:
        memory_clock = nvmlDeviceGetClockInfo(handle=self.device, type=NVML_CLOCK_MEM)
        self.min_memory_clock = min(memory_clock, self.min_memory_clock)
        self.max_memory_clock = max(memory_clock, self.max_memory_clock)
        self.__print_device_info('Memory Clock', 'MHz', memory_clock, self.min_memory_clock, self.max_memory_clock)

def get_device_info(device_index: int, interval_seconds: int) -> None:
    device = NvidiaDeviceInfo(device_index=device_index)
    while True:
        device.get_power_usage()
        device.get_temperature()
        device.get_device_usage()
        device.get_device_clock()
        device.get_memory_usage()
        device.get_memory_clock()
        device.print_device_info()
        sleep(interval_seconds)

def main() -> None:
    try:
        nvmlInit()
        get_device_info(device_index=DEVICE_INDEX, interval_seconds=INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("Monitoring stopped by user.")
    except NVMLError as err:
        print("Failed to initialize NVML or get device handle:", err)
    except Exception as e:
        print("An error occurred during monitoring:", e)
    finally:
        nvmlShutdown()

if __name__ == "__main__":
    main()
