"""Load configuration with sensible defaults."""
import json
import pathlib

DEFAULTS = {
    "thresholds": {"cpu_warn": 80, "memory_warn": 80, "disk_warn": 85},
    "network": {
        "ping_host": "8.8.8.8",
        "dns_domain": "google.com",
        "ports": [
            {"host": "google.com", "port": 443, "label": "HTTPS outbound"},
            {"host": "8.8.8.8", "port": 53, "label": "DNS outbound"},
        ],
    },
    "log_errors_to_show": 10,
}


def load(path="config.json"):
    """Load config.json, merging user values over defaults.

    Falls back to defaults if the file is missing or invalid JSON,
    so the tool never crashes on a broken config.
    """
    cfg = json.loads(json.dumps(DEFAULTS))  # deep copy of defaults
    p = pathlib.Path(path)
    if p.exists():
        try:
            user_cfg = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return cfg
        for key, value in user_cfg.items():
            if isinstance(value, dict) and key in cfg and isinstance(cfg[key], dict):
                cfg[key].update(value)
            else:
                cfg[key] = value
    return cfg
