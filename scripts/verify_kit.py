# -*- coding: utf-8 -*-
"""
verify_kit.py — correctness checks for the online-training kit.

Usage (from the project root):
    python outputs/online_training/scripts/verify_kit.py outputs/online_training

Checks:
 1. data/curve_features.csv loads and has 180 curves, 94 Problematic / 86 Normal.
 2. The deployed parameter set, when applied through the A..L cascade, reproduces
    the same verdict AND case as curve_classification_v2.csv (the approved v2 fit).
 3. Feature columns are identical (within rounding) to curve_metrics.csv.

A fully passing verification means the trainer consumes exactly the same
feature table the approved v2 optimizer consumed.
"""
import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from online_trainer.corpus import Corpus            # noqa: E402
from online_trainer import rules as Rl              # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("workspace")
    args = ap.parse_args()
    ws = Path(args.workspace)
    root = ws.parent.parent

    corpus = Corpus(ws / "data")
    ok = True

    # 1. size + labels
    n = len(corpus.table)
    pos = sum(1 for r in corpus.table.values() if r["label"] == 1)
    print(f"[1] curves={n}  Problematic={pos}  Normal={n - pos}")
    ok &= (n == 180 and pos == 94)

    # 2. deployed params reproduce v2 verdict + case
    mism_verdict = mism_case = 0
    with open(root / "outputs" / "optimization" / "curve_classification_v2.csv",
              encoding="utf-8-sig") as fh:
        exp = {f"{r['folder']}__{r['file']}": (r["predicted"], r["case"])
               for r in csv.DictReader(fh)}
    for cid in corpus.table:
        v, case, _ = Rl.evaluate(corpus.feature_dict(cid), corpus.deployed)
        pe, ce = exp.get(cid, (None, None))
        if pe and v != pe:
            mism_verdict += 1
        if ce and case != ce:
            mism_case += 1
    print(f"[2] deployed-params verdict/case vs v2 classification: "
          f"verdict mismatches={mism_verdict}, case mismatches={mism_case}")
    ok &= (mism_verdict == 0 and mism_case == 0)

    # 3. feature columns vs curve_metrics.csv
    with open(root / "outputs" / "optimization" / "curve_metrics.csv",
              encoding="utf-8-sig") as fh:
        ref = {f"{r['folder']}__{r['file']}": {k: float(r[k]) for k in
               ("z_deg", "P_deg", "LDD", "L2DD")} for r in csv.DictReader(fh)}
    big = 0
    for cid, r in corpus.table.items():
        for k in ("z_deg", "P_deg", "LDD", "L2DD"):
            if cid in ref and abs(r[k] - ref[cid][k]) > 1e-3:
                big += 1
    print(f"[3] feature deltas vs curve_metrics (tolerance 1e-3): {big} exceed")
    ok &= (big == 0)

    print("\nRESULT:", "PASS — kit data is the same table the v2 fit used" if ok
          else "FAIL — inspect mismatches")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
