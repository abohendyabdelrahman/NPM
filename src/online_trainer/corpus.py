# -*- coding: utf-8 -*-
"""online_trainer.corpus — load the labelled feature table (PRE-EXTRACTED).

The v2 extraction pipeline already produced per-curve features (curve_metrics.csv)
plus authoritative labels and the fired case (curve_classification_v2.csv).
The kit merges them into one labelled feature table -- the trainer NEVER
re-extracts features: it consumes exactly what the approved v2 fit consumed.

A "labelled example" is one curve; its features are the final-window ones from
the extraction. The simulator decides WHEN each example becomes usable for
training (operator label arrival), then hands the feature row to the fitter.
"""
from __future__ import annotations
import csv
import hashlib
from pathlib import Path

# feature columns that the fitter needs, in the same units as v2
FEATURE_COLS = ["z_deg", "P_deg", "LDD", "L2DD", "NSDD", "NS2DD"]


def _load_table(csv_path):
    """rows -> dict curve_id -> {feat-names..., label, case_v2, n, complete_day, ...}"""
    table = {}
    with open(csv_path, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            table[row["curve_id"]] = {
                "folder": row["folder"], "file": row["file"],
                "n": int(row["n"]), "n_clean": int(row["n_clean"]),
                "n_outliers": int(row["n_outliers"]),
                "polarity": int(float(row["polarity"])),
                "complete_day": int(row["complete_day"]),
                "LDV": float(row["LDV"]), "mean_c": float(row["mean_c"]),
                "std_c": float(row["std_c"]), "FR": float(row["FR"]),
                "z_deg": float(row["z_deg"]), "P_deg": float(row["P_deg"]),
                "LDD": float(row["LDD"]), "L2DD": float(row["L2DD"]),
                "NSDD": int(row["NSDD"]), "NS2DD": int(row["NS2DD"]),
                "label": int(row["label"]),
                "case_v2": row.get("case_v2", "").strip(),
            }
    return table


def _load_params(csv_path):
    p = {}
    with open(csv_path, encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            p[str(row["letter"]).strip()] = float(row["value"])
    return p


def holdout_mask(curve_ids, ratio=0.25, salt="v2"):
    """Deterministic per-curve holdout by hash -> the fixed reference test set
    reserved at deploy time (never used for fitting)."""
    out = {}
    for cid in sorted(curve_ids):
        h = hashlib.sha256(f"{salt}::{cid}".encode()).hexdigest()
        out[cid] = (int(h[:8], 16) % 100) < ratio * 100
    return out


class Corpus:
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
        self.table = _load_table(self.data_dir / "curve_features.csv")
        self.deployed = _load_params(self.data_dir / "deployed_params.csv")
        self.holdout = holdout_mask(list(self.table))

    def feature_dict(self, cid):
        """The feature dict the rules/optimizer modules expect."""
        r = self.table[cid]
        return {
            "z_deg": r["z_deg"], "P_deg": r["P_deg"],
            "LDD": r["LDD"], "L2DD": r["L2DD"],
            "NSDD": r["NSDD"], "NS2DD": r["NS2DD"],
            "analysable": True,  # extraction guarantees >=10 clean points
        }

    def example(self, cid):
        return (self.feature_dict(cid), self.table[cid]["label"])

    def examples(self, cids=None):
        cids = cids or list(self.table)
        return {cid: self.example(cid) for cid in sorted(cids)}
