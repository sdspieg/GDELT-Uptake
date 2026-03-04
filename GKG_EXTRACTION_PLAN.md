# GKG Extraction Plan — What We Can Still Squeeze Out

## The Budget Reality

| Resource | Available | Notes |
|----------|-----------|-------|
| **sdspieg@gmail.com** | ~16 GB remaining (Jan 2026) | Resets to 1 TB on Feb 1. **Q1 partial done (438 GB used Jan 28).** |
| **sdspiegus@gmail.com** | 1 TB/month | Second account. Needs GCP project + BigQuery API enabled. |
| **Each additional Gmail account** | 1 TB/month | Free. Create a GCP project, enable BigQuery API, done |
| **GDELT DOC API** | Unlimited | Free. Rate limit ~1 req/sec. No BigQuery cost |
| **GDELT raw file download** | Unlimited | Free. ~140K files, ~2.8 TB total — impractical for full GKG |

The problem: the GKG `Quotations` column alone costs **~245 GB** to scan across the full 49-month range, and any query that touches `V2Themes` adds another **~392 GB**. A single "SELECT useful stuff WHERE Quotations LIKE X AND Themes LIKE Y" scan costs ~1.5--1.8 TB. No single free account can do it in one shot.

The solution: **time-partition batching** + **column minimization** + **the free DOC API for everything that doesn't need record-level data**.

---

## TIER 0: FREE — No BigQuery Needed (DOC API)

The GDELT DOC 2.0 API provides daily article counts, tone time series, and article URL samples — all without touching BigQuery. This should be our **first extraction** because it costs nothing and answers several key research questions.

### What to extract:

| Query | URL pattern | What it gives us |
|-------|-------------|------------------|
| "red line" + russia (daily counts) | `mode=timelinevolraw` | Daily red-line discourse volume — comparable to viz 10 but at daily resolution |
| "nuclear threat" + russia (daily counts) | `mode=timelinevolraw` | Daily NTS media echo — directly comparable to code-139 GDELT events |
| "escalation" + russia (daily counts) | `mode=timelinevolraw` | Escalation discourse independent of "red line" framing |
| "red line" + russia (tone) | `mode=timelinetone` | Daily average tone of red-line articles |
| "nuclear threat" + russia (tone) | `mode=timelinetone` | Daily average tone of NTS articles |
| All above x `sourcelang:russian` | Same + lang filter | **Russian-language** media coverage (Reflexive Control channel) |
| All above x `sourcelang:german` | Same + lang filter | German media (largest EU economy, key aid debate) |
| All above x `sourcelang:chinese` | Same + lang filter | Chinese media (non-aligned framing) |
| All above x `sourcecountry:US` | Same + country filter | US-only coverage |
| All above x `sourcecountry:UK` | Same + country filter | UK-only coverage |

**Analytical value:**
- **Cross-language comparison** of red line / nuclear threat discourse — the paper currently has no data on how Russian-language media frames Putin's threats vs. English-language media. This is central to Reflexive Control.
- **Daily resolution** allows alignment with specific RRLS dates (329 statements with known dates) and specific GDELT Events peaks.
- **Tone by language** tests whether Russian media frames threats more or less negatively than Western media.

**Constraints:** 3-month maximum window per query. Need ~17 queries per series (49 months / 3). For 5 series x 5 languages x 17 windows = ~425 queries. At 1/sec = ~7 minutes. Trivial.

### Implementation:

```python
# Pseudocode — loop over 3-month windows
import requests, time
base = "https://api.gdeltproject.org/api/v2/doc/doc"
queries = [
    ('"red line" russia', 'redline_russia'),
    ('"nuclear threat" russia', 'nuclear_threat_russia'),
    ('"escalation" russia', 'escalation_russia'),
]
langs = ['', 'sourcelang:russian', 'sourcelang:german', 'sourcelang:chinese']
# ... iterate, sleep(1.1), save CSVs
```

---

## TIER 1: Cheap BigQuery — On Current Account (~454 GB)

### Q1: "nuclear threat" + "deterrence" + "ultimatum" quotation articles (combined query)

Instead of running Q1/Q2/Q5 separately (same column cost each time), run a SINGLE query with an OR filter that captures multiple discourse types in one scan:

```sql
SELECT
  GKGRECORDID, DATE, SourceCommonName, DocumentIdentifier,
  V2Themes, V2Tone, V2Persons, V2Locations, V2Organizations,
  Quotations, TranslationInfo
FROM `gdelt-bq.gdeltv2.gkg_partitioned`
WHERE _PARTITIONTIME >= '2022-01-01' AND _PARTITIONTIME < '2023-01-01'
  AND REGEXP_CONTAINS(Quotations,
    r'(?i)(nuclear\s+threat|nuclear\s+strike|nuclear\s+war|red\s+line|ultimatum|deter[a-z]*|escala[a-z]*)')
```

**Cost estimate:** ~456 GB for 12 months (Quotations=60GB + V2Themes=196 + other selected cols). Fits in the 454 GB remaining.

**What this gives us that we don't have:**
- **V2Themes** — what GKG themes co-occur with red line / nuclear discourse (WMD? SOVEREIGNTY? SANCTIONS?)
- **V2Locations** — geographic focus of each article
- **V2Organizations** — which institutions (NATO, Kremlin, Pentagon) are mentioned
- **TranslationInfo** — source language (critical for cross-national analysis)
- **All quotation types in one shot** — not just "red line" but also "nuclear threat," "escalation," "deterrence," "ultimatum"

**What we DON'T get:** Only 12 months (2022). Need to do 2023--2026 in subsequent months or on another account.

### Q2: Lightweight theme-only counts (if budget allows)

If Q1 comes in under estimate, use the remaining ~100 GB for:

```sql
SELECT
  EXTRACT(YEAR FROM _PARTITIONTIME) AS year,
  EXTRACT(MONTH FROM _PARTITIONTIME) AS month,
  COUNTIF(REGEXP_CONTAINS(V2Themes, r'WMD')) AS wmd_articles,
  COUNTIF(REGEXP_CONTAINS(V2Themes, r'ACT_HARMTHREATEN')) AS threat_articles,
  COUNTIF(REGEXP_CONTAINS(V2Themes, r'UNREST_ULTIMATUM')) AS ultimatum_articles,
  COUNTIF(REGEXP_CONTAINS(V2Themes, r'ACT_FORCEPOSTURE')) AS forceposture_articles,
  COUNTIF(REGEXP_CONTAINS(V2Themes, r'TAX_WORLDLANGUAGES_RUSSIA')) AS russia_tagged_articles
FROM `gdelt-bq.gdeltv2.gkg_partitioned`
WHERE _PARTITIONTIME >= '2022-01-01'
GROUP BY 1, 2
ORDER BY 1, 2
```

**Cost:** ~392 GB (only scans V2Themes). Doesn't fit alongside Q1 on current quota, but would fit on the Feb reset.

**What this gives us:** Monthly article counts for every analytically relevant GKG theme, across the entire 49-month range. No record-level data — just aggregate time series that can be overlaid on RRLS/NTS dates.

---

## TIER 2: sdspiegus@gmail.com (1 TB)

### Q3: The Big One — WMD + Russia Theme-Based Full Records

This is the **576K-record dataset** documented in GDELT.md. It's the key dataset for the paper's expanded analysis: every GKG article tagged with WMD themes that also mentions Russia.

**Strategy:** Batch by year to stay within 1 TB:

```sql
-- Batch 1: 2022 (12 months, ~408 GB)
SELECT
  GKGRECORDID, DATE, SourceCommonName, DocumentIdentifier,
  V2Themes, V2Tone, V2Persons, V2Locations, V2Organizations,
  Quotations, TranslationInfo
FROM `gdelt-bq.gdeltv2.gkg_partitioned`
WHERE _PARTITIONTIME >= '2022-01-01' AND _PARTITIONTIME < '2023-01-01'
  AND REGEXP_CONTAINS(V2Themes,
    r'WMD|WB_2505|WB_2469|ACT_HARMTHREATEN|UNREST_ULTIMATUM|ACT_FORCEPOSTURE|RETALIATE')
  AND (
    REGEXP_CONTAINS(V2Persons, r'(?i)putin|lavrov|medvedev|peskov|shoigu|patrushev|gerasimov')
    OR REGEXP_CONTAINS(V2Locations, r'(?i)russia|moscow|kremlin|ukraine|kyiv')
    OR REGEXP_CONTAINS(V2Themes, r'TAX_WORLDLANGUAGES_RUSSIA|TAX_ETHNICITY_RUSSIAN')
  )

-- Batch 2: 2023 (12 months, ~408 GB)
-- Same query, different _PARTITIONTIME range
-- → Total for 2 years: ~816 GB → FITS in 1 TB
```

**What this gives us:** The full media-ecosystem dataset for WMD/threat discourse about Russia. 576K articles with themes, tone, persons, locations, organizations, quotations, and source language. This is the dataset that enables:
- **Media echo measurement** — how do RRLS propagate?
- **Cross-national framing** — Russian vs Western vs Global South coverage
- **Temporal alignment** — overlay with 329 RRLS dates
- **Organization analysis** — NATO, Kremlin, Pentagon, IAEA co-occurrence
- **Quotation mining** — extract actual quotes about nuclear threats

**Remaining on Account 2:** ~184 GB (enough for 2024 partial, or save for next month).

### Q4: Remaining years on Account 2's next month, or Account 3

2024--2026 (25 months) at ~408 GB/12 months = ~850 GB. Fits in one month on the same account.

---

## TIER 3: Third Gmail Account or sdspiegus Overflow (Nice-to-Have)

### Q5: EventMentions Join — Per-Article Source Data for Threat Events

The GDELT `eventmentions` table (~800 GB) links events to individual article mentions. Joining with our 260K threat events gives per-article metadata: source name, confidence score, document tone, and timestamp.

```sql
SELECT e.GLOBALEVENTID, e.SQLDATE, e.EventCode, e.Actor2CountryCode,
       m.MentionTimeDate, m.MentionSourceName, m.MentionIdentifier,
       m.Confidence, m.MentionDocTone
FROM `gdelt-bq.gdeltv2.events` e
JOIN `gdelt-bq.gdeltv2.eventmentions` m
  ON e.GLOBALEVENTID = m.GLOBALEVENTID
WHERE e.Actor1CountryCode = 'RUS'
  AND e.EventRootCode = '13'
  AND e.Year >= 2022
```

**Cost:** ~1 TB (eventmentions is huge). Needs a dedicated account.

**What this gives us:** Source-level detail for every Russian threat event. Which outlets report which threats? Do Russian-language sources report the same events as English-language sources? This is the "media propagation" dataset.

### Q6: ACT_HARMTHREATEN Theme Without Russia Filter

A broader capture of ALL threat-language articles (not just Russia-related), enabling a comparison: what share of global threat discourse is about Russia?

---

## RECOMMENDED SEQUENCE

| Step | What | Where | Cost | Gets us |
|------|------|-------|------|---------|
| ✅ **DONE (Jan 28)** | **Q1 Batch 1: Combined quotation query (Jan 2022 – Nov 2023)** | sdspieg@gmail.com | **~438 GB** | **161,320 enriched coercive discourse records (11 cols)** |
| ✅ **DONE (Jan 28)** | **Q1 Batch 2: Combined quotation query (Dec 2023 – Jan 2026)** | sdspiegus@gmail.com | **~484 GB** | **192,867 enriched coercive discourse records (11 cols)** |
| **Next** | Q2: Theme-only monthly counts (full range) | sdspiegus@gmail.com (remaining ~516 GB) or sdspieg (Feb reset) | ~392 GB | Aggregate theme time series, 49 months |
| **Feb** | Q3: WMD+Russia full records (2022--2023) | sdspieg@gmail.com (reset) | ~816 GB | 576K articles (first 2 years) |
| **Feb/Mar** | Q3 continued (2024--2026) | sdspiegus@gmail.com (reset) | ~850 GB | Remaining WMD+Russia records |
| **Optional** | DOC API time series extraction | Local Python script | **0 GB** | Daily discourse volume + tone in 5+ languages |
| **Optional** | Q5: EventMentions join | 3rd Gmail account | ~1 TB | Per-article source data for all threat events |

**Accounts: sdspieg@gmail.com (primary) + sdspiegus@gmail.com (secondary). Total calendar time: 1--2 months remaining. Total cost: $0.**

**Status (Jan 28, 2026):**
- ✅ **Q1 COMPLETE:** Coercive discourse quotations fully extracted (354,187 records, 49 months, ~1.8 GB)
- sdspieg@gmail.com: ~16 GB remaining (resets Feb 1 → 1 TB)
- sdspiegus@gmail.com: ~516 GB remaining (resets Feb 1 → 1 TB)

---

## What Each Extraction Adds to the Paper

| Dataset | Paper Section | Research Question |
|---------|---------------|-------------------|
| DOC API time series | Media echo analysis | Do RRLS issuance dates correlate with media discourse spikes? |
| DOC API cross-language | Reflexive Control test | Does Russian-language media frame threats differently than English? |
| Enriched quotation records | Discourse analysis | What do people *actually say* when they invoke "red line" or "nuclear threat"? |
| WMD+Russia full GKG | Core empirical expansion | How does Russia's nuclear threat signaling propagate through the global media ecosystem? |
| Theme-only counts | Time series overlay | Which GKG themes co-move with RRLS issuance? |
| EventMentions | Source analysis | Which outlets amplify Russian threats most? |
