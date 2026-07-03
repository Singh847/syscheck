"""Read recent system error events on Windows or Linux.

Windows: queries the System Event Log via wevtutil (XML output).
Linux:   tries journalctl first, falls back to /var/log/syslog.
"""
import platform
import subprocess
import xml.etree.ElementTree as ET


def _windows_errors(count):
    cmd = ["wevtutil", "qe", "System", f"/c:{count}",
           "/rd:true", "/q:*[System[(Level=2)]]", "/f:xml"]
    try:
        out = subprocess.run(cmd, capture_output=True,
                             text=True, timeout=20).stdout
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []
    ns = "{http://schemas.microsoft.com/win/2004/08/events/event}"
    events = []
    for chunk in out.split("</Event>"):
        if "<Event" not in chunk:
            continue
        try:
            ev = ET.fromstring(chunk + "</Event>")
            provider = ev.find(f"{ns}System/{ns}Provider")
            time_el = ev.find(f"{ns}System/{ns}TimeCreated")
            name = provider.get("Name", "?") if provider is not None else "?"
            when = time_el.get("SystemTime", "")[:19] if time_el is not None else ""
            events.append({
                "name": f"EventLog: {name}",
                "value": when,
                "status": "WARN",
            })
        except ET.ParseError:
            continue
    return events


def _linux_errors(count):
    for cmd in (
        ["journalctl", "-p", "err", "-n", str(count), "--no-pager",
         "-o", "short"],
        ["tail", "-n", str(count), "/var/log/syslog"],
    ):
        try:
            out = subprocess.run(cmd, capture_output=True,
                                 text=True, timeout=20).stdout
        except (subprocess.TimeoutExpired, FileNotFoundError):
            continue
        lines = [line for line in out.strip().splitlines()
                 if line and not line.startswith("--")][:count]
        if lines:
            return [{"name": "Syslog error",
                     "value": line[:90],
                     "status": "WARN"} for line in lines]
    return []


def recent_errors(count=10):
    if platform.system() == "Windows":
        events = _windows_errors(count)
    else:
        events = _linux_errors(count)
    if not events:
        return [{"name": "System event log",
                 "value": "no recent errors found (or access denied)",
                 "status": "OK"}]
    return events
