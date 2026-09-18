#!/usr/bin/env bash
#
# NVIDIA Undervolt — installer and uninstaller
#
# Usage:
#   ./install.sh                install everything, ask first (interactive)
#   ./install.sh --yes          install with safe defaults, no prompts
#   ./install.sh --dry-run      print what would happen, change nothing
#   ./install.sh uninstall      remove services, wrappers and files
#   ./install.sh --help         show usage
#
# Flags:
#   --no-services     skip installing the systemd units
#   --apply-now       start the undervolt service immediately after install
#   --config FILE     config file to install (default: /etc/nvidia-undervolt.conf)
#
# Paths can also be overridden with the environment variables
# NVUNDERVOLT_INSTALL_DIR, NVUNDERVOLT_BIN_DIR and NVUNDERVOLT_CONFIG_FILE.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="${NVUNDERVOLT_INSTALL_DIR:-/opt/nvidia-undervolt}"
BIN_DIR="${NVUNDERVOLT_BIN_DIR:-/usr/local/bin}"
CONFIG_FILE="${NVUNDERVOLT_CONFIG_FILE:-/etc/nvidia-undervolt.conf}"
VENV_DIR="$INSTALL_DIR/.venv"
PYTHON_BIN="${PYTHON:-python3}"
SERVICE_DIR="$SCRIPT_DIR/systemd"
SCRIPTS_SRC="$SCRIPT_DIR/scripts"
CONFIG_EXAMPLE="$SCRIPT_DIR/config/nvidia-undervolt.conf.example"

CORE_SCRIPTS=(nvidia_device_undervolt.py nvidia_device_reset.py nvidia_device_info.py nvidia_device_monitor.py nvidia_device_pstates.py)
SCRIPTS=("${CORE_SCRIPTS[@]}" nvidia_device_config.py)
UNITS=(nvidia-undervolt.service nvidia-undervolt-suspend.service nvidia-undervolt-resume.service)

ASSUME_YES=0
DRY_RUN=0
WITH_SERVICES=1
APPLY_NOW=0

info()  { printf '\033[1;34m::\033[0m %s\n' "$*"; }
warn()  { printf '\033[1;33m!!\033[0m %s\n' "$*" >&2; }
die()   { printf '\033[1;31m!!\033[0m %s\n' "$*" >&2; exit 1; }

# Run a command, or show it when in dry-run mode.
run() {
    if [[ "$DRY_RUN" -eq 1 ]]; then
        printf '[dry-run] %s\n' "$*"
    else
        "$@"
    fi
}

need_root() {
    if [[ "$(id -u)" -ne 0 && "$DRY_RUN" -eq 0 ]]; then
        if ! sudo -v; then
            die "Administrative privileges are required. Please run as root or with a passwordless sudo."
        fi
    fi
}

as_root() {
    if [[ "$(id -u)" -eq 0 ]]; then
        run "$@"
    else
        run sudo "$@"
    fi
}

prompt_yes_no() {
    local question="$1" default="${2:-yes}" answer
    if [[ "$ASSUME_YES" -eq 1 ]]; then
        [[ "$default" == "yes" ]]
        return
    fi
    read -rp "$question [Y/n] " answer </dev/tty || return 1
    case "$answer" in
        ""|y|Y|yes|YES|Yes) return 0 ;;
        *) return 1 ;;
    esac
}

usage() {
    sed -n '2,16p' "$0" | sed -e 's/^# \{0,1\}//'
}

check_prereqs() {
    command -v "$PYTHON_BIN" >/dev/null 2>&1 || die "$PYTHON_BIN not found. Install Python 3.8+ (e.g. python3, python3-venv)."
    "$PYTHON_BIN" -m venv --help >/dev/null 2>&1 || die "$PYTHON_BIN -m venv is unavailable. Install python3-venv (Debian/Ubuntu: python3-venv)."
    if [[ "$WITH_SERVICES" -eq 1 ]]; then
        command -v systemctl >/dev/null 2>&1 || die "systemctl not found. This setup requires systemd (or use --no-services)."
    fi
    if ! command -v nvidia-smi >/dev/null 2>&1; then
        warn "nvidia-smi not found — the NVIDIA driver may be missing. Install it first."
    fi
}

install_venv() {
    info "Creating virtual environment at $VENV_DIR"
    run "$PYTHON_BIN" -m venv "$VENV_DIR"
    info "Installing Python dependencies"
    run "$VENV_DIR/bin/pip" install --quiet -r "$SCRIPT_DIR/requirements.txt"
}

install_scripts() {
    info "Installing scripts to $INSTALL_DIR"
    run mkdir -p "$INSTALL_DIR"
    local script
    for script in "${SCRIPTS[@]}"; do
        if [[ "$DRY_RUN" -eq 1 ]]; then
            printf '[dry-run] cp %s -> %s\n' "$SCRIPTS_SRC/$script" "$INSTALL_DIR/$script"
        else
            cp "$SCRIPTS_SRC/$script" "$INSTALL_DIR/"
        fi
    done
}

install_wrappers() {
    info "Creating wrappers in $BIN_DIR"
    run mkdir -p "$BIN_DIR"
    declare -A WRAPPERS=(
        [nvidia_device_undervolt.py]=nvidia-device-undervolt
        [nvidia_device_reset.py]=nvidia-device-reset
        [nvidia_device_info.py]=nvidia-device-info
        [nvidia_device_monitor.py]=nvidia-device-monitor
        [nvidia_device_pstates.py]=nvidia-device-pstates
    )
    local script name
    for script in "${!WRAPPERS[@]}"; do
        name="${WRAPPERS[$script]}"
        if [[ "$DRY_RUN" -eq 1 ]]; then
            printf '[dry-run] write wrapper %s -> %s\n' "$name" "$BIN_DIR/$name"
            continue
        fi
        cat > "$BIN_DIR/$name" <<EOF
#!/usr/bin/env bash
exec "$VENV_DIR/bin/python" "$INSTALL_DIR/$script" "\$@"
EOF
        chmod +x "$BIN_DIR/$name"
    done
}

install_config() {
    if [[ -f "$CONFIG_FILE" ]]; then
        info "Config file $CONFIG_FILE already exists — leaving it untouched."
        return
    fi
    if ! prompt_yes_no "Install example config to $CONFIG_FILE?"; then
        info "Skipping config file. The undervolt script will use built-in defaults."
        return
    fi
    if [[ "$DRY_RUN" -eq 1 ]]; then
        printf '[dry-run] cp %s -> %s\n' "$CONFIG_EXAMPLE" "$CONFIG_FILE"
        return
    fi
    as_root cp "$CONFIG_EXAMPLE" "$CONFIG_FILE"
    info "Config file installed at $CONFIG_FILE — edit it to tune your undervolt."
}

install_services() {
    info "Installing systemd units"
    local unit
    for unit in "${UNITS[@]}"; do
        as_root cp "$SERVICE_DIR/$unit" "/etc/systemd/system/$unit"
    done
    as_root systemctl daemon-reload

    if prompt_yes_no "Enable nvidia-undervolt.service (apply at boot)?"; then
        as_root systemctl enable nvidia-undervolt.service
        if [[ "$APPLY_NOW" -eq 1 ]] || prompt_yes_no "Start it now to apply the undervolt immediately?" no; then
            as_root systemctl start nvidia-undervolt.service
        fi
    fi
}

install() {
    info "NVIDIA Undervolt installer"
    check_prereqs
    need_root

    install_venv
    install_scripts
    install_wrappers
    install_config

    if [[ "$WITH_SERVICES" -eq 1 ]]; then
        local proceed=1
        if [[ "$ASSUME_YES" -eq 0 ]]; then
            prompt_yes_no "Install the systemd services (boot + suspend/resume handling)?" || proceed=0
        fi
        if [[ "$proceed" -eq 1 ]]; then
            install_services
        else
            info "Skipping systemd services. Run the scripts manually or re-run the installer."
        fi
    else
        info "Skipping systemd services (--no-services)."
    fi

    info "Done."
    warn "Remember to edit $CONFIG_FILE (or pass CLI flags) before relying on the applied values."
}

uninstall() {
    info "NVIDIA Undervolt uninstaller"
    need_root

    local unit
    for unit in "${UNITS[@]}"; do
        as_root systemctl disable --now "${unit%.service}" >/dev/null 2>&1 || true
        as_root rm -f "/etc/systemd/system/$unit"
    done
    as_root systemctl daemon-reload

    declare -A WRAPPERS=(
        [nvidia-device-undervolt]=1 [nvidia-device-reset]=1 [nvidia-device-info]=1
        [nvidia-device-monitor]=1 [nvidia-device-pstates]=1
    )
    local name
    for name in "${!WRAPPERS[@]}"; do
        as_root rm -f "$BIN_DIR/$name"
    done

    if [[ -d "$INSTALL_DIR" ]] && prompt_yes_no "Remove $INSTALL_DIR (scripts + venv)?" no; then
        as_root rm -rf "$INSTALL_DIR"
    fi

    if [[ -f "$CONFIG_FILE" ]] && prompt_yes_no "Remove $CONFIG_FILE as well?" no; then
        as_root rm -f "$CONFIG_FILE"
    fi

    info "Uninstall complete."
}

COMMAND="install"
while [[ $# -gt 0 ]]; do
    case "$1" in
        install)      COMMAND="install" ;;
        uninstall)    COMMAND="uninstall" ;;
        --yes|-y)     ASSUME_YES=1 ;;
        --dry-run)    DRY_RUN=1 ;;
        --no-services) WITH_SERVICES=0 ;;
        --apply-now)  APPLY_NOW=1 ;;
        --install-dir) shift; INSTALL_DIR="$1" ;;
        --bin-dir)    shift; BIN_DIR="$1" ;;
        --config)     shift; CONFIG_FILE="$1" ;;
        -h|--help)    usage; exit 0 ;;
        *) die "Unknown argument: $1 (see --help)" ;;
    esac
    shift
done

"$COMMAND"