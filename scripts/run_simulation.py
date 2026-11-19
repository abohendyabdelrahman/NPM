# -*- coding: utf-8 -*-
"""
run_simulation.py — Run the AOM online-training rehearsal.

Usage (from the project root):
    python outputs/online_training/scripts/run_simulation.py \
        --workspace outputs/online_training \
        [--config outputs/online_training/configs/replay_config.json] \
        [--tag my_first_run]

Prerequisites: python outputs/online_training/scripts/make_kit_data.py outputs/online_training
Outputs:       outputs/online_training/runs/<timestamp>_<tag>/
"""
import argparse
import json
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from online_trainer import simulator as SIM      # noqa: E402
from online_trainer.corpus import Corpus         # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--config", default=None)
    ap.add_argument("--tag", default="demo")
    args = ap.parse_args()

    ws = Path(args.workspace)
    cfg_path = Path(args.config) if args.config else ws / "configs" / "replay_config.json"
    with open(cfg_path, encoding="utf-8") as fh:
        raw = json.load(fh)
    cfg = SIM.ReplayConfig(**raw)

    corpus = Corpus(ws / "data")

    run_id = f"{time.strftime('%Y%m%d_%H%M%S')}_{args.tag}"
    run_dir = ws / "runs" / run_id
    if run_dir.exists():
        shutil.rmtree(run_dir)
    sim = SIM.Replayer(corpus, cfg, run_dir)
    history = sim.run()

    print(f"\n=== ONLINE TRAINING REHEARSAL DONE -> {run_dir} ===")
    print(f"curves in table: {len(corpus.table)}, max complete day: {sim.max_day}")
    for evt in history:
        if evt["action"] == "skipped":
            print(f"  day {evt['day']:>4}: SKIPPED ({evt['reason']})")
        else:
            g = evt["gate"]
            print(f"  day {evt['day']:>4}: {evt['action'].upper():8s} "
                  f"holdout {g['holdout_acc']:.4f} / deployed {g['deploy_holdout_acc']:.4f}")
    print(f"\ndeployed parameters now: {sim.current['verdict']}")
    print("read runs/<id>/proposals/ to follow the decisions.")


if __name__ == "__main__":
    main()
