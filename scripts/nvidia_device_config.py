#!/usr/bin/env python3
"""Shared helpers for the NVIDIA device scripts: load the config file.

The config file is a simple ``key = value`` format with ``#`` comments.
The default location is ``/etc/nvidia-undervolt.conf`` and can be
overridden per script with ``--config``.
"""

import os

DEFAULT_CONFIG_PATH = "/etc/nvidia-undervolt.conf"


def load_config(path=DEFAULT_CONFIG_PATH):
    """Parse the config file into a dict of key -> value strings.

    A missing or unreadable file is not an error; it simply yields an empty
    dict so scripts fall back to their built-in defaults.
    """
    config = {}
    if not path:
        return config
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                key, sep, value = line.partition("=")
                if sep:
                    config[key.strip()] = value.strip()
    except OSError:
        # File does not exist (or no permission to read it) -> use defaults.
        pass
    return config


def get_int(config, key, default):
    """Return ``config[key]`` as an int, or ``default`` when absent/invalid."""
    value = config.get(key)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError:
        raise ValueError(
            f"Invalid value for '{key}' in config: expected an integer, got '{value!r}'"
        )