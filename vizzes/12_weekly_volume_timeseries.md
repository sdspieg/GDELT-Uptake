# Visualization 12: Weekly Volume Time Series

## Descriptive Summary

**What this visualization shows:**

Weekly article counts for coercive discourse from the GKG dataset (2022-2026), showing total volume vs. Russia-relevant subset.

- **Blue area/line:** Total weekly articles matching coercive discourse patterns (nuclear, escalation, deterrence, red line, ultimatum keywords in quotations)
- **Orange area/line:** Russia-relevant subset (articles with Russia/Ukraine persons, locations, or themes)
- **Vertical dashed lines:** Key events

**Key statistics:**
- Total weeks: 212 (Dec 2021 – Jan 2026)
- Weekly range: 485 to 4,053 articles
- Russia-relevant range: 42 to 1,671 articles per week

**Major peaks:**
1. **Feb-Mar 2022:** Invasion period (2,000-2,200 articles/week, 77% Russia-relevant)
2. **Oct-Nov 2023:** Hamas attack (4,000+ articles/week, but only ~15% Russia-relevant)
3. **Aug-Sep 2024:** Kursk incursion spike

---

## Interpretive Analysis

**What this means for the research question:**

### 1. Attention as a Finite Resource

The visualization starkly illustrates that **global media attention to coercive discourse is zero-sum**:

- When Israel/Gaza dominates (Oct 2023), Russia's share collapses even though absolute volume for coercive language peaks
- Russia-relevant discourse is highest (absolute and percentage) immediately after major Russian actions (invasion, mobilization)
- This has implications for RRLS effectiveness: red line statements compete with other global crises for attention

### 2. What Triggers Media Volume?

Clear volume spikes correlate with:

| Trigger | Volume Response | Russia Share |
|---------|----------------|--------------|
| Russian invasion | +200% | 77% (highest) |
| Russian mobilization | +50% | ~60% |
| Hamas attack | +300% | 15% (lowest) |
| Kursk incursion | +40% | ~50% |
| Oreshnik missile | Moderate | ~40% |

**Pattern:** Russian kinetic actions drive Russia-relevant volume, but rhetorical escalation (RRLS alone) doesn't produce comparable spikes.

### 3. Decay Patterns

After each major event, discourse volume decays roughly exponentially:
- Post-invasion: ~6-8 weeks to return to baseline
- Post-mobilization: ~4 weeks decay
- Post-Hamas: Sustained elevated volume (different conflict)

This decay pattern matters for VARX modeling — effects have finite half-lives.

### 4. Implications for RRLS Timing

If Putin's RRLS are strategically timed to maximize impact:
- Optimal timing would be during high Russia-relevant volume periods (attention already focused)
- RRLS during low-attention periods (e.g., Oct-Nov 2023) may have minimal reach
- The clustering of RRLS in early 2022 may reflect this strategic awareness

### 5. 2024-2026 Stabilization

Volume has partially stabilized in 2024-2025:
- Less dramatic spikes than 2022
- Russia share hovering around 30-40%
- May indicate "normalization" of the conflict in media coverage
- RRLS may have diminishing returns as audiences become habituated

---

## Key Takeaway

**Media attention to Russian coercive signaling is event-driven and competitive.** Red line statements must compete with global events for coverage. The data suggests RRLS alone don't generate sustained media attention — kinetic actions do. This constrains the potential effectiveness of Reflexive Control through rhetoric.
