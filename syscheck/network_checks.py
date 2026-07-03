"""Network diagnostics: ping, DNS resolution, port connectivity.

The checks follow standard support isolation order:
1. ping        -> basic IP connectivity
2. dns_lookup  -> separates "no internet" from "DNS is broken"
3. check_port  -> detects firewall / service-level blocking
"""
import platform
import socket
import subprocess


def ping(host="8.8.8.8"):
    flag = "-n" if platform.system() == "Windows" else "-c"
    try:
        result = subprocess.run(
            ["ping", flag, "2", host],
            capture_output=True, timeout=10,
        )
        ok = result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        ok = False
    return {
        "name": f"Ping {host}",
        "value": "reachable" if ok else "unreachable",
        "status": "OK" if ok else "FAIL",
    }


def dns_lookup(domain="google.com"):
    try:
        ip = socket.gethostbyname(domain)
        return {"name": f"DNS lookup {domain}",
                "value": f"resolved to {ip}", "status": "OK"}
    except socket.gaierror:
        return {"name": f"DNS lookup {domain}",
                "value": "resolution failed", "status": "FAIL"}


def check_port(host, port, label):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(3)
    try:
        open_ = sock.connect_ex((host, port)) == 0
    except socket.gaierror:
        open_ = False
    finally:
        sock.close()
    return {
        "name": f"{label} ({host}:{port})",
        "value": "open" if open_ else "closed/blocked",
        "status": "OK" if open_ else "WARN",
    }


def run_all(cfg=None):
    net = (cfg or {}).get("network", {})
    checks = [
        ping(net.get("ping_host", "8.8.8.8")),
        dns_lookup(net.get("dns_domain", "google.com")),
    ]
    for p in net.get("ports", []):
        checks.append(check_port(p["host"], p["port"], p["label"]))
    return checks
