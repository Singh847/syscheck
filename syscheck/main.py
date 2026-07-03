"""SysCheck CLI — run diagnostics and generate a report.

Usage:
    python -m syscheck.main                  # all checks, rich table
    python -m syscheck.main --system         # system health only
    python -m syscheck.main --network        # network checks only
    python -m syscheck.main --logs           # include OS error events
    python -m syscheck.main --json           # machine-readable output
    python -m syscheck.main --report         # also save an HTML report
    python -m syscheck.main --config my.json # custom thresholds/hosts
"""
import argparse
import json as jsonlib

from rich.console import Console
from rich.table import Table

from syscheck import config, system_checks, network_checks, log_checks, report

console = Console()
STYLE = {"OK": "green", "WARN": "yellow", "FAIL": "red", "INFO": "cyan"}


def main():
    parser = argparse.ArgumentParser(
        description="SysCheck - IT support diagnostics toolkit")
    parser.add_argument("--system", action="store_true",
                        help="run system health checks only")
    parser.add_argument("--network", action="store_true",
                        help="run network checks only")
    parser.add_argument("--logs", action="store_true",
                        help="include recent system error events")
    parser.add_argument("--json", action="store_true",
                        help="print results as JSON instead of a table")
    parser.add_argument("--report", action="store_true",
                        help="also save an HTML report")
    parser.add_argument("--config", default="config.json",
                        help="path to config file (default: config.json)")
    args = parser.parse_args()

    cfg = config.load(args.config)

    run_sys = args.system or not args.network
    run_net = args.network or not args.system

    info = system_checks.get_system_info()

    checks = []
    if run_sys:
        checks += system_checks.run_all(cfg)
    if run_net:
        checks += network_checks.run_all(cfg)
    if args.logs:
        checks += log_checks.recent_errors(cfg.get("log_errors_to_show", 10))

    if args.json:
        print(jsonlib.dumps({"system": info, "checks": checks}, indent=2))
    else:
        console.print(f"[bold]SysCheck[/bold] on {info['hostname']} "
                      f"({info['os']})\n")
        table = Table(title="Diagnostic Results")
        table.add_column("Check")
        table.add_column("Result")
        table.add_column("Status")
        for c in checks:
            table.add_row(c["name"], c["value"],
                          f"[{STYLE[c['status']]}]{c['status']}[/]")
        console.print(table)

        issues = [c for c in checks if c["status"] in ("WARN", "FAIL")]
        console.print(f"\n{len(issues)} issue(s) flagged.")

    if args.report:
        path = report.build_report(info, checks)
        if not args.json:
            console.print(f"Report saved to [bold]{path}[/bold]")


if __name__ == "__main__":
    main()
