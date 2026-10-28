#!/usr/bin/env python3
"""Evaluate the alignment methods on one part's annotated images: one command, one folder of logs and CSVs.

    python evaluate.py --config configs/parts/pcb.yaml --out results/pcb
    python evaluate.py --config configs/parts/pcb.yaml --out results/pcb --resume       # continue an interrupted run
    python evaluate.py --data data/demo --methods sift_ransac,contour_shape_match --tau-px 2

The data layout (landmarks.json + images/ + templates/) is described in DATA_FORMAT.md. Outputs: run.log, results.csv,
points.csv, pairs.csv, summary/, overlays/, gt_check/, manifest.json (see inspalign/gteval.py).
"""
import argparse
import os

from inspalign import gteval


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default=None, help="YAML config (configs/parts/<part>.yaml); command-line flags override it")
    ap.add_argument("--data", default=None, help="data folder (overrides data.root)")
    ap.add_argument("--out", default=None, help="output folder (default results/<data folder name>)")
    ap.add_argument("--methods", default=None, help="comma-separated subset of the configured methods, e.g. sift_ransac,phase_correlation")
    ap.add_argument("--tau-px", type=float, default=None, help="'correct' threshold on the mean point error, original pixels")
    ap.add_argument("--work-long-side", type=int, default=None, help="shrink both images so the longer side is at most this")
    ap.add_argument("--coord-origin", choices=["center", "corner"], default=None, help="pixel convention of the points (DATA_FORMAT.md)")
    ap.add_argument("--template", default=None, help="the golden image to use for every region "
                                                     "(otherwise templates/<region>/<golden>.png or data.templates in the config)")
    ap.add_argument("--min-points", type=int, default=None, help="pairs with fewer GT points in common are skipped (default 3)")
    ap.add_argument("--overlays", choices=["none", "failures", "all"], default=None)
    ap.add_argument("--jobs", type=int, default=1, help="pairs processed in parallel (latency is only comparable at --jobs 1)")
    ap.add_argument("--resume", action="store_true", help="continue a previous run in --out: skip pairs already done")
    ap.add_argument("--limit", type=int, default=None, help="only the first N pairs (quick check)")
    ap.add_argument("--quiet", action="store_true", help="write run.log only, print nothing")
    a = ap.parse_args(argv)

    over = {"data": {}, "outputs": {}}
    if a.data:
        over["data"]["root"] = a.data
    if a.coord_origin:
        over["data"]["coord_origin"] = a.coord_origin
    if a.template:
        over["data"]["template_image"] = a.template
    if a.min_points is not None:
        over["data"]["min_points"] = a.min_points
    if a.tau_px is not None:
        over["tau_px"] = a.tau_px
    if a.work_long_side is not None:
        over["work_long_side"] = a.work_long_side
    if a.overlays:
        over["outputs"]["overlays"] = a.overlays
    cfg = gteval.load_config(a.config, over)
    if a.methods:
        from inspalign.methods import unknown_method_message
        wanted = [m.strip() for m in a.methods.split(",") if m.strip()]
        msg = unknown_method_message(wanted)
        if msg:
            ap.error(msg)
        known = {e["name"]: e for e in cfg["methods"]}
        cfg["methods"] = [known.get(n, {"name": n}) for n in wanted]
    root = cfg["data"]["root"]
    out = a.out or os.path.join("results", os.path.basename(os.path.normpath(root or "run")))
    gteval.run(cfg, out, jobs=a.jobs, resume=a.resume, limit=a.limit, quiet=a.quiet)


if __name__ == "__main__":
    main()
