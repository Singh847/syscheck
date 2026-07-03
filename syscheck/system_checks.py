"""System health checks: CPU, memory, disk, uptime, top processes."""
import platform
import datetime
import psutil


def get_system_info():
    return {
        "hostname": platform.node(),
        "os": f"{platform.system()} {platform.release()}",
        "python": platform.python_version(),
        "boot_time": datetime.datetime.fromtimestamp(
            psutil.boot_time()
        ).strftime("%Y-%m-%d %H:%M:%S"),
    }


def check_cpu(warn_at=80):
    usage = psutil.cpu_percent(interval=1)
    return {
        "name": "CPU usage",
        "value": f"{usage}%",
        "status": "WARN" if usage >= warn_at else "OK",
    }


def check_memory(warn_at=80):
    mem = psutil.virtual_memory()
    return {
        "name": "Memory usage",
        "value": f"{mem.percent}% of {round(mem.total / 1e9, 1)} GB",
        "status": "WARN" if mem.percent >= warn_at else "OK",
    }


def check_disks(warn_at=85):
    results = []
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
        except (PermissionError, OSError):
            continue
        results.append({
            "name": f"Disk {part.device}",
            "value": f"{usage.percent}% used "
                     f"({round(usage.free / 1e9, 1)} GB free)",
            "status": "WARN" if usage.percent >= warn_at else "OK",
        })
    return results


def top_processes(n=5):
    procs = []
    for p in psutil.process_iter(["name", "memory_percent"]):
        try:
            procs.append((p.info["name"], p.info["memory_percent"] or 0))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    procs.sort(key=lambda x: x[1], reverse=True)
    return [{"name": f"Process: {name}",
             "value": f"{round(mem, 1)}% memory",
             "status": "INFO"} for name, mem in procs[:n]]


def run_all(cfg=None):
    t = (cfg or {}).get("thresholds", {})
    checks = [
        check_cpu(t.get("cpu_warn", 80)),
        check_memory(t.get("memory_warn", 80)),
    ]
    checks.extend(check_disks(t.get("disk_warn", 85)))
    checks.extend(top_processes())
    return checks
