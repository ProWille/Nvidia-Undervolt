# NVIDIA Undervolt

A set of small Python + shell tools to undervolt and monitor an NVIDIA GPU
through NVML ([nvidia-ml-py](https://github.com/nicolargo/nvidia-ml-py)).

Tested on an RTX 3070 Ti with Python 3.14.

## Requirements

- Linux with an NVIDIA GPU and the proprietary driver (`nvidia-smi` works)
- Python 3.8+
- [nvidia-ml-py](https://pypi.org/project/nvidia-ml-py/) >= 13 (the `pynvml`
  module it ships is what the scripts import)

> The old `pynvml` PyPI package is a deprecated shim that prints a
> `FutureWarning` on import. Install `nvidia-ml-py` instead; the import stays
> `from pynvml import *`.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Scripts

| Script | Purpose |
| --- | --- |
| `nvidia_device_undervolt.py` | Apply the undervolt: lock GPU clocks, cap power, offset the GPU/memory V-F curve. **Requires root.** |
| `nvidia_device_reset.py` | Revert all of the above to driver defaults. **Requires root.** |
| `nvidia_device_info.py` | One-shot read of state, clocks, offsets, and power limits. |
| `nvidia_device_monitor.py` | Live monitor (clear-screen loop) of usage, clocks, temperature, fan, and power. |
| `nvidia_device_pstates.py` | Print min/max clocks per supported performance state. |
| `nvidia-device-info.sh` | Same idea as `nvidia_device_info.py` but through `nvidia-smi`. |

### Common options

All scripts accept `--gpu-index` (default `0`). The monitor additionally takes
`--interval` in seconds (default `2`).

### Undervolt defaults

Tunables live at the top of `nvidia_device_undervolt.py` (also CLI-overridable):

| Option | Default | Meaning |
| --- | --- | --- |
| `--min-clock` / `--max-clock` | `210` / `1995` MHz | Locked clock range. Valid values: `nvidia-smi -q -d SUPPORTED_CLOCKS` |
| `--power-limit` | `230` W | Hard power cap; GPU throttles clocks to stay under it |
| `--gpu-offset` | `165` MHz | Curve offset — at `max_clock` MHz the GPU uses the voltage it would use at `max_clock - offset` MHz |
| `--mem-offset` | `550` MHz | Memory offset, doubled internally for GDDR (displayed halved, e.g. `500` in info) |

Example:

```bash
sudo .venv/bin/python nvidia_device_undervolt.py \
  --gpu-index 0 --min-clock 210 --max-clock 1995 \
  --power-limit 230 --gpu-offset 165 --mem-offset 550
```

The setter scripts need root because NVML treats clock/power changes as
privileged operations.

## systemd integration

The repo ships three units that apply the undervolt at boot and re-apply it
after resume:

| Unit | Runs |
| --- | --- |
| `nvidia-undervolt.service` | `nvidia_device_undervolt.py` at boot; `nvidia_device_reset.py` on stop |
| `nvidia-undervolt-suspend.service` | `nvidia_device_reset.py` before suspend/hibernate |
| `nvidia-undervolt-resume.service` | `nvidia_device_undervolt.py` after resume (`nvidia-resume.service`) |

Install (adjusting paths to the venv):

```bash
sudo cp nvidia_device_*.py /usr/local/bin/
# point /usr/local/bin/nvidia-device-undervolt and nvidia-device-reset
# at the venv python, e.g.:
sudo tee /usr/local/bin/nvidia-device-undervolt >/dev/null <<'EOF'
#!/bin/bash
exec /opt/nvidia-undervolt/.venv/bin/python /usr/local/bin/nvidia_device_undervolt.py "$@"
EOF
# ... same for nvidia-device-reset, then:
sudo cp nvidia-undervolt*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now nvidia-undervolt.service \
  nvidia-undervolt-suspend.service nvidia-undervolt-resume.service
```