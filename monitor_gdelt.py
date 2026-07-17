import os
#!/usr/bin/env python3
"""
GDELT Database Monitor — Colorful terminal dashboard.
Shows status of all GDELT tables in the war_datasets DB.
Auto-refreshes every 30 seconds (Ctrl+C to stop).
"""

import sys
import time
import datetime as dt
from contextlib import contextmanager

import psycopg2

try:
    from rich.console import Console, Group
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich import box
except ImportError:
    print("Install rich:  pip install rich")
    sys.exit(1)

# ── DB config ────────────────────────────────────────────────────────────
DB_CONFIG = {
    "host": "138.201.62.161",
    "port": 5432,
    "dbname": "war_datasets",
    "user": "postgres",
    "password": os.environ.get("PG_WARDATASETS_PASSWORD", ""),
}
SCHEMA = "global_events"

console = Console(width=100)

BARS = "▁▂▃▄▅▆▇█"

# ── Helpers ──────────────────────────────────────────────────────────────

@contextmanager
def get_conn():
    conn = psycopg2.connect(**DB_CONFIG, connect_timeout=10)
    try:
        yield conn
    finally:
        conn.close()


def q1(cur, sql):
    cur.execute(sql)
    r = cur.fetchone()
    return r[0] if r else None


def qa(cur, sql):
    cur.execute(sql)
    return cur.fetchall()


def fmt_n(n):
    return f"{n:,}" if n is not None else "—"


def fmt_sz(b):
    if b is None: return "—"
    if b >= 1 << 30: return f"{b / (1 << 30):.1f} GB"
    if b >= 1 << 20: return f"{b / (1 << 20):.0f} MB"
    if b >= 1 << 10: return f"{b / (1 << 10):.0f} KB"
    return f"{b} B"


def stale_color(d):
    if d is None: return "dim"
    gap = (dt.date.today() - d).days
    if gap <= 1:  return "bold green"
    if gap <= 3:  return "green"
    if gap <= 7:  return "yellow"
    if gap <= 14: return "dark_orange"
    return "bold red"


def stale_label(d):
    if d is None: return ""
    gap = (dt.date.today() - d).days
    if gap == 0: return "today"
    if gap == 1: return "yesterday"
    return f"{gap}d ago"


def sparkline(daily_dict, n_days, color):
    counts = []
    for i in range(n_days, 0, -1):
        d = dt.date.today() - dt.timedelta(days=i)
        counts.append(daily_dict.get(d.strftime("%Y%m%d"), 0))
    mx = max(counts) if counts else 0
    if mx == 0:
        return Text("▁" * n_days, style="dim")
    t = Text()
    for c in counts:
        idx = int(c / mx * (len(BARS) - 1))
        t.append(BARS[idx], style=color)
    return t


# ── Table definitions ────────────────────────────────────────────────────

TABLES = [
    ("gdelt_events",                   "Events",          "⚡", "cyan",    "sqldate", "int"),
    ("gdelt_gkg_coercive_quotations",  "Coercive GKG",    "💬", "magenta", "date",    "str"),
    ("gdelt_gkg_redline_quotations",   "Red Line GKG",    "🔴", "red",     "date",    "str"),
    ("gdelt_weekly_varx",              "Weekly VARX",      "📊", "green",   "week",    "date"),
    ("gdelt_gkg_themes_lookup",        "Themes Lookup",    "📚", "blue",    None,      None),
]


# ── Fetch everything in one go ───────────────────────────────────────────

def fetch_all():
    with get_conn() as conn:
        cur = conn.cursor()
        results = {}

        for tbl, label, emoji, color, dcol, dtype in TABLES:
            ft = f"{SCHEMA}.{tbl}"
            rows = q1(cur, f"SELECT COUNT(*) FROM {ft}")
            size = q1(cur, f"SELECT pg_total_relation_size('{ft}')")
            dmin = dmax = None
            if dcol:
                if dtype == "int":
                    rmin = q1(cur, f"SELECT MIN({dcol}) FROM {ft}")
                    rmax = q1(cur, f"SELECT MAX({dcol}) FROM {ft}")
                    if rmin: dmin = dt.datetime.strptime(str(rmin), "%Y%m%d").date()
                    if rmax: dmax = dt.datetime.strptime(str(rmax), "%Y%m%d").date()
                elif dtype == "str":
                    rmin = q1(cur, f"SELECT MIN({dcol}) FROM {ft}")
                    rmax = q1(cur, f"SELECT MAX({dcol}) FROM {ft}")
                    if rmin: dmin = dt.datetime.strptime(str(rmin)[:8], "%Y%m%d").date()
                    if rmax: dmax = dt.datetime.strptime(str(rmax)[:8], "%Y%m%d").date()
                elif dtype == "date":
                    dmin = q1(cur, f"SELECT MIN({dcol})::date FROM {ft}")
                    dmax = q1(cur, f"SELECT MAX({dcol})::date FROM {ft}")
            results[tbl] = {"rows": rows, "size": size, "min": dmin, "max": dmax}

        # Daily events last 14 days
        cutoff = int((dt.date.today() - dt.timedelta(days=14)).strftime("%Y%m%d"))
        ev_daily = {str(r[0]): r[1] for r in qa(cur, f"SELECT sqldate, COUNT(*) FROM {SCHEMA}.gdelt_events WHERE sqldate >= {cutoff} GROUP BY sqldate")}

        # Daily GKG last 14 days
        cutoff_s = (dt.date.today() - dt.timedelta(days=14)).strftime("%Y%m%d") + "000000"
        gkg_daily = {r[0]: r[1] for r in qa(cur, f"SELECT LEFT(date::text,8), COUNT(*) FROM {SCHEMA}.gdelt_gkg_coercive_quotations WHERE date >= '{cutoff_s}' GROUP BY 1")}

        # Schema total size
        total_sz = q1(cur, f"SELECT SUM(pg_total_relation_size(quote_ident('{SCHEMA}')||'.'||quote_ident(tablename))) FROM pg_tables WHERE schemaname='{SCHEMA}'")

        cur.close()
    return results, ev_daily, gkg_daily, total_sz


# ── Build dashboard ──────────────────────────────────────────────────────

def build():
    try:
        results, ev_daily, gkg_daily, total_sz = fetch_all()
    except Exception as e:
        return Panel(Text(f"DB error: {e}", style="bold red"), title="GDELT Monitor", border_style="red")

    now = dt.datetime.now().strftime("%H:%M:%S")
    today = dt.date.today()

    # ── Header ────────────────────────────────────────────────────────
    hdr = Text()
    hdr.append(" GDELT MONITOR ", style="bold white on blue")
    hdr.append("  ", style="")
    hdr.append(f"{today}  {now}", style="bright_white")
    hdr.append("  │  ", style="dim")
    hdr.append("war_datasets", style="bold cyan")
    hdr.append(" @ 138.201.62.161", style="dim")

    # ── Status table ──────────────────────────────────────────────────
    t = Table(box=box.SIMPLE_HEAVY, show_header=True,
              header_style="bold bright_white on grey23",
              padding=(0, 1), expand=True)
    t.add_column("", width=2)
    t.add_column("Table", style="bold", ratio=3)
    t.add_column("Rows", justify="right", ratio=2)
    t.add_column("Size", justify="right", ratio=1)
    t.add_column("From", justify="center", ratio=2)
    t.add_column("To", justify="center", ratio=2)
    t.add_column("Age", justify="center", ratio=2)

    total_rows = 0
    for tbl, label, emoji, color, dcol, dtype in TABLES:
        s = results[tbl]
        total_rows += s["rows"] or 0
        sc = stale_color(s["max"])
        t.add_row(
            emoji,
            f"[{color}]{label}[/]",
            fmt_n(s["rows"]),
            fmt_sz(s["size"]),
            str(s["min"]) if s["min"] else "—",
            Text(str(s["max"]) if s["max"] else "—", style=sc),
            Text(stale_label(s["max"]), style=sc),
        )

    t.add_section()
    t.add_row("", "[bold]TOTAL[/]", f"[bold]{fmt_n(total_rows)}[/]",
              f"[bold]{fmt_sz(total_sz)}[/]", "", "", "")

    # ── Sparklines ────────────────────────────────────────────────────
    ev_spark = sparkline(ev_daily, 14, "cyan")
    gkg_spark = sparkline(gkg_daily, 14, "magenta")

    # Date axis: show day numbers
    axis = Text()
    for i in range(14, 0, -1):
        d = today - dt.timedelta(days=i)
        axis.append(f"{d.day % 10}", style="dim")

    spark_lines = Text()
    spark_lines.append("  Events     ", style="bold cyan")
    spark_lines.append_text(ev_spark)
    spark_lines.append("  │  ", style="dim")
    # Show max daily count
    ev_max = max(ev_daily.values()) if ev_daily else 0
    spark_lines.append(f"peak {ev_max}/day", style="dim")
    spark_lines.append("\n")
    spark_lines.append("  Coercive   ", style="bold magenta")
    spark_lines.append_text(gkg_spark)
    spark_lines.append("  │  ", style="dim")
    gkg_max = max(gkg_daily.values()) if gkg_daily else 0
    spark_lines.append(f"peak {gkg_max}/day", style="dim")
    spark_lines.append("\n")
    spark_lines.append("             ", style="")
    spark_lines.append_text(axis)

    # ── Gaps ──────────────────────────────────────────────────────────
    gaps = []
    ev_end = results["gdelt_events"]["max"]
    gkg_end = results["gdelt_gkg_coercive_quotations"]["max"]
    varx_end = results["gdelt_weekly_varx"]["max"]

    if ev_end and (today - ev_end).days > 2:
        g = (today - ev_end).days
        gaps.append(f"  [bold yellow]!![/]  [cyan]Events[/]   {ev_end} → {today}  [dim]({g}d gap)[/]")
    if gkg_end and (today - gkg_end).days > 2:
        g = (today - gkg_end).days
        gaps.append(f"  [bold yellow]!![/]  [magenta]GKG[/]      {gkg_end} → {today}  [dim]({g}d gap)[/]")
    if varx_end and (today - varx_end).days > 9:
        g = (today - varx_end).days
        gaps.append(f"  [bold yellow]!![/]  [green]VARX[/]     {varx_end} → {today}  [dim]({g}d gap)[/]")

    if gaps:
        gap_section = Text.from_markup("\n".join(gaps))
    else:
        gap_section = Text("  All tables current", style="bold green")

    # ── Quick commands ────────────────────────────────────────────────
    cmd_text = Text()
    cmd_text.append("  python update_gdelt.py --events-only --days 3", style="bright_green")
    cmd_text.append("   ← backfill events\n", style="dim")
    cmd_text.append("  python update_gdelt.py --gkg-fallback --days 3", style="bright_green")
    cmd_text.append("  ← backfill GKG\n", style="dim")
    cmd_text.append("  python update_gdelt.py --recompute-varx", style="bright_green")
    cmd_text.append("         ← rebuild VARX", style="dim")

    # ── Assemble ──────────────────────────────────────────────────────
    sep = Text("─" * 98, style="dim bright_blue")

    return Group(
        Text(""),
        hdr,
        sep,
        t,
        sep,
        Text.from_markup("  [bold]ACTIVITY (14 days)[/]"),
        spark_lines,
        Text(""),
        sep,
        Text.from_markup("  [bold]DATA GAPS[/]"),
        gap_section,
        Text(""),
        sep,
        Text.from_markup("  [bold dim]QUICK FIX[/]"),
        cmd_text,
        Text(""),
        Text("  Ctrl+C to exit  |  refreshes every 30s", style="dim"),
        Text(""),
    )


# ── Main ─────────────────────────────────────────────────────────────────

def main():
    console.clear()
    console.print(build())
    try:
        while True:
            time.sleep(30)
            console.clear()
            console.print(build())
    except KeyboardInterrupt:
        console.print("\n[dim]Stopped.[/]")


if __name__ == "__main__":
    main()
