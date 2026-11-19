# AOM Problematic Daily Trend Checker -- Parameter Optimization Report (v3)

- Corpus: 180 curves (Normal 88 / Problematic 92), window = last 60 daily points
- Objective (user): fit the 180 labeled curves as accurately as possible.
- Changes vs v2 (user-approved, 2026-11-18):
  1. Corpus relabeled: Problematic_N.png -> Normal_N.png and
     throughput_Problematic_V.png -> throughput_Normal_V.png
     (now 88 Normal / 92 Problematic).
  2. Case D (pure percentile P >= PCT_C, V) MOVED to the position just
     before the default Case L: it is now a last-resort Problematic
     catch instead of an early override (user: "move case D to before
     the last case (Case L)").
  3. LDD_E (R) may now be negative (user: "R should be a negative value
     so that no mismatches happen").
  4. Z_B (E) range widened to 10 sigma (user: "E value should be larger").
  5. PCT_C (V) free plus a guided high-V campaign (user: "V should have
     a bigger value").
- Method: free sweep (8 seeds x 2M candidates + 14 x 80k refine each)
  and a guided sweep honoring E>=2, R<0, V>=85 (5 seeds), winner selected
  within 1 curve of the free optimum; final refine + coordinate polish;
  5-fold stratified CV sanity check (400k + 12 x 40k per fold.)
- Polarity: from the KPI dictionary by file-name family -- +1 iff name
  contains a higher=degradation family (this corpus: CDR only); -1 otherwise.
  **Assumption**: dictionary maps KPI->polarity, not curve->KPI.

## Fit results

| Metric | Value |
|---|---|
| Fit accuracy (180 curves) | **0.9556 (95.6%)** |
| Balanced accuracy | 0.9550 |
| Baseline (all Normal) | 0.4889 |
| Winner campaign | targeted (user-constrained) |

## Confusion matrix (fit)

| | Predicted Normal | Predicted Problematic |
|---|---|---|
| Actual Normal | 82 | 6 |
| Actual Problematic | 2 | 90 |

Precision (Problematic) = 0.938 (n=96)
Recall (Problematic)    = 0.978 (n=92)

## Case firing (per-curve first-match, fit; evaluation order A,B,C,E,F,G,H,I,J,K,D,L)

| Case | Verdict | Curves |
|---|---|---|
| A | Problematic | 1 |
| B | Normal | 14 |
| C | Problematic | 0 |
| E | Problematic | 55 |
| F | Normal | 25 |
| G | Normal | 14 |
| H | Problematic | 24 |
| I | Problematic | 0 |
| J | Problematic | 1 |
| K | Problematic | 0 |
| D | Problematic | 15 |
| L | Normal | 31 |

Never fired on this corpus (latent rules): C, I, K


## Optimized parameters

| Param (letter) | Value | Unit | Role |
|---|---|---|---|
| Z_B (E) | 8.11866 | sigma | Case C: LDV worse than mean by >= Z_B sigma -> Problematic |
| Z_D (T) | 1.73028 | sigma | Case E: z-condition when percentile is moderate |
| Z_F (L) | 1.3977 | sigma | Case G: cap on z for the recovery-to-normal rule |
| Z_H (N) | 3.17526 | sigma | Case I: z-condition on large last-day degradation |
| Z_J (D) | 5.168 | sigma | Case K: z-condition on sustained 2-day degradation |
| PCT_C (V) | 93.5961 | % | Case D (moved to just before default L): degradation-direction percentile -> Problematic (last-resort) |
| PCT_D (S) | 48.4282 | % | Case E: percentile floor (combined with Z_D) |
| LDD_E (R) | -1.13372 | % | Case F: last-day degradation <= this -> Normal (negative-allowed per user) |
| LDD_F (J) | -8.14178 | % | Case G: LDD >= this (recovery rule, with L2DD cap) -> Normal |
| L2DD_F (I) | 9.27097 | % | Case G: 2-day degradation <= this |
| LDD_G (X) | 21.9457 | % | Case H: LDD >= this with rare history |
| LDD_H (Z) | 70.3461 | % | Case I: LDD >= this (with z or percentile) |
| PCT_H (O) | 98.4566 | % | Case I: percentile floor (OR with Z_H) |
| LDD_I (M) | 1.32575 | % | Case J: LDD <= this (sustained 2-day collapse rule) |
| L2DD_I (K) | -11.4872 | % | Case J: L2DD >= this |
| NSDD_G (Y) | 2 | count | Case H: NSDD <= this (rare event) |
| NS2DD_I (A) | 7 | count | Case J: NS2DD <= this (rare event) |
| LDD_J (B) | 32.787 | % | Case K: LDD <= this |
| L2DD_J (C) | 67.6681 | % | Case K: L2DD >= this |
| NY (NY) | 18.5416 | % | Case A: LDD >= this while LDV better than mean |
| NX (NX) | 42 | count | Case A: NSDD <= this |

## Per-curve classification (detected case per trend)

Every trend with the first-matching case (evaluation order) it fired on:

| # | Folder | File | Label | Predicted | Case | z_deg | P_deg% | LDD% | L2DD% | NSDD | NS2DD |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Normal | ERAB_SR_Normal1.png | Normal | Normal | L | 1.42 | 85.7 | 63.81 | 40.75 | 3 | 8 |
| 2 | Normal | Normal1.png | Normal | Normal | L | 1.20 | 86.2 | 7.01 | 42.68 | 24 | 7 |
| 3 | Normal | Normal10.png | Normal | Problematic | E | 1.81 | 96.6 | 7.79 | 37.30 | 21 | 6 |
| 4 | Normal | Normal13.png | Normal | Normal | G | 0.02 | 45.8 | 19.93 | -6.99 | 10 | 30 |
| 5 | Normal | Normal16.png | Normal | Normal | F | 0.43 | 61.4 | -9.38 | -8.33 | 35 | 33 |
| 6 | Normal | Normal17.png | Normal | Normal | G | 0.03 | 52.5 | 57.07 | -5.87 | 0 | 31 |
| 7 | Normal | Normal18.png | Normal | Normal | L | 0.99 | 79.3 | 3.06 | 29.89 | 25 | 5 |
| 8 | Normal | Normal19.png | Normal | Normal | F | 0.74 | 74.6 | -14.68 | -15.90 | 38 | 39 |
| 9 | Normal | Normal20.png | Normal | Normal | L | 1.35 | 86.7 | -0.35 | 32.39 | 31 | 10 |
| 10 | Normal | Normal21.png | Normal | Normal | L | 1.08 | 79.7 | 55.19 | 83.49 | 3 | 1 |
| 11 | Normal | Normal22.png | Normal | Normal | L | 1.35 | 86.7 | -0.35 | 32.39 | 31 | 10 |
| 12 | Normal | Normal23.png | Normal | Normal | B | -0.15 | 50.0 | 6.57 | 46.01 | 15 | 0 |
| 13 | Normal | Normal24.png | Normal | Normal | L | 0.49 | 68.3 | 7.03 | 16.61 | 28 | 17 |
| 14 | Normal | Normal25.png | Normal | Normal | B | -0.96 | 12.1 | 5.75 | -42.53 | 23 | 52 |
| 15 | Normal | Normal28.png | Normal | Normal | F | 0.89 | 75.4 | -4.79 | -4.26 | 34 | 31 |
| 16 | Normal | Normal29.png | Normal | Normal | G | 0.28 | 61.7 | 0.54 | 6.43 | 28 | 18 |
| 17 | Normal | Normal3.png | Normal | Normal | L | 0.73 | 81.0 | 8.92 | 29.85 | 19 | 4 |
| 18 | Normal | Normal30.png | Normal | Normal | L | 1.06 | 80.0 | 2.72 | 38.91 | 23 | 4 |
| 19 | Normal | Normal31.png | Normal | Normal | L | 0.95 | 80.0 | 8.87 | 19.70 | 21 | 20 |
| 20 | Normal | Normal32.png | Normal | Normal | F | 0.31 | 40.0 | -4.96 | -0.00 | 37 | 25 |
| 21 | Normal | Normal34.png | Normal | Normal | B | -0.41 | 41.7 | 5.41 | 7.57 | 9 | 14 |
| 22 | Normal | Normal35.png | Normal | Normal | G | 0.10 | 47.5 | 4.40 | 6.04 | 20 | 23 |
| 23 | Normal | Normal36.png | Normal | Normal | B | -1.06 | 13.6 | -9.57 | 10.00 | 38 | 17 |
| 24 | Normal | Normal39.png | Normal | Normal | L | 0.58 | 69.6 | 32.04 | 61.16 | 12 | 3 |
| 25 | Normal | Normal4.png | Normal | Normal | B | -0.55 | 29.3 | -15.12 | -19.19 | 39 | 38 |
| 26 | Normal | Normal40.png | Normal | Normal | B | -0.12 | 42.4 | -0.29 | 23.48 | 25 | 2 |
| 27 | Normal | Normal42.png | Normal | Normal | L | 0.11 | 49.1 | 5.93 | 21.48 | 20 | 12 |
| 28 | Normal | Normal43.png | Normal | Normal | B | -1.25 | 10.2 | -10.53 | -18.95 | 41 | 46 |
| 29 | Normal | Normal45.png | Normal | Normal | G | 1.28 | 93.3 | 2.86 | 8.00 | 24 | 19 |
| 30 | Normal | Normal47.png | Normal | Normal | B | -0.35 | 33.3 | -29.94 | 18.64 | 55 | 6 |
| 31 | Normal | Normal48.png | Normal | Normal | F | 0.40 | 65.0 | -5.97 | 54.03 | 40 | 1 |
| 32 | Normal | Normal49.png | Normal | Normal | G | 1.01 | 85.0 | 37.36 | 2.51 | 3 | 23 |
| 33 | Normal | Normal51.png | Normal | Normal | F | 1.00 | 83.1 | -6.87 | 26.72 | 33 | 12 |
| 34 | Normal | Normal53.png | Normal | Normal | G | 1.02 | 79.7 | -0.00 | -4.79 | 26 | 33 |
| 35 | Normal | Normal54.png | Normal | Normal | B | -1.02 | 13.6 | -14.46 | -0.00 | 43 | 23 |
| 36 | Normal | Normal55.png | Normal | Normal | L | 1.71 | 93.1 | 1.64 | 31.69 | 26 | 7 |
| 37 | Normal | Normal56.png | Normal | Normal | F | 0.01 | 50.0 | -3.36 | 13.45 | 34 | 11 |
| 38 | Normal | Normal57.png | Normal | Normal | B | -0.28 | 37.3 | -25.70 | 6.07 | 45 | 18 |
| 39 | Normal | Normal58.png | Normal | Normal | G | 0.80 | 75.4 | 8.33 | -11.81 | 17 | 31 |
| 40 | Normal | Normal6.png | Normal | Normal | L | 1.64 | 93.2 | 1.72 | 89.65 | 30 | 1 |
| 41 | Normal | Normal61.png | Normal | Normal | F | 0.55 | 65.0 | -22.46 | 5.99 | 48 | 30 |
| 42 | Normal | Normal62.png | Normal | Normal | F | 1.28 | 86.7 | -2.59 | 16.38 | 32 | 16 |
| 43 | Normal | Normal63.png | Normal | Normal | F | 0.04 | 35.0 | -2.47 | -0.93 | 32 | 22 |
| 44 | Normal | Normal67.png | Normal | Normal | L | 0.87 | 71.2 | 20.21 | 20.47 | 4 | 4 |
| 45 | Normal | Normal68.png | Normal | Normal | L | 1.18 | 86.7 | 4.76 | 61.90 | 28 | 4 |
| 46 | Normal | Normal7.png | Normal | Normal | L | 0.84 | 75.9 | 8.94 | 20.62 | 20 | 12 |
| 47 | Normal | Normal8.png | Normal | Normal | G | 0.70 | 71.7 | 52.46 | 4.23 | 2 | 24 |
| 48 | Normal | Normal9.png | Normal | Normal | L | 0.94 | 81.7 | 6.79 | 27.55 | 21 | 11 |
| 49 | Normal | Normal_N.png | Normal | Normal | L | 1.60 | 93.3 | 1.37 | 16.44 | 28 | 14 |
| 50 | Normal | Traffic_Normal1.png | Normal | Normal | B | -0.51 | 27.8 | -29.17 | -54.76 | 44 | 43 |
| 51 | Normal | Traffic_Normal10.png | Normal | Normal | G | 0.80 | 75.0 | 2.46 | 4.11 | 24 | 24 |
| 52 | Normal | Traffic_Normal12.png | Normal | Normal | F | 1.51 | 91.5 | -39.41 | -2.35 | 55 | 33 |
| 53 | Normal | Traffic_Normal13.png | Normal | Normal | B | -0.26 | 39.0 | -18.80 | 12.82 | 41 | 20 |
| 54 | Normal | Traffic_Normal14.png | Normal | Problematic | E | 2.97 | 98.1 | 84.10 | 61.00 | 0 | 0 |
| 55 | Normal | Traffic_Normal16.png | Normal | Normal | F | 1.24 | 86.8 | -1.89 | 23.40 | 28 | 8 |
| 56 | Normal | Traffic_Normal17.png | Normal | Normal | G | 0.71 | 69.1 | 39.45 | -0.46 | 5 | 25 |
| 57 | Normal | Traffic_Normal18.png | Normal | Normal | F | 1.60 | 92.9 | -30.57 | 48.52 | 44 | 1 |
| 58 | Normal | Traffic_Normal2.png | Normal | Normal | F | 0.14 | 66.7 | -51.65 | -53.17 | 50 | 41 |
| 59 | Normal | Traffic_Normal20.png | Normal | Normal | L | 1.32 | 89.8 | 2.33 | 24.15 | 28 | 11 |
| 60 | Normal | Traffic_Normal21.png | Normal | Normal | F | 1.07 | 83.1 | -3.85 | 40.17 | 34 | 5 |
| 61 | Normal | Traffic_Normal23.png | Normal | Normal | F | 1.12 | 88.1 | -13.18 | -22.99 | 45 | 43 |
| 62 | Normal | Traffic_Normal24.png | Normal | Normal | B | -0.26 | 8.2 | -7.04 | -15.49 | 35 | 39 |
| 63 | Normal | Traffic_Normal25.png | Normal | Normal | L | 0.93 | 83.1 | 4.08 | 13.78 | 26 | 20 |
| 64 | Normal | Traffic_Normal26.png | Normal | Normal | F | 1.27 | 93.0 | -2.38 | -5.95 | 35 | 39 |
| 65 | Normal | Traffic_Normal27.png | Normal | Normal | L | 0.93 | 83.1 | 4.08 | 13.78 | 26 | 20 |
| 66 | Normal | Traffic_Normal29.png | Normal | Normal | L | 0.94 | 80.7 | 8.47 | 13.56 | 23 | 14 |
| 67 | Normal | Traffic_Normal3.png | Normal | Normal | F | 1.29 | 89.1 | -3.17 | -8.16 | 29 | 37 |
| 68 | Normal | Traffic_Normal30.png | Normal | Normal | L | 0.42 | 57.6 | 16.01 | 25.62 | 9 | 8 |
| 69 | Normal | Traffic_Normal31.png | Normal | Normal | L | 0.47 | 61.0 | 38.85 | 78.66 | 3 | 0 |
| 70 | Normal | Traffic_Normal32.png | Normal | Normal | L | 0.56 | 62.7 | 14.53 | 36.32 | 14 | 4 |
| 71 | Normal | Traffic_Normal33.png | Normal | Normal | L | 0.63 | 69.5 | 11.85 | 25.97 | 14 | 7 |
| 72 | Normal | Traffic_Normal36.png | Normal | Normal | L | 0.44 | 65.5 | 15.77 | 9.38 | 11 | 15 |
| 73 | Normal | Traffic_Normal4.png | Normal | Normal | F | 0.34 | 65.0 | -7.88 | -27.72 | 36 | 45 |
| 74 | Normal | Traffic_Normal5.png | Normal | Normal | G | 0.15 | 51.7 | 3.88 | 4.41 | 26 | 26 |
| 75 | Normal | Traffic_Normal6.png | Normal | Normal | F | 0.19 | 55.4 | -9.29 | 39.33 | 34 | 9 |
| 76 | Normal | Traffic_Normal7.png | Normal | Problematic | H | 1.53 | 96.2 | 31.82 | 42.25 | 2 | 1 |
| 77 | Normal | Traffic_Normal8.png | Normal | Normal | B | -0.67 | 23.7 | -30.41 | -38.37 | 51 | 54 |
| 78 | Normal | Traffic_Normal9.png | Normal | Normal | F | 0.77 | 73.7 | -19.54 | 25.67 | 40 | 10 |
| 79 | Normal | Traffic_Normal_A.png | Normal | Normal | F | 1.43 | 83.6 | -24.88 | -3.05 | 42 | 31 |
| 80 | Normal | throughput_Normal_13.png | Normal | Problematic | D | 1.63 | 98.3 | 39.62 | 34.30 | 4 | 9 |
| 81 | Normal | throughput_Normal_16.png | Normal | Normal | L | 1.14 | 87.7 | 5.81 | 13.55 | 23 | 18 |
| 82 | Normal | throughput_Normal_17.png | Normal | Problematic | E | 2.04 | 94.3 | -12.15 | 1.77 | 36 | 23 |
| 83 | Normal | throughput_Normal_2.png | Normal | Normal | G | 1.16 | 96.5 | 2.40 | 4.00 | 21 | 25 |
| 84 | Normal | throughput_Normal_4.png | Normal | Normal | F | 0.57 | 65.0 | -7.16 | -1.10 | 31 | 30 |
| 85 | Normal | throughput_Normal_5.png | Normal | Normal | F | 1.20 | 90.0 | -7.71 | -5.93 | 39 | 35 |
| 86 | Normal | throughput_Normal_6.png | Normal | Normal | F | 1.36 | 86.2 | -5.72 | -5.31 | 31 | 30 |
| 87 | Normal | throughput_Normal_8.png | Normal | Problematic | D | 1.61 | 94.9 | 39.07 | 25.17 | 6 | 14 |
| 88 | Normal | throughput_Normal_V.png | Normal | Normal | G | 0.99 | 71.2 | 7.20 | -0.00 | 18 | 25 |
| 89 | Problematic | CDR_Problemtic_A.png | Problematic | Problematic | E | 2.06 | 96.3 | 7.65 | -48.21 | 10 | 45 |
| 90 | Problematic | Problematic1.png | Problematic | Problematic | E | 2.50 | 98.1 | 48.06 | 32.17 | 1 | 2 |
| 91 | Problematic | Problematic10.png | Problematic | Problematic | E | 3.03 | 98.3 | 57.51 | 80.22 | 0 | 0 |
| 92 | Problematic | Problematic11.png | Problematic | Problematic | H | 1.27 | 80.0 | 40.29 | 79.14 | 2 | 0 |
| 93 | Problematic | Problematic12.png | Problematic | Problematic | E | 2.26 | 98.3 | 50.00 | 60.05 | 0 | 0 |
| 94 | Problematic | Problematic13.png | Problematic | Problematic | E | 2.72 | 98.3 | 20.76 | 47.85 | 6 | 3 |
| 95 | Problematic | Problematic14.png | Problematic | Problematic | E | 2.03 | 96.6 | 66.04 | 65.41 | 0 | 1 |
| 96 | Problematic | Problematic15.png | Problematic | Problematic | E | 2.69 | 98.3 | 40.23 | 25.00 | 4 | 9 |
| 97 | Problematic | Problematic16.png | Problematic | Problematic | E | 3.49 | 98.2 | 53.33 | 54.67 | 1 | 1 |
| 98 | Problematic | Problematic17.png | Problematic | Problematic | E | 2.34 | 98.3 | 100.00 | 53.94 | 0 | 1 |
| 99 | Problematic | Problematic18.png | Problematic | Problematic | E | 3.86 | 98.3 | 43.21 | 68.83 | 1 | 0 |
| 100 | Problematic | Problematic19.png | Problematic | Problematic | E | 2.50 | 98.3 | 93.19 | 53.05 | 0 | 1 |
| 101 | Problematic | Problematic2.png | Problematic | Problematic | H | 1.28 | 93.3 | 66.67 | 38.67 | 0 | 2 |
| 102 | Problematic | Problematic20.png | Problematic | Problematic | E | 3.56 | 98.3 | 50.00 | 75.21 | 0 | 0 |
| 103 | Problematic | Problematic21.png | Problematic | Problematic | E | 1.99 | 96.7 | 50.77 | 50.16 | 0 | 1 |
| 104 | Problematic | Problematic22.png | Problematic | Problematic | E | 3.17 | 98.2 | 42.20 | 51.38 | 4 | 2 |
| 105 | Problematic | Problematic23.png | Problematic | Problematic | E | 1.92 | 96.6 | -0.90 | 42.15 | 32 | 2 |
| 106 | Problematic | Problematic24.png | Problematic | Problematic | E | 2.35 | 98.3 | 49.55 | 18.92 | 1 | 11 |
| 107 | Problematic | Problematic25.png | Problematic | Problematic | D | 1.57 | 96.7 | 17.04 | 19.24 | 8 | 12 |
| 108 | Problematic | Problematic3.png | Problematic | Problematic | E | 3.71 | 98.2 | 85.16 | 85.16 | 0 | 0 |
| 109 | Problematic | Problematic5.png | Problematic | Problematic | E | 1.82 | 94.9 | -1.86 | 85.45 | 28 | 1 |
| 110 | Problematic | Problematic6.png | Problematic | Problematic | H | 1.51 | 88.3 | 64.75 | 41.78 | 0 | 5 |
| 111 | Problematic | Problematic8.png | Problematic | Problematic | E | 1.97 | 98.3 | 26.97 | 22.65 | 3 | 6 |
| 112 | Problematic | Problematic_A.png | Problematic | Problematic | H | 1.51 | 93.3 | 89.81 | 45.22 | 0 | 7 |
| 113 | Problematic | Problematic_B.png | Problematic | Problematic | H | 1.45 | 89.8 | 54.55 | 37.27 | 0 | 1 |
| 114 | Problematic | Problematic_C.png | Problematic | Problematic | H | 0.91 | 81.0 | 82.85 | 49.63 | 0 | 1 |
| 115 | Problematic | Problematic_G.png | Problematic | Problematic | H | 0.76 | 72.9 | 52.45 | 79.62 | 1 | 0 |
| 116 | Problematic | Problematic_H.png | Problematic | Problematic | H | 0.75 | 73.3 | 44.65 | 44.34 | 1 | 4 |
| 117 | Problematic | Problematic_M.png | Problematic | Problematic | E | 2.02 | 98.2 | 26.95 | 33.33 | 9 | 8 |
| 118 | Problematic | Problematic_O.png | Problematic | Problematic | E | 1.82 | 95.0 | -3.64 | 44.13 | 35 | 4 |
| 119 | Problematic | Problematic_Q.png | Problematic | Problematic | H | 0.44 | 66.7 | 38.90 | 20.82 | 1 | 9 |
| 120 | Problematic | Problematic_R.png | Problematic | Problematic | D | 1.52 | 95.0 | 42.25 | 42.61 | 3 | 2 |
| 121 | Problematic | Problematic_S.png | Problematic | Problematic | D | 1.42 | 96.7 | 22.03 | 26.44 | 4 | 5 |
| 122 | Problematic | Problematic_T.png | Problematic | Problematic | A | -0.32 | 33.3 | 39.52 | 24.82 | 0 | 3 |
| 123 | Problematic | Problematic_U.png | Problematic | Problematic | H | 0.74 | 73.3 | 44.61 | 34.59 | 2 | 3 |
| 124 | Problematic | Problematic_V.png | Problematic | Normal | L | 0.84 | 76.7 | 41.59 | 40.98 | 3 | 5 |
| 125 | Problematic | Problematic_X.png | Problematic | Normal | L | 1.09 | 91.7 | 27.49 | 33.33 | 3 | 3 |
| 126 | Problematic | Problematic_Y.png | Problematic | Problematic | H | 0.11 | 41.8 | 63.16 | 54.39 | 0 | 0 |
| 127 | Problematic | Problematic_Z.png | Problematic | Problematic | H | 0.71 | 63.8 | 47.75 | 45.67 | 0 | 1 |
| 128 | Problematic | RRC_Problematic_1.png | Problematic | Problematic | E | 3.90 | 96.1 | -12.79 | 54.16 | 44 | 1 |
| 129 | Problematic | RRC_Problematic_2.png | Problematic | Problematic | E | 2.13 | 94.6 | 28.99 | 38.43 | 4 | 6 |
| 130 | Problematic | Traffic_Problematic_1.png | Problematic | Problematic | E | 2.09 | 92.7 | -0.39 | -2.72 | 27 | 27 |
| 131 | Problematic | Traffic_Problematic_10.png | Problematic | Problematic | D | 1.72 | 98.3 | 20.71 | 4.63 | 11 | 24 |
| 132 | Problematic | Traffic_Problematic_11.png | Problematic | Problematic | E | 2.01 | 98.3 | 25.46 | 54.60 | 14 | 5 |
| 133 | Problematic | Traffic_Problematic_12.png | Problematic | Problematic | E | 2.33 | 98.3 | 19.85 | 0.50 | 16 | 27 |
| 134 | Problematic | Traffic_Problematic_13.png | Problematic | Problematic | E | 2.88 | 98.3 | 48.54 | 32.36 | 1 | 9 |
| 135 | Problematic | Traffic_Problematic_2.png | Problematic | Problematic | D | 1.71 | 98.3 | 25.04 | 21.81 | 9 | 14 |
| 136 | Problematic | Traffic_Problematic_3.png | Problematic | Problematic | D | 1.66 | 96.7 | 22.77 | 31.68 | 6 | 6 |
| 137 | Problematic | Traffic_Problematic_4.png | Problematic | Problematic | E | 2.75 | 98.2 | 21.49 | 20.06 | 10 | 8 |
| 138 | Problematic | Traffic_Problematic_5.png | Problematic | Problematic | E | 4.83 | 98.3 | 50.00 | 76.53 | 0 | 0 |
| 139 | Problematic | Traffic_Problematic_7.png | Problematic | Problematic | E | 1.80 | 98.2 | 35.43 | 16.59 | 5 | 16 |
| 140 | Problematic | Traffic_Problematic_8.png | Problematic | Problematic | D | 1.61 | 98.2 | 6.37 | 31.57 | 23 | 10 |
| 141 | Problematic | Traffic_Problematic_A.png | Problematic | Problematic | E | 2.64 | 96.0 | 3.89 | -16.48 | 15 | 35 |
| 142 | Problematic | Traffic_Problematic_B.png | Problematic | Problematic | D | 1.73 | 94.8 | 0.77 | 23.71 | 31 | 15 |
| 143 | Problematic | Traffic_Problematic_D.png | Problematic | Problematic | H | 0.20 | 55.0 | 64.37 | 16.60 | 0 | 3 |
| 144 | Problematic | Traffic_Problematic_H.png | Problematic | Problematic | H | 0.79 | 72.9 | 82.29 | 29.69 | 0 | 6 |
| 145 | Problematic | Traffic_Problematic_N.png | Problematic | Problematic | E | 2.00 | 94.8 | -12.31 | 25.97 | 49 | 2 |
| 146 | Problematic | Traffic_Problematic_X.png | Problematic | Problematic | H | 1.30 | 88.1 | 70.69 | 60.34 | 0 | 1 |
| 147 | Problematic | Traffic_Problematic_Y.png | Problematic | Problematic | D | 1.24 | 96.5 | 35.11 | 15.60 | 4 | 17 |
| 148 | Problematic | Traffic_Problematic_Z.png | Problematic | Problematic | J | 1.31 | 92.7 | -0.93 | 52.63 | 25 | 1 |
| 149 | Problematic | problematic9.png | Problematic | Problematic | H | 0.85 | 78.9 | 66.45 | 65.50 | 0 | 0 |
| 150 | Problematic | throughput_Problematic_10.png | Problematic | Problematic | E | 2.71 | 98.3 | 94.64 | 42.63 | 0 | 4 |
| 151 | Problematic | throughput_Problematic_11.png | Problematic | Problematic | D | 1.49 | 95.0 | 8.55 | -0.00 | 19 | 28 |
| 152 | Problematic | throughput_Problematic_12.png | Problematic | Problematic | E | 1.88 | 94.9 | -10.04 | 5.21 | 37 | 26 |
| 153 | Problematic | throughput_Problematic_13.png | Problematic | Problematic | E | 3.06 | 96.3 | -4.36 | 78.55 | 31 | 0 |
| 154 | Problematic | throughput_Problematic_14.png | Problematic | Problematic | E | 2.33 | 96.2 | -21.67 | 78.33 | 40 | 1 |
| 155 | Problematic | throughput_Problematic_15.png | Problematic | Problematic | E | 1.87 | 98.3 | 6.20 | 8.69 | 22 | 20 |
| 156 | Problematic | throughput_Problematic_16.png | Problematic | Problematic | E | 2.81 | 93.8 | 6.08 | 19.89 | 16 | 5 |
| 157 | Problematic | throughput_Problematic_17.png | Problematic | Problematic | E | 3.15 | 96.4 | 3.46 | -11.85 | 21 | 37 |
| 158 | Problematic | throughput_Problematic_18.png | Problematic | Problematic | H | 1.32 | 91.2 | 91.01 | 84.55 | 0 | 0 |
| 159 | Problematic | throughput_Problematic_19.png | Problematic | Problematic | E | 3.42 | 98.2 | 33.04 | 17.70 | 4 | 9 |
| 160 | Problematic | throughput_Problematic_2.png | Problematic | Problematic | E | 2.53 | 98.3 | 0.55 | 1.91 | 30 | 25 |
| 161 | Problematic | throughput_Problematic_20.png | Problematic | Problematic | E | 3.22 | 98.3 | 78.17 | 35.53 | 0 | 3 |
| 162 | Problematic | throughput_Problematic_21.png | Problematic | Problematic | E | 1.95 | 98.3 | 2.12 | 22.22 | 25 | 9 |
| 163 | Problematic | throughput_Problematic_22.png | Problematic | Problematic | E | 1.92 | 98.3 | 100.00 | 53.92 | 0 | 3 |
| 164 | Problematic | throughput_Problematic_3.png | Problematic | Problematic | E | 1.81 | 98.3 | 45.40 | 67.82 | 2 | 1 |
| 165 | Problematic | throughput_Problematic_4.png | Problematic | Problematic | E | 2.47 | 98.1 | 3.96 | 1.44 | 17 | 20 |
| 166 | Problematic | throughput_Problematic_6.png | Problematic | Problematic | E | 1.94 | 93.0 | 69.97 | 77.03 | 0 | 0 |
| 167 | Problematic | throughput_Problematic_7.png | Problematic | Problematic | H | 1.63 | 96.6 | 76.06 | 95.76 | 0 | 0 |
| 168 | Problematic | throughput_Problematic_8.png | Problematic | Problematic | E | 2.30 | 96.6 | 47.86 | 54.66 | 1 | 1 |
| 169 | Problematic | throughput_Problematic_9.png | Problematic | Problematic | E | 4.16 | 98.2 | 56.67 | 41.52 | 0 | 0 |
| 170 | Problematic | throughput_Problematic_A.png | Problematic | Problematic | E | 1.84 | 98.2 | 52.42 | 45.82 | 4 | 5 |
| 171 | Problematic | throughput_Problematic_G.png | Problematic | Problematic | D | 1.38 | 95.0 | 16.48 | 90.50 | 12 | 0 |
| 172 | Problematic | throughput_Problematic_H.png | Problematic | Problematic | H | 0.92 | 93.0 | 57.08 | 94.90 | 1 | 0 |
| 173 | Problematic | throughput_Problematic_N.png | Problematic | Problematic | H | 1.26 | 95.0 | 31.76 | 90.82 | 2 | 0 |
| 174 | Problematic | throughput_Problematic_R.png | Problematic | Problematic | E | 1.78 | 96.6 | 28.25 | 42.75 | 7 | 5 |
| 175 | Problematic | throughput_Problematic_T.png | Problematic | Problematic | D | 1.54 | 96.6 | 2.79 | 43.02 | 24 | 5 |
| 176 | Problematic | throughput_Problematic_U.png | Problematic | Problematic | H | 1.53 | 91.7 | 70.89 | 39.87 | 0 | 3 |
| 177 | Problematic | throughput_Problematic_W.png | Problematic | Problematic | D | 1.70 | 96.6 | 8.66 | 35.82 | 21 | 9 |
| 178 | Problematic | throughput_Problematic_X.png | Problematic | Problematic | H | 0.99 | 85.7 | 85.57 | 35.05 | 0 | 2 |
| 179 | Problematic | throughput_Problematic_Y.png | Problematic | Problematic | E | 1.87 | 96.6 | 13.14 | 42.80 | 18 | 9 |
| 180 | Problematic | throughput_Problematic_Z.png | Problematic | Problematic | H | 1.26 | 92.9 | 81.61 | 24.71 | 0 | 4 |

## Residual errors (8 of 180) - structural conflicts

| File | Label | Fired case | z_deg | LDD% | L2DD% | NSDD | NS2DD | Why it cannot be fixed |
|---|---|---|---|---|---|---|---|---|
| Normal10.png | Normal | E | 1.81 | 7.79 | 37.30 | 21 | 6 | z above Z_D with percentile above PCT_D (level rule family C/E) |
| Traffic_Normal14.png | Normal | E | 2.97 | 84.10 | 61.00 | 0 | 0 | z above Z_D with percentile above PCT_D (level rule family C/E) |
| Traffic_Normal7.png | Normal | H | 1.53 | 31.82 | 42.25 | 2 | 1 | one-day drop >= LDD_G with <= NSDD_G historical occurrences = user's own rare-big-drop rule |
| throughput_Normal_13.png | Normal | D | 1.63 | 39.62 | 34.30 | 4 | 9 | P >= PCT_C on the last-resort Case D (user moved it before the default L) |
| throughput_Normal_17.png | Normal | E | 2.04 | -12.15 | 1.77 | 36 | 23 | z above Z_D with percentile above PCT_D (level rule family C/E) |
| throughput_Normal_8.png | Normal | D | 1.61 | 39.07 | 25.17 | 6 | 14 | P >= PCT_C on the last-resort Case D (user moved it before the default L) |
| Problematic_V.png | Problematic | L | 0.84 | 41.59 | 40.98 | 3 | 5 | no case fires: LDD/NSDD rectangle conflict with Normal-labeled counterparts (provable inseparability under the ladder) |
| Problematic_X.png | Problematic | L | 1.09 | 27.49 | 33.33 | 3 | 3 | no case fires: LDD/NSDD rectangle conflict with Normal-labeled counterparts (provable inseparability under the ladder) |

## Notes

- P_deg (user-corrected): %% of clean days strictly better than LDV;
  high P = LDV is bad (e.g. [100,98,97,96,90] -> 80%%).
- NSDD/NS2DD pairs: reference pair (last day) excluded; pairs touching
  an outlier-flagged point excluded.
- Signed degradations: negative LDD/L2DD = improvement (per user directive).
- Guards: n<10 -> Insufficient Data (none here); std_c=0 -> z_deg=0;
  FR=0 -> LDD=L2DD=0.
- v3 evaluation order: A, B, C, E, F, G, H, I, J, K, D, L.
- Files: `final_parameters_v3.csv`, `curve_classification_v3.csv`, `optimization_report_v3.md`.
