#!/usr/bin/env python3
"""
GDELT Incremental Update Script
=================================
Updates GDELT data in the war_datasets PostgreSQL database (global_events schema).

Two data paths:
  1. EVENTS — Downloaded from GDELT's free 15-minute file exports, filtered locally
     for Actor1CountryCode='RUS' AND EventRootCode='13' (THREATEN).
  2. GKG (coercive quotations + red line quotations) — Queried from BigQuery
     with the same regex filter used in the original extraction.
  3. WEEKLY VARX — Recomputed from the coercive quotations table in PostgreSQL.

Usage:
    python update_gdelt.py                     # Full incremental update (events + GKG + VARX)
    python update_gdelt.py --events-only       # Update events only (no BigQuery needed)
    python update_gdelt.py --gkg-only          # Update GKG only (requires BigQuery)
    python update_gdelt.py --recompute-varx    # Recompute weekly VARX from DB
    python update_gdelt.py --from 2026-01-28   # Specify start date
    python update_gdelt.py --days 7            # Last 7 days only
    python update_gdelt.py --status            # Show current data status

BigQuery authentication (for GKG updates):
    Option A: gcloud SDK — /tmp/google-cloud-sdk/bin/gcloud auth application-default login
    Option B: Service account — export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
    Option C: Place service account key at ./bigquery_credentials.json

BigQuery accounts:
    - sdspieg@gmail.com (primary, 1 TB/month)
    - sdspiegus@gmail.com (secondary, 1 TB/month)
    BigQuery project: rubase-minimal
"""

import os
import sys
import re
import io
import csv
import argparse
import datetime as dt
import tempfile
import zipfile
from pathlib import Path
from typing import Optional, List, Tuple

import pandas as pd
import psycopg2
import psycopg2.extras
import requests
from tqdm.auto import tqdm

# =============================================================================
# CONFIGURATION
# =============================================================================

SCRIPT_DIR = Path(__file__).parent.resolve()
BQ_CREDENTIALS_FILE = SCRIPT_DIR / "bigquery_credentials.json"
LOG_DIR = SCRIPT_DIR / "update_logs"

# PostgreSQL connection (remote war_datasets)
DB_CONFIG = {
    "host": "138.201.62.161",
    "port": 5432,
    "dbname": "war_datasets",
    "user": "postgres",
    "password": "***DB_PASSWORD_REDACTED***",
}

SCHEMA = "global_events"

# GDELT free file URLs
GDELT_EVENTS_URL = "http://data.gdeltproject.org/gdeltv2/{timestamp}.export.CSV.zip"
GDELT_GKG_URL = "http://data.gdeltproject.org/gdeltv2/{timestamp}.gkg.csv.zip"
GDELT_LASTUPDATE_URL = "http://data.gdeltproject.org/gdeltv2/lastupdate.txt"

# BigQuery config
BQ_PROJECT = "rubase-minimal"

# Filters (must match original extraction)
EVENTS_FILTER_ACTOR1_COUNTRY = "RUS"
EVENTS_FILTER_ROOT_CODE = "13"

COERCIVE_QUOTATION_REGEX = (
    r"(?i)(nuclear\s+threat|nuclear\s+strike|nuclear\s+war|"
    r"red\s+line|ultimatum|deter[a-z]*|escala[a-z]*)"
)
REDLINE_REGEX = r"(?i)red\s+line"

# GDELT event column names (tab-separated, no header in raw files)
EVENT_COLUMNS = [
    "GLOBALEVENTID", "SQLDATE", "MonthYear", "Year", "FractionDate",
    "Actor1Code", "Actor1Name", "Actor1CountryCode", "Actor1KnownGroupCode",
    "Actor1EthnicCode", "Actor1Religion1Code", "Actor1Religion2Code",
    "Actor1Type1Code", "Actor1Type2Code", "Actor1Type3Code",
    "Actor2Code", "Actor2Name", "Actor2CountryCode", "Actor2KnownGroupCode",
    "Actor2EthnicCode", "Actor2Religion1Code", "Actor2Religion2Code",
    "Actor2Type1Code", "Actor2Type2Code", "Actor2Type3Code",
    "IsRootEvent", "EventCode", "EventBaseCode", "EventRootCode", "QuadClass",
    "GoldsteinScale", "NumMentions", "NumSources", "NumArticles", "AvgTone",
    "Actor1Geo_Type", "Actor1Geo_FullName", "Actor1Geo_CountryCode",
    "Actor1Geo_ADM1Code", "Actor1Geo_ADM2Code", "Actor1Geo_Lat",
    "Actor1Geo_Long", "Actor1Geo_FeatureID",
    "Actor2Geo_Type", "Actor2Geo_FullName", "Actor2Geo_CountryCode",
    "Actor2Geo_ADM1Code", "Actor2Geo_ADM2Code", "Actor2Geo_Lat",
    "Actor2Geo_Long", "Actor2Geo_FeatureID",
    "ActionGeo_Type", "ActionGeo_FullName", "ActionGeo_CountryCode",
    "ActionGeo_ADM1Code", "ActionGeo_ADM2Code", "ActionGeo_Lat",
    "ActionGeo_Long", "ActionGeo_FeatureID",
    "DATEADDED", "SOURCEURL",
]

# GKG column names (tab-separated, no header)
GKG_COLUMNS = [
    "GKGRECORDID", "DATE", "SourceCollectionIdentifier", "SourceCommonName",
    "DocumentIdentifier", "Counts", "V2Counts", "Themes", "V2Themes",
    "Locations", "V2Locations", "Persons", "V2Persons", "Organizations",
    "V2Organizations", "V2Tone", "Dates", "GCAM", "SharingImage",
    "RelatedImages", "SocialImageEmbeds", "SocialVideoEmbeds",
    "Quotations", "AllNames", "Amounts", "TranslationInfo", "Extras",
]

# Columns we store in the coercive quotations table
COERCIVE_STORE_COLS = [
    "GKGRECORDID", "DATE", "SourceCommonName", "DocumentIdentifier",
    "V2Themes", "V2Tone", "V2Persons", "V2Locations", "V2Organizations",
    "Quotations", "TranslationInfo",
]

# Columns we store in the redline quotations table
REDLINE_STORE_COLS = [
    "GKGRECORDID", "DATE", "SourceCommonName", "DocumentIdentifier",
    "Quotations", "V2Tone", "V2Persons",
]

# Retry settings
MAX_RETRIES = 3
RETRY_DELAY = 2
REQUEST_TIMEOUT = 60


# =============================================================================
# DATABASE HELPERS
# =============================================================================

def get_db_connection():
    """Get PostgreSQL connection."""
    return psycopg2.connect(**DB_CONFIG)


def get_last_event_date() -> Optional[int]:
    """Get the latest SQLDATE from gdelt_events table."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT MAX(sqldate) FROM {SCHEMA}.gdelt_events")
            result = cur.fetchone()[0]
            return result


def get_last_gkg_date() -> Optional[int]:
    """Get the latest DATE from gdelt_gkg_coercive_quotations table."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT MAX(date) FROM {SCHEMA}.gdelt_gkg_coercive_quotations"
            )
            result = cur.fetchone()[0]
            return result


def get_existing_event_ids(since_date: int) -> set:
    """Get existing event IDs from the DB for deduplication."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT globaleventid FROM {SCHEMA}.gdelt_events WHERE sqldate >= %s",
                (since_date,),
            )
            return {row[0] for row in cur.fetchall()}


def get_existing_gkg_ids(since_date: int) -> set:
    """Get existing GKG record IDs for deduplication."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT gkgrecordid FROM {SCHEMA}.gdelt_gkg_coercive_quotations "
                f"WHERE date >= %s",
                (since_date,),
            )
            return {row[0] for row in cur.fetchall()}


# =============================================================================
# GDELT FILE DOWNLOAD (Events)
# =============================================================================

def generate_timestamps(start_date: dt.date, end_date: dt.date) -> List[str]:
    """Generate GDELT 15-minute timestamps between two dates."""
    timestamps = []
    current = dt.datetime.combine(start_date, dt.time(0, 0))
    end = dt.datetime.combine(end_date, dt.time(23, 45))

    while current <= end:
        timestamps.append(current.strftime("%Y%m%d%H%M%S"))
        current += dt.timedelta(minutes=15)

    return timestamps


def download_and_filter_events(
    timestamp: str,
) -> Optional[pd.DataFrame]:
    """Download a single GDELT 15-min events file, filter for RUS THREATEN."""
    url = GDELT_EVENTS_URL.format(timestamp=timestamp)

    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(url, timeout=REQUEST_TIMEOUT)
            if resp.status_code == 404:
                return None  # File doesn't exist for this timestamp
            resp.raise_for_status()
            break
        except requests.RequestException:
            if attempt < MAX_RETRIES - 1:
                import time
                time.sleep(RETRY_DELAY)
            else:
                return None

    try:
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            csv_name = zf.namelist()[0]
            with zf.open(csv_name) as f:
                df = pd.read_csv(
                    f,
                    sep="\t",
                    header=None,
                    names=EVENT_COLUMNS,
                    dtype=str,
                    on_bad_lines="skip",
                )
    except Exception:
        return None

    # Filter: Actor1CountryCode = RUS and EventRootCode = 13
    mask = (
        (df["Actor1CountryCode"] == EVENTS_FILTER_ACTOR1_COUNTRY)
        & (df["EventRootCode"] == EVENTS_FILTER_ROOT_CODE)
    )
    filtered = df[mask].copy()

    if filtered.empty:
        return None

    return filtered


def insert_events(df: pd.DataFrame) -> int:
    """Insert events DataFrame into gdelt_events table. Returns rows inserted."""
    if df.empty:
        return 0

    # Type conversions matching the DB schema
    int_cols = [
        "GLOBALEVENTID", "SQLDATE", "MonthYear", "Year", "IsRootEvent",
        "QuadClass", "NumMentions", "NumSources", "NumArticles",
        "Actor1Geo_Type", "Actor2Geo_Type", "ActionGeo_Type", "DATEADDED",
    ]
    float_cols = [
        "FractionDate", "GoldsteinScale", "AvgTone",
        "Actor1Geo_Lat", "Actor1Geo_Long", "Actor2Geo_Lat", "Actor2Geo_Long",
        "ActionGeo_Lat", "ActionGeo_Long",
    ]

    for col in int_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in float_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Replace NaN with None for SQL
    df = df.where(df.notna(), None)

    # Build insert query (all columns except geom, which we compute after)
    db_columns = [c.lower() for c in EVENT_COLUMNS]
    placeholders = ",".join(["%s"] * len(db_columns))
    cols_str = ",".join(db_columns)

    insert_sql = (
        f"INSERT INTO {SCHEMA}.gdelt_events ({cols_str}) "
        f"VALUES ({placeholders}) "
        f"ON CONFLICT (globaleventid) DO NOTHING"
    )

    rows = [tuple(row[c] for c in EVENT_COLUMNS) for _, row in df.iterrows()]

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            psycopg2.extras.execute_batch(cur, insert_sql, rows, page_size=1000)

            # Update geom for newly inserted rows
            cur.execute(
                f"UPDATE {SCHEMA}.gdelt_events "
                f"SET geom = ST_SetSRID(ST_MakePoint(actiongeo_long, actiongeo_lat), 4326) "
                f"WHERE geom IS NULL AND actiongeo_lat IS NOT NULL AND actiongeo_long IS NOT NULL"
            )
        conn.commit()

    return len(rows)


def update_events(
    start_date: dt.date,
    end_date: dt.date,
) -> int:
    """Download and insert GDELT events for a date range. Returns total new rows."""
    timestamps = generate_timestamps(start_date, end_date)
    print(f"\nUpdating GDELT events: {start_date} to {end_date}")
    print(f"  Timestamps to check: {len(timestamps)} (15-min intervals)")

    # Get existing IDs for dedup
    sqldate_start = int(start_date.strftime("%Y%m%d"))
    existing_ids = get_existing_event_ids(sqldate_start)
    print(f"  Existing events since {sqldate_start}: {len(existing_ids):,}")

    total_new = 0
    total_filtered = 0
    batch = []
    batch_size = 50  # Accumulate N files before inserting

    with tqdm(timestamps, desc="Downloading events", unit="file") as pbar:
        for ts in pbar:
            df = download_and_filter_events(ts)
            if df is not None:
                total_filtered += len(df)
                # Deduplicate against existing
                df["GLOBALEVENTID"] = pd.to_numeric(
                    df["GLOBALEVENTID"], errors="coerce"
                )
                df = df[~df["GLOBALEVENTID"].isin(existing_ids)]
                if not df.empty:
                    batch.append(df)
                    existing_ids.update(df["GLOBALEVENTID"].tolist())

            # Flush batch
            if len(batch) >= batch_size:
                combined = pd.concat(batch, ignore_index=True)
                n = insert_events(combined)
                total_new += n
                batch = []
                pbar.set_postfix({"new": total_new, "filtered": total_filtered})

    # Final flush
    if batch:
        combined = pd.concat(batch, ignore_index=True)
        n = insert_events(combined)
        total_new += n

    print(f"\n  Events matching RUS+THREATEN: {total_filtered:,}")
    print(f"  New events inserted: {total_new:,}")
    return total_new


# =============================================================================
# GDELT GKG (BigQuery)
# =============================================================================

def get_bigquery_client():
    """Get authenticated BigQuery client."""
    try:
        from google.cloud import bigquery
    except ImportError:
        print("ERROR: google-cloud-bigquery not installed.")
        print("  pip install google-cloud-bigquery")
        sys.exit(1)

    # Try service account file first
    if BQ_CREDENTIALS_FILE.exists():
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(BQ_CREDENTIALS_FILE)

    try:
        client = bigquery.Client(project=BQ_PROJECT)
        # Test connection
        client.query("SELECT 1").result()
        return client
    except Exception as e:
        print(f"ERROR: BigQuery authentication failed: {e}")
        print("\nTo authenticate:")
        print("  Option A: gcloud auth application-default login")
        print(f"  Option B: Place service account JSON at {BQ_CREDENTIALS_FILE}")
        print("  Option C: export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json")
        sys.exit(1)


def update_gkg_bigquery(
    start_date: dt.date,
    end_date: dt.date,
) -> Tuple[int, int]:
    """
    Fetch new GKG coercive quotations from BigQuery and insert into DB.
    Returns (coercive_count, redline_count).
    """
    client = get_bigquery_client()

    start_str = start_date.strftime("%Y-%m-%d")
    end_str = (end_date + dt.timedelta(days=1)).strftime("%Y-%m-%d")

    print(f"\nQuerying BigQuery for GKG coercive quotations: {start_str} to {end_str}")

    # Coercive quotations query (same filter as original extraction)
    query = f"""
    SELECT
        GKGRECORDID, DATE, SourceCommonName, DocumentIdentifier,
        V2Themes, V2Tone, V2Persons, V2Locations, V2Organizations,
        Quotations, TranslationInfo
    FROM `gdelt-bq.gdeltv2.gkg_partitioned`
    WHERE _PARTITIONTIME >= "{start_str}"
      AND _PARTITIONTIME < "{end_str}"
      AND REGEXP_CONTAINS(Quotations,
        r"(?i)(nuclear\\s+threat|nuclear\\s+strike|nuclear\\s+war|red\\s+line|ultimatum|deter[a-z]*|escala[a-z]*)")
    """

    print("  Running BigQuery query...")
    try:
        df = client.query(query).to_dataframe()
    except Exception as e:
        print(f"  BigQuery error: {e}")
        return 0, 0

    print(f"  BigQuery returned {len(df):,} records")

    if df.empty:
        return 0, 0

    # Get existing IDs for dedup
    date_min = int(start_date.strftime("%Y%m%d") + "000000")
    existing_ids = get_existing_gkg_ids(date_min)
    print(f"  Existing records since {date_min}: {len(existing_ids):,}")

    df = df[~df["GKGRECORDID"].isin(existing_ids)]
    print(f"  New records after dedup: {len(df):,}")

    if df.empty:
        return 0, 0

    # Replace NaN with None
    df = df.where(df.notna(), None)

    # Insert coercive quotations
    coercive_cols = [c.lower() for c in COERCIVE_STORE_COLS]
    placeholders = ",".join(["%s"] * len(coercive_cols))
    insert_sql = (
        f"INSERT INTO {SCHEMA}.gdelt_gkg_coercive_quotations "
        f"({','.join(coercive_cols)}) VALUES ({placeholders}) "
        f"ON CONFLICT (gkgrecordid) DO NOTHING"
    )

    rows = [
        tuple(row.get(c) for c in COERCIVE_STORE_COLS)
        for _, row in df.iterrows()
    ]

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            psycopg2.extras.execute_batch(cur, insert_sql, rows, page_size=1000)
        conn.commit()

    coercive_count = len(rows)
    print(f"  Inserted {coercive_count:,} coercive quotation records")

    # Extract and insert redline subset
    redline_mask = df["Quotations"].str.contains(REDLINE_REGEX, na=False)
    df_redline = df[redline_mask]

    redline_count = 0
    if not df_redline.empty:
        redline_cols = [c.lower() for c in REDLINE_STORE_COLS]
        placeholders = ",".join(["%s"] * len(redline_cols))
        insert_sql = (
            f"INSERT INTO {SCHEMA}.gdelt_gkg_redline_quotations "
            f"({','.join(redline_cols)}) VALUES ({placeholders}) "
            f"ON CONFLICT (gkgrecordid) DO NOTHING"
        )

        rows = [
            tuple(row.get(c) for c in REDLINE_STORE_COLS)
            for _, row in df_redline.iterrows()
        ]

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                psycopg2.extras.execute_batch(cur, insert_sql, rows, page_size=1000)
            conn.commit()

        redline_count = len(rows)
        print(f"  Inserted {redline_count:,} red line quotation records")

    return coercive_count, redline_count


# =============================================================================
# GDELT GKG (File-based fallback for when BigQuery is unavailable)
# =============================================================================

def download_and_filter_gkg(timestamp: str) -> Optional[Tuple[pd.DataFrame, pd.DataFrame]]:
    """
    Download a single GDELT 15-min GKG file, filter for coercive quotations.
    Returns (coercive_df, redline_df) or None.
    """
    url = GDELT_GKG_URL.format(timestamp=timestamp)

    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(url, timeout=REQUEST_TIMEOUT)
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            break
        except requests.RequestException:
            if attempt < MAX_RETRIES - 1:
                import time
                time.sleep(RETRY_DELAY)
            else:
                return None

    try:
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            csv_name = zf.namelist()[0]
            with zf.open(csv_name) as f:
                df = pd.read_csv(
                    f,
                    sep="\t",
                    header=None,
                    names=GKG_COLUMNS,
                    dtype=str,
                    on_bad_lines="skip",
                )
    except Exception:
        return None

    # Filter for coercive quotation patterns
    quotations = df["Quotations"].fillna("")
    coercive_mask = quotations.str.contains(COERCIVE_QUOTATION_REGEX, na=False)
    df_coercive = df[coercive_mask][COERCIVE_STORE_COLS].copy()

    if df_coercive.empty:
        return None

    # Red line subset
    redline_mask = quotations[coercive_mask].str.contains(REDLINE_REGEX, na=False)
    df_redline = df[coercive_mask][redline_mask][REDLINE_STORE_COLS].copy()

    return df_coercive, df_redline


def update_gkg_files(
    start_date: dt.date,
    end_date: dt.date,
) -> Tuple[int, int]:
    """
    Download GKG files and insert coercive/redline quotations.
    Fallback when BigQuery is unavailable.
    Returns (coercive_count, redline_count).
    """
    timestamps = generate_timestamps(start_date, end_date)
    print(f"\nUpdating GKG via file download: {start_date} to {end_date}")
    print(f"  Timestamps to check: {len(timestamps)}")
    print("  WARNING: GKG files are large (~20-50MB each). This may be slow.")

    date_min = int(start_date.strftime("%Y%m%d") + "000000")
    existing_ids = get_existing_gkg_ids(date_min)

    total_coercive = 0
    total_redline = 0
    coercive_batch = []
    redline_batch = []

    with tqdm(timestamps, desc="Downloading GKG", unit="file") as pbar:
        for ts in pbar:
            result = download_and_filter_gkg(ts)
            if result is not None:
                df_c, df_r = result
                # Dedup
                df_c = df_c[~df_c["GKGRECORDID"].isin(existing_ids)]
                if not df_c.empty:
                    existing_ids.update(df_c["GKGRECORDID"].tolist())
                    coercive_batch.append(df_c)
                    total_coercive += len(df_c)
                df_r = df_r[~df_r["GKGRECORDID"].isin(existing_ids - set(df_c["GKGRECORDID"].tolist()))]
                if not df_r.empty:
                    redline_batch.append(df_r)
                    total_redline += len(df_r)

            pbar.set_postfix({"coercive": total_coercive, "redline": total_redline})

            # Flush every 100 files
            if len(coercive_batch) >= 100:
                _flush_gkg_batch(coercive_batch, redline_batch)
                coercive_batch = []
                redline_batch = []

    # Final flush
    if coercive_batch or redline_batch:
        _flush_gkg_batch(coercive_batch, redline_batch)

    print(f"\n  New coercive quotations: {total_coercive:,}")
    print(f"  New red line quotations: {total_redline:,}")
    return total_coercive, total_redline


def _flush_gkg_batch(coercive_batch, redline_batch):
    """Insert accumulated GKG batches into DB."""
    if coercive_batch:
        df = pd.concat(coercive_batch, ignore_index=True).where(
            lambda x: x.notna(), None
        )
        cols = [c.lower() for c in COERCIVE_STORE_COLS]
        placeholders = ",".join(["%s"] * len(cols))
        sql = (
            f"INSERT INTO {SCHEMA}.gdelt_gkg_coercive_quotations "
            f"({','.join(cols)}) VALUES ({placeholders}) "
            f"ON CONFLICT (gkgrecordid) DO NOTHING"
        )
        rows = [tuple(row.get(c) for c in COERCIVE_STORE_COLS) for _, row in df.iterrows()]
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                psycopg2.extras.execute_batch(cur, sql, rows, page_size=1000)
            conn.commit()

    if redline_batch:
        df = pd.concat(redline_batch, ignore_index=True).where(
            lambda x: x.notna(), None
        )
        cols = [c.lower() for c in REDLINE_STORE_COLS]
        placeholders = ",".join(["%s"] * len(cols))
        sql = (
            f"INSERT INTO {SCHEMA}.gdelt_gkg_redline_quotations "
            f"({','.join(cols)}) VALUES ({placeholders}) "
            f"ON CONFLICT (gkgrecordid) DO NOTHING"
        )
        rows = [tuple(row.get(c) for c in REDLINE_STORE_COLS) for _, row in df.iterrows()]
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                psycopg2.extras.execute_batch(cur, sql, rows, page_size=1000)
            conn.commit()


# =============================================================================
# WEEKLY VARX RECOMPUTATION
# =============================================================================

def recompute_weekly_varx():
    """
    Recompute weekly VARX variables from the full coercive quotations table.
    Truncates and repopulates gdelt_weekly_varx.
    """
    print("\nRecomputing weekly VARX variables from coercive quotations...")

    with get_db_connection() as conn:
        # Read all coercive quotations (just the columns we need)
        print("  Loading coercive quotations from DB...")
        df = pd.read_sql(
            f"SELECT date, v2tone, v2persons, v2locations, v2themes, quotations "
            f"FROM {SCHEMA}.gdelt_gkg_coercive_quotations",
            conn,
        )

    print(f"  Loaded {len(df):,} records")

    if df.empty:
        print("  No data — skipping VARX recomputation")
        return

    # Parse date (first 8 chars of DATE integer → YYYYMMDD)
    df["parsed_date"] = pd.to_datetime(
        df["date"].astype(str).str[:8], format="%Y%m%d", errors="coerce"
    )
    df = df.dropna(subset=["parsed_date"])

    # Parse tone
    def parse_tone(x, idx):
        if pd.isna(x):
            return float("nan")
        parts = str(x).split(",")
        if len(parts) > idx:
            try:
                return float(parts[idx])
            except ValueError:
                return float("nan")
        return float("nan")

    df["tone_overall"] = df["v2tone"].apply(lambda x: parse_tone(x, 0))
    df["tone_negative"] = df["v2tone"].apply(lambda x: parse_tone(x, 2))

    # Russia-relevance flag
    df["russia_relevant"] = (
        df["v2persons"].str.contains(
            r"(?i)putin|lavrov|medvedev|peskov|shoigu|patrushev|gerasimov|zelenskyy|zelensky",
            na=False,
        )
        | df["v2locations"].str.contains(
            r"(?i)russia|moscow|kremlin|ukraine|kyiv", na=False
        )
        | df["v2themes"].str.contains(
            r"TAX_WORLDLANGUAGES_RUSSIA|TAX_ETHNICITY_RUSSIAN", na=False
        )
    )

    # Quotation pattern flags
    df["has_nuclear"] = df["quotations"].str.contains(r"(?i)nuclear", na=False)
    df["has_redline"] = df["quotations"].str.contains(r"(?i)red\s+line", na=False)
    df["has_threat"] = df["quotations"].str.contains(r"(?i)threat", na=False)
    df["has_ultimatum"] = df["quotations"].str.contains(r"(?i)ultimatum", na=False)
    df["has_escalation"] = df["quotations"].str.contains(r"(?i)escala", na=False)
    df["has_deter"] = df["quotations"].str.contains(r"(?i)deter", na=False)

    # Weekly aggregation (ISO week starting Monday, matching original)
    df["week"] = df["parsed_date"].dt.to_period("W-SUN").dt.start_time

    weekly = (
        df.groupby("week")
        .agg(
            media_volume_all=("parsed_date", "count"),
            media_volume_russia=("russia_relevant", "sum"),
            media_tone_mean=("tone_overall", "mean"),
            media_tone_std=("tone_overall", "std"),
            media_negativity_mean=("tone_negative", "mean"),
            media_negativity_std=("tone_negative", "std"),
            nuclear_quote_count=("has_nuclear", "sum"),
            redline_quote_count=("has_redline", "sum"),
            threat_quote_count=("has_threat", "sum"),
            ultimatum_quote_count=("has_ultimatum", "sum"),
            escalation_quote_count=("has_escalation", "sum"),
            deter_quote_count=("has_deter", "sum"),
        )
        .reset_index()
    )

    # Convert boolean sums to int
    for col in [
        "media_volume_russia", "nuclear_quote_count", "redline_quote_count",
        "threat_quote_count", "ultimatum_quote_count", "escalation_quote_count",
        "deter_quote_count",
    ]:
        weekly[col] = weekly[col].astype(int)

    weekly["russia_share"] = weekly["media_volume_russia"] / weekly["media_volume_all"]
    weekly["year"] = weekly["week"].dt.year
    weekly["week_of_year"] = weekly["week"].dt.isocalendar().week.astype(int)

    weekly = weekly.sort_values("week")

    # Truncate and reload
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"TRUNCATE TABLE {SCHEMA}.gdelt_weekly_varx")

            cols = [
                "week", "media_volume_all", "media_volume_russia",
                "media_tone_mean", "media_tone_std", "media_negativity_mean",
                "media_negativity_std", "nuclear_quote_count", "redline_quote_count",
                "threat_quote_count", "ultimatum_quote_count",
                "escalation_quote_count", "deter_quote_count", "russia_share",
                "year", "week_of_year",
            ]
            placeholders = ",".join(["%s"] * len(cols))
            insert_sql = (
                f"INSERT INTO {SCHEMA}.gdelt_weekly_varx "
                f"({','.join(cols)}) VALUES ({placeholders})"
            )

            rows = [tuple(row[c] for c in cols) for _, row in weekly.iterrows()]
            psycopg2.extras.execute_batch(cur, insert_sql, rows, page_size=500)
        conn.commit()

    print(f"  Recomputed {len(weekly)} weeks")
    print(f"  Date range: {weekly['week'].min().date()} to {weekly['week'].max().date()}")


# =============================================================================
# STATUS
# =============================================================================

def print_status():
    """Print current GDELT data status."""
    print("=" * 60)
    print("GDELT DATA STATUS (war_datasets.global_events)")
    print("=" * 60)

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            tables = [
                ("gdelt_events", "sqldate", "globaleventid"),
                ("gdelt_gkg_coercive_quotations", "date", "gkgrecordid"),
                ("gdelt_gkg_redline_quotations", "date", "gkgrecordid"),
                ("gdelt_weekly_varx", None, None),
                ("gdelt_gkg_themes_lookup", None, None),
            ]

            for table, date_col, id_col in tables:
                cur.execute(f"SELECT count(*) FROM {SCHEMA}.{table}")
                count = cur.fetchone()[0]

                cur.execute(
                    f"SELECT pg_size_pretty(pg_total_relation_size('{SCHEMA}.{table}'))"
                )
                size = cur.fetchone()[0]

                if date_col:
                    cur.execute(f"SELECT MIN({date_col}), MAX({date_col}) FROM {SCHEMA}.{table}")
                    min_d, max_d = cur.fetchone()
                    # Format YYYYMMDD dates
                    if min_d and date_col == "sqldate":
                        date_range = f"{min_d} – {max_d}"
                    elif min_d:
                        date_range = f"{str(min_d)[:8]} – {str(max_d)[:8]}"
                    else:
                        date_range = "empty"
                else:
                    date_range = "static"

                print(f"\n  {table}:")
                print(f"    Rows: {count:,}  |  Size: {size}  |  Range: {date_range}")

            # Show gap
            cur.execute(f"SELECT MAX(sqldate) FROM {SCHEMA}.gdelt_events")
            last_event = cur.fetchone()[0]
            cur.execute(f"SELECT MAX(date) FROM {SCHEMA}.gdelt_gkg_coercive_quotations")
            last_gkg = cur.fetchone()[0]

    today = dt.date.today().strftime("%Y%m%d")
    print(f"\n  Gap to fill:")
    if last_event:
        print(f"    Events: {last_event} → {today}")
    if last_gkg:
        print(f"    GKG:    {str(last_gkg)[:8]} → {today}")

    print()


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Incrementally update GDELT data in war_datasets.global_events",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python update_gdelt.py                     # Full incremental update
  python update_gdelt.py --events-only       # Events only (no BigQuery needed)
  python update_gdelt.py --gkg-only          # GKG only (requires BigQuery auth)
  python update_gdelt.py --gkg-fallback      # GKG via file download (slow, no BigQuery)
  python update_gdelt.py --recompute-varx    # Recompute weekly VARX from DB
  python update_gdelt.py --from 2026-01-28   # From specific date
  python update_gdelt.py --days 7            # Last 7 days
  python update_gdelt.py --status            # Show data status
        """,
    )

    parser.add_argument("--from", dest="start_date", type=str,
                        help="Start date (YYYY-MM-DD). Default: auto-detect")
    parser.add_argument("--to", dest="end_date", type=str,
                        help="End date (YYYY-MM-DD). Default: yesterday")
    parser.add_argument("--days", type=int,
                        help="Fetch last N days (overrides --from)")
    parser.add_argument("--events-only", action="store_true",
                        help="Only update events (free, no BigQuery)")
    parser.add_argument("--gkg-only", action="store_true",
                        help="Only update GKG (requires BigQuery)")
    parser.add_argument("--gkg-fallback", action="store_true",
                        help="Use file download for GKG instead of BigQuery (slow)")
    parser.add_argument("--recompute-varx", action="store_true",
                        help="Only recompute weekly VARX from existing DB data")
    parser.add_argument("--status", action="store_true",
                        help="Show current data status and exit")

    args = parser.parse_args()

    if args.status:
        print_status()
        return

    if args.recompute_varx:
        recompute_weekly_varx()
        return

    # Determine date range
    # Default end_date: yesterday (GDELT has ~1hr delay, so today's data is incomplete)
    end_date = dt.date.today() - dt.timedelta(days=1)
    start_date = None

    if args.end_date:
        end_date = dt.datetime.strptime(args.end_date, "%Y-%m-%d").date()

    if args.days:
        start_date = end_date - dt.timedelta(days=args.days)
    elif args.start_date:
        start_date = dt.datetime.strptime(args.start_date, "%Y-%m-%d").date()

    # Auto-detect start date from DB
    if start_date is None:
        if not args.gkg_only:
            last_event = get_last_event_date()
            if last_event:
                start_date = dt.datetime.strptime(str(last_event), "%Y%m%d").date()
                start_date += dt.timedelta(days=1)
                print(f"Last event in DB: {last_event}")
            else:
                start_date = dt.date(2022, 1, 1)
                print("No events in DB — starting from 2022-01-01")
        else:
            last_gkg = get_last_gkg_date()
            if last_gkg:
                start_date = dt.datetime.strptime(str(last_gkg)[:8], "%Y%m%d").date()
                start_date += dt.timedelta(days=1)
                print(f"Last GKG record in DB: {last_gkg}")
            else:
                start_date = dt.date(2022, 1, 1)
                print("No GKG data in DB — starting from 2022-01-01")

    if start_date > end_date:
        print("Data is already up to date!")
        return

    print(f"\nDate range: {start_date} to {end_date}")

    # Setup logging
    LOG_DIR.mkdir(exist_ok=True)
    log_file = LOG_DIR / f"update_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    total_events = 0
    total_coercive = 0
    total_redline = 0

    # Update events
    if not args.gkg_only:
        total_events = update_events(start_date, end_date)

    # Update GKG
    if not args.events_only:
        if args.gkg_fallback:
            total_coercive, total_redline = update_gkg_files(start_date, end_date)
        else:
            total_coercive, total_redline = update_gkg_bigquery(start_date, end_date)

    # Recompute VARX if GKG was updated
    if total_coercive > 0:
        recompute_weekly_varx()

    # Summary
    print("\n" + "=" * 60)
    print("UPDATE SUMMARY")
    print("=" * 60)
    print(f"  Date range:         {start_date} to {end_date}")
    print(f"  New events:         {total_events:,}")
    print(f"  New coercive GKG:   {total_coercive:,}")
    print(f"  New red line GKG:   {total_redline:,}")
    if total_coercive > 0:
        print(f"  Weekly VARX:        recomputed")

    # Write log
    with open(log_file, "w") as f:
        f.write(f"GDELT Update Log — {dt.datetime.now().isoformat()}\n")
        f.write(f"Date range: {start_date} to {end_date}\n")
        f.write(f"New events: {total_events}\n")
        f.write(f"New coercive GKG: {total_coercive}\n")
        f.write(f"New red line GKG: {total_redline}\n")

    print(f"\n  Log: {log_file}")


if __name__ == "__main__":
    main()
