"""
Visualize weekly VARX variables from GKG Coercive Discourse data.
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────────────────
BASE = Path(r"/mnt/g/My Drive/RuBase/Red lines/Datasets/GDELT-Events")
OUT  = BASE / "vizzes"
OUT.mkdir(exist_ok=True)

plt.rcParams.update({
    'figure.facecolor': '#0d1117',
    'axes.facecolor':   '#0d1117',
    'axes.edgecolor':   '#30363d',
    'axes.labelcolor':  '#c9d1d9',
    'text.color':       '#c9d1d9',
    'xtick.color':      '#8b949e',
    'ytick.color':      '#8b949e',
    'grid.color':       '#21262d',
    'grid.alpha':       0.6,
    'figure.dpi':       150,
    'font.family':      'sans-serif',
    'font.size':        10,
    'axes.titlesize':   13,
    'axes.titleweight': 'bold',
})

ACCENT  = '#58a6ff'
ACCENT2 = '#f0883e'
ACCENT3 = '#da3633'
ACCENT4 = '#3fb950'
ACCENT5 = '#bc8cff'
ACCENT6 = '#f778ba'

def save(fig, name):
    fig.savefig(OUT / f"{name}.png", bbox_inches='tight', dpi=180, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"  Saved {name}.png")

# Key events for annotations
KEY_EVENTS = [
    ('2022-02-24', 'Invasion'),
    ('2022-09-21', 'Mobilization'),
    ('2023-10-07', 'Hamas'),
    ('2024-08-06', 'Kursk'),
    ('2024-11-21', 'Oreshnik'),
    ('2025-01-20', 'Trump'),
]

def add_events(ax, ypos_frac=0.95):
    for datestr, label in KEY_EVENTS:
        d = pd.Timestamp(datestr)
        ax.axvline(d, color='#484f58', linestyle=':', alpha=0.5)
        ylim = ax.get_ylim()
        ypos = ylim[0] + (ylim[1] - ylim[0]) * ypos_frac
        ax.annotate(label, xy=(d, ypos), fontsize=7,
                   color='#8b949e', ha='center', va='top', rotation=90)

# ═══════════════════════════════════════════════════════════════════════════════
# LOAD DATA
# ═══════════════════════════════════════════════════════════════════════════════
print("Loading weekly VARX variables...")
df = pd.read_csv(BASE / "gkg_weekly_varx_variables.csv")
df['week'] = pd.to_datetime(df['week'])
print(f"  {len(df)} weeks loaded")

# ═══════════════════════════════════════════════════════════════════════════════
# VIZ 12 — Weekly Volume: All vs Russia-Relevant
# ═══════════════════════════════════════════════════════════════════════════════
print("\n[1/6] Weekly volume time series...")

fig, ax = plt.subplots(figsize=(18, 6))
ax.fill_between(df['week'], df['media_volume_all'], alpha=0.3, color=ACCENT)
ax.plot(df['week'], df['media_volume_all'], color=ACCENT, linewidth=1.5, label='All coercive discourse')
ax.fill_between(df['week'], df['media_volume_russia'], alpha=0.3, color=ACCENT2)
ax.plot(df['week'], df['media_volume_russia'], color=ACCENT2, linewidth=1.5, label='Russia-relevant')

add_events(ax)
ax.set_title("Weekly Coercive Discourse Volume (GKG 2022–2026)")
ax.set_ylabel("Number of articles")
ax.legend(fontsize=10, framealpha=0.3, loc='upper right')
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
ax.tick_params(axis='x', rotation=45)
ax.grid(axis='y', alpha=0.2)
save(fig, "12_weekly_volume_timeseries")

# ═══════════════════════════════════════════════════════════════════════════════
# VIZ 13 — Russia Share Over Time
# ═══════════════════════════════════════════════════════════════════════════════
print("[2/6] Russia share over time...")

fig, ax = plt.subplots(figsize=(18, 5))
ax.fill_between(df['week'], df['russia_share'] * 100, alpha=0.4, color=ACCENT)
ax.plot(df['week'], df['russia_share'] * 100, color=ACCENT, linewidth=1.5)

# Rolling average
rolling = df['russia_share'].rolling(4, center=True).mean() * 100
ax.plot(df['week'], rolling, color=ACCENT3, linewidth=2, linestyle='--', label='4-week rolling avg')

add_events(ax)
ax.axhline(50, color='#484f58', linestyle='--', alpha=0.3)
ax.set_title("Russia-Relevant Share of Coercive Discourse (Weekly)")
ax.set_ylabel("% Russia-relevant")
ax.set_ylim(0, 100)
ax.legend(fontsize=10, framealpha=0.3)
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
ax.tick_params(axis='x', rotation=45)
ax.grid(axis='y', alpha=0.2)
save(fig, "13_russia_share_timeseries")

# ═══════════════════════════════════════════════════════════════════════════════
# VIZ 14 — Media Tone Over Time
# ═══════════════════════════════════════════════════════════════════════════════
print("[3/6] Media tone over time...")

fig, ax = plt.subplots(figsize=(18, 6))

# Plot tone with confidence band
ax.fill_between(df['week'],
                df['media_tone_mean'] - df['media_tone_std'],
                df['media_tone_mean'] + df['media_tone_std'],
                alpha=0.2, color=ACCENT)
ax.plot(df['week'], df['media_tone_mean'], color=ACCENT, linewidth=1.5, label='Mean tone ± 1 std')

# Zero line
ax.axhline(0, color='#484f58', linestyle='--', alpha=0.5)

# Color the area based on tone
ax.fill_between(df['week'], df['media_tone_mean'], 0,
                where=(df['media_tone_mean'] < 0), color=ACCENT3, alpha=0.3, label='Negative')
ax.fill_between(df['week'], df['media_tone_mean'], 0,
                where=(df['media_tone_mean'] > 0), color=ACCENT4, alpha=0.3, label='Positive')

add_events(ax)
ax.set_title("Weekly Media Tone in Coercive Discourse (GKG V2Tone)")
ax.set_ylabel("Average tone (negative = hostile)")
ax.legend(fontsize=9, framealpha=0.3, loc='lower right')
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
ax.tick_params(axis='x', rotation=45)
ax.grid(axis='y', alpha=0.2)
save(fig, "14_media_tone_timeseries")

# ═══════════════════════════════════════════════════════════════════════════════
# VIZ 15 — Nuclear & Red Line Quote Frequency
# ═══════════════════════════════════════════════════════════════════════════════
print("[4/6] Nuclear and red line quote frequency...")

fig, ax = plt.subplots(figsize=(18, 6))

ax.bar(df['week'], df['nuclear_quote_count'], width=6, alpha=0.7, color=ACCENT3, label='Nuclear quotes')
ax.bar(df['week'], df['redline_quote_count'], width=6, alpha=0.7, color=ACCENT5,
       bottom=df['nuclear_quote_count'], label='Red line quotes')

add_events(ax)
ax.set_title("Weekly Nuclear & 'Red Line' Quote Frequency (GKG 2022–2026)")
ax.set_ylabel("Number of quotes")
ax.legend(fontsize=10, framealpha=0.3, loc='upper right')
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
ax.tick_params(axis='x', rotation=45)
ax.grid(axis='y', alpha=0.2)
save(fig, "15_nuclear_redline_frequency")

# ═══════════════════════════════════════════════════════════════════════════════
# VIZ 16 — All Quote Pattern Frequencies (Stacked)
# ═══════════════════════════════════════════════════════════════════════════════
print("[5/6] All quote pattern frequencies...")

fig, ax = plt.subplots(figsize=(18, 7))

patterns = ['nuclear_quote_count', 'redline_quote_count', 'threat_quote_count',
            'ultimatum_quote_count', 'escalation_quote_count']
labels = ['Nuclear', 'Red line', 'Threat', 'Ultimatum', 'Escalation']
colors = [ACCENT3, ACCENT5, ACCENT2, ACCENT6, ACCENT4]

ax.stackplot(df['week'], *[df[p].values for p in patterns],
             labels=labels, colors=colors, alpha=0.8)

add_events(ax, ypos_frac=0.92)
ax.set_title("Weekly Coercive Quote Patterns — Stacked Composition (GKG 2022–2026)")
ax.set_ylabel("Number of quotes")
ax.legend(fontsize=9, framealpha=0.3, loc='upper right')
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
ax.tick_params(axis='x', rotation=45)
ax.grid(axis='y', alpha=0.2)
save(fig, "16_quote_patterns_stacked")

# ═══════════════════════════════════════════════════════════════════════════════
# VIZ 17 — Correlation Heatmap
# ═══════════════════════════════════════════════════════════════════════════════
print("[6/6] Variable correlation heatmap...")

# Select numeric columns for correlation
corr_cols = ['media_volume_all', 'media_volume_russia', 'media_tone_mean',
             'media_negativity_mean', 'nuclear_quote_count', 'redline_quote_count',
             'threat_quote_count', 'escalation_quote_count', 'russia_share']
corr_labels = ['Volume (All)', 'Volume (Russia)', 'Tone (Mean)',
               'Negativity', 'Nuclear', 'Red Line',
               'Threat', 'Escalation', 'Russia %']

corr_matrix = df[corr_cols].corr()

fig, ax = plt.subplots(figsize=(10, 8))
im = ax.imshow(corr_matrix, cmap='RdBu_r', vmin=-1, vmax=1, aspect='auto')

# Add text annotations
for i in range(len(corr_cols)):
    for j in range(len(corr_cols)):
        val = corr_matrix.iloc[i, j]
        color = 'white' if abs(val) > 0.5 else '#c9d1d9'
        ax.text(j, i, f'{val:.2f}', ha='center', va='center', color=color, fontsize=8)

ax.set_xticks(range(len(corr_labels)))
ax.set_yticks(range(len(corr_labels)))
ax.set_xticklabels(corr_labels, rotation=45, ha='right', fontsize=8)
ax.set_yticklabels(corr_labels, fontsize=8)
ax.set_title("Correlation Matrix — Weekly VARX Variables")

# Colorbar
cbar = fig.colorbar(im, ax=ax, shrink=0.8)
cbar.set_label('Pearson correlation', color='#c9d1d9')
cbar.ax.yaxis.set_tick_params(color='#8b949e')
plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='#8b949e')

fig.tight_layout()
save(fig, "17_varx_correlation_heatmap")

print(f"\n{'='*60}")
print(f"All done. 6 new visualizations saved to:\n  {OUT}")
print(f"{'='*60}")
