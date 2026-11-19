# -*- coding: utf-8 -*-
"""
make_kit_data.py — Build the input files that the "online training" operation consumes.

Run from the project root:
    python outputs/online_training/scripts/make_kit_data.py <workspace_dir>

IMPORTANT: this script does NOT re-extract features. It reuses the feature tables
already produced in this project (the approved v2 extraction pipeline):

  - outputs/optimization/curve_metrics.csv            per-curve FEATURES (n, n_clean,
    n_outliers, polarity, LDV, mean_c, std_c, FR, z_deg, P_deg, LDD, L2DD, NSDD, NS2DD)
  - outputs/optimization/curve_classification_v2.csv  authoritative LABELS + fired case
  - outputs/optimization/final_parameters.csv         deployed parameter set

Outputs (into <workspace_dir>/data/):
  - curve_features.csv   the labelled feature table the trainer fits on (one row = one curve)
  - labels.csv           curve_id -> true_label (Problematic=1 / Normal=0)
  - polarity_kpi.csv     polarity documentation (comes from curve_metrics.polarity)
  - deployed_params.csv  frozen live parameter table (baseline for every retrain)
  - curve_id_map.csv     folder/file -> curve_id

These four files are exactly what a real online trainer must be fed: features
(precomputed), labels (operator-confirmed), polarity (already inside features),
deployed params (what is live NOW).
"""
import argparse
import csv
import sys
from pathlib import Path


def curve_id(folder, file):
    return f"{folder}__{file}"


# curves relabeled during the v2 run: the old file name appeared in the raw
# extraction, the corrected name+label appears in the classification table.
RENAMES = {
    "Normal__Normal_N.png": "Problematic__Problematic_N.png",
    "Normal__throughput_Normal_V.png": "Problematic__throughput_Problematic_V.png",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("workspace", help="outputs/online_training dir")
    args = ap.parse_args()

    ws = Path(args.workspace)
    data_dir = ws / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    root = ws.parent.parent  # .../Trends/Problematic
    feats_src = root / "outputs" / "optimization" / "curve_metrics.csv"
    class_src = root / "outputs" / "optimization" / "curve_classification_v2.csv"
    params_src = root / "outputs" / "optimization" / "final_parameters.csv"
    for p in (feats_src, class_src, params_src):
        if not p.exists():
            sys.exit(f"missing source: {p}")

    # ---- authoritative labels (94 Problematic / 86 Normal after relabels) ----
    labels = {}
    cases = {}
    with open(class_src, encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            cid = curve_id(row["folder"], row["file"])
            labels[cid] = 1 if str(row["label"]).strip().lower().startswith("problem") else 0
            cases[cid] = row.get("case", "")

    # ---- feature table (polarity already encoded in curve_metrics.z_deg etc.) ----
    # complete_day = calendar day the curve's series ENDED in the data lake,
    # taken from the raw extraction (extracted_values.idx max) -- timeline metadata,
    # NOT a feature recomputation.
    raw_src = root / "outputs" / "distributions" / "extracted_values.csv"
    end_day = {}
    if raw_src.exists():
        with open(raw_src, encoding="utf-8-sig") as fh:
            for row in csv.DictReader(fh):
                cid_old = curve_id(row["folder"], row["file"])
                cid = RENAMES.get(cid_old, cid_old)
                d = int(row["idx"])
                if cid not in end_day or d > end_day[cid]:
                    end_day[cid] = d

    feat_columns = ["folder", "file", "n", "n_clean", "n_outliers", "polarity",
                    "LDV", "mean_c", "std_c", "FR",
                    "z_deg", "P_deg", "LDD", "L2DD", "NSDD", "NS2DD"]
    out_rows = []
    with open(feats_src, encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            cid_old = curve_id(row["folder"], row["file"])
            cid = RENAMES.get(cid_old, cid_old)
            label = labels.get(cid, -1)          # -1 = label not found (should not happen)
            case = cases.get(cid, "")
            out_rows.append([
                cid.split("__")[0], cid.split("__", 1)[1], cid,
            ] + [row[c] for c in feat_columns[2:]] + [end_day.get(cid, row["n"]),
                                                      label, case])

    out_rows.sort(key=lambda r: r[0] + r[1])
    with open(data_dir / "curve_features.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["folder", "file", "curve_id"] + feat_columns[2:]
                   + ["complete_day", "label", "case_v2"])
        w.writerows(out_rows)

    # ---- labels.csv ----
    with open(data_dir / "labels.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["curve_id", "true_label"])
        for r in out_rows:
            w.writerow([r[2], r[-2]])

    # ---- polarity_kpi.csv (documentation) ----
    with open(data_dir / "polarity_kpi.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["curve_id", "polarity", "notes"])
        # polarity column = feat_columns.index('polarity')-2+3 within out_rows
        pol_idx = 3 + feat_columns[2:].index("polarity")
        for r in out_rows:
            w.writerow([r[2], r[pol_idx],
                        "+1 higher=degradation (CDR family), -1 others (v2 §0.4)"])

    # ---- deployed params (copy of frozen fit) ----
    with open(params_src, encoding="utf-8-sig") as fh:
        content = fh.read()
    with open(data_dir / "deployed_params.csv", "w", newline="", encoding="utf-8") as fh:
        fh.write(content)

    # ---- curve_id_map.csv ----
    with open(data_dir / "curve_id_map.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["folder", "file", "curve_id"])
        for r in out_rows:
            w.writerow([r[0], r[1], r[2]])

    unknowns = [r[2] for r in out_rows if r[-2] == -1]
    print(f"kit data written to {data_dir}")
    print(f"  curves            : {len(out_rows)}")
    print(f"  problematic labels: {sum(1 for r in out_rows if r[-2] == 1)} / Normal {sum(1 for r in out_rows if r[-2] == 0)}")
    print(f"  missing labels    : {unknowns if unknowns else 'none'}")
    print(f"  polarity +1 curves: {[r[2] for r in out_rows if int(r[3 + feat_columns[2:].index('polarity')]) == 1]}")


if __name__ == "__main__":
    main()
