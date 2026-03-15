#!/usr/bin/env python3
import sys
import argparse
from pynvml import *
from math import inf
from time import sleep

DEFAULT_DEVICE_INDEX = 0
DEFAULT_INTERVAL_SECONDS = 2

class NvidiaDeviceInfo:
    def __init__(self, device_index: int) -> None:
        self.min_performance_state, self.max_performance_state = -inf, inf
        self.min_power_usage, self.max_power_usage = inf, -inf
        self.min_temperature, self.max_temperature = inf, -inf
        self.min_fan_speed, self.max_fan_speed = inf, -inf
        self.min_device_usage, self.max_device_usage = inf, -inf
        self.min_gpu_clock, self.max_gpu_clock = inf, -inf
        self.min_memory_usage, self.max_memory_usage = inf, -inf
        self.min_memory_clock, self.max_memory_clock = inf, -inf
        self.lines = []
        self.device = nvmlDeviceGetHandleByIndex(index=device_index)

    def __print_device_info(self, measurement: str, unit: str, value: int, min_value: int, max_value: int) -> None:
        if unit:
            self.lines.append(f"{measurement} ({unit}):")
        else:
            self.lines.append(f"{measurement}:")
        self.lines.append(f"Current\t\tMin\t\tMax")
        self.lines.append(f"{value:<5}\t\t{min_value:<5}\t\t{max_value:<5}\n")

    def print_device_info(self) -> None:
        print('\033c', end='')
        print('\n'.join(self.lines))
        self.lines.clear()

    def get_performance_state(self) -> None:
        performance_state = nvmlDeviceGetPerformanceState(handle=self.device)
        self.min_performance_state = max(performance_state, self.min_performance_state)
        self.max_performance_state = min(performance_state, self.max_performance_state)
        self.__print_device_info('Performance State', '', performance_state, self.min_performance_state, self.max_performance_state)

    def get_power_usage(self) -> None:
        power_usage = nvmlDeviceGetPowerUsage(handle=self.device) // 1000
        self.min_power_usage = min(power_usage, self.min_power_usage)
        self.max_power_usage = max(power_usage, self.max_power_usage)
        self.__print_device_info('Power Usage', 'W', power_usage, self.min_power_usage, self.max_power_usage)

    def get_temperature(self) -> None:
        temperature = nvmlDeviceGetTemperature(handle=self.device, sensor=NVML_TEMPERATURE_GPU)
        self.min_temperature = min(temperature, self.min_temperature)
        self.max_temperature = max(temperature, self.max_temperature)
        self.__print_device_info('Temperature', '°C', temperature, self.min_temperature, self.max_temperature)

    def get_fan_speed(self) -> None:
        fan_speed = nvmlDeviceGetFanSpeed(handle=self.device)
        self.min_fan_speed = min(fan_speed, self.min_fan_speed)
        self.max_fan_speed = max(fan_speed, self.max_fan_speed)
        self.__print_device_info('Fan Speed', '%', fan_speed, self.min_fan_speed, self.max_fan_speed)

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
        memory_info = nvmlDeviceGetMemoryInfo(handle=self.device)
        memory_usage = round((memory_info.used / memory_info.total) * 100)
        self.min_memory_usage = min(memory_usage, self.min_memory_usage)
        self.max_memory_usage = max(memory_usage, self.max_memory_usage)
        self.__print_device_info('Memory Usage', '%', memory_usage, self.min_memory_usage, self.max_memory_usage)

    def get_memory_clock(self) -> None:
        memory_clock = nvmlDeviceGetClockInfo(handle=self.device, type=NVML_CLOCK_MEM)
        self.min_memory_clock = min(memory_clock, self.min_memory_clock)
        self.max_memory_clock = max(memory_clock, self.max_memory_clock)
        self.__print_device_info('Memory Clock', 'MHz', memory_clock, self.min_memory_clock, self.max_memory_clock)

def get_device_info(device_index: int, interval_seconds: int) -> None:
    device = NvidiaDeviceInfo(device_index=device_index)
    while True:
        device.get_performance_state()
        device.get_power_usage()
        device.get_temperature()
        device.get_fan_speed()
        device.get_device_usage()
        device.get_device_clock()
        device.get_memory_usage()
        device.get_memory_clock()
        device.print_device_info()
        sleep(interval_seconds)

def main() -> None:
    parser = argparse.ArgumentParser(description="NVIDIA GPU Monitor")
    parser.add_argument("--gpu-index", type=int, default=DEFAULT_DEVICE_INDEX, help="GPU device index (default: %(default)s)")
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL_SECONDS, help="Monitoring interval in seconds (default: %(default)s)")
    args = parser.parse_args()

    try:
        nvmlInit()
        get_device_info(device_index=args.gpu_index, interval_seconds=args.interval)
    except KeyboardInterrupt:
        print("Monitoring stopped by user.")
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
