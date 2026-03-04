# 2026 Research Expansion: Goals and Rationale

**Document Purpose:** Explains what the January 2026 data expansion is trying to accomplish and why.

---

## The Original Paper (2024)

**Title:** "Lost in Translation: Decoding Putin's Red Lines"

**Authors:** Stephan De Spiegeleire (HCSS) and Adam Stulberg (GA Tech)

**Core dataset:** 329 Russian Red Line Statements (RRLS) and 58 Nuclear Threat Statements (NTS) extracted from 2,583 Kremlin speeches (2000-2024).

**Key finding:** Putin's nuclear signaling follows **"Reflexive Control"** — deliberate ambiguity and inconsistency designed to manipulate adversary perceptions. Red lines are "consistently inconsistent."

**Original analytical approach:** VARX time series analysis with ACLED conflict events, POLECAT diplomatic sentiment, and US DoD weapons assistance data.

---

## Why Expand? The Limitations of the Original Analysis

### Problem 1: Limited Russian Source Coverage
The original 329 RRLS came **only from Kremlin speeches** — Putin's public statements on kremlin.ru. This misses:
- State Duma debates (parliamentary rhetoric)
- Federation Council debates (upper house)
- Ministry websites (MFA, MOD)
- Official Telegram channels (real-time messaging)

### Problem 2: Missing Media Discourse Data
The original VARX used:
- ACLED (conflict events) — measures what happens on the ground
- POLECAT (diplomatic sentiment) — measures state-to-state relations
- US DoD (weapons) — measures Western material support

**Missing:** How does global **media discourse** respond to Russian signaling? The original paper couldn't measure:
- Media volume (how much coverage do RRLS generate?)
- Media tone (does coverage become more negative after threats?)
- Nuclear discourse frequency (do nuclear quotes spike after NTS?)
- Framing patterns (escalation vs. deterrence vs. red line language)

### Problem 3: Causality Questions Unanswered
The original paper characterized Russian signaling patterns but couldn't rigorously test:
1. **What TRIGGERS RRLS?** (Are they reactive to Western actions or proactive?)
2. **What do RRLS TRIGGER?** (Do they affect Western behavior or media framing?)

---

## The 2026 Expansion: Two Axes

### Axis A: Expand Russian Official Source Coverage

| Source | Status | Expected Additions |
|--------|--------|-------------------|
| Kremlin speeches | ✅ Done | 329 RRLS (baseline) |
| State Duma debates | 🔄 Planned | TBD parliamentary RRLS |
| Federation Council | 🔄 Planned | TBD upper house RRLS |
| Ministry websites | 🔄 Planned | MFA/MOD statements |
| Official Telegram | 🔄 Planned | Real-time messaging |

**Goal:** Multi-institutional view of Russian signaling — not just Putin, but the full apparatus.

### Axis B: Add GDELT Media Discourse Data

| Dataset | Records | What It Measures |
|---------|---------|------------------|
| GDELT Events (RUS→THREATEN) | 291,869 | Machine-coded Russian threat behavior |
| **GKG Coercive Discourse** | **354,187** | Media articles with nuclear/deterrence/escalation quotations |
| GKG "Red Line" Only | 8,618 | Explicit "red line" phrase usage |

**Goal:** Measure media response to Russian signaling with weekly time series variables.

---

## The Core Research Questions

### Question 1: What TRIGGERS Russian RRLS/NTS?

**Hypotheses to test:**
- H1a: Western weapons deliveries → increased RRLS frequency
- H1b: Battlefield setbacks (ACLED) → escalated rhetoric
- H1c: Media discourse volume → reactive RRLS (attention-seeking)
- H1d: RRLS timing is strategic (precedes planned actions, not reactive)

**Data needed:**
- RRLS dates (329 statements with timestamps)
- US DoD weapons delivery dates
- ACLED event counts
- GKG media volume (weekly)

### Question 2: What Do RRLS/NTS TRIGGER?

**Hypotheses to test:**
- H2a: RRLS → increased media volume (attention spike)
- H2b: NTS → nuclear discourse spike (specific language amplification)
- H2c: RRLS → worsened media tone (more negative coverage)
- H2d: RRLS → reduced Western support (deterrence success)
- H2e: RRLS → increased Western support (backfire effect)

**Data needed:**
- RRLS/NTS dates as treatment variables
- GKG weekly variables: volume, tone, nuclear quotes, Russia share
- US DoD weapons assistance (for H2d/H2e)

### Question 3: Is Russian Signaling Strategic or Reactive?

**If Reflexive Control (strategic):**
- RRLS should be proactive (precede, not follow, Western actions)
- Variance pattern should show calculated ambiguity
- Different statement types (RRLS vs NTS) should serve different purposes
- Media should internalize frames and amplify autonomously

**If Reactive:**
- RRLS should follow Western actions (response to provocation)
- Patterns should correlate with external events
- Signaling intensity should match threat severity

---

## What the GDELT Data Adds

### 354K Coercive Discourse Records (GKG)

**Query pattern:**
```sql
WHERE Quotations LIKE '%nuclear threat%' OR '%nuclear strike%' OR '%nuclear war%'
   OR '%red line%' OR '%ultimatum%' OR '%deter%' OR '%escala%'
```

**What this captures:**
- Articles where journalists quote sources using coercive language
- Global media (not just Western — includes Global South)
- 49 months of coverage (Jan 2022 – Jan 2026)

**Variables extracted (weekly):**
| Variable | Description |
|----------|-------------|
| media_volume_all | Total coercive discourse articles |
| media_volume_russia | Russia-relevant subset |
| russia_share | % of discourse about Russia |
| media_tone_mean | Average sentiment (V2Tone) |
| nuclear_quote_count | "Nuclear" in quotations |
| redline_quote_count | "Red line" in quotations |
| threat_quote_count | "Threat" in quotations |
| escalation_quote_count | "Escalation" in quotations |

### 291K GDELT Events (RUS→THREATEN)

**What this captures:**
- Machine-coded Russian threat actions
- CAMEO event taxonomy
- Goldstein conflict-cooperation scores
- Actor-target-action triplets

**Why it matters:**
- Distinguishes Russian *behavior* from Russian *rhetoric*
- Allows testing whether media discourse tracks behavior or operates independently

---

## Key Findings So Far (January 2026)

### From the Visualizations:

1. **Russia's share of coercive discourse declined from 77% (Feb 2022) to 22% (full period)**
   - Hamas attack (Oct 2023) permanently restructured attention landscape
   - RRLS now compete with Israel/Gaza, Iran, North Korea for bandwidth

2. **Nuclear discourse spikes have diminishing returns**
   - Feb 2022: 500+ nuclear quotes/week
   - Nov 2024 (Oreshnik): ~150/week
   - Suggests habituation to nuclear rhetoric

3. **Media tone is structurally negative and action-driven**
   - Never positive (range: -4.5 to -1.1)
   - Kinetic events (invasion, Kursk) drive tone more than rhetoric

4. **Three series, zero correlation**
   - GDELT events: peaked at invasion, then flat
   - Coercive discourse: grew independently, peaked on Hamas
   - "Red line" language: independent episodic lifecycle
   - **Media discourse has decoupled from Russian behavior**

### Net Assessment:

**"Putin's red line statements reach global discourse but don't control it."**

Evidence suggests Reflexive Control may be the *intent* but not the *outcome*:
- ✅ Signals achieve media salience (first objective)
- ❌ Signals don't reliably shift tone (failed perception manipulation)
- ❌ Signals have diminishing returns (habituation)
- ❌ Media generates autonomous threat narratives (self-sustaining, not Kremlin-driven)

---

## Remaining Work

### Immediate (Statistical)
1. **Granger causality tests:** RRLS → media variables
2. **Event study design:** 329 RRLS dates as treatment
3. **Local projections:** Impulse response functions

### Medium-term (Data Expansion)
1. Expand RRLS corpus to include Duma, Federation Council, ministries
2. Consider WMD+Russia theme extraction (~576K articles) if quotation-based data insufficient

### Long-term (Paper Integration)
1. Integrate GDELT findings into "Lost in Translation" paper
2. Develop theoretical implications for Reflexive Control effectiveness
3. Policy recommendations for Western response to Russian signaling

---

## Document Locations

| Document | Purpose |
|----------|---------|
| `OVERVIEW.md` | Project-wide overview (in Red lines root) |
| `GDELT.md` | GDELT data documentation |
| `Handover.md` | Session-by-session progress tracking |
| **This file** | 2026 expansion goals and rationale |
| `vizzes/00_big_picture_synthesis.md` | Visualization synthesis and conclusions |

---

*Last updated: January 29, 2026*
