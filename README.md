# NVIDIA Undervolt

A small set of Python tools to undervolt and monitor an NVIDIA GPU through
NVML ([nvidia-ml-py](https://github.com/nicolargo/nvidia-ml-py)), with an
interactive installer for systemd integration.

Tested on an RTX 3070 Ti with Python 3.14.

> **Disclaimer:** undervolting reduces voltage at a given clock, which lowers
> heat and power draw — it is generally safe, but pushing clocks too far can
> cause instability. The values here are conservative starting points. Tune
> them and stress-test with your usual workload.

## Features

- `undervolt` — lock GPU clocks, cap power, offset the GPU/memory V-F curve
- `reset` — revert everything to driver defaults
- `info` — one-shot read of clocks, offsets, power limits, temperature
- `monitor` — live full-screen monitor of usage, clocks, temperature, fan
- `pstates` — min/max clocks per performance state
- systemd integration: apply at boot, re-apply after resume

## Prerequisites

- Linux with an NVIDIA GPU and the proprietary driver (`nvidia-smi` works)
- Python 3.8+ (with `venv` support; on Debian/Ubuntu: `python3-venv`)

## Quick start

### Option A — run in place (no root)

```bash
git clone https://github.com/ProWille/Nvidia-Undervolt.git
cd Nvidia-Undervolt
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

.venv/bin/python scripts/nvidia_device_info.py          # read-only, safe
sudo .venv/bin/python scripts/nvidia_device_undervolt.py # apply (needs root)
```

The read-only scripts (`info`, `monitor`, `pstates`) work without root;
`undervolt` and `reset` need root because NVML treats clock/power changes as
privileged operations.

### Option B — install with `install.sh` (recommended)

```bash
./install.sh        # interactive: installs everything and asks how far to go
```

What it does:

1. Creates a venv at `/opt/nvidia-undervolt/` (override: `NVUNDERVOLT_INSTALL_DIR`)
2. Installs the scripts and `nvidia-device-*` wrappers in `/usr/local/bin`
3. Installs `/etc/nvidia-undervolt.conf` from the bundled example (skipped if present)
4. Installs the systemd units from `systemd/` and offers to enable / apply now

Useful invocations:

```bash
./install.sh --yes          # non-interactive, safe defaults (does NOT apply the undervolt)
./install.sh --no-services  # install scripts/wrappers/config only
./install.sh --dry-run      # see exactly what would happen
./install.sh uninstall      # remove services, wrappers, venv, config
```

See `./install.sh --help` for all flags.

## Configuration

All values live in `/etc/nvidia-undervolt.conf` (or wherever `--config` points
to). A documented example ships as `nvidia-undervolt.conf.example`.

```ini
gpu-index   = 0
min-clock   = 210
max-clock   = 1995
power-limit = 230
gpu-offset  = 165
mem-offset  = 550
```

**Precedence:** command-line flags > config file > built-in defaults.

| Key | Default | Meaning |
| --- | --- | --- |
| `gpu-index` | `0` | Target GPU; others read this too (`nvidia-smi -L` lists yours) |
| `min-clock` / `max-clock` | `210` / `1995` MHz | Locked clock range; valid values via `nvidia-smi -q -d SUPPORTED_CLOCKS` |
| `power-limit` | `230` W | Hard cap; GPU throttles to stay under it. Valid range shown by `info` |
| `gpu-offset` | `165` MHz | Curve offset: at `max-clock` MHz the GPU uses the voltage of `max-clock - offset` MHz |
| `mem-offset` | `550` MHz | Memory offset (effective GDDR clock; doubled internally, displayed halved) |

To generate a config pre-filled with *your* GPU's detected limits:

```bash
sudo .venv/bin/python scripts/nvidia_device_undervolt.py --emit-config > nvidia-undervolt.conf
```

> `nvidia-undervolt.conf` is git-ignored so you can generate it in the repo
> without accidentally committing your personal values.

## Scripts

All scripts live in `scripts/`. `install.sh` places `nvidia-device-*` wrappers
in `/usr/local/bin`, after which you can call them by name from anywhere.

| Script | Purpose |
| --- | --- |
| `nvidia_device_undervolt.py` | Apply locked clocks, power limit, and curve offsets |
| `nvidia_device_reset.py` | Revert all settings to driver defaults |
| `nvidia_device_info.py` | State, clocks, offsets, power limits, temperature |
| `nvidia_device_monitor.py` | Live monitor loop (`Ctrl+C` to stop) |
| `nvidia_device_pstates.py` | Min/max clocks per performance state |
| `nvidia-device-info.sh` | Quick `nvidia-smi`-based info dump (no Python needed) |
| `nvidia_device_config.py` | Shared config loader (not meant to be run directly) |

All Python scripts accept `--gpu-index` and `--config`; `monitor` also takes
`--interval <seconds>` (default `2`).

Example:

```bash
sudo nvidia-device-undervolt --max-clock 1995 --power-limit 230 --gpu-offset 165 --mem-offset 550
nvidia-device-monitor --interval 1
```

## systemd integration

Two units (installed by `install.sh` from `systemd/`):

| Unit | Runs |
| --- | --- |
| `nvidia-undervolt.service` | `nvidia-device-undervolt` at boot; `nvidia-device-reset` on stop (`RemainAfterExit`) |
| `nvidia-undervolt-resume.service` | `nvidia-device-undervolt` after resume (ordered after `nvidia-resume.service`) |

```bash
systemctl status nvidia-undervolt.service        # check boot-time apply
journalctl -u nvidia-undervolt.service           # see what was applied
```

## Troubleshooting

- **`NVMLError: Insufficient Permissions`** — the setter scripts must run as
  root (`sudo`), or via the installed systemd service.
- **`Insufficient Permissions` after resume**: the resume service needs
  `nvidia-persistenced` running for NVML to work when waking up; enable it with
  `systemctl enable --now nvidia-persistenced`.
- **`ValueError: Power limit ... is out of range`** — your `power-limit` is
  outside the card's supported range; run `info` and use its `Power Limit
  Range` values.
- **GPU loses the undervolt after resume** — check that
  `nvidia-undervolt-resume.service` is enabled and that `nvidia-resume.service`
  (from the driver) exists; the resume unit orders after it.

## License

MIT — see [LICENSE](LICENSE).