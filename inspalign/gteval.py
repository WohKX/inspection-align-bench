"""Evaluate alignment methods on annotated image pairs: golden (template) images, test images, clicked landmark points.

For every pair and every method:
  1. both images are loaded (and, if `work_long_side` is set, shrunk by the same factor);
  2. the method estimates a live -> template transform;
  3. the transform is converted back to ORIGINAL image pixels and applied to the live ground-truth points;
  4. the distance to the matching template ground-truth points is the error.
Everything is written to the output folder:
  run.log        human-readable log of the whole run (also printed to the terminal)
  results.csv    one row per pair x method: errors, outcome, the method's own confidence, latency, the 3x3 matrix
  points.csv     one row per pair x method x point: where each GT point landed and how far it is from its target
  pairs.csv      one row per pair: what was read, image sizes, the GT pose and the annotation floor
  summary/       SUMMARY.md + summary_methods.csv + summary_groups.csv (re-computable with another tau: gtsummary.py)
  overlays/      pictures of the alignments (all, failures only, or none)
  gt_check/      one picture per pair with the GT points as they were read (check the annotation was understood)
  manifest.json  config, versions, data fingerprint, available / unavailable methods

The floor. With hand-clicked points, part of every error is click noise. For each pair the similarity that best fits the GT
points themselves (least squares) is computed; its mean point error, `gt_floor_mean_px`, is roughly the smallest error ANY
similarity-model method can show on that pair. Differences below it are not interpretable. `excess_px` = error - floor.
"""
import csv
import json
import os
import platform
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

import cv2
import numpy as np
import yaml

from . import __version__
from . import annotations as A
from . import geometry as G
from .imio import imread, imwrite
from . import masks as MK
from . import methods as METHODS

DEFAULT_CONFIG = {
    "data": {"root": None, "coord_origin": "center", "mask": "auto", "min_points": 3, "templates": {}, "template_image": None},
    "work_long_side": None,
    "tau_px": 3.0,
    "cv2_threads": 1,
    "methods": [  # identity = reference line (its error is the raw misalignment), then the five arms
        {"name": "identity"},
        {"name": "phase_correlation"},
        {"name": "sift_ransac"},
        {"name": "lightglue_disk"},
        {"name": "lightglue_sift"},
        {"name": "contour_shape_match", "params": {"max_rotation_deg": 15, "max_scale_deviation": 0.15, "max_translation_ratio": 0.15},
         "declared": {"rotation_deg": 15, "scale_dev": 0.15, "shift_frac": 0.15}},
    ],
    "outputs": {"overlays": "failures", "gt_check": True, "overlay_max_side": 1280},
    "symmetry": {},          # {"<region>": {"order": n, "cycle": [names]}} or {"<region>": {"order": n, "center": ...}}: DATA_FORMAT.md 5
}

RESULT_COLS = ["pair_id", "group", "method", "family", "model", "success", "outcome", "reason", "score", "checks_ok", "conf", "n_good", "n_inl",
               "latency_ms", "n_points", "err_mean_px", "err_median_px", "err_rms_px", "err_max_px", "err_centroid_px",
               "err_rot_deg", "err_scale_pct", "gt_floor_mean_px", "excess_px", "tau_px", "in_declared_range",
               "gt_rot_deg", "gt_scale", "gt_shift_px", "sym_order", "sym_rot_deg", "err_mean_strict_px", "template", "live",
               "m00", "m01", "m02", "m10", "m11", "m12", "m20", "m21", "m22"]
POINT_COLS = ["pair_id", "method", "point", "tpl_x", "tpl_y", "live_x", "live_y", "est_x", "est_y", "err_px"]
PAIR_COLS = ["pair_id", "group", "status", "template", "live", "gt_file", "n_points", "notes", "template_w", "template_h",
             "live_w", "live_h", "work_scale", "mask_source", "mask_area_frac", "gt_rot_deg", "gt_scale", "gt_shift_px",
             "gt_floor_mean_px", "gt_floor_max_px", "gt_sim_rms_px", "gt_h_rms_px", "sym_order", "sym_mode", "sym_center_x",
             "sym_center_y", "gt_rot_deg_raw"]

_CFG = None
_METHODS = []


# ---------------------------------------------------------------------------------------------------------------------------
# config

def _merge(base, over):
    out = dict(base)
    for k, v in (over or {}).items():
        out[k] = _merge(base[k], v) if isinstance(v, dict) and isinstance(base.get(k), dict) else v
    return out


class _StrictLoader(yaml.SafeLoader):
    """YAML loader that refuses a key written twice in the same block. Plain YAML silently keeps the LAST one, so a second
    `symmetry:` line further down the file would quietly cancel the first."""


def _no_duplicates(loader, node, deep=False):
    seen = {}
    for k_node, _ in node.value:
        k = loader.construct_object(k_node, deep=deep)
        if k in seen:
            raise SystemExit(f"config error: '{k}' is written twice (lines {seen[k] + 1} and {k_node.start_mark.line + 1}); "
                             f"YAML would silently use the second one. Keep one.")
        seen[k] = k_node.start_mark.line
    return loader.construct_mapping(node, deep=deep)


_StrictLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _no_duplicates)
_TOP_LEVEL_ONLY = ("symmetry", "tau_px", "work_long_side", "methods", "outputs", "cv2_threads")


def load_config(path=None, overrides=None):
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))
    if path:
        with open(path, encoding="utf-8") as f:
            user = yaml.load(f, Loader=_StrictLoader) or {}
        misplaced = [k for k in _TOP_LEVEL_ONLY if isinstance(user.get("data"), dict) and k in user["data"]]
        if misplaced:
            raise SystemExit(f"config error: {', '.join(misplaced)} must be at the top level of {path} (no indentation), "
                             f"not inside 'data:'")
        unknown = sorted(set(user) - set(DEFAULT_CONFIG))
        if unknown:
            raise SystemExit(f"config error: unknown top-level key(s) {unknown} in {path}; known: {sorted(DEFAULT_CONFIG)}")
        cfg = _merge(cfg, user)
        from .methods import unknown_method_message
        msg = unknown_method_message([str((e or {}).get("name")) for e in cfg.get("methods") or []])
        if msg:
            raise SystemExit(f"config error in {path}: {msg}")
        check_symmetry_config(cfg)
    return _merge(cfg, overrides or {})


# ---------------------------------------------------------------------------------------------------------------------------
# geometry of the evaluation

def similarity_lsq(src, dst):
    """Least-squares similarity src -> dst (closed form, complex-number form of Umeyama's solution). 3x3, or None."""
    src, dst = np.asarray(src, float).reshape(-1, 2), np.asarray(dst, float).reshape(-1, 2)
    if len(src) == 0:
        return None
    ms, md = src.mean(0), dst.mean(0)
    zs = (src[:, 0] - ms[0]) + 1j * (src[:, 1] - ms[1])
    zd = (dst[:, 0] - md[0]) + 1j * (dst[:, 1] - md[1])
    den = float(np.real(np.vdot(zs, zs)))
    a = (np.vdot(zs, zd) / den) if den > 1e-12 else 1.0 + 0j          # one point (or all identical): translation only
    M = np.eye(3)
    M[:2, :2] = [[a.real, -a.imag], [a.imag, a.real]]
    M[:2, 2] = md - M[:2, :2] @ ms
    return M


def gt_diagnostics(gt):
    """Pose of the ground truth (from the best-fit similarity) and how well a similarity can explain the clicked points."""
    n = len(gt.live_pts)
    S = similarity_lsq(gt.live_pts, gt.tpl_pts)
    res = np.hypot(*(G.apply(S, gt.live_pts) - gt.tpl_pts).T)
    c_live = gt.live_pts.mean(0)
    rot, scale, _ = G.jacobian_params(S, c_live)
    out = dict(gt_rot_deg=rot if n >= 2 else float("nan"), gt_scale=scale if n >= 2 else float("nan"),
               gt_shift_px=float(np.hypot(*(gt.tpl_pts.mean(0) - c_live))),
               gt_floor_mean_px=float(res.mean()) if n >= 3 else float("nan"),
               gt_floor_max_px=float(res.max()) if n >= 3 else float("nan"),
               gt_sim_rms_px=float(np.sqrt((res ** 2).mean())) if n >= 3 else float("nan"), gt_h_rms_px=float("nan"))
    if n >= 5:
        H, _ = cv2.findHomography(gt.live_pts.astype(np.float64), gt.tpl_pts.astype(np.float64), 0)
        if H is not None:
            out["gt_h_rms_px"] = float(np.sqrt((np.hypot(*(G.apply(H, gt.live_pts) - gt.tpl_pts).T) ** 2).mean()))
    return S, out


def errors(M, gt, S_gt, floor):
    """Error columns for one estimated live -> template matrix (original pixels), or NaNs when there is no pose."""
    nan = float("nan")
    out = dict(err_mean_px=nan, err_median_px=nan, err_rms_px=nan, err_max_px=nan, err_centroid_px=nan, err_rot_deg=nan,
               err_scale_pct=nan, excess_px=nan)
    if M is None or not np.all(np.isfinite(M)):
        return out, None
    est = G.apply(M, gt.live_pts)
    d = np.hypot(*(est - gt.tpl_pts).T)
    out.update(err_mean_px=float(d.mean()), err_median_px=float(np.median(d)), err_rms_px=float(np.sqrt((d ** 2).mean())),
               err_max_px=float(d.max()), err_centroid_px=float(np.hypot(*(est.mean(0) - gt.tpl_pts.mean(0)))))
    if len(gt.live_pts) >= 2:
        c = gt.live_pts.mean(0)
        re_, se, _ = G.jacobian_params(M, c)
        rg, sg, _ = G.jacobian_params(S_gt, c)
        out["err_rot_deg"] = float(G.wrap_deg(re_ - rg))
        out["err_scale_pct"] = float(100.0 * (se / sg - 1.0)) if sg > 0 else nan
    if np.isfinite(floor):
        out["excess_px"] = out["err_mean_px"] - floor
    return out, est


# ---------------------------------------------------------------------------------------------------------------------------
# symmetric parts

def symmetry_for(cfg, group):
    """The symmetry declared for this part as a dict {"order": n, "cycle": [...] or None, "center": spec}, or None.
    The key is the part (group) name or its region (the part of the group name before '/')."""
    table = cfg.get("symmetry") or {}
    for key in (group, str(group).split("/")[0]):
        v = table.get(key)
        if not v:
            continue
        if isinstance(v, (int, float)):
            v = {"order": int(v)}
        n = int(v.get("order", 1))
        if n >= 2:
            return {"order": n, "cycle": v.get("cycle"), "center": v.get("center", "mask")}
    return None


def check_symmetry_config(cfg):
    """Refuse a symmetry declaration that cannot work, before anything runs."""
    for k, v in (cfg.get("symmetry") or {}).items():
        if isinstance(v, (int, float)):
            continue
        if not isinstance(v, dict) or int(v.get("order", 1)) < 2:
            raise SystemExit(f"config error: symmetry '{k}' must be a number >= 2 or {{order: n, cycle: [...]}} / {{order: n, center: ...}}")
        cyc = v.get("cycle")
        if cyc is not None:
            if not isinstance(cyc, (list, tuple)) or len(cyc) < 2 or len(set(map(str, cyc))) != len(cyc):
                raise SystemExit(f"config error: symmetry '{k}': cycle must list the repeated points in order round the part, each once")
            if len(cyc) % int(v["order"]):
                raise SystemExit(f"config error: symmetry '{k}': {len(cyc)} points in the cycle cannot be shared by "
                                 f"{v['order']} identical sectors (the count must be a multiple of the order)")


def equivalents(gt, sym, mask):
    """The n equivalent ground truths of an n-fold symmetric part, k = 0 .. n-1 (k = 0 is the labelling as clicked).

    cycle mode: the golden points of the repeated features are shifted along the cycle by k sectors (the test point labelled
        p1 may equally be the golden's p2, p3, ...), points outside the cycle stay. The equivalents are the golden's OWN
        clicked points, so a part that is only roughly symmetric (hand-made, food) is judged against its real features.
    centre mode: the golden points are turned by k x 360/n degrees about the centre (a landmark, the mean of the golden's
        points, the mask centroid, or [x, y]). Exact for a machined part; an irregular part is better served by a cycle.
    Returns (list of golden-point arrays, centre (x, y) or (nan, nan), mode)."""
    n = sym["order"]
    if sym.get("cycle"):
        cyc = [str(c) for c in sym["cycle"]]
        missing = [c for c in cyc if c not in gt.names]
        if missing:
            raise A.AnnotationError(f"symmetry cycle needs every point of {cyc} on both images; missing here: {','.join(missing)}")
        step = len(cyc) // n
        idx = {nm: i for i, nm in enumerate(gt.names)}
        out = []
        for k in range(n):
            t = gt.tpl_pts.copy()
            for j, nm in enumerate(cyc):
                t[idx[nm]] = gt.tpl_pts[idx[cyc[(j + k * step) % len(cyc)]]]
            out.append(t)
        return out, (float("nan"), float("nan")), "cycle"
    cspec = sym.get("center", "mask")
    if isinstance(cspec, (list, tuple)):
        c = (float(cspec[0]), float(cspec[1]))
    elif cspec == "points":                                           # the mean of this golden's own clicked points
        c = tuple(float(v) for v in gt.tpl_pts.mean(0))
    elif isinstance(cspec, str) and cspec != "mask":                 # a landmark name, e.g. "p6" clicked on the centre
        if cspec not in gt.names:
            raise A.AnnotationError(f"symmetry centre is the point '{cspec}', but this pair has no '{cspec}' on both images")
        i = gt.names.index(cspec)
        c = (float(gt.tpl_pts[i, 0]), float(gt.tpl_pts[i, 1]))
    else:
        if mask is None or not mask.any():
            raise A.AnnotationError("symmetry is declared for this part, but there is no golden mask to find its centre: "
                                    "use a cycle, a landmark name or [x, y]")
        mo = cv2.moments((mask > 0).astype(np.uint8), binaryImage=True)
        c = (mo["m10"] / mo["m00"], mo["m01"] / mo["m00"])
    return [G.apply(G.rotation_about(360.0 * k / n, c), gt.tpl_pts) for k in range(n)], c, "centre"


def with_template_points(gt, tpl_pts):
    return A.GroundTruth(np.asarray(tpl_pts, float), gt.live_pts, gt.names, gt.notes)


def symmetric_errors(M, gt, equiv):
    """Errors against the closest of the equivalent ground truths. Each equivalent is judged with its own best-fit pose and
    floor. Returns (errors of the best equivalent, estimated points, its index k, its ground truth, strict error)."""
    best, strict = None, float("nan")
    for k, tpts in enumerate(equiv):
        g = gt if k == 0 else with_template_points(gt, tpts)
        S_k, d_k = gt_diagnostics(g)
        e, est = errors(M, g, S_k, d_k["gt_floor_mean_px"])
        if k == 0:
            strict = e["err_mean_px"]
        if best is None or (np.isfinite(e["err_mean_px"]) and not e["err_mean_px"] >= best[0]["err_mean_px"]):
            best = (e, est, k, g)
    return best[0], best[1], best[2], best[3], strict


def classify(success, err, tau):
    if err is None or not np.isfinite(err):
        return "no_pose"
    if success:
        return "correct" if err <= tau else "silent_wrong"
    return "lost" if err <= tau else "rejected"


def _scale_matrix(s):
    """Original -> working pixel coordinates for a resize by s (OpenCV pixel-centre convention)."""
    o = 0.5 * s - 0.5
    return np.array([[s, 0.0, o], [0.0, s, o], [0.0, 0.0, 1.0]])


def _in_range(gdiag, declared, width):
    if not declared or not np.isfinite(gdiag.get("gt_rot_deg", float("nan"))):
        return True
    ok = True
    if "rotation_deg" in declared:
        ok &= abs(gdiag["gt_rot_deg"]) <= declared["rotation_deg"]
    if "scale_dev" in declared:
        ok &= abs(gdiag["gt_scale"] - 1.0) <= declared["scale_dev"]
    if "shift_frac" in declared:
        ok &= gdiag["gt_shift_px"] <= declared["shift_frac"] * width
    return bool(ok)


# ---------------------------------------------------------------------------------------------------------------------------
# pictures

def _fit(img, max_side):
    h, w = img.shape[:2]
    d = min(1.0, float(max_side) / max(h, w))
    return (cv2.resize(img, (int(round(w * d)), int(round(h * d))), interpolation=cv2.INTER_AREA) if d < 1 else img), d


def _pt(p, d):
    return int(round((p[0] + 0.5) * d - 0.5)), int(round((p[1] + 0.5) * d - 0.5))


def overlay_picture(tpl_bgr, live_bgr, M, gt, est, label, max_side):
    """The live image warped onto the template by M, in the blue channel; the template in red + green. Where the two agree
    the picture is grey; yellow fringes = template brighter there, blue fringes = warped live image brighter there.
    Green circles: GT template points. Red crosses: where the live GT points land under M. Orange line: the error."""
    H, W = tpl_bgr.shape[:2]
    tg = cv2.cvtColor(tpl_bgr, cv2.COLOR_BGR2GRAY)
    lg = cv2.cvtColor(cv2.warpPerspective(live_bgr, G.to3(M), (W, H), flags=cv2.INTER_LINEAR), cv2.COLOR_BGR2GRAY) if M is not None else np.zeros_like(tg)
    img, d = _fit(np.dstack([lg, tg, tg]), max_side)
    img = img.copy()
    r = max(4, int(round(0.008 * max(img.shape[:2]))))
    for i, t in enumerate(gt.tpl_pts):
        cv2.circle(img, _pt(t, d), r, (0, 255, 0), 1, cv2.LINE_AA)
        if est is not None:
            cv2.line(img, _pt(t, d), _pt(est[i], d), (0, 140, 255), 1, cv2.LINE_AA)
            cv2.drawMarker(img, _pt(est[i], d), (0, 0, 255), cv2.MARKER_CROSS, 2 * r, 1, cv2.LINE_AA)
    _label(img, label)
    return img


def gt_check_picture(tpl_bgr, live_bgr, gt, title, max_side):
    """Template (left) and live image (right) with the GT points numbered and joined: a quick visual check that the points
    were read correctly (order, names, coordinate convention)."""
    h = min(int(max_side * 0.6), max(tpl_bgr.shape[0], live_bgr.shape[0]))
    ims, ds = [], []
    for im in (tpl_bgr, live_bgr):
        d = h / float(im.shape[0])
        ims.append(cv2.resize(im, (int(round(im.shape[1] * d)), h), interpolation=cv2.INTER_AREA if d < 1 else cv2.INTER_LINEAR))
        ds.append(d)
    canvas = np.hstack([ims[0], np.full((h, 8, 3), 255, np.uint8), ims[1]])
    off = ims[0].shape[1] + 8
    rng = np.random.default_rng(0)
    for i, (t, l) in enumerate(zip(gt.tpl_pts, gt.live_pts)):
        col = tuple(int(c) for c in rng.integers(60, 256, 3))
        a, b = _pt(t, ds[0]), _pt(l, ds[1])
        b = (b[0] + off, b[1])
        cv2.line(canvas, a, b, col, 1, cv2.LINE_AA)
        for p in (a, b):
            cv2.circle(canvas, p, 5, col, 2, cv2.LINE_AA)
            cv2.putText(canvas, str(gt.names[i]), (p[0] + 6, p[1] - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.45, col, 1, cv2.LINE_AA)
    _label(canvas, title)
    return canvas


def _label(img, text):
    cv2.rectangle(img, (0, 0), (img.shape[1], 22), (0, 0, 0), -1)
    cv2.putText(img, text, (6, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)


def _safe(s):
    return "".join(c if c.isalnum() or c in "-_." else "_" for c in s)


# ---------------------------------------------------------------------------------------------------------------------------
# one pair

def init_worker(cfg):
    global _CFG, _METHODS
    _CFG = cfg
    cv2.setNumThreads(int(cfg.get("cv2_threads") or 1))
    _METHODS = []
    for entry in cfg["methods"]:
        try:
            m = METHODS.build(entry["name"], entry.get("params"))
        except METHODS.Unavailable:
            continue
        _METHODS.append((m, entry.get("declared") or {}))


def _read(path):
    img = imread(path, cv2.IMREAD_COLOR)
    if img is None:
        raise A.AnnotationError(f"cannot read image {_rel(path)}")
    return img


def _template_mask(pair, tpl, mode):
    """Template object mask at the ORIGINAL template size -> (mask uint8 0/255 or None, source, area fraction).
    The methods get it resized (nearest) to the working size, so every resolution sees the same mask."""
    if mode in ("auto", "file") and pair.template_mask_path:
        m = imread(pair.template_mask_path, cv2.IMREAD_GRAYSCALE)
        if m is None:
            raise A.AnnotationError(f"cannot read mask {_rel(pair.template_mask_path)}")
        if m.shape != tpl.shape[:2]:
            raise A.AnnotationError(f"mask {_rel(pair.template_mask_path)} is {m.shape[1]}x{m.shape[0]}, template is {tpl.shape[1]}x{tpl.shape[0]}")
        m = ((m > 127) * 255).astype(np.uint8)
        return m, "file", float((m > 0).mean())
    if mode == "file":
        raise A.AnnotationError("mask: file, but there is no <template>_mask.png")
    if mode in ("auto", "otsu"):
        m, info = MK.object_mask(tpl)
        return m, "otsu", float(info["area_frac"])
    if mode != "none":
        raise ValueError("data.mask must be auto | file | otsu | none")
    return None, "none", float("nan")


def _check_gt(pair, gt, tpl, live, min_points):
    """Refuse ground truth that cannot belong to these images: too few points, points outside the image, or images whose
    size differs from the one the points were clicked on (a stale annotation)."""
    for what, expect, img in (("golden", pair.expect_template_size, tpl), ("test image", pair.expect_live_size, live)):
        if expect and tuple(expect) != (img.shape[1], img.shape[0]):
            raise A.AnnotationError(f"the {what} is {img.shape[1]}x{img.shape[0]} px but its points were clicked on a "
                                    f"{expect[0]}x{expect[1]} image (stale points)")
    if len(gt.tpl_pts) < min_points:
        raise A.AnnotationError(f"only {len(gt.tpl_pts)} point(s) in common with the golden (need >= {min_points})")
    for what, pts, img in (("golden", gt.tpl_pts, tpl), ("test image", gt.live_pts, live)):
        h, w = img.shape[:2]
        bad = (pts[:, 0] < -0.5 - 1e-6) | (pts[:, 0] > w - 0.5 + 1e-6) | (pts[:, 1] < -0.5 - 1e-6) | (pts[:, 1] > h - 0.5 + 1e-6)
        if bad.any():
            i = int(np.argmax(bad))
            raise A.AnnotationError(f"point '{gt.names[i]}' ({pts[i, 0]:.2f}, {pts[i, 1]:.2f}) lies outside the {w}x{h} {what}: "
                                    f"wrong image, or wrong coord_origin?")
    if len(gt.tpl_pts) >= 3:
        proper, mirrored = _fit_residual(gt.live_pts, gt.tpl_pts, False), _fit_residual(gt.live_pts, gt.tpl_pts, True)
        if proper > 3 * max(mirrored, 0.5) and proper - mirrored > 5:
            raise A.AnnotationError(f"the points fit a MIRROR image (mean residual {mirrored:.1f} px) far better than any turn "
                                    f"({proper:.1f} px): on one of the two images the labels go round in the opposite direction "
                                    f"(e.g. two names swapped), or the part lies flipped over. Fix the labels")


def _fit_residual(a, b, mirror):
    """Mean residual of the least-squares similarity a -> b; with mirror=True, of the best similarity that includes a
    reflection (used only to recognise labels that go round in the opposite direction)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    if mirror:
        a = a * np.array([-1.0, 1.0])
    A_, B_ = a - a.mean(0), b - b.mean(0)
    U, S, Vt = np.linalg.svd(B_.T @ A_)
    D = np.diag([1.0, np.sign(np.linalg.det(U @ Vt)) or 1.0])
    R = U @ D @ Vt
    s = (S * np.diag(D)).sum() / max((A_ ** 2).sum(), 1e-12)
    return float(np.hypot(*((s * (R @ A_.T)).T - B_).T).mean())


def _rel(path):
    """A file path as written to the outputs: relative to the data folder, so result files carry no machine-specific
    folder names (user names, company names in home directories) when they are shared."""
    root = _CFG["data"].get("root") if _CFG else None
    if not path or not root:
        return path
    try:
        return os.path.relpath(os.path.abspath(path), os.path.abspath(root)).replace(os.sep, "/")
    except ValueError:                             # another drive (Windows): keep the file name only
        return os.path.basename(path)


def process_pair(pair):
    cfg = _CFG
    tau = float(cfg["tau_px"])
    outs = cfg["outputs"]
    t0 = time.perf_counter()
    prow = dict(pair_id=pair.pair_id, group=pair.group, template=_rel(pair.template_path), live=_rel(pair.live_path), gt_file=_rel(pair.gt_path))
    log = []
    try:
        tpl = _read(pair.template_path)
        live = _read(pair.live_path)
        long_side = cfg.get("work_long_side")
        s = min(1.0, float(long_side) / max(tpl.shape[:2] + live.shape[:2])) if long_side else 1.0
        rs = (lambda im: cv2.resize(im, (int(round(im.shape[1] * s)), int(round(im.shape[0] * s))), interpolation=cv2.INTER_AREA)) if s < 1 else (lambda im: im)
        tpl_w, live_w = rs(tpl), rs(live)
        mask, mask_src, mask_area = _template_mask(pair, tpl, cfg["data"].get("mask", "auto"))
        mask_w = None if mask is None else (mask if s == 1.0 else cv2.resize(mask, (tpl_w.shape[1], tpl_w.shape[0]), interpolation=cv2.INTER_NEAREST))
        S = _scale_matrix(s)
        Sinv = np.linalg.inv(S)

        gt = A.load_ground_truth(pair, cfg["data"].get("coord_origin", "center"))
        _check_gt(pair, gt, tpl, live, int(cfg["data"].get("min_points") or 1))
        S_gt, gdiag = gt_diagnostics(gt)
        gdiag["gt_rot_deg_raw"] = gdiag["gt_rot_deg"]
        equiv, sym_n, sym_c, sym_mode = [gt.tpl_pts], 1, (float("nan"), float("nan")), ""
        sym = symmetry_for(cfg, pair.group)
        if sym:
            sym_n = sym["order"]
            equiv, sym_c, sym_mode = equivalents(gt, sym, mask)
            raw_rot = gdiag["gt_rot_deg"]
            eq = min((gt_diagnostics(with_template_points(gt, t))[1] for t in equiv), key=lambda d: abs(d["gt_rot_deg"]))
            gdiag.update(gt_rot_deg=eq["gt_rot_deg"], gt_scale=eq["gt_scale"], gt_shift_px=eq["gt_shift_px"])  # the equivalent nearest no rotation
            gdiag["gt_rot_deg_raw"] = raw_rot
        prow.update(sym_order=sym_n, sym_mode=sym_mode, sym_center_x=sym_c[0], sym_center_y=sym_c[1])
        prow.update(status="ok", n_points=len(gt.tpl_pts), notes="; ".join(gt.notes), template_w=tpl.shape[1],
                    template_h=tpl.shape[0], live_w=live.shape[1], live_h=live.shape[0], work_scale=s, mask_source=mask_src,
                    mask_area_frac=mask_area, **gdiag)
    except Exception as e:                         # a broken pair is reported, not fatal
        prow.update(status=f"error: {type(e).__name__}: {e}")
        log.append(f"{pair.pair_id}: SKIPPED  {prow['status']}")
        return pair, prow, [], [], log, time.perf_counter() - t0

    floor = gdiag["gt_floor_mean_px"]
    head = (f"{pair.pair_id}   points={len(gt.tpl_pts)}   GT: rot {gdiag['gt_rot_deg']:+.2f} deg, scale {gdiag['gt_scale']:.4f}, "
            f"shift {gdiag['gt_shift_px']:.1f} px   floor {floor:.2f} px"
            + ((f"   {sym_n}-fold symmetric (label shift)" if sym_mode == "cycle" else
                f"   {sym_n}-fold symmetric about ({sym_c[0]:.1f}, {sym_c[1]:.1f})") if sym_n > 1 else "")
            + (f"   [{'; '.join(gt.notes)}]" if gt.notes else ""))
    log.append(head)
    rrows, prows_ = [], []
    odir, cdir = cfg.get("_overlay_dir"), cfg.get("_gtcheck_dir")
    if cdir and outs.get("gt_check"):
        imwrite(os.path.join(cdir, _safe(pair.pair_id.replace("/", "__")) + ".png"),
                    gt_check_picture(tpl, live, gt, f"{pair.pair_id}: {len(gt.tpl_pts)} GT points", outs.get("overlay_max_side", 1280)))
    for method, declared in _METHODS:
        a0 = time.perf_counter()
        try:
            r = method.align(live_w, tpl_w, mask_w)
        except Exception as e:                     # a crash is a failed attempt, recorded as such
            r = METHODS.Result(False, None, reason=f"exception: {type(e).__name__}: {e}")
        latency = (time.perf_counter() - a0) * 1000.0
        M = None if r.M is None else Sinv @ G.to3(r.M) @ S
        err, est, k_sym, gt_k, strict = symmetric_errors(M, gt, equiv)
        outcome = classify(r.success, err["err_mean_px"], tau)
        row = dict(pair_id=pair.pair_id, group=pair.group, method=method.name, family=method.family, model=method.model,
                   success=bool(r.success), outcome=outcome, reason=r.reason, score=method.score(r) if r.M is not None else float("nan"),
                   checks_ok=bool(r.checks_ok), conf=r.conf, n_good=r.n_good, n_inl=r.n_inl,
                   latency_ms=latency, n_points=len(gt.tpl_pts), gt_floor_mean_px=floor, tau_px=tau,
                   in_declared_range=_in_range(gdiag, declared, tpl.shape[1]), gt_rot_deg=gdiag["gt_rot_deg"],
                   gt_scale=gdiag["gt_scale"], gt_shift_px=gdiag["gt_shift_px"], sym_order=sym_n, sym_rot_deg=360.0 * k_sym / sym_n,
                   err_mean_strict_px=strict, template=_rel(pair.template_path), live=_rel(pair.live_path), **err)
        if M is not None:
            row.update({f"m{i}{j}": float(M[i, j]) for i in range(3) for j in range(3)})
        rrows.append(row)
        for i, name in enumerate(gt.names):
            prows_.append(dict(pair_id=pair.pair_id, method=method.name, point=name, tpl_x=gt_k.tpl_pts[i, 0], tpl_y=gt_k.tpl_pts[i, 1],
                               live_x=gt.live_pts[i, 0], live_y=gt.live_pts[i, 1],
                               est_x=est[i, 0] if est is not None else float("nan"), est_y=est[i, 1] if est is not None else float("nan"),
                               err_px=float(np.hypot(*(est[i] - gt_k.tpl_pts[i]))) if est is not None else float("nan")))
        e = err["err_mean_px"]
        extra = (f"inliers {r.n_inl}/{r.n_good}" if r.n_inl is not None and r.n_good is not None else "")
        conf = f"conf {r.conf:.3f}" if isinstance(r.conf, (int, float)) and r.conf is not None and np.isfinite(r.conf) else ""
        errs = (f"err mean {e:8.2f} px  max {err['err_max_px']:8.2f}  rot {err['err_rot_deg']:+7.3f} deg  scale {err['err_scale_pct']:+6.2f} %"
                if np.isfinite(e) else f"{'no pose':>58s}")
        log.append(f"    {method.name:20s} {'ACCEPT' if r.success else 'REJECT'}  {errs}  {conf:11s} {extra:18s} {latency:8.0f} ms  "
                   f"{outcome}" + (f"  [symmetric equivalent {360.0 * k_sym / sym_n:+.0f} deg]" if k_sym else "")
                   + (f"  ({r.reason})" if r.reason else ""))
        mode = outs.get("overlays", "failures")
        if odir and (mode == "all" or (mode == "failures" and outcome != "correct")) and method.name != "identity":
            label = f"{method.name}  {outcome}  " + (f"err {e:.2f}px" if np.isfinite(e) else "no pose")
            imwrite(os.path.join(odir, _safe(f"{pair.pair_id.replace('/', '__')}__{method.name}") + ".png"),
                        overlay_picture(tpl, live, M, gt_k, est, label, outs.get("overlay_max_side", 1280)))
    return pair, prow, rrows, prows_, log, time.perf_counter() - t0


# ---------------------------------------------------------------------------------------------------------------------------
# run

class _Csv:
    def __init__(self, path, cols):
        new = not os.path.exists(path) or os.path.getsize(path) == 0
        self.f = open(path, "a", newline="", encoding="utf-8-sig")   # BOM: Excel shows non-ASCII paths correctly
        self.w = csv.DictWriter(self.f, fieldnames=cols, extrasaction="ignore")
        if new:
            self.w.writeheader()

    def write(self, rows):
        self.w.writerows(rows)
        self.f.flush()


class _Log:
    def __init__(self, path, quiet=False):
        self.f = open(path, "a", encoding="utf-8")
        self.quiet = quiet

    def __call__(self, line=""):
        stamp = time.strftime("%Y-%m-%d %H:%M:%S")
        for ln in str(line).split("\n"):
            self.f.write(f"{stamp}  {ln}\n")
            if not self.quiet:
                print(ln, file=sys.stderr)
        self.f.flush()


def _learned_info(m):
    """Where a learned method runs (for a +rot method: its base method), so its latency can be read correctly."""
    t = getattr(m, "_torch", None)
    return dict(device=str(getattr(m, "device", "")), torch=getattr(t, "__version__", None),
                cuda_available=bool(t.cuda.is_available()) if t is not None else None)


def _git_commit():
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                              cwd=os.path.dirname(os.path.abspath(__file__))).stdout.strip() or None
    except Exception:
        return None


def run(cfg, out, jobs=1, resume=False, limit=None, quiet=False):
    root = cfg["data"]["root"]
    if not root:
        raise SystemExit("no data folder: set data.root in the config or pass --data")
    os.makedirs(out, exist_ok=True)
    done_path = os.path.join(out, "done_pairs.txt")
    if os.path.exists(done_path) and not resume:
        raise SystemExit(f"{out} already holds a run; pass --resume to continue it, or choose another --out")
    done = set(open(done_path, encoding="utf-8").read().split("\n")) if os.path.exists(done_path) else set()
    pairs, problems = A.discover_pairs(root, cfg["data"].get("templates") or {}, cfg["data"].get("template_image"))
    if limit:
        pairs = pairs[:limit]
    outs = cfg["outputs"]
    if outs.get("overlays", "failures") != "none":
        cfg["_overlay_dir"] = os.path.join(out, "overlays")
        os.makedirs(cfg["_overlay_dir"], exist_ok=True)
    if outs.get("gt_check"):
        cfg["_gtcheck_dir"] = os.path.join(out, "gt_check")
        os.makedirs(cfg["_gtcheck_dir"], exist_ok=True)

    init_worker(cfg)
    log = _Log(os.path.join(out, "run.log"), quiet)
    files = sorted({p.template_path for p in pairs} | {p.live_path for p in pairs} | {p.gt_path for p in pairs if p.gt_path}
                   | {p.template_mask_path for p in pairs if p.template_mask_path})
    available = [m.name for m, _ in _METHODS]
    unavailable = {}
    for e in cfg["methods"]:
        if e["name"] not in available:
            try:
                METHODS.build(e["name"], e.get("params"))
            except METHODS.Unavailable as ex:
                unavailable[e["name"]] = str(ex)
    manifest = dict(inspalign=__version__, mode="annotated_pairs", data_root=str(root), n_pairs=len(pairs),
                    data_fingerprint=A.file_digest(files), config={k: v for k, v in cfg.items() if not k.startswith("_")},
                    opencv=cv2.__version__, numpy=np.__version__, python=platform.python_version(), platform=platform.platform(),
                    cpu_count=os.cpu_count(), jobs=jobs, git_commit=_git_commit(), started=time.strftime("%Y-%m-%dT%H:%M:%S"),
                    methods=[dict(name=m.name, family=m.family, model=m.model) for m, _ in _METHODS], unavailable=unavailable,
                    learned={m.name: _learned_info(getattr(m, "base", m)) for m, _ in _METHODS if getattr(m, "family", "") == "learned_matcher"})
    if not resume or not os.path.exists(os.path.join(out, "manifest.json")):
        with open(os.path.join(out, "manifest.json"), "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, default=str)

    log("=" * 100)
    log(f"inspalign {__version__} -- annotated-pair evaluation   {'(resumed)' if resume and done else ''}")
    log(f"data: {root}   pairs: {len(pairs)}   fingerprint: {manifest['data_fingerprint']}")
    log(f"methods: {', '.join(available)}")
    for n, why in unavailable.items():
        log(f"  unavailable: {n} -- {why}")
    if cfg.get("symmetry"):
        log("symmetry-aware scoring (declared before the run): " + ", ".join(
            f"{k}: {v if isinstance(v, (int, float)) else v.get('order')}-fold"
            + ("" if isinstance(v, (int, float)) else (f", label shift along {list(v['cycle'])}" if v.get("cycle")
                                                       else f", centre {v.get('center', 'mask')}")) for k, v in cfg["symmetry"].items()))
        groups = {p.group for p in pairs} | {p.group.split("/")[0] for p in pairs}
        for k, v in cfg["symmetry"].items():
            tpls = {p.template_path for p in pairs if p.group == k or p.group.startswith(k + "/")}
            if isinstance(v, dict) and isinstance(v.get("center"), (list, tuple)) and len(tpls) > 1:
                log(f"  WARNING: '{k}' has {len(tpls)} goldens but one fixed centre {list(v['center'])}: those are the pixels of "
                    f"ONE golden. Use center: points (each golden's own clicked points) or a landmark name instead")
            if k not in groups:
                log(f"  WARNING: symmetry is declared for '{k}', but no pair belongs to a part of that name "
                    f"(parts in this data: {', '.join(sorted({p.group for p in pairs}))})")
    else:
        log("symmetry: none declared -- every pose is scored against the orientation the points were labelled in")
    log(f"tau = {cfg['tau_px']} px (original pixels)   working long side: {cfg.get('work_long_side') or 'native'}   "
        f"coord origin: {cfg['data'].get('coord_origin', 'center')}   mask: {cfg['data'].get('mask', 'auto')}")
    for path, why in problems:
        log(f"  note: {path} -- {why}")
    log("=" * 100)

    results = _Csv(os.path.join(out, "results.csv"), RESULT_COLS)
    points = _Csv(os.path.join(out, "points.csv"), POINT_COLS)
    pairs_csv = _Csv(os.path.join(out, "pairs.csv"), PAIR_COLS)
    todo = [p for p in pairs if p.pair_id not in done]
    donef = open(done_path, "a", encoding="utf-8")

    def record(res, i):
        pair, prow, rrows, prows_, lines, secs = res
        pairs_csv.write([prow])
        results.write(rrows)
        points.write(prows_)
        lines = list(lines)
        lines[0] = f"[{i}/{len(todo)}] " + lines[0] + f"   ({secs:.1f} s)"
        log("\n".join(lines))
        if prow.get("status") == "ok":            # a pair that failed to load is retried by --resume (after you fix its file)
            donef.write(pair.pair_id + "\n")
            donef.flush()

    if jobs <= 1:
        for i, p in enumerate(todo, 1):
            record(process_pair(p), i)
    else:
        with ProcessPoolExecutor(max_workers=jobs, initializer=init_worker, initargs=(cfg,)) as ex:
            futs = [ex.submit(process_pair, p) for p in todo]
            for i, fu in enumerate(as_completed(futs), 1):
                record(fu.result(), i)

    from . import gtsummary
    report = gtsummary.summarize(out, tau_px=None)
    log("=" * 100)
    log(report)
    log(f"done -> {out}")
    return out
