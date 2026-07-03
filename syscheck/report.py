"""Generate an HTML diagnostic report — like documentation on a ticket."""
import datetime
import pathlib

COLORS = {"OK": "#2e7d32", "WARN": "#ef6c00",
          "FAIL": "#c62828", "INFO": "#546e7a"}


def build_report(system_info, checks, out_dir="reports"):
    stamp = datetime.datetime.now()
    rows = "".join(
        f"<tr><td>{c['name']}</td><td>{c['value']}</td>"
        f"<td style='color:{COLORS[c['status']]};font-weight:bold'>"
        f"{c['status']}</td></tr>"
        for c in checks
    )
    info = "".join(f"<li><b>{k}:</b> {v}</li>"
                   for k, v in system_info.items())
    issues = sum(1 for c in checks if c["status"] in ("WARN", "FAIL"))
    html = f"""<html><head><title>SysCheck Report</title>
    <style>body{{font-family:Arial;margin:40px}}
    table{{border-collapse:collapse;width:100%}}
    td,th{{border:1px solid #ccc;padding:8px;text-align:left}}
    th{{background:#1f3864;color:white}}</style></head><body>
    <h1>SysCheck Diagnostic Report</h1>
    <p>Generated: {stamp.strftime('%Y-%m-%d %H:%M:%S')} —
    <b>{issues} issue(s) flagged</b></p>
    <h2>System</h2><ul>{info}</ul>
    <h2>Checks</h2>
    <table><tr><th>Check</th><th>Result</th><th>Status</th></tr>
    {rows}</table></body></html>"""

    out = pathlib.Path(out_dir)
    out.mkdir(exist_ok=True)
    path = out / f"syscheck_{stamp.strftime('%Y%m%d_%H%M%S')}.html"
    path.write_text(html, encoding="utf-8")
    return str(path)
