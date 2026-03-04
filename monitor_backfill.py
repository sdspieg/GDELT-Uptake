#!/usr/bin/env python3
"""
GDELT Backfill Monitor — Live colorful progress tracker.
Connects to VPS, parses /tmp/gdelt_backfill.log, shows progress.

Usage:
    pip install rich
    python monitor_backfill.py
"""

import re
import subprocess
import sys
import time
import datetime as dt

try:
    from rich.console import Console, Group
    from rich.live import Live
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich import box
except ImportError:
    print("pip install rich")
    sys.exit(1)

VPS = "138.201.62.161"
VPS_USER = "root"
VPS_PASS = "r6XPuJKbnm4k5G"
LOG_FILE = "/tmp/gdelt_backfill.log"

console = Console()


def ssh_cmd(cmd: str) -> str:
    try:
        r = subprocess.run(
            ["sshpass", "-p", VPS_PASS, "ssh", "-o", "StrictHostKeyChecking=no",
             "-o", "ConnectTimeout=5", f"{VPS_USER}@{VPS}", cmd],
            capture_output=True, text=True, timeout=15
        )
        return r.stdout.strip()
    except Exception as e:
        return f"ERROR: {e}"


def parse_progress(line: str):
    """Parse tqdm line like: Downloading events:  69%|..| 96951/141216 [12:43:21<5:40:05, 2.17file/s, new=48416, filtered=...]"""
    m = re.search(
        r'(\d+)%\|[^|]*\|\s*(\d+)/(\d+)\s*\[([^<]+)<([^,]+),\s*([\d.]+)file/s(?:,\s*new=(\d+))?(?:,\s*filtered=(\d+))?',
        line
    )
    if not m:
        return None
    return {
        "pct": int(m.group(1)),
        "current": int(m.group(2)),
        "total": int(m.group(3)),
        "elapsed": m.group(4).strip(),
        "eta": m.group(5).strip(),
        "speed": float(m.group(6)),
        "new": int(m.group(7)) if m.group(7) else 0,
        "filtered": int(m.group(8)) if m.group(8) else 0,
    }


def check_alive() -> bool:
    out = ssh_cmd("pgrep -f 'update_gdelt.*--from' 2>/dev/null")
    return bool(out.strip()) and "ERROR" not in out


def get_db_count() -> str:
    return ssh_cmd(
        "psql -h localhost -U postgres -d war_datasets -t -c "
        "\"SELECT to_char(COUNT(*), 'FM999,999,999') FROM global_events.gdelt_events\" 2>/dev/null"
    ).strip()


def build_display(p: dict | None, alive: bool, db_count: str, refresh: int):
    """Returns a Group of (panel with header+bar, stats table)."""
    now = dt.datetime.now().strftime("%H:%M:%S")

    if p is None:
        panel = Panel(
            Text("Waiting for progress data...", style="yellow"),
            title="[bold blue] GDELT BACKFILL MONITOR [/]",
            border_style="blue",
        )
        return Group(panel)

    # Status indicator
    if not alive:
        status_text = " FINISHED " if p["pct"] >= 99 else " STOPPED "
        status_style = "bold white on green" if p["pct"] >= 99 else "bold white on red"
    else:
        status_text = " RUNNING "
        status_style = "bold white on green"

    # Progress bar
    bar_width = 50
    filled = int(bar_width * p["current"] / p["total"])
    bar = Text()
    bar.append("█" * filled, style="bold cyan")
    bar.append("░" * (bar_width - filled), style="dim")
    bar.append(f"  {p['pct']}%", style="bold white")

    # Estimate which date the backfill has reached
    files_per_day = 96  # 24h * 4 per hour
    days_done = p["current"] / files_per_day
    start_date = dt.date(2022, 2, 21)
    current_date = start_date + dt.timedelta(days=days_done)

    # Header line
    header = Text()
    header.append("  GDELT BACKFILL ", style="bold white on blue")
    header.append(f"  {now}", style="bright_white")
    header.append(f"  │  refresh #{refresh}", style="dim")

    # Panel content: header + bar
    content = Text()
    content.append_text(header)
    content.append("\n\n  ")
    content.append_text(bar)
    content.append("\n")

    panel = Panel(
        content,
        title="[bold blue]  update_gdelt.py --events-only --from 2022-02-21  [/]",
        subtitle="[dim]Ctrl+C to exit  │  refreshes every 10s[/]",
        border_style="bright_blue",
        padding=(0, 1),
    )

    # Stats table
    t = Table(box=box.SIMPLE, show_header=False, padding=(0, 2), expand=True)
    t.add_column("label", style="bold", width=16)
    t.add_column("value", ratio=1)
    t.add_column("label2", style="bold", width=16)
    t.add_column("value2", ratio=1)

    t.add_row(
        "Files:", f"[cyan]{p['current']:,}[/] / [white]{p['total']:,}[/]",
        "Speed:", f"[yellow]{p['speed']:.1f}[/] files/sec",
    )
    t.add_row(
        "Current date:", f"[bright_green]~{current_date}[/]",
        "Target:", "[white]2026-03-02[/]",
    )
    t.add_row(
        "Elapsed:", f"[magenta]{p['elapsed']}[/]",
        "ETA:", f"[{'green' if alive else 'dim'}]{p['eta']}[/]",
    )
    t.add_row(
        "New events:", f"[bold green]{p['new']:,}[/]",
        "Filtered:", f"[yellow]{p['filtered']:,}[/]",
    )
    t.add_row(
        "DB total:", f"[bold cyan]{db_count}[/]" if db_count and not db_count.startswith("ERROR") else f"[dim]{db_count}[/]",
        "Process:", Text(status_text, style=status_style),
    )

    return Group(panel, t)


def main():
    refresh = 0
    db_cache = "..."
    alive_cache = True
    console.clear()

    with Live(console=console, refresh_per_second=1, screen=False) as live:
        try:
            while True:
                refresh += 1

                # Get last progress line — tqdm uses \r not \n, so tail + tr to get latest
                raw = ssh_cmd(
                    f"tail -c 500 {LOG_FILE} | tr '\\r' '\\n' | grep 'Downloading' | tail -1"
                )
                p = parse_progress(raw) if raw and "ERROR" not in raw else None

                # Check if still alive (every 3rd refresh to save SSH calls)
                if refresh % 3 == 1:
                    alive_cache = check_alive()

                # DB count (every 5th refresh)
                if refresh % 5 == 1:
                    result = get_db_count()
                    if result and "ERROR" not in result:
                        db_cache = result

                display = build_display(p, alive_cache, db_cache, refresh)
                live.update(display)

                time.sleep(10)

        except KeyboardInterrupt:
            console.print("\n[dim]Stopped.[/]")


if __name__ == "__main__":
    main()
