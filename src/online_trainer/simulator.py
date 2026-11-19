# -*- coding: utf-8 -*-
"""online_trainer.replay — day-by-day replay of the ONLINE TRAINING OPERATION.

This is the rehearsal of the live operation, built on the PRE-EXTRACTED
feature table (curve_features.csv) -- exactly like the production/v2 fit.

Each simulated day, the trainer does:

  1. DATA LANDS      curves whose series reaches day `n` become COMPLETE
                     (their pre-extracted feature row is now available).
  2. LIVE SCORING    the CURRENT DEPLOYED parameter set scores each newly
                     completed curve -> the daily dashboard verdict.
  3. LABELS ARRIVE   the operator label becomes usable `label_latency` days
                     after completion; the curve's feature row + label then
                     enter the labelled training POOL.
  4. RETRAIN TRIGGER every `retrain_interval` days the trainer refits on the
                     pool (randomized search + local polish), validates on the
                     holdout reference set, runs the regression gate against
                     the deployed parameters, and writes a CHANGE PROPOSAL.
                     Promotion only if the gate passes.

Key operational lesson: you can only ever RETRAIN on curves whose label has
arrived. Early on the pool is small; late labels pull the fit. Data files:

  data/curve_features.csv    precomputed features + labels (the training table)
  data/deployed_params.csv   live parameter set
  data/labels.csv            all known ground truth

Outputs go to runs/<run_id>/:
  completion_log.csv     day -> curves completed, their features, deployed verdict
  labels_arrived.csv     when each label became usable
  live_verdicts.csv      deployed verdict per curve (once completed)
  proposals/             one markdown per retrain event (READ THESE)
  params/                candidate + accepted parameter tables
  summary.json           machine-readable summary
"""
from __future__ import annotations
import csv
import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from . import rules as Rl
from . import optimize as Op
from .corpus import Corpus


@dataclass
class ReplayConfig:
    label_latency: int = 3           # days between curve completion and label use
    retrain_interval: int = 5        # retrain every N days
    first_retrain_day: int = 0       # 0 = first retrain as soon as a trigger day arrives
    fit_budget: int = 1500           # candidate samples per fit
    do_cv: bool = False              # 5-fold CV sanity at each retrain
    gate_tolerance: float = 0.0      # candidate must not lose holdout acc vs deployed
    min_holdout_for_gate: int = 8    # fewer holdout labels -> keep deployed
    seed: int = 1

    def ready_after(self, day):
        return day - 60 if day > 60 else 0  # unused; kept for api stability


_FEATURE_KEYS = ["z_deg", "P_deg", "LDD", "L2DD", "NSDD", "NS2DD"]


class Replayer:
    def __init__(self, corpus: Corpus, cfg: ReplayConfig, run_dir: Path):
        self.corpus = corpus
        self.cfg = cfg
        self.run_dir = Path(run_dir)
        self.prop_dir = self.run_dir / "proposals"
        self.param_dir = self.run_dir / "params"
        for d in (self.prop_dir, self.param_dir):
            d.mkdir(parents=True, exist_ok=True)

        self.current = {"params": dict(corpus.deployed), "verdict": "deployed"}
        self.history = []
        self.events = []
        self.max_day = max(r["complete_day"] for r in corpus.table.values())
        # curves complete on their extraction day; label ready complete_d+lateny
        self.label_day = {cid: r["complete_day"] + cfg.label_latency
                          for cid, r in corpus.table.items()}

    # ------------------------------------------------------------------
    def _pool_on_day(self, day):
        return {cid: self.corpus.example(cid)
                for cid, r in self.corpus.table.items()
                if self.label_day[cid] <= day}

    # ------------------------------------------------------------------
    def step(self, day):
        completed = []
        new_labels = []
        for cid, r in self.corpus.table.items():
            if r["complete_day"] == day:      # 1. data lands (curve complete)
                verdict, case, why = Rl.evaluate(self.corpus.feature_dict(cid),
                                                 self.current["params"])
                completed.append({"day": day, "curve_id": cid,
                                  "label": r["label"], "verdict": verdict,
                                  "case": case, "why": why, **{
                                      k: (int(r[k]) if k in ("NSDD", "NS2DD") else round(float(r[k]), 4))
                                      for k in _FEATURE_KEYS}})
            if self.label_day[cid] == day:    # 3. label arrives
                new_labels.append((day, cid, r["label"]))
        # 2. live scoring persisted
        if completed:
            with open(self.run_dir / "live_verdicts.csv", "a", newline="", encoding="utf-8") as fh:
                if fh.tell() == 0:
                    fh.write(",".join(completed[0].keys()) + "\n")
                for row in completed:
                    fh.write(",".join(str(row[k]) for k in row) + "\n")
            with open(self.run_dir / "completion_log.csv", "a", newline="", encoding="utf-8") as fh:
                if fh.tell() == 0:
                    fh.write(",".join(completed[0].keys()) + "\n")
                for row in completed:
                    fh.write(",".join(str(row[k]) for k in row) + "\n")
        if new_labels:
            with open(self.run_dir / "labels_arrived.csv", "a", newline="", encoding="utf-8") as fh:
                if fh.tell() == 0:
                    fh.write("day,curve_id,label\n")
                for d, cid, lab in new_labels:
                    fh.write(f"{d},{cid},{lab}\n")
        return completed, new_labels

    # ------------------------------------------------------------------
    def retrain(self, day):
        pool = self._pool_on_day(day)
        train_ex = {c: e for c, e in pool.items() if not self.corpus.holdout[c]}
        hold_ex = {c: e for c, e in pool.items() if self.corpus.holdout[c]}
        evt = {"day": day, "pool": len(pool), "train": len(train_ex),
               "holdout": len(hold_ex), "action": "skipped", "reason": "",
               "candidate": {}, "gate": {}}

        if len(train_ex) < 40 or len(hold_ex) < self.cfg.min_holdout_for_gate:
            evt["reason"] = (f"insufficient labels (train={len(train_ex)}, "
                             f"holdout={len(hold_ex)}); keep deployed set — do not "
                             "promote on weak evidence")
            self.events.append((day, f"RETRAIN skipped: {evt['reason']}"))
            self.history.append(evt)
            self._write_proposal(evt, day)
            return evt

        cand = Op.fit(train_ex, budget=self.cfg.fit_budget, seed=self.cfg.seed + day,
                      objective="balanced_accuracy")
        cand = Op.local_polish(train_ex, cand, rounds=300, seed=self.cfg.seed + day)
        m_cand = Op.evaluate_params(pool, cand)
        m_dep = Op.evaluate_params(pool, self.current["params"])
        gh_cand = Op.evaluate_params(hold_ex, cand)
        gh_dep = Op.evaluate_params(hold_ex, self.current["params"])
        delta = gh_cand["accuracy"] - gh_dep["accuracy"]
        passed = delta >= -self.cfg.gate_tolerance
        cv = Op.strided_cv(train_ex, n_folds=5, seed=self.cfg.seed + day) if self.cfg.do_cv else None

        evt.update({
            "action": "accepted" if passed else "rejected",
            "candidate": cand,
            "gate": {
                "train_acc": m_cand["accuracy"], "deploy_train_acc": m_dep["accuracy"],
                "holdout_acc": gh_cand["accuracy"], "deploy_holdout_acc": gh_dep["accuracy"],
                "delta_holdout": round(delta, 4), "passed": passed, "cv": cv,
            },
        })
        if passed:
            self.current = {"params": dict(cand), "verdict": f"accepted_day{day}"}
        self.events.append((day, f"RETRAIN {evt['action']} (holdout acc "
                                 f"{gh_cand['accuracy']:.3f} vs deployed "
                                 f"{gh_dep['accuracy']:.3f})"))
        self._write_proposal(evt, day)
        self._save_params(day, cand, passed)
        self.history.append(evt)
        return evt

    # ------------------------------------------------------------------
    def _write_proposal(self, evt, day):
        p = self.prop_dir / f"proposal_day{day:03d}.md"
        lines = [f"# Change proposal — retrain event on day {day}",
                 f"\n- Labelled pool: **{evt['pool']}** curves "
                 f"(train {evt['train']} / holdout {evt['holdout']})",
                 f"- Action: **{evt['action']}**"]
        if evt["reason"]:
            lines.append(f"- Reason: {evt['reason']}")
            lines.append("\n_No parameter change — evidence too thin. "
                         "Operation continues with the deployed set._")
            p.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return

        g = evt["gate"]
        lines += [
            f"- Fit accuracy (pool): {g['train_acc']:.4f} "
            f"(deployed: {g['deploy_train_acc']:.4f})",
            f"- **Holdout accuracy {g['holdout_acc']:.4f} (deployed "
            f"{g['deploy_holdout_acc']:.4f}, delta {g['delta_holdout']:+.4f})**",
            f"- Gate: {'PASS -> promote candidate' if g['passed'] else 'FAIL -> keep deployed'}",
        ]
        if g.get("cv"):
            lines.append(f"- 5-fold CV (train pool): {g['cv']['cv_acc_mean']:.4f}")
        lines.append("\n### Parameter diff vs deployed\n\n| param | deployed | candidate | delta |")
        for k, v in sorted(evt["candidate"].items()):
            cur = self.corpus.deployed[k]
            lines.append(f"| {k} | {cur:.4f} | {v:.4f} | {v - cur:+.4f} |")
        p.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _save_params(self, day, cand, passed):
        tag = f"day{day:03d}_{'ACCEPT' if passed else 'REJECT'}"
        with open(self.param_dir / f"params_{tag}.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["param", "value"])
            for k, v in sorted(cand.items()):
                w.writerow([k, f"{v:.4f}"])

    # ------------------------------------------------------------------
    def run(self, days=None):
        days = days or (self.max_day + self.cfg.label_latency)
        for f in ("live_verdicts.csv", "completion_log.csv", "labels_arrived.csv"):
            with open(self.run_dir / f, "w", newline="", encoding="utf-8") as fh:
                fh.write("")  # headers written lazily
        for d in range(1, days + 1):
            self.step(d)
            if self.cfg.first_retrain_day <= d and d % self.cfg.retrain_interval == 0:
                self.retrain(d)
        if days % self.cfg.retrain_interval != 0:      # catch-up after last labels
            self.retrain(days)
        self._write_summary(days)
        return self.history

    def _write_summary(self, days):
        body = {"run_end_day": days, "config": self.cfg.__dict__,
                "curves": len(self.corpus.table),
                "events": [{"day": d, "msg": m} for d, m in self.events],
                "retrains": [
                    {k: ("params" if k == "candidate" else v) for k, v in evt.items()}
                    for evt in self.history],
                "final": {"verdict": self.current["verdict"],
                          "params": {k: round(v, 4) for k, v in self.current["params"].items()}}}
        with open(self.run_dir / "summary.json", "w", encoding="utf-8") as fh:
            json.dump(body, fh, indent=2, ensure_ascii=False)
