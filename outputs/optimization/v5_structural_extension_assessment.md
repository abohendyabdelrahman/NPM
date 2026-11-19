# V5 Structural-Extension Assessment
## AOM Problematic Daily Trend Checker

**Date:** 2026-11-19
**Question:** Can structural rule extensions push accuracy past 98% (>176/180)?
**Answer (evidence-backed):** No — not *generalizably*. The honest ceiling for
monotone threshold rules on per-curve metrics is **173/180 = 96.1%**. Reaching
≥98% is possible only with **per-curve exception overrides (memorization)** or by
**relabeling near-duplicate curves**. Both are documented below.

---

## 1. Where we stand: the v4 result is genuine

The jointly-optimized v4 ladder (order **A→B→C→E→F→G→H→I→J→K→D→L**, 21
parameters optimized with full order freedom) reaches:

- **Fit: 173 / 180 = 96.11%** (confusion 83 TP / 5 FP / 2 FN / 90 TN)
- **5-fold CV: 0.882 ± 0.062**
- Precision 0.947, Recall 0.978.

Note the optimizer independently converged on the **identity order** the user
proposed (D just before default L). This is the honest, generalizable score.

The **7 residual errors** are the entire gap to 98%:

| File | Truth | v4 fired | z | P% | LDD | L2DD | NSDD | NS2DD |
|---|---|---|---|---|---|---|---|---|
| Normal10 | Normal | E | 1.81 | 96.6 | 7.8 | 37.3 | 21 | 6 |
| Traffic_Normal14 | Normal | C | 2.97 | 98.1 | 84.1 | 61.0 | 0 | 0 |
| Traffic_Normal7 | Normal | E | 1.53 | 96.2 | 31.8 | 42.3 | 2 | 1 |
| throughput_Normal_13 | Normal | E | 1.63 | 98.3 | 39.6 | 34.3 | 4 | 9 |
| throughput_Normal_8 | Normal | E | 1.61 | 94.9 | 39.1 | 25.2 | 6 | 14 |
| Problematic_V | Problematic | L | 0.84 | 76.7 | 41.6 | 41.0 | 3 | 5 |
| Traffic_Problematic_Z | Problematic | F | 1.31 | 92.7 | −0.9 | 52.6 | 25 | 1 |

## 2. Why they are hard: each residual is a label-ambiguous near-twin

In normalized metric space every residual sits almost on top of a
**correctly-classified curve of the opposite label**:

| Residual | Nearest opposite curve | distance |
|---|---|---|
| Normal10 | throughput_Problematic_W | 0.07 |
| Traffic_Normal7 | Problematic_R | 0.12 |
| throughput_Normal_8 | Traffic_Problematic_7 | 0.18 |
| Traffic_Problematic_Z | Normal68 | 0.31 |
| throughput_Normal_13 | throughput_Problematic_R | 0.36 |
| Traffic_Normal14 | Problematic19 | 0.36 |
| Problematic_V | Normal67 | 0.99 |

If a rule correctly classifies the twin, it misclassifies the residual (and vice
versa). These pairs are genuinely ambiguous at the metric level — the label
difference is essentially a human judgment call on the shape, not a metric gap.

## 3. Extension 1 — per-curve guard boxes (v5a): 180/180 but memorization

Inserting 7 guard boxes derived from each residual's clean box yields a perfect
**180/180** on training. **This is not real.** Each guard box captures **exactly
one curve** (its own target) and sits a razor-thin margin from the nearest
excluded opposite curve:

| Guard | Target | margin to nearest opposite (% FR) |
|---|---|---|
| G1 | Traffic_Normal14 | **0.13%** |
| G2 | Normal10 | 6.1% |
| G3 | Traffic_Normal7 | 0.64% |
| G4 | throughput_Normal_13 | **0.06%** |
| G5 | throughput_Normal_8 | 16.7% |
| G6 | Problematic_V | 6.5% |
| G7 | Traffic_Problematic_Z | 12.0% |

A rule that fires for one and only one curve, with a 0.06%–17% buffer, is a
**fingerprint**. The "CV = 1.0" reported for v5a is circular — the boxes were
built from the exact curves in every fold. **The v5a 180/180 is memorization, not
a 98% score.**

## 4. Extension 2 — 13 new curve-shape features: no univariate separator

Features extracted from the raw per-day values (last-3/5-day slope, tail
curvature, tail volatility, position of LDV within clean range, direction-reversal
count, volatility ratio, days-since-max/min, diff skew/kurtosis). **All 13 fall
inside the opposite-label range for every residual** → no single new feature
separates any residual.

## 5. Extension 3 — combined 19-D maximum-margin separability: dimensionality artifact

Searching all axis-aligned boxes over the 19 features (6 metrics + 13 shape) and
maximizing the minimum relative margin to opposite curves. Every residual returns
a "robust" margin — **but the catch is decisive:**

- **No residual is separable by ANY single feature** (r≤1: infeasible for all 7).
- Margin grows **monotonically** with the number of features allowed:

| Residual | r≤1 | r≤2 | r≤3 | r≤4 |
|---|---|---|---|---|
| Normal10 | — | 0.18 | 0.84 | 0.85 |
| Traffic_Normal14 | — | 0.24 | 0.57 | 0.58 |
| Traffic_Normal7 | — | 0.15 | 0.73 | 1.22 |
| throughput_Normal_13 | — | 0.28 | 0.95 | 1.06 |
| throughput_Normal_8 | — | 0.90 | 1.29 | 1.43 |
| Problematic_V | — | 0.29 | 0.73 | 1.05 |
| Traffic_Problematic_Z | — | 0.26 | 0.76 | 0.88 |

- **Every best box captures exactly 1 curve** (0 same-label others, 0 opposite).

Margin rising with dimensionality while each box isolates a single point is the
**textbook signature of overfitting an isolated point**, not a structural insight.
In 19 dimensions you can always fence off any one point with 4 chosen features.
A real structural rule separating 180 curves would show up at 1–2 interpretable
features with a *moderate* margin and would capture a *group* of same-label
curves — none of that is present.

---

## 6. Conclusion

Structural extensions do **not** yield a genuine, generalizable rule set above
96.1%. The physical reason is that the 7 residuals are near-twin, label-ambiguous
curves; no monotone combination of the per-curve metrics (original or newly
extracted shape features) separates them with a boundary that would hold on
unseen data.

**Options to exceed 96.1% (in order of honesty):**

1. **Accept 173/180 = 96.1%** — the genuine, generalizable production score with
   the v4 ladder. Recommended as the baseline.
2. **Documented per-curve exception overrides (→ 180/180)** — add an explicit,
   clearly-labelled exception list (the 7 guard boxes above) that forces the
   correct verdict for these specific known curves. This is legitimate in
   production *only if labelled as memorization* (an operator exception table),
   NOT sold as a generalizable 98%.
3. **Relabel near-duplicate pairs** — the 7 twins (Normal10↔throughput_Problematic_W,
   etc.) are label-ambiguous. If the labelling policy is refined so a near-twin
   pair gets a consistent label, the metric gap closes and 98%+ becomes reachable
   by the ordinary ladder. This is a **data** decision that only the user can make.

**No combination of threshold rules on these curves gives a real ≥98%.**
