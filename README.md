# AOM Problematic Trend Checker — Online-Training Rehearsal Kit

A runnable rehearsal of what **online training** of your AOM Daily Trend Checker
(v2, 12 cases A–L, 21 thresholds) would look like — so you can experience the
operation **without going online**.

The kit reuses the **already-extracted** feature tables from this project
(`outputs/optimization/curve_metrics.csv` + `curve_classification_v2.csv`).
It does **not** re-extract features from raw curves — the trainer consumes the
same labeled feature table the approved v2 fit consumed.

---

## 1. Where things live

```
outputs/online_training/
├── data/                                  <- the FILES you give the trainer
│   ├── curve_features.csv                 <- labelled feature table (180 rows)
│   ├── labels.csv                         <- curve_id -> Problematic/Normal
│   ├── polarity_kpi.csv                   <- per-curve degradation polarity
│   ├── deployed_params.csv                <- live parameter set (frozen v2)
│   └── curve_id_map.csv                   <- folder/file -> curve_id
├── configs/replay_config.json             <- operation knobs (see §4)
├── scripts/
│   ├── make_kit_data.py                   <- (re)builds data/ once
│   ├── verify_kit.py                      <- proves data == the v2 fit's data
│   └── run_simulation.py                  <- runs the online-training rehearsal
└── src/online_trainer/
    ├── corpus.py      load feature table, labels, deployed params, holdout split
    ├── rules.py       the A..L cascade (decision algorithm, exact v2 order)
    ├── optimize.py    fit (random search + polish) + metrics + 5-fold CV
    └── simulator.py   the day-by-day online operation engine
```

`data/` is exactly what a live online trainer must be handed each day:

| file | received from | meaning |
|---|---|---|
| `curve_features.csv` | extraction pipeline | one row per curve: features + label |
| `labels.csv` | operator confirmation | ground truth (Problematic/Normal) |
| `polarity_kpi.csv` | spec §0.4 | +1 higher=degradation (CDR), −1 others |
| `deployed_params.csv` | your V&V gate | the params live in AOM today |

## 2. Quick start (3 commands, run from project root)

```bash
# 1) build the input files (only once, or after anything in outputs/ changes)
python outputs/online_training/scripts/make_kit_data.py outputs/online_training

# 2) verify the kit consumes the same data the v2 fit used (PASS expected)
python outputs/online_training/scripts/verify_kit.py outputs/online_training

# 3) run the online-training rehearsal
python outputs/online_training/scripts/run_simulation.py \
    --workspace outputs/online_training --tag my_first_run
```

Latest run: `outputs/online_training/runs/<timestamp>_my_first_run/`
Read the **proposals/** folder — that is the "how the operation goes" trace.

## 3. What the simulation does (the online operation, day by day)

```
day ───►  DATA LANDS       a curve's series ends -> its feature row is available
   │      LIVE SCORING     deployed params score it -> dashboard verdict (live_verdicts.csv)
   │      LABELS ARRIVE    operator label becomes usable label_latency days later
   │                       -> curve enters the labelled POOL
   │      RETRAIN TRIGGER  every retrain_interval days: re-fit on the pool
   │                       (random search + polish)
   │      VALIDATION       holdout reference set (25%, fixed) -> accuracy
   │      REGRESSION GATE  candidate must not lose holdout accuracy vs deployed
   │      PROPOSAL         proposals/<day>.md = parameter diff + metrics + verdict
   └──►   PROMOTE only if the gate PASSES; otherwise keep deployed
```

Outputs per run:

| output | what you learn |
|---|---|
| `completion_log.csv` | which curves finished each day, their features, deployed verdict |
| `live_verdicts.csv` | what the dashboard would have shown, per curve |
| `labels_arrived.csv` | when each label became usable (the scarce resource) |
| `proposals/*.md` | one per retrain: gate result + full parameter diff (**read these**) |
| `params/*.csv` | candidate parameter tables (ACCEPT/REJECT tagged) |
| `summary.json` | machine-readable run summary + final deployed state |

## 4. Operation knobs (`configs/replay_config.json`)

| key | default | what it changes | try to see |
|---|---|---|---|
| `label_latency` | 3 | days until a confirmed label is usable | 14 → most retrains skip (no labels) |
| `retrain_interval` | 2 | days between retrain attempts | 10 → fewer, bigger refits |
| `fit_budget` | 1500 | random-search candidates per refit | 200 → candidates lose more often |
| `do_cv` | false | 5-fold CV inside each retrain proposal | true → extra sanity metric |
| `gate_tolerance` | 0.0 | allowed holdout-accuracy loss | 0.05 → some candidates promoted |
| `min_holdout_for_gate` | 8 | skip the gate when holdout is this small | 30 → rarely gateable early |
| `seed` | 1 | reproducibility | any int |

## 5. The important lesson from the first run

Run `rehearsal_1` (config as shipped) **rejected every candidate** — including
day 83 when the pool already had all 180 curves:

```
day 83: fit acc 0.9222 vs deployed 0.9500 ; holdout 0.8837 vs 0.9535 -> REJECT
```

That is not a bug: it is the correct behaviour of online training for this
algorithm. The deployed v2 set was fit with millions of candidates on these same
180 curves; a 1,500-candidate refit on a subset cannot beat it, and the gate
protects the live dashboard from a worse refit. This is exactly the experience
you asked to rehearse — online retraining rarely "improves" at first; it is a
**governance loop**, not a free accuracy boost.
To see a promotion, relax `gate_tolerance` to ~0.05 and/or raise `fit_budget`,
then re-run: `python outputs/online_training/scripts/run_simulation.py --workspace outputs/online_training --tag tol005 --config outputs/online_training/configs/replay_config_tol005.json`

## 6. Going "real" later

When you actually move online, the same five files keep their roles. You swap:

- `curve_features.csv`  ← generated each day by your extraction pipeline
- `labels.csv`          ← operator confirmations with real storage/provenance
- `deployed_params.csv` ← the parameter version AOM currently runs
- proposals            ← your change-approval records (audit trail)
- the gate above       ← your promotion rule (never promote on weak evidence)

Constraints that stay true in production:
- You can only retrain on curves whose label has already arrived — label latency
  is your real bottleneck.
- The holdout must never be used for fitting, or the gate is meaningless.
- Keep the last-known-good parameter file; promotion/rollback is a file swap.
