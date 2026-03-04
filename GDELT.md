# GDELT Data for Red Lines Research

**Created:** January 28, 2026
**BigQuery project:** `rubase-minimal`
**Accounts:**
- `sdspieg@gmail.com` — primary account (1 TB/month, resets 1st of each month)
- `sdspiegus@gmail.com` — secondary account (1 TB/month)
**Automation:** Fully automated as of 2026-03-02 — VPS cron runs `update_gdelt.py` daily (events at 06:00 UTC, GKG via BigQuery at 07:00 UTC, VARX weekly). See `CRONJOB.md` for details.

---

## What We Have

### 1. GDELT Events: Russia-Source THREATEN Dataset

**File:** `events_rus_threaten_20220101_20260128.csv`
**Size:** 115 MB
**Rows:** 291,869 (+ 1 header)
**Format:** CSV (comma-separated, with quoted fields containing commas)
**Source:** BigQuery table `gdelt-bq.gdeltv2.events`
**Query filter:** `Actor1CountryCode = 'RUS' AND EventRootCode = '13' AND Year >= 2022`

This is the **complete** set of GDELT-coded events where Russia is the source actor performing a THREATEN action (CAMEO root code 13), from January 1, 2022 through January 27, 2026. Includes all target actors (state and non-state), all sub-codes, all geographic data, tone, Goldstein conflict scores, and source URLs.

#### Counts by Year

| Year | Total | Code 138 (Military Force) | Code 139 (WMD) | Target: UKR | Target: USA | Target: Unknown |
|------|------:|:---:|:---:|:---:|:---:|:---:|
| 2022 | 97,347 | 32,918 | 1,123 | 28,740 | 4,616 | 33,497 |
| 2023 | 66,283 | 25,713 | 543 | 18,926 | 2,204 | 24,950 |
| 2024 | 65,687 | 26,288 | 280 | 15,585 | 2,984 | 24,050 |
| 2025 | 58,508 | 22,130 | **1,553** | 13,048 | 2,695 | 22,349 |
| 2026 (Jan) | 4,044 | 1,355 | 39 | 813 | 239 | 1,455 |
| **Total** | **291,869** | **108,404** | **3,538** | **77,112** | **12,738** | **106,301** |

**Key observations:**
- 2025 has a massive WMD threat spike (1,553 — nearly 6x the 2024 count of 280), driven by the Oreshnik hypersonic missile launch (Nov 2024) and revised Russian nuclear doctrine
- ~36% of targets are unknown/non-state actors (coded events where Actor2 has no country code)
- Ukraine is the target in 26% of all events; USA in 4%

#### All 61 Columns

| # | Column | Description |
|---|--------|-------------|
| 1 | GLOBALEVENTID | Unique event identifier |
| 2 | SQLDATE | Event date (YYYYMMDD) |
| 3 | MonthYear | YYYYMM |
| 4 | Year | YYYY |
| 5 | FractionDate | Decimal year |
| 6 | Actor1Code | Source actor code (always contains RUS) |
| 7 | Actor1Name | Source actor name (e.g., "RUSSIAN", "MOSCOW", "PUTIN") |
| 8 | Actor1CountryCode | Always "RUS" in this dataset |
| 9 | Actor1KnownGroupCode | Named group (e.g., military branch) |
| 10 | Actor1EthnicCode | Ethnic identifier |
| 11 | Actor1Religion1Code | Primary religion |
| 12 | Actor1Religion2Code | Secondary religion |
| 13 | Actor1Type1Code | Actor type (GOV, MIL, etc.) |
| 14 | Actor1Type2Code | Secondary type |
| 15 | Actor1Type3Code | Tertiary type |
| 16 | Actor2Code | Target actor code |
| 17 | Actor2Name | Target actor name |
| 18 | Actor2CountryCode | Target country (UKR, USA, GBR, etc.) |
| 19 | Actor2KnownGroupCode | Target named group |
| 20 | Actor2EthnicCode | Target ethnic identifier |
| 21 | Actor2Religion1Code | Target religion |
| 22 | Actor2Religion2Code | Target secondary religion |
| 23 | Actor2Type1Code | Target type (GOV, MIL, CVL, etc.) |
| 24 | Actor2Type2Code | Target secondary type |
| 25 | Actor2Type3Code | Target tertiary type |
| 26 | IsRootEvent | 1 = primary event of the article |
| 27 | EventCode | Full CAMEO code (see below) |
| 28 | EventBaseCode | Base CAMEO code |
| 29 | EventRootCode | Always "13" (THREATEN) in this dataset |
| 30 | QuadClass | Goldstein quadrant (3 = verbal conflict, 4 = material conflict) |
| 31 | GoldsteinScale | Conflict/cooperation score (-10 to +10) |
| 32 | NumMentions | Total article mentions of this event |
| 33 | NumSources | Number of distinct sources |
| 34 | NumArticles | Number of articles |
| 35 | AvgTone | Average article tone (-100 to +100) |
| 36 | Actor1Geo_Type | Geo resolution (1=country, 2=state, 3=city, 4=landmark) |
| 37 | Actor1Geo_FullName | Full place name |
| 38 | Actor1Geo_CountryCode | FIPS country code |
| 39 | Actor1Geo_ADM1Code | Admin division 1 |
| 40 | Actor1Geo_ADM2Code | Admin division 2 |
| 41 | Actor1Geo_Lat | Latitude |
| 42 | Actor1Geo_Long | Longitude |
| 43 | Actor1Geo_FeatureID | GeoNames/GNIS feature ID |
| 44 | Actor2Geo_Type | Target geo resolution |
| 45 | Actor2Geo_FullName | Target place name |
| 46 | Actor2Geo_CountryCode | Target FIPS country |
| 47 | Actor2Geo_ADM1Code | Target admin 1 |
| 48 | Actor2Geo_ADM2Code | Target admin 2 |
| 49 | Actor2Geo_Lat | Target latitude |
| 50 | Actor2Geo_Long | Target longitude |
| 51 | Actor2Geo_FeatureID | Target feature ID |
| 52 | ActionGeo_Type | Action location resolution |
| 53 | ActionGeo_FullName | Action location name |
| 54 | ActionGeo_CountryCode | Action FIPS country |
| 55 | ActionGeo_ADM1Code | Action admin 1 |
| 56 | ActionGeo_ADM2Code | Action admin 2 |
| 57 | ActionGeo_Lat | Action latitude |
| 58 | ActionGeo_Long | Action longitude |
| 59 | ActionGeo_FeatureID | Action feature ID |
| 60 | DATEADDED | Timestamp added to GDELT (YYYYMMDDHHmmSS) |
| 61 | SOURCEURL | Article URL |

#### CAMEO Threat Codes in This Dataset

| Code | Meaning | Use for Red Lines |
|------|---------|-------------------|
| 130 | Threaten, not specified | Generic threat language |
| 131 | Threaten non-force | Diplomatic/political threats |
| 132 | Threaten with political sanctions, boycott | Economic coercion |
| 133 | Threaten to halt negotiations | Diplomatic leverage |
| 134 | Threaten with political action | Political coercion |
| 135 | Threaten with political action, not specified | Same |
| 136 | Threaten with military mobilization | Escalation signal |
| 137 | Threaten military blockade | Military coercion |
| **138** | **Threaten with military force** | **Conventional red line enforcement** |
| **139** | **Threaten with WMD/unconventional violence** | **Nuclear threats — direct RRLS/NTS proxy** |
| 1382 | Threaten with unconventional attack | Hybrid threats |
| 1384 | Threaten with military occupation | Territorial coercion |

---

### 2. GKG Themes Lookup

**File:** `gkg_themes_lookup.txt`
**Size:** 2.0 MB
**Lines:** 59,315
**Format:** Tab-separated: `THEME_NAME\tFREQUENCY_COUNT`
**Source:** `http://data.gdeltproject.org/api/v2/guides/LOOKUP-GKGTHEMES.TXT`

Complete GDELT GKG theme taxonomy with global frequency counts. Used to identify which themes to filter when extracting GKG article-level records.

### 3. GKG: "Red Line" Quotations Dataset

**File:** `gkg_redline_quotations_20220101_20260128.csv`
**Size:** 6.7 MB
**Rows:** 8,618 (+ 1 header)
**Format:** CSV (comma-separated)
**Source:** BigQuery table `gdelt-bq.gdeltv2.gkg_partitioned`
**Query filter:** `REGEXP_CONTAINS(Quotations, r'(?i)red line') AND _PARTITIONTIME >= "2022-01-01"`
**BigQuery cost:** ~148 GB (COUNT: ~7 GB + extraction: ~141 GB)

GKG article-level records where someone is **directly quoted** using the phrase "red line." These are NLP-extracted quotations from news articles — capturing actual speech acts by officials, analysts, and commentators.

#### Columns (7)

| # | Column | Description |
|---|--------|-------------|
| 1 | GKGRECORDID | Unique GKG record ID |
| 2 | DATE | Timestamp (YYYYMMDDHHmmSS integer) |
| 3 | SourceCommonName | Media outlet (e.g., "bbc.co.uk") |
| 4 | DocumentIdentifier | Article URL |
| 5 | Quotations | Extracted direct quotations with offsets |
| 6 | V2Tone | Tone scores (6 comma-separated values) |
| 7 | V2Persons | Named persons with offsets |

#### Russia/Ukraine Subset

The 8,618 records are **worldwide** — covering all "red line" quotations in any context (Israel/Palestine, UK labour, EU trade, etc.). A local grep for Russia/Ukraine-related terms (russia, putin, kremlin, moscow, ukraine, lavrov, medvedev, zelensky) identifies **~1,087 records** (~12.6%) directly relevant to the research. Precise filtering should be done in PostgreSQL after import.

#### Why Quotations, Not Full-Text

GDELT's BigQuery tables do **not** contain article body text. The Quotations column is the closest proxy — it contains NLP-extracted direct quotes from the article. Searching Quotations for "red line" captures cases where the phrase appears in actual speech acts (e.g., "Putin has crossed a red line"), which is more analytically valuable for red lines research than general article mentions.

The DOC API full-text search found ~67,600 articles mentioning "red line" + russia, but those are article-level counts with no structured data beyond URL and title. This GKG extraction gives us structured records (tone, persons, source) for the subset where "red line" appears in a quoted statement.

---

## What We Still Need

### 4. GKG: WMD + Russia Theme-Based Records (NOT YET DOWNLOADED)

The GDELT Global Knowledge Graph (GKG) contains **article-level metadata** — one row per article processed by GDELT, with NLP-extracted themes, entities, tone, quotations, locations, and organizations. This is the **media discourse** dataset that would measure how Russia's red line statements propagate through the global information ecosystem.

#### Remaining GKG subsets to extract:

| Dataset | Query | Estimated Records | Source |
|---------|-------|------------------:|--------|
| **GKG: WMD + Russia** | theme:WMD + Russia in persons/locations | ~576,000 | BigQuery |
| **GKG: "nuclear threat" quotations** | REGEXP_CONTAINS(Quotations, 'nuclear threat') | TBD (need COUNT) | BigQuery |

#### GKG Schema (27 columns in BigQuery `gdelt-bq.gdeltv2.gkg_partitioned`)

| # | Column | Description | Key for Red Lines? |
|---|--------|-------------|:---:|
| 1 | GKGRECORDID | Unique record ID | |
| 2 | DATE | Timestamp (YYYYMMDDHHmmSS integer) | Yes — temporal alignment with RRLS |
| 3 | SourceCollectionIdentifier | 1=web, 2=citation-only, etc. | |
| 4 | SourceCommonName | Media outlet name (e.g., "bbc.co.uk") | Yes — media ecosystem analysis |
| 5 | DocumentIdentifier | Article URL | Yes — source verification |
| 6 | Counts | V1 count objects | |
| 7 | V2Counts | Enhanced count objects | |
| 8 | Themes | V1 themes (semicolon-separated) | |
| 9 | V2Themes | Enhanced themes with offsets | **Yes — primary filter** |
| 10 | Locations | V1 locations | |
| 11 | V2Locations | Enhanced locations with geo | **Yes — Russia/Ukraine filter** |
| 12 | Persons | V1 person names | |
| 13 | V2Persons | Enhanced persons with offsets | **Yes — Putin/Lavrov/etc. filter** |
| 14 | Organizations | V1 organizations | |
| 15 | V2Organizations | Enhanced organizations | Yes — NATO, Kremlin, etc. |
| 16 | V2Tone | Tone scores (6 values, comma-sep) | **Yes — escalatory framing** |
| 17 | Dates | Date references in text | |
| 18 | GCAM | Global Content Analysis Measures | Yes — detailed sentiment |
| 19 | SharingImage | Article sharing image URL | |
| 20 | RelatedImages | Related image URLs | |
| 21 | SocialImageEmbeds | Social media image embeds | |
| 22 | SocialVideoEmbeds | Social media video embeds | |
| 23 | Quotations | Extracted direct quotations | **Yes — closest to RRLS text** |
| 24 | AllNames | All named entities | |
| 25 | Amounts | Numerical amounts in text | |
| 26 | TranslationInfo | Source language + translation metadata | Yes — language coverage |
| 27 | Extras | Additional XML metadata | |

#### V2Tone Format (column 16)

Six comma-separated values per record:
1. **Tone** — overall tone (-100 to +100)
2. **Positive score** — % positive words
3. **Negative score** — % negative words
4. **Polarity** — positive + negative (emotional intensity)
5. **Activity Reference Density** — % activity-related words
6. **Self/Group Reference Density** — % self-referential words

### 4. GKG: Coercive Discourse Quotations (Enriched) — COMPLETE

This is the **expanded coercive discourse** dataset — capturing every GKG article where someone is directly quoted using nuclear threat, escalation, deterrence, ultimatum, or red line language, with full enriched columns.

**Coverage:** January 2022 – January 2026 (49 months, complete)
**Total records:** 354,187 (161,320 + 192,867)
**Total size:** ~1.8 GB

#### Batch 1: Jan 2022 – Nov 2023

**File:** `gkg_coercive_quotations_20220101_20231130.csv`
**Size:** 889 MB
**Rows:** 161,320 (+ 1 header)
**Account:** `sdspieg@gmail.com`
**BigQuery cost:** ~438 GB
**Extracted:** January 28, 2026

#### Batch 2: Dec 2023 – Jan 2026

**File:** `gkg_coercive_quotations_20231201_20260128.csv`
**Size:** 923 MB
**Rows:** 192,867 (+ 1 header)
**Account:** `sdspiegus@gmail.com`
**BigQuery cost:** ~484 GB
**Extracted:** January 28, 2026

#### Extraction Commands Used

```bash
# Reinstall gcloud SDK if /tmp was cleared:
curl -sL https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-linux-x86_64.tar.gz | tar -xz -C /tmp/
/tmp/google-cloud-sdk/install.sh --quiet --path-update false

# Authenticate (opens browser):
/tmp/google-cloud-sdk/bin/gcloud auth login --account=sdspiegus@gmail.com
/tmp/google-cloud-sdk/bin/gcloud config set project project-25928243-c2b3-4e29-89f

# Batch 1 (sdspieg@gmail.com, Jan 2022 – Nov 2023):
export PATH="/tmp/google-cloud-sdk/bin:$PATH" && bq query --use_legacy_sql=false --format=csv --max_rows=1000000 '
SELECT
  GKGRECORDID, DATE, SourceCommonName, DocumentIdentifier,
  V2Themes, V2Tone, V2Persons, V2Locations, V2Organizations,
  Quotations, TranslationInfo
FROM `gdelt-bq.gdeltv2.gkg_partitioned`
WHERE _PARTITIONTIME >= "2022-01-01" AND _PARTITIONTIME < "2023-12-01"
  AND REGEXP_CONTAINS(Quotations,
    r"(?i)(nuclear\\s+threat|nuclear\\s+strike|nuclear\\s+war|red\\s+line|ultimatum|deter[a-z]*|escala[a-z]*)")
' > gkg_coercive_quotations_20220101_20231130.csv

# Batch 2 (sdspiegus@gmail.com, Dec 2023 – Jan 2026):
export PATH="/tmp/google-cloud-sdk/bin:$PATH" && bq query --use_legacy_sql=false --format=csv --max_rows=1000000 '
SELECT
  GKGRECORDID, DATE, SourceCommonName, DocumentIdentifier,
  V2Themes, V2Tone, V2Persons, V2Locations, V2Organizations,
  Quotations, TranslationInfo
FROM `gdelt-bq.gdeltv2.gkg_partitioned`
WHERE _PARTITIONTIME >= "2023-12-01" AND _PARTITIONTIME < "2026-02-01"
  AND REGEXP_CONTAINS(Quotations,
    r"(?i)(nuclear\\s+threat|nuclear\\s+strike|nuclear\\s+war|red\\s+line|ultimatum|deter[a-z]*|escala[a-z]*)")
' > gkg_coercive_quotations_20231201_20260128.csv
```

#### Query Filter (both batches)

```sql
REGEXP_CONTAINS(Quotations, r'(?i)(nuclear\s+threat|nuclear\s+strike|nuclear\s+war|red\s+line|ultimatum|deter[a-z]*|escala[a-z]*)')
```

This captures articles where direct quotations contain:
- `nuclear threat` / `nuclear strike` / `nuclear war`
- `red line`
- `ultimatum`
- `deter*` (deterrence, determined, deter, etc.)
- `escala*` (escalation, escalate, escalating, etc.)

#### Columns (11)

| # | Column | Description |
|---|--------|-------------|
| 1 | GKGRECORDID | Unique GKG record ID |
| 2 | DATE | Timestamp (YYYYMMDDHHmmSS integer) |
| 3 | SourceCommonName | Media outlet (e.g., "bbc.co.uk") |
| 4 | DocumentIdentifier | Article URL |
| 5 | V2Themes | Semicolon-separated GKG theme codes with offsets |
| 6 | V2Tone | Tone scores (6 comma-separated values) |
| 7 | V2Persons | Named persons with offsets |
| 8 | V2Locations | Geographic locations with coordinates |
| 9 | V2Organizations | Organizations with offsets |
| 10 | Quotations | Extracted direct quotations with offsets |
| 11 | TranslationInfo | Source language info (100% NULL — all English-language articles) |

#### Quotation Pattern Distribution

| Pattern | Records | Share |
|---------|--------:|------:|
| `deter*` (deterrence, determined, etc.) | 113,216 | 70.2% |
| `escala*` (escalation, escalate, etc.) | 41,250 | 25.6% |
| `nuclear war` | 3,723 | 2.3% |
| `red line` | 3,250 | 2.0% |
| `ultimatum` | 983 | 0.6% |
| `nuclear threat` | 901 | 0.6% |
| `nuclear strike` | 844 | 0.5% |

*Note: patterns overlap — one article can match multiple patterns.*

#### Russia-Relevance vs. Contamination

| Marker | Records | Share |
|--------|--------:|------:|
| ANY Russia/Ukraine marker (persons, locations, or themes) | 43,603 | **27.0%** |
| Russia/Ukraine locations (V2Locations) | 43,284 | 26.8% |
| Russia/Russian themes (V2Themes) | 36,098 | 22.4% |
| Russia/Ukraine persons (V2Persons) | 19,790 | 12.3% |
| ANY Israel/Gaza marker | 19,116 | 11.8% |
| Israel/Gaza locations | 19,095 | 11.8% |
| Israel/Gaza persons | 7,298 | 4.5% |

**Key insight:** Only 27% of records have explicit Russia/Ukraine markers. The remaining 73% is broader global deterrence/escalation discourse. This is expected — "deterrence" and "escalation" are general-purpose IR concepts used in every geopolitical context. For Russia-specific analysis, filter using the person/location/theme markers above.

**Israel/Gaza contamination:** 11.8% of records relate to Israel/Gaza, concentrated in Oct–Nov 2023 (Hamas attack). The Oct 2023 monthly spike (14,831 records — 2x the average) is almost entirely driven by this.

#### Monthly Distribution

| Month | Records | | Month | Records |
|-------|--------:|-|-------|--------:|
| 2022-01 | 5,650 | | 2023-01 | 5,381 |
| 2022-02 | 7,625 | | 2023-02 | 5,462 |
| 2022-03 | 7,269 | | 2023-03 | 6,525 |
| 2022-04 | 5,295 | | 2023-04 | 8,748 |
| 2022-05 | 4,897 | | 2023-05 | 8,283 |
| 2022-06 | 6,810 | | 2023-06 | 8,510 |
| 2022-07 | 5,204 | | 2023-07 | 6,529 |
| 2022-08 | 6,438 | | 2023-08 | 10,183 |
| 2022-09 | 5,070 | | 2023-09 | 6,767 |
| 2022-10 | 6,501 | | 2023-10 | **14,831** |
| 2022-11 | 6,447 | | 2023-11 | 8,298 |
| 2022-12 | 4,597 | | | |

**2022 total:** 71,803 | **2023 total (Jan–Nov):** 89,517

#### Top 10 Sources

| Source | Records |
|--------|--------:|
| msn.com | 3,306 |
| yahoo.com | 2,459 |
| iheart.com | 1,650 |
| theguardian.com | 970 |
| streetinsider.com | 924 |
| menafn.com | 876 |
| indiatimes.com | 775 |
| jdsupra.com | 754 |
| bbc.co.uk | 597 |
| dawn.com | 547 |

**Total unique sources:** 8,245

---

#### GKG Extraction Status

**Done:**
- "Red line" Quotations subset (8,618 records, 7 columns, ~148 GB of quota used) — `sdspieg@gmail.com`
- **Coercive Discourse Quotations Batch 1** (161,320 records, 11 columns, ~438 GB) — Jan 2022 – Nov 2023 — `sdspieg@gmail.com`
- **Coercive Discourse Quotations Batch 2** (192,867 records, 11 columns, ~484 GB) — Dec 2023 – Jan 2026 — `sdspiegus@gmail.com`

**Coercive discourse extraction: COMPLETE** (354,187 total records, 49 months coverage)

#### Extraction Plan (Full Details: `GKG_EXTRACTION_PLAN.md`)

**TIER 0 — FREE (GDELT DOC API, zero BigQuery cost):**
- Daily article-count time series for "red line" + russia, "nuclear threat" + russia, "escalation" + russia
- Same series broken out by **source language** (Russian, German, Chinese, English) — critical for Reflexive Control cross-national framing analysis
- Daily tone time series per language/query
- Implementation: Python script, ~425 DOC API calls, ~7 minutes runtime

**TIER 1 — Coercive Discourse Quotations: ✅ COMPLETE**

| Query | Description | GB Used | Status |
|-------|-------------|---------|--------|
| Batch 1 (Jan 2022–Nov 2023) | 161,320 records via `sdspieg@gmail.com` | ~438 GB | ✅ Done Jan 28, 2026 |
| Batch 2 (Dec 2023–Jan 2026) | 192,867 records via `sdspiegus@gmail.com` | ~484 GB | ✅ Done Jan 28, 2026 |
| **TOTAL** | **354,187 records** | **~922 GB** | **COMPLETE** |

**TIER 1b — Theme-only monthly counts (optional):**

| Query | Description | GB/12mo | Schedule |
|-------|-------------|---------|----------|
| Theme-only monthly counts | Aggregate counts of WMD, ACT_HARMTHREATEN, UNREST_ULTIMATUM, etc. across full 49-month range (no record-level data) | ~392 | Feb (sdspieg reset) or use remaining sdspiegus quota (~516 GB) |

**TIER 2 — WMD + Russia theme-based full records:**

| Query | Description | GB/12mo | Schedule |
|-------|-------------|---------|----------|
| WMD + Russia theme-based full records | ~576K articles: `V2Themes LIKE 'WMD\|ACT_HARMTHREATEN\|...'` AND Russia in persons/locations. Full 11 columns | ~408 | Can start now with remaining sdspiegus quota (~516 GB for ~15 months), complete on Feb reset |

**TIER 3 — Third Gmail account (nice-to-have):**

| Query | Description | GB | Schedule |
|-------|-------------|-----|----------|
| EventMentions join | Per-article source data for all 260K threat events | ~1,000 | Dedicated account, 1 month |

**Total cost: $0. Total accounts: 2–3. Total calendar time: ~3 months for everything.**

#### Why the DOC API Should Be First

The DOC API is unlimited, free, and answers several key questions that BigQuery cannot:
- **Cross-language discourse volume** — does Russian-language media spike on the same days as English?
- **Daily resolution** — allows precise alignment with 329 RRLS issuance dates
- **Tone by language** — is Russian media *more* or *less* negative in red-line framing?
- **No column-scan cost** — BigQuery charges for column bytes scanned regardless of row count; DOC API has no such constraint

#### BigQuery Cost Structure (Why It's Expensive)

BigQuery charges per **byte scanned**, not per row returned. For the GKG partitioned table:
- `Quotations` column: ~5 GB/month × 49 months = **~245 GB** just to scan
- `V2Themes` column: ~8 GB/month × 49 months = **~392 GB** just to scan
- `GCAM` column: ~15 GB/month × 49 months = **~735 GB** (never worth scanning on free tier)
- Any query touching Quotations + V2Themes costs ~637 GB minimum for the full range
- **Solution: time-partition batching** — `WHERE _PARTITIONTIME >= X AND _PARTITIONTIME < Y` limits scan to those months only

---

## What We Know (Article Counts from GDELT DOC API)

### Full-text: "red line" + russia (English exact phrase)

| Quarter | Articles |
|---------|----------|
| Feb–Apr 2022 (invasion) | **15,883** |
| May–Jul 2022 | 4,628 |
| Aug–Oct 2022 | 4,968 |
| Nov 2022–Jan 2023 | 7,755 |
| Feb–Apr 2023 (anniversary + ICC warrant) | **12,751** |
| May–Jul 2023 | 1,389 |
| Aug–Oct 2023 | 1,298 |
| Nov 2023–Jan 2024 | 1,058 |
| Feb–Apr 2024 | 2,273 |
| May–Jul 2024 | 2,045 |
| Aug–Oct 2024 | 2,226 |
| Nov 2024–Jan 2025 | 2,088 |
| Feb–Apr 2025 | 3,745 |
| May–Jul 2025 | 1,251 |
| Aug–Oct 2025 | 1,619 |
| Oct 2025–Jan 2026 | 2,633 |
| **TOTAL** | **~67,600** |

### Full-text: "nuclear threat" + russia (English exact phrase)

| Quarter | Articles |
|---------|----------|
| Feb–Apr 2022 | 8,697 |
| May–Jul 2022 | 4,532 |
| **Aug–Oct 2022** (annexation + nuclear escalation) | **9,459** |
| Nov 2022–Jan 2023 | 3,787 |
| Feb–Apr 2023 | 3,747 |
| May–Jul 2023 | 1,667 |
| Aug–Oct 2023 | 1,163 |
| Nov 2023–Jan 2024 | 571 |
| Feb–Apr 2024 | 1,009 |
| May–Jul 2024 | 616 |
| Aug–Oct 2024 | 858 |
| Nov 2024–Jan 2025 | 1,088 |
| Feb–Apr 2025 | 401 |
| May–Jul 2025 | 503 |
| Aug 2025–Jan 2026 | 1,431 |
| **TOTAL** | **~39,500** |

### Theme-based: `WMD` + russia (GKG taxonomy, all languages)

| Period | GKG Articles |
|--------|-------------|
| Feb–Apr 2022 | **151,066** |
| May–Jul 2022 | 37,753 |
| **Aug–Oct 2022** | **93,968** |
| Nov 2022–Jan 2023 | 51,832 |
| Feb–Jul 2023 | 89,571 |
| Aug–Oct 2023 | 14,577 |
| Nov 2023–Jan 2024 | 12,389 |
| Feb–Jul 2024 | 26,953 |
| Aug–Oct 2024 | 17,471 |
| Nov 2024–Jan 2025 | 26,798 |
| Feb–Apr 2025 | 14,521 |
| May–Jul 2025 | 11,868 |
| Aug 2025–Jan 2026 | 27,561 |
| **TOTAL** | **~576,000** |

### Why the N difference matters

| Approach | N | What It Captures |
|----------|--:|------------------|
| Full-text "red line" (EN) | 67,600 | Only articles using the exact English phrase |
| Full-text "nuclear threat" (EN) | 39,500 | Only articles using the exact English phrase |
| Theme: WMD + Russia | 576,000 | All languages, all phrasings, NLP-classified |
| Theme: threat/coercion combo | ~1.3M est. | Broadest capture of coercive signaling |

The theme-based approach is **8–19x larger** because GDELT's NLP classifies articles by topic regardless of exact wording or language. The full-text approach captures only one specific phrasing in one language.

For the paper's purposes, both matter:
- **Full-text "red line"**: precisely captures discourse explicitly using this IR concept
- **Theme-based WMD/threat**: captures the broader phenomenon regardless of framing

---

## GKG Themes Relevant to Red Lines Research

### Tier 1: Core (Always Filter)

| Theme | Global Frequency | Maps to RRLS Concept |
|-------|:---:|---|
| `WMD` | 5.8M | Nuclear/WMD discourse |
| `WB_2505_WEAPONS_OF_MASS_DESTRUCTION` | 302K | Same (World Bank taxonomy) |
| `WB_2503_WEAPONS_PROLIFERATION_AND_ARMS_CONTROL` | 673K | Arms control regime |
| `WB_2469_NUCLEAR_AND_CHEMICAL_WAR` | 351K | Nuclear warfare discourse |
| `ACT_FORCEPOSTURE` | 1.7M | Military posture changes |
| `ACT_HARMTHREATEN` | 672K | Explicit threat language |
| `UNREST_ULTIMATUM` | 1.6M | Ultimatum rhetoric |
| `RETALIATE` | 6.1M | Retaliatory actions/threats |
| `SANCTIONS` | 14.6M | Economic coercion / Western responses |

### Tier 2: Conflict & Escalation

| Theme | Freq | Notes |
|-------|:---:|---|
| `ARMEDCONFLICT` | 143M | Base conflict events |
| `WB_2462_POLITICAL_VIOLENCE_AND_WAR` | 45.7M | Political violence framing |
| `WB_2468_CONVENTIONAL_WAR` | 7.1M | Conventional vs nuclear framing |
| `SOVEREIGNTY` | 7.5M | Core red line trigger |
| `CEASEFIRE` | 6.2M | De-escalation signals |
| `NEGOTIATIONS` | 31.4M | Diplomatic context |
| `WB_2510_WAR_CRIMES` | 1.6M | Accountability discourse |
| `WB_2494_TERRITORIAL_DEFENSE` | 39K | Territorial integrity themes |

### Tier 3: Weapons & Military

| Theme | Freq | Notes |
|-------|:---:|---|
| `TAX_WEAPONS_WARHEAD` | 408K | Nuclear warhead discourse |
| `TAX_WEAPONS_CRUISE_MISSILES` | 320K | Missile systems |
| `TAX_WEAPONS_AIR_DEFENSE_SYSTEM` | 92K | Air defense/intercept |
| `MIL_SELF_IDENTIFIED_ARMS_DEAL` | 621K | Arms transfers |
| `MANMADE_DISASTER_RADIOACTIVE` | 890K | Nuclear incidents (Zaporizhzhia) |
| `ENV_NUCLEARPOWER` | 771K | Nuclear power infrastructure |
| `GOV_MILITARY_DRAFT` | 33K | Mobilization signals |
| `TAX_FNCACT_CONSCRIPTS` | 152K | Conscription discourse |

### Tier 4: Information & Perception

| Theme | Freq | Notes |
|-------|:---:|---|
| `PROPAGANDA` | 5.7M | Reflexive control channel |
| `CYBER_ATTACK` | 9.7M | Hybrid warfare |
| `UNREST_BELLIGERENT` | 30.5M | Belligerent framing |
| `EPU_CATS_NATIONAL_SECURITY` | 72.4M | National security framing |
| `EPU_UNCERTAINTY` | 12.6M | Policy uncertainty |
| `EPU_POLICY_DUMA` | 1.8M | Russian domestic signals |

### Tier 5: Energy Weaponization

| Theme | Freq | Notes |
|-------|:---:|---|
| `WB_507_ENERGY_AND_EXTRACTIVES` | 78.3M | Energy sector (broad) |
| `ENV_OIL` | 35.1M | Oil markets |
| `ENV_NATURALGAS` | 5.5M | Gas weaponization |
| `WB_2299_PIPELINES` | 5.8M | Pipelines (Nord Stream) |
| `BLOCKADE` | 5.9M | Economic/military blockade |

### Tier 6: Humanitarian & Consequences

| Theme | Freq | Notes |
|-------|:---:|---|
| `REFUGEES` | 21.5M | Humanitarian consequences |
| `SELF_IDENTIFIED_ATROCITY` | 6.5M | Atrocity framing |
| `WB_2509_GENOCIDE` | 2.3M | Genocide discourse |
| `WB_2508_ETHNIC_CLEANSING` | 438K | Ethnic cleansing discourse |
| `ALLIANCE` | 31.8M | NATO/alliance discourse |

### NOT in Themes Taxonomy

- **"red line" / "redline"** — No match. The concept only appears in full-text article content, not as a GKG theme. Closest proxy: `UNREST_ULTIMATUM` + `ACT_HARMTHREATEN`.
- **Named persons** (Putin, Lavrov, Shoigu) — Not in themes. These appear in the GKG `V2Persons` column.
- **Country names** (Russia, Ukraine) — Not direct themes. Proxied by `TAX_WORLDLANGUAGES_RUSSIA` (41.8M) and `TAX_ETHNICITY_RUSSIAN` (35.4M), or via `V2Locations` column.

---

## How This Maps to the Paper

The Stulberg & De Spiegeleire paper ("Lost in Translation — Decoding Putin's Red Lines") uses:
- **329 RRLS** (Russian Real Red Line Statements) from 2,583 Kremlin documents
- **58 NTS** (Nuclear Threat Statements) — subset of RRLS
- **ACLED** for conflict events (already in our PostgreSQL database)
- **US DoD weapons aid** data (already in our Datasets folder)
- **POLECAT** for media sentiment (already in our Datasets folder)

### What GDELT adds that the paper lacks

| Gap in Paper | GDELT Source | What It Measures |
|-------------|-------------|------------------|
| No media echo measurement | GKG articles with WMD/threat themes | How RRLS propagate through global media |
| No non-Kremlin threat data | Events Actor1=RUS THREATEN | GDELT-coded threats from news (not just Kremlin transcripts) |
| No target-actor directionality | Events Actor2CountryCode | Who Russia threatens — and how that changes over time |
| No cross-national framing | GKG SourceCommonName + TranslationInfo | How Russian threats are framed differently in Russian vs. Western vs. Global South media |
| No Goldstein conflict intensity | Events GoldsteinScale | Quantified conflict/cooperation score per event |
| No WMD threat time series | Events EventCode=139 | Daily count of WMD-specific threats — directly comparable to NTS |
| No quotation extraction | GKG Quotations column | Actual quotes from articles — can cross-reference with RRLS text |

### Key joins with existing data

```
GDELT Events (date, EventCode, Actor2)
  ↕ JOIN on date
RRLS/NTS statements (date, theme, threat_type)
  ↕ JOIN on date
ACLED events (event_date, sub_event_type, fatalities)
  ↕ JOIN on date
US DoD weapons aid (date, weapon_system)
  ↕ JOIN on date
PetroIvaniuk missile attacks (date, weapon_model, launched, intercepted)
```

---

## BigQuery Access

### Authentication

```bash
# gcloud SDK location (not persistent across reboots)
/tmp/google-cloud-sdk/bin/gcloud auth login
/tmp/google-cloud-sdk/bin/gcloud config set project rubase-minimal

# Or reinstall if /tmp was cleared:
curl -sL https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-linux-x86_64.tar.gz | tar -xz -C /tmp/
/tmp/google-cloud-sdk/install.sh --quiet
```

### GDELT BigQuery Tables

| Table | Size | Description |
|-------|------|-------------|
| `gdelt-bq.gdeltv2.events` | ~200 GB | Event records with Actor1/Actor2 + CAMEO codes |
| `gdelt-bq.gdeltv2.eventmentions` | ~800 GB | Individual article mentions of events |
| `gdelt-bq.gdeltv2.gkg_partitioned` | ~3.6 TB | Global Knowledge Graph (article metadata) |

### Quota Status (as of Jan 28, 2026)

**sdspieg@gmail.com (primary):**
- Free tier: 1 TB/month
- Used: ~984 GB
  - Events extraction: ~398 GB
  - GKG "red line" Quotations (COUNT + extraction): ~148 GB
  - GKG Coercive Discourse Quotations (Jan 2022 – Nov 2023): ~438 GB
- **Remaining: ~16 GB** (effectively exhausted for this month)
- Resets: February 1, 2026 → 1 TB available

**sdspiegus@gmail.com (secondary):**
- Free tier: 1 TB/month
- Used: ~484 GB (Jan 28, 2026)
  - GKG Coercive Discourse Quotations Batch 2 (Dec 2023 – Jan 2026): ~484 GB
- **Remaining: ~516 GB** (Jan 2026)
- GCP project: `project-25928243-c2b3-4e29-89f` ("My First Project")
- Resets: February 1, 2026 → 1 TB available

### Ready-to-Run Queries

#### GKG: WMD + Russia-related articles (theme-filtered, all 27 columns)

```sql
-- Cost: ~15 GB per month of data scanned
-- Total estimated: ~768 GB for full 48 months (exceeds remaining free quota)
-- Solution: batch across 2 billing months, or pay ~$3-5 for on-demand

SELECT *
FROM `gdelt-bq.gdeltv2.gkg_partitioned`
WHERE _PARTITIONTIME >= '2022-01-01'
  AND REGEXP_CONTAINS(V2Themes,
    r'WMD|WB_2505|WB_2469|ACT_HARMTHREATEN|UNREST_ULTIMATUM|ACT_FORCEPOSTURE|RETALIATE')
  AND (
    REGEXP_CONTAINS(V2Persons, r'(?i)putin|lavrov|medvedev|peskov|shoigu|patrushev|gerasimov')
    OR REGEXP_CONTAINS(V2Locations, r'(?i)russia|moscow|kremlin|ukraine|kyiv')
    OR REGEXP_CONTAINS(V2Themes, r'TAX_WORLDLANGUAGES_RUSSIA|TAX_ETHNICITY_RUSSIAN')
  )
```

#### GKG: Broader nuclear/threat articles (theme-filtered only, no person/location filter)

```sql
-- Smaller scan: skips V2Persons and V2Locations columns
-- Can filter for Russia locally in PostgreSQL

SELECT
  GKGRECORDID, DATE, SourceCommonName, DocumentIdentifier,
  V2Themes, V2Tone, V2Persons, V2Locations, V2Organizations,
  Quotations, TranslationInfo
FROM `gdelt-bq.gdeltv2.gkg_partitioned`
WHERE _PARTITIONTIME >= '2022-01-01' AND _PARTITIONTIME < '2022-04-01'
  AND REGEXP_CONTAINS(V2Themes,
    r'WMD|WB_2505|WB_2469|ACT_HARMTHREATEN|UNREST_ULTIMATUM|ACT_FORCEPOSTURE')
```

#### Events: full RUS→THREATEN with EventMentions (richer source data)

```sql
-- Join events with their individual article mentions
SELECT e.*, m.MentionTimeDate, m.MentionType, m.MentionSourceName,
       m.MentionIdentifier, m.Confidence, m.MentionDocTone
FROM `gdelt-bq.gdeltv2.events` e
JOIN `gdelt-bq.gdeltv2.eventmentions` m
  ON e.GLOBALEVENTID = m.GLOBALEVENTID
WHERE e.Actor1CountryCode = 'RUS'
  AND e.EventRootCode = '13'
  AND e.Year >= 2022
```

---

## GDELT DOC API Reference

The GDELT DOC 2.0 API provides full-text search across all GDELT-monitored articles. It does NOT give GKG record-level data, but it returns article metadata and counts.

**Base URL:** `https://api.gdeltproject.org/api/v2/doc/doc`

### Key Parameters

| Parameter | Values | Notes |
|-----------|--------|-------|
| `query` | search terms | Supports `"exact phrase"`, `theme:THEME_NAME`, `sourcecountry:XX`, `sourcelang:XX`, boolean `OR`/`AND` |
| `mode` | `artlist`, `timelinevolraw`, `timelinevol`, `tonechart` | `timelinevolraw` gives daily article counts |
| `TIMESPAN` | 1–131580 (minutes) | Max ~3 months |
| `STARTDATETIME` | YYYYMMDDHHmmSS | Alternative to TIMESPAN |
| `ENDDATETIME` | YYYYMMDDHHmmSS | End of range |
| `format` | `csv`, `json`, `html` | |
| `maxrecords` | 1–250 | For `artlist` mode |

### Example: daily article counts for "red line" + russia

```
https://api.gdeltproject.org/api/v2/doc/doc?query=%22red%20line%22%20russia&mode=timelinevolraw&STARTDATETIME=20220201000000&ENDDATETIME=20220501000000&format=csv
```

Returns CSV with three columns: `Date`, `Series` (either "Article Count" or "Total Monitored Articles"), `Value`.

### Limitations

- Maximum 3-month window per query
- Full-text only — no GKG column-level data
- Only ~250 articles returned in `artlist` mode
- English phrases only capture English articles; use multilingual OR queries for broader coverage
- Rate limited (~1 request/second)

---

## Folder Contents

```
GDELT-Events/
├── events_rus_threaten_20220101_20260128.csv              ← 291,869 events, 115 MB, 61 cols
├── gkg_redline_quotations_20220101_20260128.csv           ← 8,618 GKG records, 6.7 MB, 7 cols
├── gkg_coercive_quotations_20220101_20231130.csv          ← 161,320 GKG records, 889 MB, 11 cols
│                                                             Batch 1: Jan 2022 – Nov 2023
│                                                             Account: sdspieg@gmail.com
├── gkg_coercive_quotations_20231201_20260128.csv          ← 192,867 GKG records, 923 MB, 11 cols
│                                                             Batch 2: Dec 2023 – Jan 2026
│                                                             Account: sdspiegus@gmail.com
│                                                             ** COERCIVE DISCOURSE NOW COMPLETE **
│                                                             Combined: 354,187 records, ~1.8 GB
├── gkg_themes_lookup.txt                                  ← 59,315 themes with frequency counts
├── GDELT.md                                               ← This file
├── GKG_EXTRACTION_PLAN.md                                 ← Full extraction roadmap (Tiers 0–3)
├── gdelt_vizzes.py                                        ← Visualization script (8 vizzes from enriched dataset)
└── vizzes/                                                ← 8 PNGs + 8 companion MDs + cross-cutting themes
    ├── 01_coercive_discourse_volume_breakdown              All vs Russia-relevant vs nuclear monthly
    ├── 02_quotation_pattern_composition                    Stacked area: deter*/escala*/nuclear/red line
    ├── 03_russia_vs_israel_share_over_time                 Geographic relevance shares (who is it about?)
    ├── 04_top_gkg_themes_coercive                          Top 30 GKG themes co-occurring
    ├── 05_top_organizations_coercive                       Top 25 organizations (NATO, White House, etc.)
    ├── 06_geographic_focus_coercive                        Top 25 locations, color-coded by region
    ├── 07_source_domains_comparison                        Coercive (161K) vs red-line-only (8.6K) sources
    └── 08_triple_events_vs_coercive_vs_redline             Events vs coercive discourse vs red line only
```

---

## PostgreSQL Import Plan

### Events table

```sql
CREATE SCHEMA IF NOT EXISTS gdelt;

CREATE TABLE gdelt.events_rus_threaten (
    globaleventid BIGINT PRIMARY KEY,
    sqldate INTEGER,
    monthyear INTEGER,
    year INTEGER,
    fractiondate NUMERIC(8,4),
    actor1code TEXT,
    actor1name TEXT,
    actor1countrycode TEXT,           -- Always 'RUS' in this dataset
    actor1knowngroupcode TEXT,
    actor1ethniccode TEXT,
    actor1religion1code TEXT,
    actor1religion2code TEXT,
    actor1type1code TEXT,
    actor1type2code TEXT,
    actor1type3code TEXT,
    actor2code TEXT,
    actor2name TEXT,
    actor2countrycode TEXT,           -- Target country
    actor2knowngroupcode TEXT,
    actor2ethniccode TEXT,
    actor2religion1code TEXT,
    actor2religion2code TEXT,
    actor2type1code TEXT,
    actor2type2code TEXT,
    actor2type3code TEXT,
    isrootevent INTEGER,
    eventcode TEXT,                   -- CAMEO code (130-139, 1382, 1384)
    eventbasecode TEXT,
    eventrootcode TEXT,               -- Always '13' (THREATEN)
    quadclass INTEGER,                -- 3=verbal conflict, 4=material conflict
    goldsteinscale NUMERIC(4,1),      -- -10 to +10
    nummentions INTEGER,
    numsources INTEGER,
    numarticles INTEGER,
    avgtone NUMERIC(8,6),
    actor1geo_type INTEGER,
    actor1geo_fullname TEXT,
    actor1geo_countrycode TEXT,
    actor1geo_adm1code TEXT,
    actor1geo_adm2code TEXT,
    actor1geo_lat NUMERIC(9,6),
    actor1geo_long NUMERIC(10,6),
    actor1geo_featureid TEXT,
    actor2geo_type INTEGER,
    actor2geo_fullname TEXT,
    actor2geo_countrycode TEXT,
    actor2geo_adm1code TEXT,
    actor2geo_adm2code TEXT,
    actor2geo_lat NUMERIC(9,6),
    actor2geo_long NUMERIC(10,6),
    actor2geo_featureid TEXT,
    actiongeo_type INTEGER,
    actiongeo_fullname TEXT,
    actiongeo_countrycode TEXT,
    actiongeo_adm1code TEXT,
    actiongeo_adm2code TEXT,
    actiongeo_lat NUMERIC(9,6),
    actiongeo_long NUMERIC(10,6),
    actiongeo_featureid TEXT,
    dateadded BIGINT,
    sourceurl TEXT
);

CREATE INDEX idx_events_date ON gdelt.events_rus_threaten(sqldate);
CREATE INDEX idx_events_code ON gdelt.events_rus_threaten(eventcode);
CREATE INDEX idx_events_target ON gdelt.events_rus_threaten(actor2countrycode);
CREATE INDEX idx_events_goldstein ON gdelt.events_rus_threaten(goldsteinscale);
```

### Import command

```bash
# From psql connected to russian_ukrainian_war (localhost:5433)
\COPY gdelt.events_rus_threaten FROM 'events_rus_threaten_20220101_20260128.csv' WITH (FORMAT CSV, HEADER TRUE);
```

### GKG "red line" Quotations table

```sql
CREATE TABLE gdelt.gkg_redline_quotations (
    gkgrecordid TEXT PRIMARY KEY,
    date BIGINT,                      -- YYYYMMDDHHmmSS
    sourcecommonname TEXT,
    documentidentifier TEXT,          -- Article URL
    quotations TEXT,                  -- Extracted direct quotes with offsets
    v2tone TEXT,                      -- 6 comma-separated tone values
    v2persons TEXT                    -- Named persons with offsets
);

CREATE INDEX idx_gkg_rl_date ON gdelt.gkg_redline_quotations(date);
CREATE INDEX idx_gkg_rl_source ON gdelt.gkg_redline_quotations(sourcecommonname);
```

```bash
\COPY gdelt.gkg_redline_quotations FROM 'gkg_redline_quotations_20220101_20260128.csv' WITH (FORMAT CSV, HEADER TRUE);
```

### GKG Coercive Discourse Quotations table

```sql
CREATE TABLE gdelt.gkg_coercive_quotations (
    gkgrecordid TEXT PRIMARY KEY,
    date BIGINT,                      -- YYYYMMDDHHmmSS
    sourcecommonname TEXT,
    documentidentifier TEXT,          -- Article URL
    v2themes TEXT,                    -- Semicolon-separated GKG themes
    v2tone TEXT,                      -- 6 comma-separated tone values
    v2persons TEXT,                   -- Named persons with offsets
    v2locations TEXT,                 -- Geographic locations with coordinates
    v2organizations TEXT,             -- Organizations with offsets
    quotations TEXT,                  -- Extracted direct quotations
    translationinfo TEXT              -- Source language (mostly NULL for English)
);

CREATE INDEX idx_gkg_cq_date ON gdelt.gkg_coercive_quotations(date);
CREATE INDEX idx_gkg_cq_source ON gdelt.gkg_coercive_quotations(sourcecommonname);
CREATE INDEX idx_gkg_cq_themes_gin ON gdelt.gkg_coercive_quotations USING gin(to_tsvector('simple', v2themes));
CREATE INDEX idx_gkg_cq_persons_gin ON gdelt.gkg_coercive_quotations USING gin(to_tsvector('simple', v2persons));
CREATE INDEX idx_gkg_cq_locs_gin ON gdelt.gkg_coercive_quotations USING gin(to_tsvector('simple', v2locations));
```

```bash
# Import both batches:
\COPY gdelt.gkg_coercive_quotations FROM 'gkg_coercive_quotations_20220101_20231130.csv' WITH (FORMAT CSV, HEADER TRUE);
\COPY gdelt.gkg_coercive_quotations FROM 'gkg_coercive_quotations_20231201_20260128.csv' WITH (FORMAT CSV, HEADER TRUE);
-- Total: 354,187 records
```

### GKG full table (for when WMD theme-based GKG data is downloaded)

```sql
CREATE TABLE gdelt.gkg_articles (
    gkgrecordid TEXT PRIMARY KEY,
    date BIGINT,                      -- YYYYMMDDHHmmSS
    sourcecollectionidentifier INTEGER,
    sourcecommonname TEXT,
    documentidentifier TEXT,          -- Article URL
    counts TEXT,
    v2counts TEXT,
    themes TEXT,
    v2themes TEXT,                    -- Semicolon-separated theme list
    locations TEXT,
    v2locations TEXT,
    persons TEXT,
    v2persons TEXT,                   -- Semicolon-separated person list
    organizations TEXT,
    v2organizations TEXT,
    v2tone TEXT,                      -- 6 comma-separated tone values
    dates TEXT,
    gcam TEXT,
    sharingimage TEXT,
    relatedimages TEXT,
    socialimageembeds TEXT,
    socialvideoembeds TEXT,
    quotations TEXT,                  -- Extracted direct quotes
    allnames TEXT,
    amounts TEXT,
    translationinfo TEXT,
    extras TEXT
);

CREATE INDEX idx_gkg_date ON gdelt.gkg_articles(date);
CREATE INDEX idx_gkg_source ON gdelt.gkg_articles(sourcecommonname);
-- Full-text indexes on themes and persons for efficient filtering:
CREATE INDEX idx_gkg_themes_gin ON gdelt.gkg_articles USING gin(to_tsvector('simple', v2themes));
CREATE INDEX idx_gkg_persons_gin ON gdelt.gkg_articles USING gin(to_tsvector('simple', v2persons));
```
