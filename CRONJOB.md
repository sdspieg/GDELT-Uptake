# GDELT Automated Update — Cronjob Reference

**Last updated:** 2026-03-02
**Status:** FULLY AUTOMATED — DB ingestion runs via cron on VPS (138.201.62.161); dashboard export/deploy runs via GitHub Actions

---

## Overview

Five GDELT tables in `war_datasets.global_events` on `138.201.62.161:5432` need periodic updates:

| Table | Update method | Auth needed | Frequency | Typical volume |
|-------|--------------|-------------|-----------|----------------|
| `gdelt_events` | Free file download | None | Daily | ~50–120 events/day |
| `gdelt_gkg_coercive_quotations` | BigQuery query | Google OAuth | Daily | ~200–500 records/day |
| `gdelt_gkg_redline_quotations` | BigQuery query (subset of above) | Google OAuth | Daily | ~5–10 records/day |
| `gdelt_weekly_varx` | Recomputed from coercive table | DB only | Weekly | 1 row/week |
| `gdelt_gkg_themes_lookup` | Static | None | Never | 59,315 rows (fixed) |

---

## Scripts

### Primary: `update_gdelt.py`

**Location:** `/mnt/g/My Drive/RuBase/Red lines/Datasets/GDELT-Events/update_gdelt.py`

```bash
# Full update (events + GKG via BigQuery + VARX recompute)
python update_gdelt.py

# Events only — no auth needed, free GDELT file downloads
python update_gdelt.py --events-only

# GKG only — requires BigQuery credentials
python update_gdelt.py --gkg-only

# GKG via file download — no BigQuery needed, but much slower (~2.5 files/sec × 96 files/day)
python update_gdelt.py --gkg-fallback

# Recompute VARX from existing DB data
python update_gdelt.py --recompute-varx

# Status check (no changes)
python update_gdelt.py --status

# Custom date range
python update_gdelt.py --from 2026-02-01 --to 2026-02-28
python update_gdelt.py --days 7
```

**Auto-detection:** Without `--from`, the script queries the DB for the most recent record and starts from the next day. Safe to run repeatedly — triple dedup (Python filter + SQL `ON CONFLICT DO NOTHING` + unique constraints).

**Logs:** Written to `update_logs/update_YYYYMMDD_HHMMSS.log`

### Master orchestrator: `update_all_datasets.py`

**Location:** `/mnt/g/My Drive/RuBase/Red lines/Datasets/update_all_datasets.py`

Covers ACLED, ISW, OpenSanctions, Oryx, SIPRI, Ukrainian sanctions, US DoD. **Does NOT yet include GDELT** — needs to be integrated when automation is set up.

### Monitor: `monitor_gdelt.py`

**Location:** `/mnt/g/My Drive/RuBase/Red lines/Datasets/GDELT-Events/monitor_gdelt.py`

```bash
cd "/mnt/g/My Drive/RuBase/Red lines/Datasets/GDELT-Events" && python3 monitor_gdelt.py
```

Colorful terminal dashboard showing table status, sparklines, gap detection. Auto-refreshes every 30s.

---

## Authentication

### BigQuery (required for GKG updates)

Two Google accounts with BigQuery access, each with 1 TB/month free tier:

| Account | BigQuery Project | Status |
|---------|-----------------|--------|
| `sdspieg@gmail.com` | `rubase-minimal` | Active — used by `update_gdelt.py` |
| `sdspiegus@gmail.com` | `project-25928243-c2b3-4e29-89f` | Active — backup account |

**Credential locations:**

```
~/.config/gcloud/legacy_credentials/sdspieg@gmail.com/adc.json      ← primary
~/.config/gcloud/legacy_credentials/sdspiegus@gmail.com/adc.json    ← secondary
```

Both contain `authorized_user` type credentials with refresh tokens.

**How `update_gdelt.py` finds credentials (in order):**

1. `./bigquery_credentials.json` in the script directory (currently a copy of `sdspieg` adc.json)
2. `GOOGLE_APPLICATION_CREDENTIALS` environment variable
3. Default gcloud application credentials

**To set up on a fresh machine or after token expiry:**

```bash
# Option A: Copy the adc.json manually
cp ~/.config/gcloud/legacy_credentials/sdspieg@gmail.com/adc.json \
   "/mnt/g/My Drive/RuBase/Red lines/Datasets/GDELT-Events/bigquery_credentials.json"

# Option B: Re-authenticate with gcloud (if installed)
gcloud auth application-default login --account=sdspieg@gmail.com

# Option C: Install gcloud SDK fresh (it lived in /tmp/ which is non-persistent)
curl https://sdk.cloud.google.com | bash
gcloud init
gcloud auth application-default login
```

**BigQuery cost:** Each coercive quotation query scans ~4–5 GB per month of data. Well within free tier. See `GDELT.md` for detailed cost tracking.

### PostgreSQL

```
Host:     138.201.62.161
Port:     5432
Database: war_datasets
Schema:   global_events
User:     postgres
Password: (see .CLAUDE.md or GitHub Actions secrets)
```

Runs in Docker container `postgres_database` (PostgreSQL 15.1) on the remote server.
SSH access: `ssh root@138.201.62.161` (password in .CLAUDE.md)

### Events (no auth needed)

GDELT publishes free 15-minute file exports at:
```
http://data.gdeltproject.org/gdeltv2/{YYYYMMDDHHMMSS}.export.CSV.zip
```
No API key, no authentication. The script downloads, filters for `Actor1CountryCode='RUS' AND EventRootCode='13'`, and inserts.

---

## Deduplication (triple layer)

1. **Python-side:** Loads existing IDs from DB (`globaleventid` / `gkgrecordid`), filters with `~df.isin(existing_ids)` before insert
2. **SQL:** All INSERTs use `ON CONFLICT (id) DO NOTHING`
3. **DB constraints:**
   - `uq_events_globaleventid` on `gdelt_events`
   - `uq_coercive_gkgrecordid` on `gdelt_gkg_coercive_quotations`
   - `uq_redline_gkgrecordid` on `gdelt_gkg_redline_quotations`

Safe to run multiple times per day. Will never duplicate.

---

## Recommended Cron Schedule

### Daily (events — no auth)

```cron
# GDELT events update — runs at 06:00 UTC daily
0 6 * * * cd "/mnt/g/My Drive/RuBase/Red lines/Datasets/GDELT-Events" && python3 update_gdelt.py --events-only --days 2 >> /tmp/gdelt_events_cron.log 2>&1
```

Uses `--days 2` for overlap safety (dedup handles it). GDELT files have ~1h delay, so 06:00 ensures yesterday's data is complete.

### Daily (GKG — requires BigQuery)

```cron
# GDELT GKG update — runs at 07:00 UTC daily (after events)
0 7 * * * cd "/mnt/g/My Drive/RuBase/Red lines/Datasets/GDELT-Events" && python3 update_gdelt.py --gkg-only --days 2 >> /tmp/gdelt_gkg_cron.log 2>&1
```

### Weekly (VARX recompute)

```cron
# Recompute weekly VARX — Mondays at 08:00 UTC
0 8 * * 1 cd "/mnt/g/My Drive/RuBase/Red lines/Datasets/GDELT-Events" && python3 update_gdelt.py --recompute-varx >> /tmp/gdelt_varx_cron.log 2>&1
```

### Alternative: single daily job (everything)

```cron
# Full GDELT update — 06:00 UTC daily
0 6 * * * cd "/mnt/g/My Drive/RuBase/Red lines/Datasets/GDELT-Events" && python3 update_gdelt.py --days 2 >> /tmp/gdelt_full_cron.log 2>&1
```

---

## Estimated Runtime

| Operation | Duration | Network | BigQuery cost |
|-----------|----------|---------|---------------|
| Events (1 day) | ~2 min | ~96 HTTP downloads | Free |
| Events (7 days) | ~12 min | ~672 downloads | Free |
| Events (30 days) | ~20 min | ~2,880 downloads | Free |
| GKG BigQuery (1 day) | ~30 sec | 1 BigQuery query | ~0.15 GB |
| GKG BigQuery (30 days) | ~2 min | 1 BigQuery query | ~5 GB |
| GKG file fallback (1 day) | ~40 sec | ~96 downloads | Free |
| GKG file fallback (30 days) | ~20 min | ~2,880 downloads | Free |
| VARX recompute | ~10 sec | DB only | Free |

---

## Dependencies

```bash
pip install pandas psycopg2-binary requests tqdm google-cloud-bigquery db-dtypes rich
```

All currently installed on the WSL machine.

---

## Data Filters (must match original extraction)

### Events
```sql
Actor1CountryCode = 'RUS' AND EventRootCode = '13'  -- THREATEN events by Russia
```
Source: `gdelt-bq.gdeltv2.events` / free file exports

### GKG Coercive Quotations
```sql
REGEXP_CONTAINS(Quotations,
  r"(?i)(nuclear\s+threat|nuclear\s+strike|nuclear\s+war|red\s+line|ultimatum|deter[a-z]*|escala[a-z]*)")
```
Source: `gdelt-bq.gdeltv2.gkg_partitioned`

### GKG Red Line Quotations
Subset of coercive where `Quotations` matches `(?i)red\s+line`

### Weekly VARX
Aggregated from coercive quotations: media volume (all + Russia-relevant), tone (mean/std), negativity, keyword counts (nuclear, redline, threat, ultimatum, escalation, deter). See `extract_weekly_varx_variables.py` for the original computation logic replicated in `update_gdelt.py:recompute_weekly_varx()`.

---

## Related Documentation

| File | What it covers |
|------|---------------|
| `GDELT.md` | BigQuery queries, column definitions, extraction history, cost tracking |
| `GKG_EXTRACTION_PLAN.md` | Original GKG extraction strategy, quota management |
| `Handover.md` | Project context, what was built, key decisions |
| `DATABASE_DOCUMENTATION.md` (parent dir) | Full schema docs for all 5 tables, column descriptions, indexes |
| `MIGRATION_TO_REMOTE_SERVER.md` (parent dir) | How the DB was set up on 138.201.62.161 |
| `extract_weekly_varx_variables.py` | Original VARX computation from CSV (now replicated in update script) |
| `update_all_datasets.py` (parent dir) | Master updater for other datasets (ACLED, ISW, etc.) |

---

## Dashboard Integration (Automated)

As of 2026-03-02, the **dashboard export and deployment** is fully automated via GitHub Actions:

- **Workflow:** `war-datasets-dashboard/.github/workflows/daily-update.yml`
- **Schedule:** Daily at 6 AM UTC
- **What it does:** Checks if any of 18 tracked DB tables (including `gdelt_events`, `gdelt_gkg_coercive_quotations`, `gdelt_gkg_redline_quotations`) have new data → selectively re-exports JSON → rebuilds dashboard → deploys to GitHub Pages
- **Full docs:** `Datasets/DAILY_UPDATE_PIPELINE.md` or `war-datasets-dashboard/docs/DAILY_UPDATE_PIPELINE.md`

**Full pipeline:** Data sources → `update_gdelt.py` (cron on VPS) → PostgreSQL → `check_new_data.py` + `export_changed.py` (GitHub Actions daily at 6 AM UTC) → JSON export → Vite build → GitHub Pages deploy. Fully hands-off.

## VPS Cron (DB Ingestion) — ACTIVE

Deployed 2026-03-02 to `/stratbase/apps/webapps/gdelt-updater/` on the VPS.

```cron
# Events: daily at 06:00 UTC, last 2 days overlap (dedup handles it)
0 6 * * * /stratbase/apps/webapps/gdelt-updater/env/bin/python /stratbase/apps/webapps/gdelt-updater/update_gdelt.py --events-only --days 2 >> /stratbase/apps/webapps/gdelt-updater/update_logs/cron_events.log 2>&1

# GKG (BigQuery): daily at 07:00 UTC, last 2 days overlap
0 7 * * * /stratbase/apps/webapps/gdelt-updater/env/bin/python /stratbase/apps/webapps/gdelt-updater/update_gdelt.py --gkg-only --days 2 >> /stratbase/apps/webapps/gdelt-updater/update_logs/cron_gkg.log 2>&1

# Weekly VARX recompute: Mondays at 08:00 UTC
0 8 * * 1 /stratbase/apps/webapps/gdelt-updater/env/bin/python /stratbase/apps/webapps/gdelt-updater/update_gdelt.py --recompute-varx >> /stratbase/apps/webapps/gdelt-updater/update_logs/cron_varx.log 2>&1
```

**VPS path:** `/stratbase/apps/webapps/gdelt-updater/`
**Venv:** `./env/` (Python 3.12, pandas, psycopg2-binary, google-cloud-bigquery, etc.)
**BigQuery creds:** `./bigquery_credentials.json` (sdspieg@gmail.com authorized_user token)
**Logs:** `./update_logs/cron_events.log`, `cron_gkg.log`, `cron_varx.log`

## TODO

- [x] ~~Dashboard export/deploy automation~~ — Done via GitHub Actions (2026-03-02)
- [x] ~~Set up crontab for DB ingestion on the remote server~~ — Done (2026-03-02)
- [ ] Add GDELT to `update_all_datasets.py` as a new dataset module
- [ ] Add alerting for failed updates (email/Slack notification on error)
- [ ] Monitor BigQuery quota usage (1 TB/month per account)
- [ ] Test OAuth token refresh — the `adc.json` refresh tokens should auto-renew, but verify after 30+ days
- [ ] Add `--gkg-fallback` as automatic fallback if BigQuery auth fails (currently must be specified manually)
