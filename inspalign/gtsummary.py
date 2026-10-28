"""Summary of one run (results.csv + pairs.csv) -> summary/SUMMARY.md and CSVs.

    python -m inspalign.gtsummary results/pcb                                  # with the tau the run used
    python -m inspalign.gtsummary results/pcb --tau-px 5                       # another tau -> summary_tau5/
    python -m inspalign.gtsummary results/pcb --thresholds results/pcb_calib/thresholds.json   # -> summary_calibrated/

Outcomes per attempt (tau in original pixels, applied to the mean point error):
    correct       accepted by the method and error <= tau
    silent_wrong  accepted by the method and error  > tau     <- the dangerous one: a wrong pose nobody is warned about
    lost          rejected by the method although its pose was within tau
    rejected      rejected, and its pose was wrong too (a correct refusal)
    no_pose       the method returned no transform at all

Every method decides by a threshold on one number of its own, its decision score (`score` in results.csv: the RANSAC inlier
count for the correspondence methods, the correlation peak, the edge score). The summary judges that score without any
threshold (how well it ranks right poses above wrong ones), and, with --thresholds, re-decides every attempt with the
thresholds calibrated on held-out images (inspalign/calibrate.py). With several goldens per part it also reports what a
system that keeps several goldens would get: the method picks the golden itself, by its own score.
"""
import argparse
import json
import os

import numpy as np
import pandas as pd

OUTCOMES = ["correct", "silent_wrong", "lost", "rejected", "no_pose"]
RISK = 0.05                                    # the risk level of the "coverage at 5 % risk" column


# ---------------------------------------------------------------------------------------------------------------------------
# building blocks (also used by calibrate.py and report.py)

def _bool(s):
    return s.astype(str).str.lower().isin(["true", "1"])


def prepare(res):
    """Normalise a results table: boolean success / checks_ok, a decision score, region, golden and test-image keys.
    Works on results.csv files written before the score column existed (score taken from conf or n_inl)."""
    from .methods import score_field
    res = res.copy()
    res["success_b"] = _bool(res["success"])
    if "checks_ok" in res:
        res["checks_ok_b"] = _bool(res["checks_ok"])
    else:                                       # older files: only the shape arm had extra checks, named in its reason
        res["checks_ok_b"] = ~res["reason"].fillna("").str.contains("outside the declared")
    if "score" not in res:
        res["score"] = [r.n_inl if score_field(r.method) == "n_inl" else r.conf for r in res.itertuples()]
    res["has_pose"] = res["err_mean_px"].notna()
    res["score"] = pd.to_numeric(res["score"], errors="coerce").where(res["has_pose"])
    res["region"] = res["group"].astype(str).str.split("/").str[0]
    res["golden"] = res["template"].map(lambda p: os.path.splitext(os.path.basename(str(p)))[0])
    res["test"] = res["live"].map(lambda p: os.path.basename(str(p)))
    return res


def classify(accepted, err, tau):
    err = pd.Series(err)
    accepted = pd.Series(accepted, index=err.index).astype(bool)
    has = err.notna()
    within = has & (err <= tau)
    return pd.Series(np.where(~has, "no_pose", np.where(accepted & within, "correct", np.where(accepted & ~within, "silent_wrong",
                     np.where(~accepted & within, "lost", "rejected")))), index=err.index)


def decide(res, thresholds=None):
    """The accept / reject decision of every attempt: the method's own (default), or score >= the calibrated threshold."""
    if not thresholds:
        return res["success_b"]

    def t_of(m):
        e = thresholds.get(m) or {}
        if e.get("accept_none"):
            return np.inf                                       # no threshold met the criterion: the method accepts nothing
        return np.nan if e.get("threshold") is None else float(e["threshold"])
    thr = res["method"].map(t_of).astype(float)
    cal = res["has_pose"] & res["checks_ok_b"] & (res["score"] >= thr)
    return cal.where(thr.notna(), res["success_b"])            # a method without a calibrated threshold keeps its own rule


def auroc(score, right):
    """P(score of a right pose > score of a wrong pose), ties counted half; NaN with fewer than 3 of either."""
    s, r = np.asarray(score, float), np.asarray(right, bool)
    ok = np.isfinite(s)
    pos, neg = s[ok & r], s[ok & ~r]
    if len(pos) < 3 or len(neg) < 3:
        return float("nan")
    allv = np.concatenate([pos, neg])
    ranks = pd.Series(allv).rank(method="average").to_numpy()
    return float((ranks[: len(pos)].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg)))


def risk_coverage(score, right, n_total):
    """For every threshold t on the score: coverage = accepted / all attempts, risk = wrong / accepted (accepted = has a
    pose and score >= t). Returns a DataFrame sorted by threshold, highest first."""
    s, r = np.asarray(score, float), np.asarray(right, bool)
    ok = np.isfinite(s)
    s, r = s[ok], r[ok]
    if len(s) == 0:
        return pd.DataFrame(columns=["threshold", "accepted", "wrong", "coverage", "risk"])
    order = np.argsort(-s, kind="stable")
    s, r = s[order], r[order]
    acc = np.arange(1, len(s) + 1)
    wrong = np.cumsum(~r)
    last = np.r_[s[1:] != s[:-1], True]                       # one row per distinct threshold (all ties accepted together)
    return pd.DataFrame(dict(threshold=s[last], accepted=acc[last], wrong=wrong[last],
                             coverage=acc[last] / max(n_total, 1), risk=wrong[last] / acc[last]))


def own_pick(res, k_goldens, thresholds=None, tau=None):
    """Several goldens per part: for every (method, test image) the method keeps the golden whose attempt has its highest
    decision score (the ground truth plays no part), then accepts or rejects that attempt as usual. k_goldens: how many
    goldens (the first k by name, per region). Returns the picked rows with their outcome."""
    rows = []
    for region, g in res.groupby("region"):
        names = sorted(g["golden"].unique(), key=_natural)
        use = g[g["golden"].isin(names[:k_goldens])].copy()
        use["_s"] = use["score"].fillna(-np.inf)
        use["_g"] = use["golden"].map({n: i for i, n in enumerate(names)})
        rows.append(use.sort_values(["method", "test", "_s", "_g"], ascending=[True, True, False, True])
                       .groupby(["method", "test"], sort=False).head(1))
    picked = pd.concat(rows) if rows else res.iloc[:0]
    t = picked["tau_px"] if tau is None else tau
    picked = picked.assign(outcome_pick=classify(decide(picked, thresholds).to_numpy(), picked["err_mean_px"], t).to_numpy())
    return picked


def _natural(s):
    import re
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", str(s))]


def _q(s, q):
    s = s.dropna()
    return float(s.quantile(q)) if len(s) else float("nan")


def md_table(df, fmt="{:.3f}"):
    if df is None or df.empty:
        return "(none)\n"
    cols = list(df.columns)
    out = ["| " + " | ".join(str(c) for c in cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for _, r in df.astype(object).iterrows():        # object: whole numbers stay whole
        cells = []
        for c in cols:
            v = r[c]
            if isinstance(v, (float, np.floating)):
                cells.append("" if not np.isfinite(v) else fmt.format(v))
            else:
                cells.append(str(v))
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------------------------------------------------------------------
# tables

def method_table(res, by=("method",)):
    rows = []
    order = list(dict.fromkeys(res["method"]))
    for key, g in res.groupby(list(by), sort=False):
        key = key if isinstance(key, tuple) else (key,)
        acc = g[g.outcome.isin(["correct", "silent_wrong"])]
        r = dict(zip(by, key))
        r.update(family=g["family"].iloc[0], n_pairs=len(g), accepted=float(g.accepted.mean()))
        for o in OUTCOMES:
            r[o] = float((g.outcome == o).mean())
        if "sym_rot_deg" in g and (g.get("sym_order", pd.Series([1])).fillna(1) > 1).any():
            r["correct_via_symmetry"] = float(((g.outcome == "correct") & (g.sym_rot_deg.fillna(0) != 0)).mean())
        r.update(err_median_accepted_px=_q(acc.err_mean_px, 0.5), err_p95_accepted_px=_q(acc.err_mean_px, 0.95),
                 err_median_all_px=_q(g.err_mean_px, 0.5), excess_median_px=_q(acc.excess_px, 0.5),
                 rot_err_median_abs_deg=_q(acc.err_rot_deg.abs(), 0.5), latency_median_ms=_q(g.latency_ms, 0.5))
        rows.append(r)
    t = pd.DataFrame(rows)
    if len(t):
        t["_o"] = t["method"].map({m: i for i, m in enumerate(order)})
        t = t.sort_values(list(by[:-1]) + ["_o"] if len(by) > 1 else ["_o"]).drop(columns="_o").reset_index(drop=True)
    return t


def tau_sweep(res, taus):
    """Correct rate per method at several tau values (same poses, same decisions; only the tolerance changes)."""
    rows = []
    for m in dict.fromkeys(res["method"]):
        g = res[res.method == m]
        r = {"method": m}
        for t in taus:
            r[f"<= {t:g} px"] = float((classify(g.accepted.to_numpy(), g.err_mean_px, t) == "correct").mean())
        rows.append(r)
    return pd.DataFrame(rows)


def sweep_taus(tau, floor_values):
    ts = {1.0, 2.0, 3.0, 5.0, 10.0, 20.0}
    if np.isfinite(tau):
        ts.add(float(tau))
        ts.add(float(2 * tau))
    fl = floor_values.dropna() if hasattr(floor_values, "dropna") else pd.Series([], dtype=float)
    if len(fl):
        ts.add(round(2 * float(fl.quantile(0.95)), 1))
    return sorted(ts)


def confidence_table(res):
    """Per method, without any threshold: how well its own decision score separates right poses from wrong ones."""
    rows, curves = [], []
    for m in dict.fromkeys(res["method"]):
        g = res[res.method == m]
        if m == "identity":
            continue
        right = (g.err_mean_px <= g.tau_px).to_numpy()
        rc = risk_coverage(g.score.where(g.checks_ok_b), right, len(g))
        ok = rc[rc.risk <= RISK]
        half = rc[rc.coverage >= 0.5]
        rows.append(dict(method=m, auroc=auroc(g.score, right), right_pose_any_decision=float(right.mean()),
                         coverage_at_5pct_risk=float(ok.coverage.max()) if len(ok) else 0.0,
                         risk_at_50pct_coverage=float(half.risk.iloc[0]) if len(half) else float("nan")))
        curves.append(rc.assign(method=m))
    return pd.DataFrame(rows), (pd.concat(curves, ignore_index=True) if curves else pd.DataFrame())


def goldens_table(res, thresholds=None):
    """Several goldens: each golden alone, the method's own pick among the first k, and the best possible pick."""
    n_g = int(res.groupby("region")["golden"].nunique().max()) if len(res) else 0
    if n_g < 2:
        return pd.DataFrame()
    rows = []
    for m in dict.fromkeys(res["method"]):
        if m == "identity":
            continue
        g = res[res.method == m]
        r = {"method": m}
        for region, gg in g.groupby("region"):
            for i, name in enumerate(sorted(gg["golden"].unique(), key=_natural)):
                r[f"golden {i + 1} alone"] = float((gg[gg.golden == name].outcome == "correct").mean())
        for k in range(1, n_g + 1):
            pk = own_pick(g, k, thresholds)
            r[f"own pick of {k}: correct"] = float((pk.outcome_pick == "correct").mean())
            r[f"own pick of {k}: silent_wrong"] = float((pk.outcome_pick == "silent_wrong").mean())
        for k in range(2, n_g + 1):
            names = {reg: sorted(x["golden"].unique(), key=_natural)[:k] for reg, x in g.groupby("region")}
            sub = g[[gol in names[reg] for reg, gol in zip(g.region, g.golden)]]
            r[f"best possible of {k}"] = float(sub.groupby("test").outcome.apply(lambda s: (s == "correct").any()).mean())
        rows.append(r)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------------------------------------------------------
# the report

def summarize(folder, tau_px=None, write=True, thresholds=None):
    """Writes <folder>/summary (summary_tau<k> with tau_px, summary_calibrated with thresholds) and returns the report."""
    res = pd.read_csv(os.path.join(folder, "results.csv"))
    pairs = pd.read_csv(os.path.join(folder, "pairs.csv")).drop_duplicates("pair_id", keep="last")
    man = {}
    if os.path.exists(os.path.join(folder, "manifest.json")):
        man = json.load(open(os.path.join(folder, "manifest.json"), encoding="utf-8"))
    thr, thr_note = None, ""
    if thresholds:
        tj = json.load(open(thresholds, encoding="utf-8")) if isinstance(thresholds, str) else thresholds
        thr = tj.get("methods", tj)
        thr_note = (f"Acceptance thresholds calibrated on {tj.get('calibration_run', 'held-out images')} "
                    f"({tj.get('criterion', '')}); methods without one keep their own rule.\n")
    tau = float(tau_px) if tau_px is not None else (float(res.tau_px.median()) if len(res) else float("nan"))
    if thr and isinstance(thresholds, str):
        tj_tau = json.load(open(thresholds, encoding="utf-8")).get("tau_px")
        if tj_tau is not None and abs(float(tj_tau) - tau) > 1e-9:
            thr_note += f"WARNING: the thresholds were calibrated with tau = {tj_tau} px, this summary uses {tau:g} px.\n"
    if len(res):
        res = prepare(res)
        res["tau_px"] = tau                        # the tolerance these outcomes are judged with
        res["accepted"] = decide(res, thr)
        res["outcome"] = classify(res["accepted"].to_numpy(), res["err_mean_px"], tau).to_numpy()
    ok_pairs = pairs[pairs.status == "ok"]
    bad_pairs = pairs[pairs.status != "ok"]

    mt = method_table(res) if len(res) else pd.DataFrame()
    gt_ = method_table(res, ("group", "method")) if len(res) else pd.DataFrame()
    fl = ok_pairs["gt_floor_mean_px"].dropna()
    floor = pd.DataFrame([dict(pairs=len(ok_pairs), pairs_with_floor=len(fl), floor_median_px=_q(fl, 0.5), floor_p95_px=_q(fl, 0.95),
                               floor_max_px=float(fl.max()) if len(fl) else float("nan"),
                               gt_points_median=float(ok_pairs.n_points.median()) if len(ok_pairs) else float("nan"))])
    per_golden = pd.DataFrame()
    if ok_pairs["group"].nunique() > 1:
        per_golden = (ok_pairs.groupby("group", sort=True)["gt_floor_mean_px"]
                      .agg(pairs="count", floor_median_px="median", floor_p95_px=lambda s: s.quantile(0.95), floor_max_px="max")
                      .reset_index())
    pose = pd.DataFrame([dict(rot_abs_median_deg=_q(ok_pairs.gt_rot_deg.abs(), 0.5),
                              rot_abs_max_deg=float(ok_pairs.gt_rot_deg.abs().max()) if len(ok_pairs) else float("nan"),
                              shift_median_px=_q(ok_pairs.gt_shift_px, 0.5),
                              shift_max_px=float(ok_pairs.gt_shift_px.max()) if len(ok_pairs) else float("nan"),
                              scale_dev_max_pct=float((100 * (ok_pairs.gt_scale - 1).abs()).max()) if len(ok_pairs) else float("nan"))])
    conf_t, curves = confidence_table(res) if len(res) else (pd.DataFrame(), pd.DataFrame())
    gold_t = goldens_table(res, thr) if len(res) else pd.DataFrame()
    sym_parts = sorted(set(res.loc[res.sym_order.fillna(1) > 1, "region"])) if len(res) and "sym_order" in res else []

    lines = ["# Annotated-pair evaluation: summary\n",
             f"Pairs evaluated: {len(ok_pairs)}" + (f"; pairs that could not be read: {len(bad_pairs)}" if len(bad_pairs) else "") +
             f". tau = {tau:g} px (original image pixels, on the mean point error). Working long side: "
             f"{(man.get('config') or {}).get('work_long_side') or 'native'}.\n",
             thr_note,
             (f"Symmetry-aware scoring for: {', '.join(sym_parts)} (a pose counts against the nearest of the part's equivalent "
              "orientations; correct_via_symmetry = share of pairs that are correct only because of that; err_mean_strict_px in "
              "results.csv is the error without it).\n" if sym_parts else ""),
             "Unavailable methods: " + (", ".join(f"{k} ({v})" for k, v in (man.get("unavailable") or {}).items()) or "none") + "\n",
             "## 1. The annotation floor (read this first)\n",
             "Mean point error of the similarity that best fits the clicked points themselves: click scatter plus the real shape "
             "difference between the two pieces. No similarity-model method can be expected to do better on a pair; differences "
             "between methods smaller than it are not interpretable. tau should be clearly above floor_p95.\n", md_table(floor, "{:.2f}"),
             ("\nThe same, per golden. Each pair's floor contains the clicks and the shape of BOTH images, so every golden brings "
              "its own floor; the pooled p95 above therefore changes with the set of goldens. Fix tau once per part and keep it "
              "for every golden condition.\n\n" + md_table(per_golden, "{:.2f}")) if len(per_golden) else "",
             "\nThe poses in the data (from the ground-truth fit):\n\n", md_table(pose, "{:.2f}"),
             "## 2. Per method (all pairs)\n",
             "Rates are fractions of pairs. err_*_accepted: mean point error over the poses the method accepted; err_median_all: "
             "over every pose it returned (also rejected ones); excess = error minus that pair's floor. `identity` is the "
             "reference line: its error is the raw misalignment.\n", md_table(mt),
             "## 2b. Correct rate at other tolerances\n",
             "The same poses and the same accept/reject decisions, judged with a range of tau values (the headline tau is the one "
             "fixed before the run). A method whose rate only rises at tolerances far above the floor is coarse, not wrong.\n",
             md_table(tau_sweep(res, sweep_taus(tau, fl))) if len(res) else "(none)\n",
             "## 3. Does the method's own score tell right from wrong?\n",
             "Without any threshold. auroc: how often a right pose (error <= tau) scores higher than a wrong one, over the poses "
             "the method returned (0.5 = no better than chance; blank = fewer than 3 right or 3 wrong poses). "
             "right_pose_any_decision: share of pairs whose pose is right, whatever the method decided. "
             f"coverage_at_5pct_risk: the largest share of pairs a threshold on the score can accept while at most "
             f"{RISK:.0%} of the accepted poses are wrong (0 = no threshold achieves it). risk_at_50pct_coverage: the share of "
             "wrong poses among the accepted ones when the threshold accepts half of the pairs. The full curves are in "
             "risk_coverage.csv.\n", md_table(conf_t),
             ]
    if len(gold_t):
        lines += ["## 4. Several goldens\n",
                  "golden i alone: correct rate with that golden only. own pick of k: the method is given the first k goldens, keeps "
                  "the one its own decision score likes best (the ground truth plays no part), and accepts or rejects that pose as "
                  "usual: what a system that stores k goldens would get. best possible of k: share of test images for which at least "
                  "one of the k goldens gives a correct pose (an upper bound no method can claim).\n", md_table(gold_t)]
    lines += ["## 5. Per group and method\n",
              md_table(gt_[["group", "method", "n_pairs", "correct", "silent_wrong", "lost", "rejected", "no_pose",
                            "err_median_accepted_px", "latency_median_ms"]] if len(gt_) else gt_)]
    if len(bad_pairs):
        lines += ["## 6. Pairs that could not be evaluated\n", md_table(bad_pairs[["pair_id", "status"]])]
    report = "\n".join(lines)
    if write:
        name = ("summary" if tau_px is None else f"summary_tau{tau:g}") + ("_calibrated" if thr else "")
        out = os.path.join(folder, name)
        os.makedirs(out, exist_ok=True)
        mt.to_csv(os.path.join(out, "summary_methods.csv"), index=False)
        if len(res):
            tau_sweep(res, sweep_taus(tau, fl)).to_csv(os.path.join(out, "tau_sweep.csv"), index=False)
        gt_.to_csv(os.path.join(out, "summary_groups.csv"), index=False)
        floor.to_csv(os.path.join(out, "floor.csv"), index=False)
        if len(per_golden):
            per_golden.to_csv(os.path.join(out, "floor_per_group.csv"), index=False)
        if len(conf_t):
            conf_t.to_csv(os.path.join(out, "confidence.csv"), index=False)
            curves.to_csv(os.path.join(out, "risk_coverage.csv"), index=False)
        if len(gold_t):
            gold_t.to_csv(os.path.join(out, "goldens.csv"), index=False)
        keep = [c for c in res.columns if c not in ("success_b", "checks_ok_b", "has_pose")]
        res[keep].to_csv(os.path.join(out, "results_classified.csv"), index=False)
        with open(os.path.join(out, "SUMMARY.md"), "w", encoding="utf-8") as f:
            f.write(report)
    return report


def main(argv=None):
    ap = argparse.ArgumentParser(description="Summarise a run (optionally with another tau or calibrated thresholds).")
    ap.add_argument("folder")
    ap.add_argument("--tau-px", type=float, default=None)
    ap.add_argument("--thresholds", default=None, help="thresholds.json from python -m inspalign.calibrate fit")
    a = ap.parse_args(argv)
    print(summarize(a.folder, a.tau_px, thresholds=a.thresholds))


if __name__ == "__main__":
    main()
