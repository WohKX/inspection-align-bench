"""Figures and tables across the parts of a benchmark, for the README and a post.

    python -m inspalign.report results/pcb results/metal_nut results/screw results/chewing_gum results/fryum \\
           --out report --show-images pcb,chewing_gum,fryum

Each argument is one part's evaluate.py output folder. If <run>_calib/thresholds.json exists (inspalign/calibrate.py), the
calibrated decisions are reported next to the methods' own ones. Writes into --out:

    REPORT.md                 the tables behind every figure (also the accessible version of the figures)
    fig1_correct.png          correct rate, method x part (default decisions; fig1b with calibrated thresholds)
    fig2_outcomes.png         what happened on every pair: correct / right pose rejected / declined / silent wrong, per part
    fig3_confidence.png       how well each method's own score tells right from wrong (AUROC, one dot per part)
    fig4_rotation.png         right-pose rate against the pair's rotation, each method with and without rotation search
    fig5_goldens.png          several goldens: best possible pick vs the method's own pick, and its silent-wrong rate
    carousel.pdf              the figures as square pages (a document post)
    examples/                 a few alignment pictures, ONLY from the parts named in --show-images (licence: see README)

Every number is recomputed from results.csv; nothing is typed in by hand.
"""
import argparse
import json
import os
import shutil

import numpy as np
import pandas as pd

from . import gtsummary as GS

# colours: validated with the dataviz palette checks (light surface #fcfcfb)
SURFACE, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]                                  # blue, orange, aqua: safe as any 3 together
OUTCOME_COLORS = {"correct": "#008300", "lost": "#eda100", "declined": "#6da7ec", "silent_wrong": "#e34948"}
OUTCOME_LABELS = {"correct": "Correct", "lost": "Right pose, rejected by the method", "declined": "Declined (rejected or no pose)",
                  "silent_wrong": "Silent wrong: wrong pose accepted"}
BLUE_RAMP = ["#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7", "#3987e5", "#2a78d6", "#256abf", "#1c5cab",
             "#184f95", "#104281", "#0d366b"]
NAMES = {"phase_correlation": "Phase correlation", "sift_ransac": "SIFT + RANSAC", "lightglue_disk": "LightGlue (DISK)",
         "lightglue_sift": "LightGlue (SIFT)", "contour_shape_match": "Contour shape match"}
ROT_BINS, ROT_LABELS = [0, 5, 15, 45, 181], ["0-5", "5-15", "15-45", "45-180"]


SHORT = {"phase_correlation": "Phase corr.", "sift_ransac": "SIFT", "lightglue_disk": "LightGlue-DISK",
         "lightglue_sift": "LightGlue-SIFT", "contour_shape_match": "Contour"}


def nice(m):
    base = m[:-4] if m.endswith("+rot") else m
    return NAMES.get(base, base) + (" + rotation search" if m.endswith("+rot") else "")


def short(m):
    """Compact label for figure axes, e.g. 'LightGlue-SIFT + rot.' (rotation search)."""
    base = m[:-4] if m.endswith("+rot") else m
    return SHORT.get(base, base) + (" + rot." if m.endswith("+rot") else "")


def label_of(run, labels):
    key = os.path.basename(os.path.normpath(run))
    return labels.get(key, key.replace("_", " "))


def load(runs, labels, thresholds=None):
    frames, thr = [], {}
    for run in runs:
        res = GS.prepare(pd.read_csv(os.path.join(run, "results.csv")))
        part = label_of(run, labels)
        res["part"] = part
        res["run"] = run
        key = os.path.basename(os.path.normpath(run))
        tpath = (thresholds or {}).get(key) or os.path.normpath(run) + "_calib/thresholds.json"
        if os.path.isfile(tpath):
            thr[part] = json.load(open(tpath, encoding="utf-8"))["methods"]
        frames.append(res)
    res = pd.concat(frames, ignore_index=True)
    res = res[res.method != "identity"]
    res["right"] = res.err_mean_px <= res.tau_px
    res["outcome_default"] = GS.classify(res.success_b.to_numpy(), res.err_mean_px, res.tau_px).to_numpy()
    if thr:
        cal = []
        for part, g in res.groupby("part", sort=False):
            acc = GS.decide(g, thr.get(part))
            cal.append(pd.Series(GS.classify(acc.to_numpy(), g.err_mean_px, g.tau_px).to_numpy(), index=g.index))
        res["outcome_cal"] = pd.concat(cal)
    return res, thr


def _style(plt):
    plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Segoe UI", "Helvetica", "Arial", "DejaVu Sans"],
                         "font.size": 10, "text.color": INK, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
                         "axes.edgecolor": AXIS, "axes.linewidth": 0.6, "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
                         "savefig.facecolor": SURFACE, "axes.titleweight": "bold", "axes.titlesize": 11})


def _clean(ax, grid_axis="x"):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis=grid_axis, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)


def _title(fig, title, subtitle):
    fig.text(0.04, 0.965, title, fontsize=15, fontweight="bold", color=INK, va="top")
    fig.text(0.04, 0.925, subtitle, fontsize=10, color=INK2, va="top", wrap=True)


def _grid(fig, n, cols=2, top=0.80, bottom=0.15, left=0.1, right=0.97, hgap=0.1, vgap=0.085):
    """n panel axes in a grid under the title block, row by row."""
    rows_ = int(np.ceil(n / cols))
    w = (right - left - hgap * (cols - 1)) / cols
    h = (top - bottom - vgap * (rows_ - 1)) / rows_
    return [fig.add_axes([left + (k % cols) * (w + hgap), top - (k // cols + 1) * h - (k // cols) * vgap, w, h]) for k in range(n)]


def fig_correct(res, outcome_col, path, title, subtitle):
    import matplotlib.pyplot as plt
    parts = list(dict.fromkeys(res.part))
    methods = list(dict.fromkeys(res.method))
    t = res.groupby(["method", "part"])[outcome_col].apply(lambda s: 100 * (s == "correct").mean()).unstack("part").reindex(index=methods, columns=parts)
    fig = plt.figure(figsize=(6, 6), dpi=200)
    _title(fig, title, subtitle)
    ax = fig.add_axes([0.36, 0.06, 0.6, 0.72])
    v = t.to_numpy()
    idx = np.clip((v / 100 * (len(BLUE_RAMP) - 1)).round().astype(int), 0, len(BLUE_RAMP) - 1)
    for i in range(v.shape[0]):
        for j in range(v.shape[1]):
            if not np.isfinite(v[i, j]):
                continue
            col = BLUE_RAMP[idx[i, j]]
            ax.add_patch(plt.Rectangle((j + 0.03, i + 0.03), 0.94, 0.94, color=col, linewidth=0))
            dark = idx[i, j] >= 6
            ax.text(j + 0.5, i + 0.5, f"{v[i, j]:.0f}%", ha="center", va="center", fontsize=10,
                    color="#ffffff" if dark else INK, fontweight="bold" if v[i, j] == np.nanmax(v[:, j]) else "normal")
    ax.set_xlim(0, len(parts)); ax.set_ylim(len(methods), 0)
    ax.set_xticks(np.arange(len(parts)) + 0.5, [p.replace(" ", "\n", 1) if len(p) > 9 else p for p in parts]); ax.set_yticks(np.arange(len(methods)) + 0.5, [short(m) for m in methods])
    ax.xaxis.tick_top()
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0)
    fig.savefig(path)
    plt.close(fig)
    return t


def fig_outcomes(res, outcome_col, path):
    import matplotlib.pyplot as plt
    parts = list(dict.fromkeys(res.part))
    methods = [m for m in dict.fromkeys(res.method) if not m.endswith("+rot")]   # the rotation search has its own figure
    o = res[outcome_col].replace({"rejected": "declined", "no_pose": "declined"})
    cats = ["correct", "lost", "declined", "silent_wrong"]
    fig = plt.figure(figsize=(6, 6), dpi=200)
    _title(fig, "What happened on every pair", "Share of pairs per method (as it is, own thresholds). Red is the dangerous "
           "outcome: a wrong pose the method accepted.")
    n = len(parts)
    top, bottom, gap = 0.80, 0.13, 0.045
    h = (top - bottom - gap * (n - 1)) / n
    tab = {}
    for k, part in enumerate(parts):
        ax = fig.add_axes([0.36, top - (k + 1) * h - k * gap, 0.6, h])
        g = res[res.part == part]
        left = np.zeros(len(methods))
        for c in cats:
            share = np.array([100 * (o[g.index][g.method == m] == c).mean() for m in methods])
            tab[(part, c)] = share
            ax.barh(np.arange(len(methods)), share, left=left, height=0.62, color=OUTCOME_COLORS[c], edgecolor=SURFACE, linewidth=0.72)
            left += share
        ax.set_xlim(0, 100); ax.set_ylim(len(methods) - 0.5, -0.5)
        ax.set_yticks(np.arange(len(methods)), [short(m) for m in methods], fontsize=7)
        ax.set_xticks([0, 25, 50, 75, 100], ["0", "25", "50", "75", "100%"] if k == n - 1 else [""] * 5, fontsize=7)
        ax.text(-0.42, 1.04, part, transform=ax.transAxes, fontsize=9, fontweight="bold", va="bottom", ha="left")
        _clean(ax)
        ax.spines["left"].set_visible(False)
    handles = [plt.Rectangle((0, 0), 1, 1, color=OUTCOME_COLORS[c]) for c in cats]
    fig.legend(handles, [OUTCOME_LABELS[c] for c in cats], loc="lower left", bbox_to_anchor=(0.03, 0.005), ncol=2, frameon=False, fontsize=7.5)
    fig.savefig(path)
    plt.close(fig)


def confidence(res):
    rows = []
    for (part, m), g in res.groupby(["part", "method"], sort=False):
        rows.append(dict(part=part, method=m, auroc=GS.auroc(g.score.where(g.checks_ok_b), g.right.to_numpy()),
                         right_pose=100 * g.right.mean()))
    return pd.DataFrame(rows)


def fig_confidence(conf, path):
    import matplotlib.pyplot as plt
    methods = list(dict.fromkeys(conf.method))
    fig = plt.figure(figsize=(6, 6), dpi=200)
    _title(fig, "Does a method know when it is right?", "AUROC of each method's own score: right poses vs wrong ones. "
           "Grey dots: one per part; bar: the median. 0.5 = no better than a coin.")
    ax = fig.add_axes([0.36, 0.1, 0.58, 0.74])
    for i, m in enumerate(methods):
        v = conf[conf.method == m].auroc.dropna()
        ax.scatter(v, np.full(len(v), i), s=28, color=MUTED, edgecolor=SURFACE, linewidth=1.0, zorder=3)
        if len(v):
            med = float(v.median())
            ax.plot([med, med], [i - 0.28, i + 0.28], color=SERIES[0], linewidth=2.5, solid_capstyle="round", zorder=4)
            ax.text(1.02, i, f"{med:.2f}", va="center", fontsize=8, color=INK2, transform=ax.get_yaxis_transform())
    ax.axvline(0.5, color=AXIS, linewidth=0.8, zorder=1)
    ax.text(0.5, -0.75, "chance", ha="center", fontsize=7, color=MUTED)
    ax.set_xlim(0, 1); ax.set_ylim(len(methods) - 0.5, -0.9)
    ax.set_yticks(np.arange(len(methods)), [short(m) for m in methods], fontsize=8)
    ax.set_xlabel("AUROC (1 = its score always ranks a right pose above a wrong one)", fontsize=8)
    _clean(ax)
    ax.spines["left"].set_visible(False)
    fig.savefig(path)
    plt.close(fig)


def rotation(res):
    order = list(dict.fromkeys(res.method))
    r = res.assign(rotbin=pd.cut(res.gt_rot_deg.abs(), ROT_BINS, labels=ROT_LABELS, right=False))
    return r.groupby(["method", "rotbin"], observed=False).right.agg(lambda s: 100 * s.mean() if len(s) else np.nan).unstack("rotbin").reindex(order), \
        r[r.method == r.method.iloc[0]].groupby("rotbin", observed=False).size()


def fig_rotation(rt, counts, path):
    import matplotlib.pyplot as plt
    bases = list(dict.fromkeys(m[:-4] if m.endswith("+rot") else m for m in rt.index))
    fig = plt.figure(figsize=(6, 6), dpi=200)
    _title(fig, "Rotation decides", "Share of pairs whose pose is right (whatever the method decided), by how far the part is "
           "turned. Blue: the method as it is; orange: with rotation search.")
    x = np.arange(len(ROT_LABELS))
    for ax, b in zip(_grid(fig, len(bases)), bases):
        for j, (m, col) in enumerate(((b, SERIES[0]), (b + "+rot", SERIES[1]))):
            if m in rt.index:
                ax.plot(x, rt.loc[m].to_numpy(), color=col, linewidth=2, marker="o", markersize=4.5, markeredgecolor=SURFACE,
                        markeredgewidth=1.0, solid_capstyle="round")
        ax.set_title(nice(b), fontsize=9, loc="left")
        ax.set_ylim(0, 100); ax.set_yticks([0, 50, 100], ["0", "50", "100%"], fontsize=7)
        ax.set_xticks(x, [f"{l}°" for l in ROT_LABELS], fontsize=7)
        _clean(ax, "y")
    fig.text(0.04, 0.012, "Pairs per bin (all parts): " + ", ".join(f"{l}°: {int(c)}" for l, c in zip(ROT_LABELS, counts.to_numpy())),
             fontsize=7.5, color=MUTED)
    handles = [plt.Line2D([0], [0], color=SERIES[0], linewidth=2), plt.Line2D([0], [0], color=SERIES[1], linewidth=2)]
    fig.legend(handles, ["as it is", "with rotation search"], loc="lower left", bbox_to_anchor=(0.03, 0.035), ncol=2, frameon=False, fontsize=8)
    fig.savefig(path)
    plt.close(fig)


def goldens(res):
    rows = []
    n_g = int(res.groupby("part").golden.nunique().max())
    for m in dict.fromkeys(res.method):
        if m.endswith("+rot"):
            continue
        g = res[res.method == m]
        for k in range(1, n_g + 1):
            picks, best = [], []
            for part, gp in g.groupby("part"):
                gp = gp.assign(outcome=gp.outcome_default)
                picks.append(GS.own_pick(gp, k))
                names = {reg: sorted(x.golden.unique(), key=GS._natural)[:k] for reg, x in gp.groupby("region")}
                sub = gp[[gol in names[reg] for reg, gol in zip(gp.region, gp.golden)]]
                best.append(sub.groupby("test").outcome.apply(lambda s: (s == "correct").any()))
            pk = pd.concat(picks)
            rows.append(dict(method=m, k=k, best_possible=100 * pd.concat(best).mean(),
                             own_pick_correct=100 * (pk.outcome_pick == "correct").mean(),
                             own_pick_silent_wrong=100 * (pk.outcome_pick == "silent_wrong").mean()))
    return pd.DataFrame(rows)


def fig_goldens(gd, path):
    import matplotlib.pyplot as plt
    methods = list(dict.fromkeys(gd.method))
    fig = plt.figure(figsize=(6, 6), dpi=200)
    _title(fig, "More goldens raise the ceiling, not the result", "All parts pooled. The method picks the golden by its own "
           "score; the best possible pick needs the answer key.")
    for ax, m in zip(_grid(fig, len(methods)), methods):
        g = gd[gd.method == m]
        for col, c in zip(("best_possible", "own_pick_correct", "own_pick_silent_wrong"), SERIES):
            ax.plot(g.k, g[col], color=c, linewidth=2, marker="o", markersize=4.5, markeredgecolor=SURFACE, markeredgewidth=1.0)
        ax.set_title(nice(m), fontsize=9, loc="left")
        ax.set_ylim(0, 100); ax.set_yticks([0, 50, 100], ["0", "50", "100%"], fontsize=7)
        ax.set_xticks(sorted(g.k.unique()), [f"{k} golden" + ("s" if k > 1 else "") for k in sorted(g.k.unique())], fontsize=7)
        _clean(ax, "y")
    handles = [plt.Line2D([0], [0], color=c, linewidth=2) for c in SERIES]
    fig.legend(handles, ["best possible", "own pick: correct", "own pick: silent wrong"], loc="lower left", bbox_to_anchor=(0.03, 0.005),
               ncol=3, frameon=False, fontsize=8)
    fig.savefig(path)
    plt.close(fig)


def examples(res, out, show):
    """Copy a few existing overlay pictures, only from the parts the licence allows to show."""
    dst = os.path.join(out, "examples")
    copied = []
    for part, g in res[res.part.isin(show)].groupby("part"):
        for outcome in ("silent_wrong", "lost"):
            cand = g[g.outcome_default == outcome].sort_values("err_mean_px", ascending=(outcome == "lost"))
            for r in cand.itertuples():
                src = os.path.join(r.run, "overlays", _safe(f"{r.pair_id.replace('/', '__')}__{r.method}") + ".png")
                if os.path.isfile(src):
                    os.makedirs(dst, exist_ok=True)
                    name = f"{part.replace(' ', '_')}__{outcome}__{os.path.basename(src)}"
                    shutil.copy2(src, os.path.join(dst, name))
                    copied.append(name)
                    break
    return copied


def _safe(s):
    return "".join(c if c.isalnum() or c in "-_." else "_" for c in s)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("runs", nargs="+", help="one evaluate.py output folder per part")
    ap.add_argument("--out", default="report")
    ap.add_argument("--labels", default="", help="folder=Label pairs, e.g. pcb=PCB,metal_nut=Metal nut")
    ap.add_argument("--show-images", default="", help="parts (folder names) whose pictures may be shown, e.g. pcb,chewing_gum,fryum")
    ap.add_argument("--thresholds", default="", help="folder=thresholds.json pairs, when the calibration run is not <run>_calib, "
                                                     "e.g. pcb_check_3g=results/pcb_calib/thresholds.json")
    a = ap.parse_args(argv)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    _style(plt)
    labels = dict(kv.split("=", 1) for kv in a.labels.split(",") if "=" in kv)
    os.makedirs(a.out, exist_ok=True)
    tmap = dict(kv.split("=", 1) for kv in a.thresholds.split(",") if "=" in kv)
    res, thr = load(a.runs, labels, tmap)
    figs = []
    p = os.path.join(a.out, "fig1_correct.png")
    t1 = fig_correct(res, "outcome_default", p, "No method wins everywhere",
                     "Correct rate: the pose is accepted by the method and within the part's tolerance. Bold: best in the part.")
    figs.append(p)
    t1b = None
    if "outcome_cal" in res:
        p = os.path.join(a.out, "fig1b_correct_calibrated.png")
        t1b = fig_correct(res, "outcome_cal", p, "After calibrating the thresholds",
                          "The same poses, accepted by thresholds set on held-out images (at most 5% wrong among the accepted).")
        figs.append(p)
    p = os.path.join(a.out, "fig2_outcomes.png"); fig_outcomes(res, "outcome_default", p); figs.append(p)
    conf = confidence(res)
    p = os.path.join(a.out, "fig3_confidence.png"); fig_confidence(conf, p); figs.append(p)
    rt, counts = rotation(res)
    p = os.path.join(a.out, "fig4_rotation.png"); fig_rotation(rt, counts, p); figs.append(p)
    gd = goldens(res) if res.groupby("part").golden.nunique().max() > 1 else pd.DataFrame()
    if len(gd):
        p = os.path.join(a.out, "fig5_goldens.png"); fig_goldens(gd, p); figs.append(p)
    with PdfPages(os.path.join(a.out, "carousel.pdf")) as pdf:
        for f in figs:
            img = plt.imread(f)
            fig = plt.figure(figsize=(6, 6), dpi=200)
            fig.figimage(img, resize=True)
            pdf.savefig(fig)
            plt.close(fig)
    shown = examples(res, a.out, [label_of(s, labels) for s in a.show_images.split(",") if s])
    ex_dir = os.path.join(a.out, "examples")
    if not shown and os.path.isdir(ex_dir):            # re-run without the overlays (e.g. from published CSVs): keep the pictures
        shown = sorted(f for f in os.listdir(ex_dir) if f.lower().endswith(".png"))

    sw = res.groupby(["method", "part"]).outcome_default.apply(lambda s: 100 * (s == "silent_wrong").mean()).unstack("part")
    lat = res.groupby(["method", "part"]).latency_ms.median().unstack("part")
    au = conf.pivot(index="method", columns="part", values="auroc")
    order = list(dict.fromkeys(res.method)); parts = list(dict.fromkeys(res.part))
    fmt = lambda df, f="{:.0f}": GS.md_table(df.reindex(index=order, columns=parts).rename(index=nice).reset_index().rename(columns={"method": "method"}), f)
    md = ["# Results\n", f"Parts: {', '.join(parts)}. Pairs per part: " + ", ".join(f"{p_} {res[(res.part == p_)].pair_id.nunique()}" for p_ in parts) +
          ". Each part is judged with its own tolerance (2 x the 95th percentile of its annotation floor).\n",
          "## Correct rate (%), the methods' own decisions\n", fmt(t1)]
    if t1b is not None:
        md += ["## Correct rate (%), thresholds calibrated on held-out images\n", fmt(t1b)]
    if thr:
        crow = []
        for part, mt in thr.items():
            for m, e in mt.items():
                n_acc = int(round(e.get("coverage", 0) * e.get("pairs", 0)))
                crow.append(dict(part=part, method=nice(m), threshold="accept none" if e.get("accept_none") else f"{e['threshold']:g}",
                                 calibration_pairs=e.get("pairs"), right_poses=e.get("right_poses"), accepted=n_acc,
                                 note="rests on fewer than 5 accepted poses" if 0 < n_acc < 5 else ""))
        md += ["## Calibrated thresholds\n", "Fitted on held-out images (inspalign/calibrate.py). accepted: calibration pairs the "
               "threshold accepts; a threshold resting on fewer than 5 of them is marked.\n", GS.md_table(pd.DataFrame(crow))]
    md += ["## Silent wrong (%): wrong poses the method accepted\n", fmt(sw),
           "## AUROC of the method's own score (right vs wrong poses)\n", fmt(au, "{:.2f}"),
           "## Right pose (%) by rotation of the part, all parts pooled\n", GS.md_table(rt.rename(index=nice).reset_index(), "{:.0f}")]
    if len(gd):
        md += ["## Several goldens, all parts pooled (%)\n", GS.md_table(gd.assign(method=gd.method.map(nice)), "{:.0f}")]
    md += ["## Median time per pair (ms)\n", fmt(lat), "## Figures\n"] + [f"![{os.path.basename(f)}]({os.path.basename(f)})\n" for f in figs]
    if shown:
        md += ["## Example pictures\n"] + [f"![{s}](examples/{s})\n" for s in shown]
    with open(os.path.join(a.out, "REPORT.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    print(f"wrote {a.out}: {len(figs)} figures, carousel.pdf, REPORT.md" + (f", {len(shown)} example pictures" if shown else ""))


if __name__ == "__main__":
    main()
