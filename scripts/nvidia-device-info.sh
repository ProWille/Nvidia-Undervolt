#!/bin/bash
# This script retrieves and displays various NVIDIA GPU information using nvidia-smi.

# Display basic GPU info
nvidia-smi --query-gpu=index,name,driver_version --format=csv
echo

# Display power limits and usage
nvidia-smi --query-gpu=power.default_limit,power.min_limit,power.max_limit --format=csv
nvidia-smi --query-gpu=power.draw,power.limit,power.draw.average --format=csv
echo

# Display clock speeds
nvidia-smi --query-gpu=clocks.max.graphics,clocks.max.memory --format=csv
nvidia-smi --query-gpu=clocks.current.graphics,clocks.current.memory --format=csv
echo

# Display temperature, utilization, fan speed, performance state, and memory usage
nvidia-smi --query-gpu=temperature.gpu,utilization.gpu --format=csv
nvidia-smi --query-gpu=fan.speed,pstate --format=csv
nvidia-smi --query-gpu=memory.total,memory.used,memory.free --format=csv
