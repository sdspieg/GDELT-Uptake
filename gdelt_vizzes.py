"""
GDELT Visualizations for "Decoding Putin's Red Lines" — Expanded Paper
Generates 8+ visualizations from the enriched coercive discourse dataset:
  - Primary: gkg_coercive_quotations (both batches, 354K records total)
    - Batch 1: 20220101_20231130.csv (161K records, Jan 2022 – Nov 2023)
    - Batch 2: 20231201_20260128.csv (193K records, Dec 2023 – Jan 2026)
  - Context: events_rus_threaten_20220101_20260128.csv (260K non-reflexive events)
  - Context: gkg_redline_quotations_20220101_20260128.csv (8.6K "red line" records)
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
from matplotlib.patches import Patch
import seaborn as sns
from collections import Counter
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

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

# ═══════════════════════════════════════════════════════════════════════════════
# LOAD DATA
# ═══════════════════════════════════════════════════════════════════════════════
print("Loading enriched coercive discourse data (both batches)...")
cq1 = pd.read_csv(BASE / "gkg_coercive_quotations_20220101_20231130.csv",
                  dtype={'DATE': str}, low_memory=False)
print(f"  Batch 1 (Jan 2022 – Nov 2023): {len(cq1):,} records")
# Batch 2's first data row is malformed (missing quotes), skip it
cq2 = pd.read_csv(BASE / "gkg_coercive_quotations_20231201_20260128.csv",
                  dtype={'DATE': str}, low_memory=False, skiprows=[1])
print(f"  Batch 2 (Dec 2023 – Jan 2026): {len(cq2):,} records")
cq = pd.concat([cq1, cq2], ignore_index=True)
del cq1, cq2  # Free memory
print(f"  Combined total: {len(cq):,} records")
cq['date'] = pd.to_datetime(cq['DATE'].astype(str).str[:8], format='%Y%m%d', errors='coerce')
bad_dates = cq['date'].isna().sum()
if bad_dates > 0:
    print(f"  WARNING: {bad_dates} rows with invalid DATE values dropped")
    cq = cq.dropna(subset=['date'])
cq['ym']   = cq['date'].dt.to_period('M')
cq['tone'] = cq['V2Tone'].apply(lambda x: float(str(x).split(',')[0]) if pd.notna(x) else np.nan)

# Tag quotation patterns
cq['has_nuclear_threat'] = cq['Quotations'].str.contains(r'(?i)nuclear\s+threat', na=False)
cq['has_nuclear_strike'] = cq['Quotations'].str.contains(r'(?i)nuclear\s+strike', na=False)
cq['has_nuclear_war']    = cq['Quotations'].str.contains(r'(?i)nuclear\s+war', na=False)
cq['has_red_line']       = cq['Quotations'].str.contains(r'(?i)red\s+line', na=False)
cq['has_ultimatum']      = cq['Quotations'].str.contains(r'(?i)ultimatum', na=False)
cq['has_deter']          = cq['Quotations'].str.contains(r'(?i)deter[a-z]+', na=False)
cq['has_escala']         = cq['Quotations'].str.contains(r'(?i)escala[a-z]+', na=False)

# Russia-relevance flag
cq['russia_relevant'] = (
    cq['V2Persons'].str.contains(r'(?i)putin|lavrov|medvedev|peskov|shoigu|patrushev|gerasimov|zelenskyy|zelensky', na=False) |
    cq['V2Locations'].str.contains(r'(?i)russia|moscow|kremlin|ukraine|kyiv', na=False) |
    cq['V2Themes'].str.contains(r'TAX_WORLDLANGUAGES_RUSSIA|TAX_ETHNICITY_RUSSIAN', na=False)
)
# Israel/Gaza flag
cq['israel_gaza'] = (
    cq['V2Persons'].str.contains(r'(?i)netanyahu|hagari|nasrallah|hamas|gallant', na=False) |
    cq['V2Locations'].str.contains(r'(?i)israel|gaza|rafah|tel aviv|jerusalem|palestine', na=False)
)
print(f"  {len(cq):,} records loaded")
print(f"  Russia-relevant: {cq['russia_relevant'].sum():,} ({cq['russia_relevant'].mean():.1%})")
print(f"  Israel/Gaza: {cq['israel_gaza'].sum():,} ({cq['israel_gaza'].mean():.1%})")

print("Loading events data (for context)...")
ev_raw = pd.read_csv(BASE / "events_rus_threaten_20220101_20260128.csv",
                     dtype={'SQLDATE': str, 'EventCode': str, 'EventBaseCode': str},
                     low_memory=False)
ev = ev_raw[ev_raw['Actor2CountryCode'] != 'RUS'].copy()
ev['date'] = pd.to_datetime(ev['SQLDATE'], format='%Y%m%d')
ev['ym']   = ev['date'].dt.to_period('M')
print(f"  {len(ev):,} events (non-reflexive)")

print("Loading GKG 'red line' data (for context)...")
gkg = pd.read_csv(BASE / "gkg_redline_quotations_20220101_20260128.csv",
                  dtype={'DATE': str})
gkg['date'] = pd.to_datetime(gkg['DATE'].str[:8], format='%Y%m%d')
gkg['ym']   = gkg['date'].dt.to_period('M')
print(f"  {len(gkg):,} 'red line' records loaded")

# ═══════════════════════════════════════════════════════════════════════════════
# VIZ 01 — Coercive Discourse Volume: All vs. Russia-Relevant vs. Nuclear
# ═══════════════════════════════════════════════════════════════════════════════
print("\n[01/08] Coercive discourse volume breakdown...")

cq_monthly_all = cq.groupby('ym').size()
cq_monthly_all.index = cq_monthly_all.index.to_timestamp()

cq_monthly_ru = cq[cq['russia_relevant']].groupby('ym').size()
cq_monthly_ru.index = cq_monthly_ru.index.to_timestamp()

cq_nuclear = cq[cq['has_nuclear_threat'] | cq['has_nuclear_strike'] | cq['has_nuclear_war']].copy()
cq_monthly_nuc = cq_nuclear.groupby('ym').size()
cq_monthly_nuc.index = cq_monthly_nuc.index.to_timestamp()

fig, ax = plt.subplots(figsize=(16, 7))
ax.fill_between(cq_monthly_all.index, cq_monthly_all.values, alpha=0.2, color=ACCENT)
ax.plot(cq_monthly_all.index, cq_monthly_all.values, color=ACCENT, linewidth=2,
        label=f'All coercive discourse ({len(cq):,})')
ax.fill_between(cq_monthly_ru.index, cq_monthly_ru.values, alpha=0.2, color=ACCENT2)
ax.plot(cq_monthly_ru.index, cq_monthly_ru.values, color=ACCENT2, linewidth=2,
        label=f'Russia-relevant ({cq["russia_relevant"].sum():,})')
ax.fill_between(cq_monthly_nuc.index, cq_monthly_nuc.values, alpha=0.2, color=ACCENT3)
ax.plot(cq_monthly_nuc.index, cq_monthly_nuc.values, color=ACCENT3, linewidth=2,
        label=f'Nuclear-specific ({len(cq_nuclear):,})')

# Key events (2022-2026)
for datestr, label in [('2022-02', 'Invasion'), ('2022-09', 'Mobilization'),
                        ('2023-10', 'Hamas attack'), ('2024-08', 'Kursk'),
                        ('2024-11', 'Oreshnik'), ('2025-01', 'Trump')]:
    d = pd.Timestamp(datestr + '-15')
    ax.axvline(d, color='#484f58', linestyle=':', alpha=0.5)
    ax.annotate(label, xy=(d, ax.get_ylim()[1]*0.95), fontsize=8,
               color='#8b949e', ha='center', va='top')

ax.set_title("Monthly Coercive Discourse Volume: All vs. Russia-Relevant vs. Nuclear (GKG 2022–2026)")
ax.set_ylabel("Number of articles")
ax.legend(fontsize=9, framealpha=0.3)
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
ax.tick_params(axis='x', rotation=45)
ax.grid(axis='y', alpha=0.2)
save(fig, "01_coercive_discourse_volume_breakdown")

# ═══════════════════════════════════════════════════════════════════════════════
# VIZ 02 — Quotation Pattern Composition Over Time (stacked area)
# ═══════════════════════════════════════════════════════════════════════════════
print("[02/08] Quotation pattern composition over time...")

pattern_cols = {
    'has_nuclear_threat': 'Nuclear threat',
    'has_nuclear_strike': 'Nuclear strike',
    'has_nuclear_war': 'Nuclear war',
    'has_red_line': 'Red line',
    'has_ultimatum': 'Ultimatum',
    'has_deter': 'Deterrence',
    'has_escala': 'Escalation',
}
pattern_monthly = cq.groupby('ym')[list(pattern_cols.keys())].sum()
pattern_monthly.index = pattern_monthly.index.to_timestamp()
pattern_monthly.columns = [pattern_cols[c] for c in pattern_monthly.columns]

fig, ax = plt.subplots(figsize=(16, 7))
colors_p = [ACCENT3, '#ff7b72', ACCENT2, ACCENT6, ACCENT5, ACCENT, ACCENT4]
ax.stackplot(pattern_monthly.index, *[pattern_monthly[c].values for c in pattern_monthly.columns],
             labels=pattern_monthly.columns, colors=colors_p, alpha=0.8)
ax.set_title("Monthly Composition of Coercive Quotation Patterns (GKG 2022–2026)")
ax.set_ylabel("Number of articles matching each pattern")
ax.legend(loc='upper left', fontsize=8, framealpha=0.3)
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
ax.tick_params(axis='x', rotation=45)
ax.grid(axis='y', alpha=0.2)
save(fig, "02_quotation_pattern_composition")

# ═══════════════════════════════════════════════════════════════════════════════
# VIZ 03 — Russia-Relevance vs. Israel/Gaza Share Over Time
# ═══════════════════════════════════════════════════════════════════════════════
print("[03/08] Russia-relevance vs Israel/Gaza share over time...")

monthly_total_cq = cq.groupby('ym').size()
monthly_ru_cq = cq[cq['russia_relevant']].groupby('ym').size()
monthly_il_cq = cq[cq['israel_gaza']].groupby('ym').size()
monthly_other_cq = cq[~cq['russia_relevant'] & ~cq['israel_gaza']].groupby('ym').size()

share_ru = (monthly_ru_cq / monthly_total_cq).fillna(0)
share_il = (monthly_il_cq / monthly_total_cq).fillna(0)
share_other = (monthly_other_cq / monthly_total_cq).fillna(0)

share_ru.index = share_ru.index.to_timestamp()
share_il.index = share_il.index.to_timestamp()
share_other.index = share_other.index.to_timestamp()

fig, ax = plt.subplots(figsize=(16, 6))
ax.stackplot(share_ru.index,
             share_ru.values, share_il.values, share_other.values,
             labels=['Russia/Ukraine', 'Israel/Gaza', 'Other contexts'],
             colors=[ACCENT, ACCENT3, '#484f58'], alpha=0.8)
ax.set_title("Geographic Relevance of Coercive Discourse — Who Is It Really About? (GKG 2022–2026)")
ax.set_ylabel("Share of monthly articles")
ax.yaxis.set_major_formatter(mticker.PercentFormatter(1.0))
ax.legend(loc='upper left', fontsize=9, framealpha=0.3)
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
ax.tick_params(axis='x', rotation=45)
ax.grid(axis='y', alpha=0.2)
save(fig, "03_russia_vs_israel_share_over_time")

# ═══════════════════════════════════════════════════════════════════════════════
# VIZ 04 — Top GKG Themes in Coercive Discourse
# ═══════════════════════════════════════════════════════════════════════════════
print("[04/08] Top GKG themes in coercive discourse...")

theme_counter = Counter()
for row in cq['V2Themes'].dropna():
    for entry in str(row).split(';'):
        parts = entry.split(',')
        if len(parts) >= 1 and parts[0].strip():
            theme = parts[0].strip()
            if theme and not theme.startswith('TAX_FNCACT') and len(theme) > 3:
                theme_counter[theme] += 1

top_themes = pd.Series(dict(theme_counter.most_common(30)))

fig, ax = plt.subplots(figsize=(14, 9))
ax.barh(range(len(top_themes)), top_themes.values, color=ACCENT4, alpha=0.8)
ax.set_yticks(range(len(top_themes)))
ax.set_yticklabels(top_themes.index, fontsize=7)
ax.invert_yaxis()
ax.set_xlabel("Number of articles containing theme")
ax.set_title("Top 30 GKG Themes in Coercive Discourse Articles (2022–2026)")
for i, v in enumerate(top_themes.values):
    ax.text(v + top_themes.values[0]*0.005, i, f'{v:,}', va='center', fontsize=6, color='#8b949e')
ax.grid(axis='x', alpha=0.2)
save(fig, "04_top_gkg_themes_coercive")

# ═══════════════════════════════════════════════════════════════════════════════
# VIZ 05 — Top Organizations in Coercive Discourse
# ═══════════════════════════════════════════════════════════════════════════════
print("[05/08] Top organizations in coercive discourse...")

org_counter = Counter()
for row in cq['V2Organizations'].dropna():
    for entry in str(row).split(';'):
        parts = entry.split(',')
        if len(parts) >= 1 and parts[0].strip():
            org = parts[0].strip()
            if org and len(org) > 2:
                org_counter[org] += 1

top_orgs = pd.Series(dict(org_counter.most_common(25)))

fig, ax = plt.subplots(figsize=(14, 8))
ax.barh(range(len(top_orgs)), top_orgs.values, color=ACCENT2, alpha=0.8)
ax.set_yticks(range(len(top_orgs)))
ax.set_yticklabels(top_orgs.index, fontsize=8)
ax.invert_yaxis()
ax.set_xlabel("Number of articles mentioning organization")
ax.set_title("Top 25 Organizations in Coercive Discourse Articles (GKG 2022–2026)")
for i, v in enumerate(top_orgs.values):
    ax.text(v + top_orgs.values[0]*0.005, i, f'{v:,}', va='center', fontsize=7, color='#8b949e')
ax.grid(axis='x', alpha=0.2)
save(fig, "05_top_organizations_coercive")

# ═══════════════════════════════════════════════════════════════════════════════
# VIZ 06 — Geographic Focus: Top Locations in Coercive Discourse
# ═══════════════════════════════════════════════════════════════════════════════
print("[06/08] Geographic focus — top locations...")

loc_counter = Counter()
for row in cq['V2Locations'].dropna():
    for entry in str(row).split(';'):
        parts = entry.split('#')
        if len(parts) >= 2 and parts[1].strip():
            loc_name = parts[1].strip()
            if loc_name and len(loc_name) > 1:
                loc_counter[loc_name] += 1

top_locs = pd.Series(dict(loc_counter.most_common(25)))

fig, ax = plt.subplots(figsize=(14, 8))
loc_colors = []
for loc in top_locs.index:
    loc_lower = loc.lower()
    if any(x in loc_lower for x in ['russia', 'moscow', 'ukraine', 'kyiv', 'kremlin', 'russian', 'ukrainian']):
        loc_colors.append(ACCENT)
    elif any(x in loc_lower for x in ['israel', 'gaza', 'jerusalem', 'tel aviv', 'palestinian']):
        loc_colors.append(ACCENT3)
    elif any(x in loc_lower for x in ['united states', 'washington', 'american']):
        loc_colors.append(ACCENT4)
    elif any(x in loc_lower for x in ['china', 'chinese', 'beijing']):
        loc_colors.append(ACCENT5)
    else:
        loc_colors.append('#484f58')

ax.barh(range(len(top_locs)), top_locs.values, color=loc_colors, alpha=0.8)
ax.set_yticks(range(len(top_locs)))
ax.set_yticklabels(top_locs.index, fontsize=8)
ax.invert_yaxis()
ax.set_xlabel("Number of articles mentioning location")
ax.set_title("Top 25 Locations in Coercive Discourse Articles (GKG 2022–2026)")
legend_elements = [Patch(facecolor=ACCENT, label='Russia/Ukraine'),
                   Patch(facecolor=ACCENT3, label='Israel/Gaza'),
                   Patch(facecolor=ACCENT4, label='United States'),
                   Patch(facecolor=ACCENT5, label='China'),
                   Patch(facecolor='#484f58', label='Other')]
ax.legend(handles=legend_elements, fontsize=8, framealpha=0.3, loc='lower right')
for i, v in enumerate(top_locs.values):
    ax.text(v + top_locs.values[0]*0.005, i, f'{v:,}', va='center', fontsize=7, color='#8b949e')
ax.grid(axis='x', alpha=0.2)
save(fig, "06_geographic_focus_coercive")

# ═══════════════════════════════════════════════════════════════════════════════
# VIZ 07 — Source Domains: Coercive Discourse vs Red-Line-Only
# ═══════════════════════════════════════════════════════════════════════════════
print("[07/08] Source domains comparison...")

cq_domains = cq['SourceCommonName'].value_counts().head(20)
gkg_domains_top = gkg['SourceCommonName'].value_counts().head(20)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))

ax1.barh(range(len(cq_domains)), cq_domains.values, color=ACCENT, alpha=0.8)
ax1.set_yticks(range(len(cq_domains)))
ax1.set_yticklabels(cq_domains.index, fontsize=7)
ax1.invert_yaxis()
ax1.set_xlabel("Articles")
ax1.set_title(f"Coercive Discourse Sources\n({len(cq)//1000}K articles, 2022–2026)")
for i, v in enumerate(cq_domains.values):
    ax1.text(v + cq_domains.values[0]*0.01, i, f'{v:,}', va='center', fontsize=6, color='#8b949e')
ax1.grid(axis='x', alpha=0.2)

ax2.barh(range(len(gkg_domains_top)), gkg_domains_top.values, color=ACCENT3, alpha=0.8)
ax2.set_yticks(range(len(gkg_domains_top)))
ax2.set_yticklabels(gkg_domains_top.index, fontsize=7)
ax2.invert_yaxis()
ax2.set_xlabel("Articles")
ax2.set_title("'Red Line' Only Sources\n(8.6K articles, 2022–2026)")
for i, v in enumerate(gkg_domains_top.values):
    ax2.text(v + gkg_domains_top.values[0]*0.01, i, f'{v:,}', va='center', fontsize=6, color='#8b949e')
ax2.grid(axis='x', alpha=0.2)

fig.suptitle("Media Source Comparison: Broad Coercive Discourse vs. 'Red Line' Only", fontsize=13, fontweight='bold', y=1.02)
fig.tight_layout()
save(fig, "07_source_domains_comparison")

# ═══════════════════════════════════════════════════════════════════════════════
# VIZ 08 — Triple-Axis: Events vs. Coercive Discourse vs. Red Line Discourse
# ═══════════════════════════════════════════════════════════════════════════════
print("[08/08] Triple comparison — events vs coercive vs red line...")

# Use full date range for all three datasets (2022-2026)
ev_monthly = ev.groupby('ym').size()
ev_monthly.index = ev_monthly.index.to_timestamp()

gkg_monthly = gkg.groupby('ym').size()
gkg_monthly.index = gkg_monthly.index.to_timestamp()

fig, ax1 = plt.subplots(figsize=(16, 7))

ax1.bar(ev_monthly.index, ev_monthly.values, width=25,
        color=ACCENT, alpha=0.4, label='GDELT threat events')
ax1.set_ylabel('Russian threat events', color=ACCENT)
ax1.tick_params(axis='y', labelcolor=ACCENT)

ax2 = ax1.twinx()
ax2.plot(cq_monthly_all.index, cq_monthly_all.values, color=ACCENT2, linewidth=2.5,
         label=f'Coercive discourse ({len(cq)//1000}K)')
ax2.plot(gkg_monthly.index, gkg_monthly.values, color=ACCENT3, linewidth=2,
         linestyle='--', label='"Red line" only (8.6K)')
ax2.set_ylabel('GKG discourse articles', color=ACCENT2)
ax2.tick_params(axis='y', labelcolor=ACCENT2)

# Key events (expanded for 2022-2026)
for datestr, label in [('2022-02', 'Invasion'), ('2022-09', 'Mobilization'),
                        ('2023-10', 'Hamas\nattack'), ('2024-08', 'Kursk'),
                        ('2024-11', 'Oreshnik'), ('2025-01', 'Trump')]:
    d = pd.Timestamp(datestr + '-15')
    ax1.axvline(d, color='#484f58', linestyle=':', alpha=0.5)
    ax1.annotate(label, xy=(d, ax1.get_ylim()[1]*0.95), fontsize=8,
                color='#8b949e', ha='center', va='top')

ax1.set_title("Russian Threat Events vs. Coercive Media Discourse vs. 'Red Line' Only (2022–2026)")
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=9, framealpha=0.3)
ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
ax1.tick_params(axis='x', rotation=45)
ax1.grid(axis='y', alpha=0.15)
save(fig, "08_triple_events_vs_coercive_vs_redline")

# ═══════════════════════════════════════════════════════════════════════════════
# VIZ 10 — Coercive Discourse with RRLS Date Overlay
# ═══════════════════════════════════════════════════════════════════════════════
print("[09/10] RRLS date overlay on coercive discourse...")

# Load RRLS dates (329 Russian Red Line Statements)
rrls_path = Path(r"/mnt/g/My Drive/RuBase/Red lines/RLS/240901/Datasets/241014_RRLS_classified.csv")
if rrls_path.exists():
    rrls = pd.read_csv(rrls_path, low_memory=False)
    rrls['date'] = pd.to_datetime(rrls['date_published'], errors='coerce')
    rrls = rrls.dropna(subset=['date'])
    # Filter to 2022+ to match our discourse data
    rrls = rrls[rrls['date'] >= '2022-01-01']
    print(f"  {len(rrls)} RRLS dates in 2022+ range")

    fig, ax = plt.subplots(figsize=(18, 8))

    # Plot coercive discourse volume
    ax.fill_between(cq_monthly_all.index, cq_monthly_all.values, alpha=0.3, color=ACCENT)
    ax.plot(cq_monthly_all.index, cq_monthly_all.values, color=ACCENT, linewidth=2,
            label=f'All coercive discourse ({len(cq):,})')
    ax.fill_between(cq_monthly_ru.index, cq_monthly_ru.values, alpha=0.3, color=ACCENT2)
    ax.plot(cq_monthly_ru.index, cq_monthly_ru.values, color=ACCENT2, linewidth=2,
            label=f'Russia-relevant ({cq["russia_relevant"].sum():,})')

    # Add RRLS dates as vertical lines
    for d in rrls['date']:
        ax.axvline(d, color=ACCENT3, alpha=0.4, linewidth=0.8)

    # Add dummy line for legend
    ax.axvline(pd.Timestamp('1900-01-01'), color=ACCENT3, alpha=0.7, linewidth=1.5,
               label=f'Putin RRLS dates ({len(rrls)} statements)')

    ax.set_title("Coercive Media Discourse with Putin Red Line Statement Dates (GKG 2022–2026)")
    ax.set_ylabel("Number of articles")
    ax.legend(fontsize=10, framealpha=0.3, loc='upper right')
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.tick_params(axis='x', rotation=45)
    ax.grid(axis='y', alpha=0.2)
    ax.set_xlim(cq_monthly_all.index.min(), cq_monthly_all.index.max())
    save(fig, "10_rrls_dates_overlay")
else:
    print(f"  RRLS file not found at {rrls_path}, skipping viz 10")

# ═══════════════════════════════════════════════════════════════════════════════
# VIZ 11 — Media Tone Time Series
# ═══════════════════════════════════════════════════════════════════════════════
print("[10/10] Media tone time series...")

cq_ru = cq[cq['russia_relevant']].copy()
tone_weekly = cq_ru.groupby(pd.Grouper(key='date', freq='W'))['tone'].agg(['mean', 'count'])
tone_weekly = tone_weekly[tone_weekly['count'] >= 10]  # Filter weeks with <10 articles

fig, ax = plt.subplots(figsize=(18, 6))
ax.plot(tone_weekly.index, tone_weekly['mean'], color=ACCENT, linewidth=1.5, alpha=0.8)
ax.axhline(0, color='#484f58', linestyle='--', alpha=0.5)
ax.fill_between(tone_weekly.index, tone_weekly['mean'], 0,
                where=(tone_weekly['mean'] > 0), color=ACCENT4, alpha=0.3, label='Positive tone')
ax.fill_between(tone_weekly.index, tone_weekly['mean'], 0,
                where=(tone_weekly['mean'] < 0), color=ACCENT3, alpha=0.3, label='Negative tone')

# Key events
for datestr, label in [('2022-02', 'Invasion'), ('2022-09', 'Mobilization'),
                        ('2023-10', 'Hamas'), ('2024-08', 'Kursk'),
                        ('2024-11', 'Oreshnik'), ('2025-01', 'Trump')]:
    d = pd.Timestamp(datestr + '-15')
    ax.axvline(d, color='#484f58', linestyle=':', alpha=0.5)
    ax.annotate(label, xy=(d, ax.get_ylim()[1]*0.9), fontsize=7,
               color='#8b949e', ha='center', va='top')

ax.set_title("Weekly Media Tone in Russia-Relevant Coercive Discourse (GKG 2022–2026)")
ax.set_ylabel("Average V2Tone (negative = hostile)")
ax.legend(fontsize=9, framealpha=0.3, loc='lower right')
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
ax.tick_params(axis='x', rotation=45)
ax.grid(axis='y', alpha=0.2)
save(fig, "11_media_tone_timeseries")

print(f"\n{'='*60}")
print(f"All done. {len(list(OUT.glob('*.png')))} visualizations saved to:\n  {OUT}")
print(f"{'='*60}")
