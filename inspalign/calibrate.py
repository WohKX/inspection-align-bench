"""Calibrating every method's accept / reject threshold on held-out images (never on the test images).

Each method accepts a pose when its decision score reaches a threshold (inlier count >= 6, correlation peak >= 0.1, edge
score >= 0.5). Those defaults are generic; on a given part one can be far too strict (the shape method's right poses on the
PCB all scored 0.21-0.37, under its 0.5) or far too lax (a matcher that accepts wrong poses). Calibration sets each threshold
from images that are NOT in the test set, with one rule for every method, decided before looking at test results.

Three steps per part (DATA_FORMAT.md, section 6, has the details):

  1. Annotate 10 extra images of the part (the next ones in file order after the test images) in the landmark picker, with
     golden 000 loaded as the golden, and save the picker's landmarks.json. Then build the calibration folder:

        python -m inspalign.calibrate store --test data/pcb --export path/to/picker/landmarks.json \\
               --images path/to/the/10/images --out data/pcb_calib

     It takes the goldens (images and points) from the test folder, the 10 images' points from the export, refuses any image
     that is also a test image or a golden, and writes data/pcb_calib.

  2. Run the methods on it with the part's config, exactly as on the test set:

        python evaluate.py --config configs/parts/pcb.yaml --data data/pcb_calib --out results/pcb_calib

  3. Fit the thresholds, then apply them to the test run (the test run is not repeated):

        python -m inspalign.calibrate fit results/pcb_calib
        python -m inspalign.gtsummary results/pcb --thresholds results/pcb_calib/thresholds.json

The rule (criterion "max-risk", default): the LOWEST threshold at which at most 5 % of the accepted calibration poses are
wrong, i.e. accept as much as possible while keeping silent wrong poses rare. If no threshold achieves that, the method is
calibrated to accept nothing (it cannot be made safe by a threshold on its own score), and the summary shows it.
"youden" (maximise right-accepted rate minus wrong-accepted rate) is available as an alternative.
"""
import argparse
import json
import os
import shutil
import sys

import numpy as np
import pandas as pd

from . import annotations as A
from . import gtsummary as GS


# ---------------------------------------------------------------------------------------------------------------------------
# 1. the calibration folder

def build_store(test_root, export_path, images_dir, out):
    test, test_path = A.read_store(test_root)
    try:
        exp = json.load(open(export_path, encoding="utf-8-sig"))
    except Exception as e:
        raise SystemExit(f"{export_path}: {type(e).__name__}: {e}")
    if not isinstance(exp.get("regions"), dict) or not exp["regions"]:
        raise SystemExit(f"{export_path}: no 'regions'; is it a landmarks.json from the picker?")
    t_regions, e_regions = list(test["regions"]), list(exp["regions"])
    mapping = {r: r for r in e_regions if r in test["regions"]}
    if not mapping and len(t_regions) == 1 and len(e_regions) == 1:
        mapping = {e_regions[0]: t_regions[0]}
    if not mapping:
        raise SystemExit(f"region names differ: test folder {t_regions}, export {e_regions}; name the region the same in the picker")

    # every file already used for testing or as a golden, by content and by name
    used_hash, used_name = {}, {}
    for region, d in test["regions"].items():
        for im in d.get("images") or []:
            p = A.live_image(test_root, im)
            if p:
                used_hash[A.sha1_12(p)] = f"test image {os.path.basename(p)}"
            used_name[str(im.get("filename") or "")] = "test image"
        for tname in d.get("templates") or {}:
            p = A.template_image(test_root, region, tname)
            if p:
                used_hash[A.sha1_12(p)] = f"golden {os.path.basename(p)}"
                used_name[os.path.basename(p)] = "golden"

    store = {"version": 1, "regions": {}}
    os.makedirs(os.path.join(out, "images"), exist_ok=True)
    problems, n_img = [], 0
    for e_region, region in mapping.items():
        d = test["regions"][region]
        names = [str(n) for n in d.get("point_names") or []]
        for tname in d.get("templates") or {}:
            src = A.template_image(test_root, region, tname)
            if src is None:
                raise SystemExit(f"golden {region}/{tname} has no image file in {test_root}/templates")
            dst = os.path.join(out, "templates", region, os.path.basename(src))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
        images = []
        for im in exp["regions"][e_region].get("images") or []:
            fn = str(im.get("filename") or "")
            src = os.path.join(images_dir, fn) if fn and os.path.isfile(os.path.join(images_dir, fn)) else None
            if src is None:
                problems.append(f"{fn}: not found in {images_dir}")
                continue
            h = A.sha1_12(src)
            if h in used_hash:
                problems.append(f"{fn}: the same file as the {used_hash[h]} -- calibration images must not be test images or goldens")
                continue
            if fn in used_name:
                problems.append(f"{fn}: a {used_name[fn]} of the test folder has this file name; rename one of them")
                continue
            extra = sorted(set(im.get("points") or {}) - set(names))
            if extra:
                problems.append(f"{fn}: point names not used in the test folder: {', '.join(extra)}")
                continue
            shutil.copy2(src, os.path.join(out, "images", fn))
            images.append(dict(im, id=h))
            n_img += 1
        store["regions"][region] = {"point_names": names, "templates": d.get("templates") or {}, "images": images}
    if problems:
        shutil.rmtree(out, ignore_errors=True)
        raise SystemExit("calibration folder NOT written:\n  " + "\n  ".join(problems))
    with open(os.path.join(out, "landmarks.json"), "w", encoding="utf-8") as f:
        json.dump(store, f, indent=1)
    return n_img


# ---------------------------------------------------------------------------------------------------------------------------
# 3. the thresholds

def fit(run, criterion="max-risk", risk=0.05):
    res = pd.read_csv(os.path.join(run, "results.csv"))
    res = GS.prepare(res)
    tau = float(res.tau_px.median())
    out = {}
    for m in dict.fromkeys(res["method"]):
        if m == "identity":
            continue
        g = res[res.method == m]
        right = (g.err_mean_px <= tau).to_numpy()
        score = g.score.where(g.checks_ok_b)
        rc = GS.risk_coverage(score, right, len(g))
        dflt = g.success_b.to_numpy()
        e = dict(score=_score_name(m), pairs=int(len(g)), right_poses=int(right.sum()),
                 default_rule=dict(coverage=float(dflt.mean()), risk=float((dflt & ~right).sum() / max(dflt.sum(), 1))))
        if criterion == "youden":
            n_r, n_w = max(int(right.sum()), 1), max(int((~right).sum()), 1)
            if len(rc):
                j = (rc.accepted - rc.wrong) / n_r - rc.wrong / n_w
                best = rc.iloc[int(np.argmax(j.to_numpy()))]
                e.update(threshold=float(best.threshold), coverage=float(best.coverage), risk=float(best.risk))
            else:
                e.update(threshold=None, accept_none=True, coverage=0.0, risk=0.0)
        else:
            ok = rc[rc.risk <= risk]
            if len(ok):
                best = ok.loc[ok.coverage.idxmax()]
                e.update(threshold=float(best.threshold), coverage=float(best.coverage), risk=float(best.risk))
            else:
                e.update(threshold=None, accept_none=True, coverage=0.0, risk=0.0)
        if right.sum() < 5:
            e["warning"] = f"only {int(right.sum())} right poses in the calibration set: the threshold is poorly determined"
        out[m] = e
    return dict(calibration_run=run, tau_px=tau,
                criterion=(f"max-risk {risk:g}: lowest threshold with at most {risk:.0%} of accepted poses wrong"
                           if criterion != "youden" else "youden: maximise right-accepted rate minus wrong-accepted rate"),
                methods=out)


def _score_name(m):
    from .methods import score_field
    return {"n_inl": "RANSAC inliers", "conf": "own confidence (peak / edge score)"}[score_field(m)]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("store", help="build a calibration folder from the test folder's goldens and newly annotated images")
    s.add_argument("--test", required=True, help="the part's test data folder (its goldens are reused)")
    s.add_argument("--export", required=True, help="landmarks.json saved by the picker for the calibration images")
    s.add_argument("--images", required=True, help="folder holding the calibration image files")
    s.add_argument("--out", required=True, help="new calibration data folder, e.g. data/pcb_calib")
    f = sub.add_parser("fit", help="fit the thresholds on a calibration run")
    f.add_argument("run", help="the evaluate.py output folder of the calibration images")
    f.add_argument("--criterion", choices=["max-risk", "youden"], default="max-risk")
    f.add_argument("--risk", type=float, default=0.05, help="max-risk: the largest share of wrong poses among accepted ones")
    f.add_argument("--out", default=None, help="default: <run>/thresholds.json")
    a = ap.parse_args(argv)
    if a.cmd == "store":
        if os.path.exists(a.out) and os.listdir(a.out):
            raise SystemExit(f"{a.out} exists and is not empty; choose a new folder")
        n = build_store(a.test, a.export, a.images, a.out)
        print(f"wrote {a.out}: the goldens of {a.test} + {n} calibration image(s)\nnext: python evaluate.py --config "
              f"configs/parts/<part>.yaml --data {a.out} --out results/<part>_calib")
        return
    t = fit(a.run, a.criterion, a.risk)
    path = a.out or os.path.join(a.run, "thresholds.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(t, fh, indent=2)
    rows = [dict(method=m, score=e["score"], threshold="accept none" if e.get("accept_none") else round(e["threshold"], 3),
                 coverage=round(e["coverage"], 2), risk=round(e["risk"], 2), default_coverage=round(e["default_rule"]["coverage"], 2),
                 default_risk=round(e["default_rule"]["risk"], 2)) for m, e in t["methods"].items()]
    print(GS.md_table(pd.DataFrame(rows)))
    for m, e in t["methods"].items():
        if e.get("warning"):
            print(f"  {m}: {e['warning']}", file=sys.stderr)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
