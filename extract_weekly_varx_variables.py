"""
Extract weekly VARX variables from GKG Coercive Discourse data.
Outputs a CSV with weekly aggregates for time series analysis.

Variables extracted:
- media_volume_weekly: COUNT of articles
- media_volume_russia: COUNT of Russia-relevant articles
- media_tone_weekly: AVG(V2Tone[0]) - overall tone
- media_negativity_weekly: AVG(V2Tone[2]) - negative score
- nuclear_quote_freq: COUNT WHERE Quotations LIKE '%nuclear%'
- redline_quote_freq: COUNT WHERE Quotations LIKE '%red line%'
"""

import pandas as pd
import numpy as np
from pathlib import Path

BASE = Path(r"/mnt/g/My Drive/RuBase/Red lines/Datasets/GDELT-Events")

print("Loading coercive discourse data...")
cq1 = pd.read_csv(BASE / "gkg_coercive_quotations_20220101_20231130.csv",
                  dtype={'DATE': str}, low_memory=False)
print(f"  Batch 1: {len(cq1):,} records")
cq2 = pd.read_csv(BASE / "gkg_coercive_quotations_20231201_20260128.csv",
                  dtype={'DATE': str}, low_memory=False, skiprows=[1])
print(f"  Batch 2: {len(cq2):,} records")
cq = pd.concat([cq1, cq2], ignore_index=True)
del cq1, cq2
print(f"  Combined: {len(cq):,} records")

# Parse dates
cq['date'] = pd.to_datetime(cq['DATE'].astype(str).str[:8], format='%Y%m%d', errors='coerce')
cq = cq.dropna(subset=['date'])
print(f"  After date parsing: {len(cq):,} records")

# Parse tone (6 comma-separated values: overall, positive, negative, polarity, activity, self)
def parse_tone(x, idx):
    if pd.isna(x):
        return np.nan
    parts = str(x).split(',')
    if len(parts) > idx:
        try:
            return float(parts[idx])
        except:
            return np.nan
    return np.nan

cq['tone_overall'] = cq['V2Tone'].apply(lambda x: parse_tone(x, 0))
cq['tone_negative'] = cq['V2Tone'].apply(lambda x: parse_tone(x, 2))

# Russia-relevance flag
cq['russia_relevant'] = (
    cq['V2Persons'].str.contains(r'(?i)putin|lavrov|medvedev|peskov|shoigu|patrushev|gerasimov|zelenskyy|zelensky', na=False) |
    cq['V2Locations'].str.contains(r'(?i)russia|moscow|kremlin|ukraine|kyiv', na=False) |
    cq['V2Themes'].str.contains(r'TAX_WORLDLANGUAGES_RUSSIA|TAX_ETHNICITY_RUSSIAN', na=False)
)

# Quotation pattern flags
cq['has_nuclear'] = cq['Quotations'].str.contains(r'(?i)nuclear', na=False)
cq['has_redline'] = cq['Quotations'].str.contains(r'(?i)red\s+line', na=False)
cq['has_threat'] = cq['Quotations'].str.contains(r'(?i)threat', na=False)
cq['has_ultimatum'] = cq['Quotations'].str.contains(r'(?i)ultimatum', na=False)
cq['has_escalation'] = cq['Quotations'].str.contains(r'(?i)escala', na=False)
cq['has_deter'] = cq['Quotations'].str.contains(r'(?i)deter', na=False)

# Create week column (ISO week starting Monday)
cq['week'] = cq['date'].dt.to_period('W-SUN').dt.start_time

print("\nAggregating weekly variables...")

# Aggregate by week
weekly = cq.groupby('week').agg(
    media_volume_all=('date', 'count'),
    media_volume_russia=('russia_relevant', 'sum'),
    media_tone_mean=('tone_overall', 'mean'),
    media_tone_std=('tone_overall', 'std'),
    media_negativity_mean=('tone_negative', 'mean'),
    media_negativity_std=('tone_negative', 'std'),
    nuclear_quote_count=('has_nuclear', 'sum'),
    redline_quote_count=('has_redline', 'sum'),
    threat_quote_count=('has_threat', 'sum'),
    ultimatum_quote_count=('has_ultimatum', 'sum'),
    escalation_quote_count=('has_escalation', 'sum'),
    deter_quote_count=('has_deter', 'sum'),
).reset_index()

# Convert boolean sums to integers
for col in ['media_volume_russia', 'nuclear_quote_count', 'redline_quote_count',
            'threat_quote_count', 'ultimatum_quote_count', 'escalation_quote_count', 'deter_quote_count']:
    weekly[col] = weekly[col].astype(int)

# Calculate Russia share
weekly['russia_share'] = weekly['media_volume_russia'] / weekly['media_volume_all']

# Add week number and year for easier analysis
weekly['year'] = weekly['week'].dt.year
weekly['week_of_year'] = weekly['week'].dt.isocalendar().week

# Sort by week
weekly = weekly.sort_values('week')

# Save
outfile = BASE / "gkg_weekly_varx_variables.csv"
weekly.to_csv(outfile, index=False)
print(f"\nSaved {len(weekly)} weeks to:\n  {outfile}")

# Print summary
print("\n" + "="*60)
print("SUMMARY")
print("="*60)
print(f"Date range: {weekly['week'].min()} to {weekly['week'].max()}")
print(f"Number of weeks: {len(weekly)}")
print(f"\nVariable ranges:")
for col in weekly.columns:
    if col != 'week':
        print(f"  {col}: {weekly[col].min():.2f} to {weekly[col].max():.2f}")

print("\n" + "="*60)
print("Sample data (first 10 weeks):")
print(weekly.head(10).to_string())
