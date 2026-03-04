# Visualization 17: VARX Variable Correlation Heatmap

## Descriptive Summary

**What this visualization shows:**

Pearson correlation matrix for all weekly VARX variables extracted from the GKG coercive discourse data.

**Variables:**
- **Volume (All):** Total weekly article count
- **Volume (Russia):** Russia-relevant article count
- **Tone (Mean):** Average V2Tone score (negative = hostile)
- **Negativity:** Average negative tone component
- **Nuclear:** Articles with nuclear quotes
- **Red Line:** Articles with red line quotes
- **Threat:** Articles with threat quotes
- **Escalation:** Articles with escalation quotes
- **Russia %:** Share of Russia-relevant articles

**Color scale:**
- **Blue:** Strong positive correlation (+1)
- **White:** No correlation (0)
- **Red:** Strong negative correlation (-1)

---

## Interpretive Analysis

**What this means for the research question:**

### 1. The Volume-Content Correlation Structure

**High correlations (r > 0.7):**
- Volume (All) ↔ Escalation (0.94): Escalation language dominates discourse
- Volume (All) ↔ Threat (0.73): Threats drive coverage
- Volume (Russia) ↔ Nuclear (0.70): Russia coverage tied to nuclear topics

**Interpretation:** Media volume is structurally tied to escalation/threat framing. More coverage = more escalation language, not just proportionally but because escalation *is* what gets covered.

### 2. The Russia-Nuclear Nexus

**Volume (Russia) correlations:**
- With Nuclear: +0.70 (strong)
- With Red Line: +0.63 (moderate-strong)
- With Escalation: +0.62 (moderate-strong)

**Finding:** Russia-relevant coverage is disproportionately nuclear-focused compared to general coercive discourse. When media covers Russia in a coercive context, they invoke nuclear themes.

### 3. The Tone-Volume Relationship

**Tone (Mean) correlations:**
- With Volume (All): -0.36 (moderate negative)
- With Volume (Russia): -0.48 (moderate-strong negative)
- With Russia %: -0.55 (strong negative)

**Interpretation:** More coverage = more negative tone. Specifically:
- Higher Russia share → more negative framing
- This could be: (a) Russia coverage is inherently negative, or (b) negative events drive both coverage and tone

### 4. Red Line vs. Nuclear Patterns

**Red Line correlations:**
- With Nuclear: +0.67 (strong)
- With Russia %: +0.61 (strong)
- With Threat: +0.33 (weak-moderate)

**Nuclear correlations:**
- With Red Line: +0.67 (strong)
- With Russia %: +0.79 (very strong)
- With Escalation: +0.51 (moderate)

**Insight:** "Red line" and "nuclear" co-occur frequently — they're part of the same discursive package. But nuclear is more tightly bound to Russia-specific coverage than general threat/escalation language.

### 5. What's Independent?

**Weakly correlated variables (candidates for independent VARX inputs):**
- Threat ↔ Russia % (0.06): "Threat" language isn't Russia-specific
- Negativity ↔ Red Line (0.19): Red line invocations don't drive negativity
- Tone ↔ Nuclear (0.12): Nuclear language doesn't independently worsen tone

**Implication for VARX:** These weak correlations suggest that some variables capture independent information. A VARX model should include both Russia-specific (Nuclear, Red Line) and general (Threat, Escalation) indicators.

### 6. The Negativity-Tone Relationship

**Negativity correlations:**
- With Tone (Mean): +0.78 (strong positive — more negative tone = higher negativity score)
- With Russia %: -0.20 (weak negative)

**Note:** Tone is measured as overall sentiment (can be positive), while Negativity is the negative component only. Their high correlation confirms media coverage is predominantly negative.

### 7. Implications for Causal Analysis

The correlation structure suggests potential causal pathways to test:

**Hypothesis 1:** RRLS → Nuclear quotes → Volume (Russia) → Tone (worsening)
- Supported by: Nuclear ↔ Russia Volume (0.70), Russia Volume ↔ Tone (-0.48)

**Hypothesis 2:** Events → Escalation → Volume (All) → Russia % (dilution)
- Supported by: Escalation ↔ Volume All (0.94), Volume All ↔ Russia % (-0.35)

**Hypothesis 3:** Red Line language operates semi-independently
- Supported by: Red Line ↔ Threat (0.33, weak), Red Line ↔ Negativity (0.19, weak)

---

## Key Takeaway

**The correlation structure reveals that nuclear and red line language are tightly bound to Russia-specific coverage, while escalation/threat are more general.** Tone worsens with increased Russia coverage. For VARX modeling, this suggests treating Russia-specific and general coercive indicators as separate causal channels. The weak correlations between some variables confirm they capture independent information about discourse dynamics.
