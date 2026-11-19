# -*- coding: utf-8 -*-
"""online_trainer.optimize — fit + evaluate a parameter set on a labelled corpus.

Metrics mirror the v2 report: accuracy, balanced accuracy, confusion matrix,
per-case fire distribution, 5-fold stratified CV.
The fitter is a multi-seed randomized search over the 21-threshold space with a
configurable candidate budget and random seed (the live trainer re-runs this on
whatever labelled data it has — the simulator keeps the budget small).
"""
from __future__ import annotations
import copy
import random


def predict_all(examples, p):
    """examples: {cid: (feat,label)}. Returns {cid: 'Problematic'/'Normal'}."""
    from . import rules as Rr
    Rr.check_params(p)
    return {cid: Rr.evaluate(feat, p)[0] for cid, (feat, _lab) in examples.items()}


def evaluate_params(examples, p):
    """Accuracy, balanced accuracy, confusion (TP/FP/FN/TN), per-case fires."""
    from . import rules as Rr
    Rr.check_params(p)
    tp = fp = fn = tn = 0
    cases = {}
    n_problem = 0
    for cid, (feat, lab) in examples.items():
        verdict, case, _ = Rr.evaluate(feat, p)
        pred = 1 if verdict == "Problematic" else 0
        cases[case] = cases.get(case, 0) + 1
        if lab == 1:
            n_problem += 1
            if pred == 1:
                tp += 1
            else:
                fn += 1
        else:
            if pred == 1:
                fp += 1
            else:
                tn += 1
    n = tp + fp + fn + tn
    acc = (tp + tn) / n if n else 0.0
    n_pos = tp + fn
    n_neg = fp + tn
    sens = tp / n_pos if n_pos else 0.0
    spec = tn / n_neg if n_neg else 0.0
    bal = 0.5 * (sens + spec)
    return {
        "n": n, "n_problem": n_problem,
        "accuracy": acc, "balanced_accuracy": bal,
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "precision": (tp / (tp + fp)) if (tp + fp) else 0.0,
        "recall": sens,
        "cases": cases,
    }


def strided_cv(examples, n_folds=5, seed=1):
    """Stratified k-fold over curves. Returns per-fold METRICS evaluated on the
    test fold using params fitted on the train fold (still random-search fit).
    Small budget — this is a sanity check, not the production 2M-candidate run."""
    cids = sorted(examples)
    labs = [examples[c][1] for c in cids]
    pos = [c for c, l in zip(cids, labs) if l == 1]
    neg = [c for c, l in zip(cids, labs) if l == 0]
    rng1, rng2 = random.Random(seed), random.Random(seed + 7)
    rng1.shuffle(pos)
    rng2.shuffle(neg)

    folds = {}
    for k in range(n_folds):
        folds[k] = {"train": [], "test": []}
    for k, c in enumerate(pos):
        folds[k % n_folds]["test"].append(c)
    for k, c in enumerate(neg):
        folds[k % n_folds]["test"].append(c)

    out = []
    for k in range(n_folds):
        test_ids = set(folds[k]["test"])
        train_ex = {c: examples[c] for c in cids if c not in test_ids}
        if not train_ex:
            continue
        test_ex = {c: examples[c] for c in test_ids}
        p = fit(train_ex, budget=1200, seed=seed + k)
        out.append(evaluate_params(test_ex, p))
    if out:
        accs = [m["accuracy"] for m in out]
        return {"cv_acc_mean": sum(accs) / len(accs), "cv_folds": out}
    return {"cv_acc_mean": None, "cv_folds": []}


# --------------------------------------------------------------------------
# fitting: randomized search over the threshold space
# --------------------------------------------------------------------------
def _random_params(rng):
    p = {
        # z thresholds (sigma), positive
        "E": rng.uniform(1.0, 4.0),   # Z_B
        "T": rng.uniform(1.0, 4.0),   # Z_D
        "L": rng.uniform(2.0, 8.0),   # Z_F
        "N": rng.uniform(1.0, 4.0),   # Z_H
        "D": rng.uniform(0.0, 2.0),   # Z_J
        # percentile thresholds (%)
        "V": rng.uniform(80.0, 100.0),  # PCT_C
        "S": rng.uniform(70.0, 100.0),  # PCT_D
        "O": rng.uniform(0.0, 60.0),    # PCT_H
        # LDD thresholds (%)
        "R": rng.uniform(0.0, 25.0),   # LDD_E
        "J": rng.uniform(0.0, 60.0),   # LDD_F
        "X": rng.uniform(0.0, 20.0),   # LDD_G
        "Z": rng.uniform(30.0, 100.0), # LDD_H
        "M": rng.uniform(0.0, 60.0),   # LDD_I
        "B": rng.uniform(0.0, 60.0),   # LDD_J
        "I": rng.uniform(0.0, 60.0),   # L2DD_F
        "K": rng.uniform(0.0, 100.0),  # L2DD_I
        "C": rng.uniform(0.0, 60.0),   # L2DD_J
        "Y": rng.randint(0, 5),        # NSDD_G (int)
        "A": rng.randint(0, 50),       # NS2DD_I
        "NY": rng.uniform(0.0, 40.0),  # Case A
        "NX": rng.randint(5, 45),      # Case A
    }
    return p


def fit(examples, budget=2000, seed=1, objective="balanced_accuracy"):
    """Randomized search maximizing the objective on `examples` (dict of feats)."""
    rng = random.Random(seed)
    best_p, best_score = None, -1.0
    for _ in range(budget):
        p = _random_params(rng)
        m = evaluate_params(examples, p)
        s = m[objective]
        if s > best_score:
            best_score, best_p = s, copy.deepcopy(p)
    return best_p


def local_polish(examples, p0, rounds=300, seed=2):
    """Perturb a parameter set a little; keep improvements (optional)."""
    rng = random.Random(seed)
    best_p, best_score = copy.deepcopy(p0), evaluate_params(examples, p0)[
        "balanced_accuracy"]
    for _ in range(rounds):
        p = copy.deepcopy(best_p)
        key = rng.choice(list(p))
        if isinstance(p[key], int):
            p[key] += rng.choice([-1, 1])
        else:
            p[key] *= rng.uniform(0.85, 1.18)
        s = evaluate_params(examples, p)["balanced_accuracy"]
        if s > best_score:
            best_score, best_p = s, p
    return best_p
