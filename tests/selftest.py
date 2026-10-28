"""Self-tests: python tests/selftest.py   (a few minutes on a laptop; no dataset needed).

What they pin down: the landmark store is read as written (and broken annotations are refused with a reason), the error
arithmetic measures what it claims, symmetric parts are scored against their real equivalent poses, every method recovers
easy known poses (the learned ones too, when torch + LightGlue are installed), the rotation search finds turned parts, runs
are resumable and deterministic, the summary's multi-golden and confidence numbers are computed as documented, calibration
never touches test images, and the report renders. If one of these fails, no benchmark number means anything.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

import cv2
import numpy as np
import pandas as pd

import synth
from inspalign import annotations as A
from inspalign import geometry as G
from inspalign import gteval as E
from inspalign import gtsummary as GS
from inspalign import masks as MK
from inspalign import methods as METHODS

SRC = synth.make_part(seed=3, shape="plate", dark_bg=True)
MASK, INFO = MK.object_mask(SRC)


def render(src, rot=0.0, scale=1.0, tx=0.0, ty=0.0):
    """The test image: src under a known similarity P (golden -> test). Returns (image, P)."""
    H, W = src.shape[:2]
    c = ((W - 1) / 2.0, (H - 1) / 2.0)
    P = G.translation(tx, ty) @ G.rotation_about(rot, c) @ G.scaling_about(scale, c)
    return cv2.warpAffine(src, P[:2], (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE), P


def pose_error(M, P, mask=MASK, n=200):
    """Mean distance, over points of the part, between where M sends the test-image points and where they belong."""
    if M is None:
        return float("nan")
    ys, xs = np.nonzero(mask)
    take = np.linspace(0, len(xs) - 1, n).astype(int)
    pts = np.column_stack([xs[take], ys[take]]).astype(float)
    return float(np.hypot(*(G.apply(M, G.apply(P, pts)) - pts).T).mean())


def _evaluate(args):
    return subprocess.run([sys.executable, "evaluate.py"] + args, cwd=ROOT, capture_output=True, text=True)


def _learned_installed():
    import importlib.util
    return all(importlib.util.find_spec(m) is not None for m in ("torch", "kornia", "lightglue"))


def _store(root, region, goldens, images, names):
    """Write a landmark store. goldens: {name: (img, points)}; images: {filename: (img, points)}."""
    os.makedirs(os.path.join(root, "templates", region), exist_ok=True)
    os.makedirs(os.path.join(root, "images"), exist_ok=True)
    tj, ims = {}, []
    for g, (img, pts) in goldens.items():
        cv2.imwrite(os.path.join(root, "templates", region, g + ".png"), img)
        tj[g] = {"size": [img.shape[1], img.shape[0]], "points": {n: [float(x), float(y)] for n, (x, y) in zip(names, pts)}}
    for fn, (img, pts) in images.items():
        cv2.imwrite(os.path.join(root, "images", fn), img)
        ims.append({"id": "", "filename": fn, "width": img.shape[1], "height": img.shape[0],
                    "points": {n: [float(x), float(y)] for n, (x, y) in zip(names, pts)}})
    json.dump({"version": 1, "regions": {region: {"point_names": list(names), "templates": tj, "images": ims}}},
              open(os.path.join(root, "landmarks.json"), "w"))


# ---------------------------------------------------------------------------------------------------------------------------
def test_geometry_params():
    c = (100.0, 80.0)
    rot, sc, refl = G.jacobian_params(G.rotation_about(30, c) @ G.scaling_about(1.3, c), c)
    assert abs(rot - 30) < 1e-6 and abs(sc - 1.3) < 1e-6 and not refl
    _, _, refl = G.jacobian_params(np.diag([-1.0, 1.0, 1.0]), c)
    assert refl
    assert abs(G.wrap_deg(190) + 170) < 1e-9 and abs(G.wrap_deg(-180) - 180) < 1e-9


def test_masks():
    for dark in (True, False):
        for shape in ("plate", "lshape", "disc"):
            img = synth.make_part(seed=2, shape=shape, dark_bg=dark)
            m, info = MK.object_mask(img)
            assert 0.05 < info["area_frac"] < 0.5 and not info["touches_border"] and info["n_components"] == 1
            assert info["polarity"] == ("fg_brighter" if dark else "fg_darker")


def test_error_arithmetic():
    rng = np.random.default_rng(0)
    live = rng.uniform(50, 500, (10, 2))
    true = G.translation(12, -7) @ G.rotation_about(8.0, (300, 200)) @ G.scaling_about(1.03, (300, 200))
    gt = A.GroundTruth(G.apply(true, live), live, [str(i) for i in range(10)])
    S, d = E.gt_diagnostics(gt)
    assert np.allclose(S, true, atol=1e-9) and d["gt_floor_mean_px"] < 1e-9                 # exact points: zero floor
    assert abs(d["gt_rot_deg"] - 8.0) < 1e-6 and abs(d["gt_scale"] - 1.03) < 1e-9
    e, _ = E.errors(true, gt, S, d["gt_floor_mean_px"])
    assert e["err_mean_px"] < 1e-9 and abs(e["err_rot_deg"]) < 1e-6
    e, _ = E.errors(G.translation(3, -4) @ true, gt, S, 0.0)                                 # off by (3, -4) everywhere
    assert abs(e["err_mean_px"] - 5) < 1e-9 and abs(e["err_max_px"] - 5) < 1e-9 and abs(e["err_centroid_px"] - 5) < 1e-9
    e, _ = E.errors(G.rotation_about(1.0, (0, 0)) @ true, gt, S, 0.0)
    assert abs(e["err_rot_deg"] - 1.0) < 1e-6
    assert np.isnan(E.errors(None, gt, S, 0.0)[0]["err_mean_px"])
    noisy = A.GroundTruth(gt.tpl_pts + rng.normal(0, 0.5, gt.tpl_pts.shape), live, gt.names)
    _, d = E.gt_diagnostics(noisy)
    assert 0.1 < d["gt_floor_mean_px"] < 1.0                                                  # click scatter shows up as the floor
    assert [E.classify(True, 0.5, 1), E.classify(True, 2, 1), E.classify(False, 0.5, 1), E.classify(False, 2, 1),
            E.classify(True, float("nan"), 1)] == ["correct", "silent_wrong", "lost", "rejected", "no_pose"]
    # original <-> working pixel convention matches cv2.resize: a dot at x lands at (x + 0.5) * s - 0.5
    img = np.zeros((400, 600), np.float32)
    img[100, 300] = 1.0
    small = cv2.resize(cv2.GaussianBlur(img, (0, 0), 4), None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
    yy, xx = np.mgrid[0:small.shape[0], 0:small.shape[1]]
    c = np.array([(small * xx).sum(), (small * yy).sum()]) / small.sum()
    assert np.allclose(G.apply(E._scale_matrix(0.5), [[300.0, 100.0]])[0], c, atol=0.02), c
    assert E.similarity_lsq(np.zeros((0, 2)), np.zeros((0, 2))) is None


def test_methods_recover_easy_poses():
    cases = [("sift_ransac", dict(rot=10), 1.0), ("sift_ransac", dict(tx=15, ty=-9), 1.0), ("phase_correlation", dict(tx=6, ty=-4), 1.0),
             ("contour_shape_match", dict(rot=5), 0.5), ("contour_shape_match", dict(scale=1.1), 0.5),
             ("lightglue_disk", dict(rot=10), 1.0), ("lightglue_sift", dict(rot=10), 1.0)]
    for name, pose, tol in cases:
        try:
            m = METHODS.build(name)
        except METHODS.Unavailable as e:
            print(f"      (skipping {name}: {e})")
            continue
        live, P = render(SRC, **pose)
        r = m.align(live, SRC, MASK)
        err = pose_error(r.M, P)
        assert r.success and err < tol, f"{name} on {pose}: success={r.success} err={err} reason={r.reason}"
        assert np.isfinite(m.score(r)) and m.score_field in ("conf", "n_inl")
    ident = METHODS.build("identity").align(SRC, SRC, MASK)
    assert ident.success and np.allclose(ident.M, np.eye(3))


def test_rotation_search_finds_turned_parts():
    live, P = render(SRC, rot=90, tx=10, ty=5)
    plain = METHODS.build("phase_correlation").align(live, SRC, MASK)
    assert pose_error(plain.M, P) > 50                                       # a shift-only method cannot see a quarter turn
    m = METHODS.build("phase_correlation+rot", dict(step_deg=90, range_deg=360))
    assert m.name == "phase_correlation+rot" and m.family == "dense_global" and len(m.angles) == 4
    r = m.align(live, SRC, MASK)
    assert pose_error(r.M, P) < 1.5 and "best of 4 angles" in r.reason, (pose_error(r.M, P), r.reason)
    turned, R = __import__("inspalign.methods.rotsearch", fromlist=["x"]).rotate_with_canvas(SRC, 37)
    assert turned.shape[0] > SRC.shape[0] and np.allclose(G.apply(R, [[383.5, 287.5]])[0], [(turned.shape[1] - 1) / 2, (turned.shape[0] - 1) / 2], atol=1.0)
    if _learned_installed():                                                 # DISK is not rotation invariant; the search fixes that
        live, P = render(SRC, rot=120, tx=-8, ty=6)
        r = METHODS.build("lightglue_disk+rot", dict(step_deg=30, range_deg=360)).align(live, SRC, MASK)
        assert r.success and pose_error(r.M, P) < 2.0, (pose_error(r.M, P), r.reason)
    else:
        print("      (skipping lightglue_disk+rot: LightGlue not installed)")


def test_learned_matchers_build_or_are_reported_unavailable():
    for name in ("lightglue_disk", "lightglue_sift"):
        try:
            METHODS.build(name)
            assert _learned_installed(), f"{name} built without torch/lightglue?"
        except METHODS.Unavailable:
            assert not _learned_installed(), f"{name} reported unavailable although torch, kornia and lightglue are installed"


def test_contour_declared_range_and_no_mask():
    m = METHODS.build("contour_shape_match")
    live, P = render(SRC, rot=20)                                  # outside the default declared +/-15 deg: never accepted
    r = m.align(live, SRC, MASK)
    assert not r.success
    live, P = render(SRC, tx=1, ty=-1)                             # no mask: the whole golden is the model
    r = m.align(live, SRC, None)
    assert r.success and pose_error(r.M, P) < 0.5, r.reason
    wide = METHODS.build("contour_shape_match", dict(max_rotation_deg=180))
    live, P = render(SRC, rot=90)
    r = wide.align(live, SRC, MASK)
    assert r.success and r.checks_ok and pose_error(r.M, P) < 0.5, r.reason
    strict = METHODS.build("contour_shape_match", dict(min_score=0.999))   # a score below the threshold: rejected, checks still ok
    r = strict.align(render(SRC, rot=3)[0], SRC, MASK)
    assert not r.success and r.checks_ok and "edge score" in r.reason


def test_landmark_store():
    import make_demo
    with tempfile.TemporaryDirectory() as tmp:
        root = os.path.join(tmp, "store")
        truth = make_demo.build_landmarks(root)
        pairs, notes = A.discover_pairs(root)
        assert {p.pair_id for p in pairs} == set(truth) and len(pairs) == 16, sorted(p.pair_id for p in pairs)
        assert any("golden_b" in w and "source_hash" in m for w, m in notes)                 # hash mismatch is reported
        for p in pairs:
            gt = A.load_ground_truth(p)
            res = np.hypot(*(G.apply(truth[p.pair_id], gt.live_pts) - gt.tpl_pts).T)
            assert res.mean() < 1.2 and res.max() < 2.5, (p.pair_id, res)
            assert p.expect_template_size == (768, 576) and p.expect_live_size == (768, 576)
        p2 = next(p for p in pairs if p.pair_id == "RegionA/board_002")
        g2 = A.load_ground_truth(p2)
        assert len(g2.names) == 7 and any("hidden by a cable" in n for n in g2.notes) and any("pt8" in n for n in g2.notes)
        a = A.load_ground_truth(p2, "center"); b = A.load_ground_truth(p2, "corner")            # corner convention: -0.5 px
        assert np.allclose(a.tpl_pts - 0.5, b.tpl_pts) and np.allclose(a.live_pts - 0.5, b.live_pts)
        os.remove(os.path.join(root, "templates", "RegionA", "golden_template.png"))           # missing golden: reported
        pairs2, notes2 = A.discover_pairs(root)
        assert not any(p.group == "RegionA" for p in pairs2) and any("golden image not found" in m for _, m in notes2)
        pairs3, _ = A.discover_pairs(root, templates={"RegionA": os.path.join(root, "templates", "RegionB", "golden_template.png")})
        assert any(p.group == "RegionA" for p in pairs3)                                       # explicit mapping wins
        make_demo.build_landmarks(root)
        out = os.path.join(tmp, "out")
        r = _evaluate(["--data", root, "--out", out, "--methods", "identity,sift_ransac", "--quiet", "--overlays", "none"]); assert r.returncode == 0, r.stderr
        pp = pd.read_csv(os.path.join(out, "pairs.csv")).set_index("pair_id")
        assert "only 2 point" in pp.loc["RegionA/board_004", "status"]
        assert all("stale points" in pp.loc[f"RegionC/board_00{k}", "status"] for k in range(1, 5))
        res = pd.read_csv(os.path.join(out, "results.csv"))
        assert res.pair_id.nunique() == 11 and (res[res.method == "sift_ransac"].outcome == "correct").all()
        assert (res[res.method == "sift_ransac"].score == res[res.method == "sift_ransac"].n_inl).all()   # its decision score
        st = json.load(open(os.path.join(root, "landmarks.json")))                            # a point outside the image
        st["regions"]["RegionA"]["images"][0]["points"]["pt1"] = [900.0, 10.0]
        json.dump(st, open(os.path.join(root, "landmarks.json"), "w"))
        out2 = os.path.join(tmp, "out2")
        r = _evaluate(["--data", root, "--out", out2, "--methods", "identity", "--quiet", "--overlays", "none"]); assert r.returncode == 0, r.stderr
        assert "outside the 768x576 test image" in pd.read_csv(os.path.join(out2, "pairs.csv")).set_index("pair_id").loc["RegionA/board_001", "status"]


def test_golden_is_never_paired_with_itself_and_floor_is_shown_per_golden():
    with tempfile.TemporaryDirectory() as tmp:
        root = os.path.join(tmp, "store")
        rng = np.random.default_rng(3)
        corners = [(60, 50), (260, 50), (260, 190), (60, 190)]
        imgs, pts = {}, {}
        for i in range(4):                                         # four textured images; 000 and 001 are also the goldens
            im = np.full((240, 320, 3), 40, np.uint8); cv2.rectangle(im, (60, 50), (260, 190), (200, 200, 200), -1)
            for _ in range(40):
                cv2.circle(im, (int(rng.integers(70, 250)), int(rng.integers(60, 180))), 2, (120, 120, 120), -1)
            imgs[i] = im
            pts[i] = np.array(corners, float) + rng.normal(0, 1.0 + 2 * i, (4, 2))       # later images clicked less carefully
        _store(root, "R", {"g0": (imgs[0], pts[0]), "g1": (imgs[1], pts[1])}, {f"{i:03d}.png": (imgs[i], pts[i]) for i in range(4)}, "abcd")
        pairs, notes = A.discover_pairs(root)
        ids = sorted(p.pair_id for p in pairs)
        assert ids == ["R/g0/001", "R/g0/002", "R/g0/003", "R/g1/000", "R/g1/002", "R/g1/003"], ids
        assert sum("golden image" in m for _, m in notes) == 2, notes
        out = os.path.join(tmp, "out")
        r = _evaluate(["--data", root, "--out", out, "--methods", "identity", "--overlays", "none", "--quiet"]); assert r.returncode == 0, r.stderr
        rep = open(os.path.join(out, "summary", "SUMMARY.md"), encoding="utf-8").read()
        assert "per golden" in rep and os.path.isfile(os.path.join(out, "summary", "floor_per_group.csv"))
        fpg = pd.read_csv(os.path.join(out, "summary", "floor_per_group.csv"))
        assert sorted(fpg.group) == ["R/g0", "R/g1"] and (fpg.pairs == 3).all()


def test_mirrored_labels_are_refused_and_centre_points_follows_each_golden():
    with tempfile.TemporaryDirectory() as tmp:
        root = os.path.join(tmp, "store")

        def bar(cx, cy):                                           # a plain bar: 2-fold symmetric about its centre
            im = np.full((300, 400, 3), 30, np.uint8); cv2.rectangle(im, (cx - 120, cy - 40), (cx + 120, cy + 40), (210, 210, 210), -1)
            return im, np.array([[cx - 120.0, cy - 40.0], [cx + 120.0, cy - 40.0], [cx + 120.0, cy + 40.0], [cx - 120.0, cy + 40.0]])
        g0, g1, (im, p) = bar(200, 150), bar(170, 120), bar(215, 160)
        turned = p[[2, 3, 0, 1]]                                   # labelled after a half turn
        mirrored = p[[1, 0, 3, 2]]                                 # labels go round the other way
        _store(root, "R", {"g0": g0, "g1": g1}, {"t_ok.png": (im, turned), "t_mirror.png": (cv2.flip(im, 0), mirrored)}, ["TL", "TR", "BR", "BL"])
        shift = {"R/g0/t_ok": np.hypot(15, 10), "R/g1/t_ok": np.hypot(45, 40)}
        for tag, sym in (("points", {"order": 2, "center": "points"}), ("cycle", {"order": 2, "cycle": ["TL", "TR", "BR", "BL"]}),
                         ("fixed", {"order": 2, "center": [200.0, 150.0]})):
            cfg = os.path.join(tmp, f"{tag}.yaml"); out = os.path.join(tmp, f"out_{tag}")
            open(cfg, "w").write("symmetry: " + json.dumps({"R": sym}) + "\n")
            r = _evaluate(["--config", cfg, "--data", root, "--out", out, "--methods", "identity", "--tau-px", "2", "--overlays", "none", "--quiet"])
            assert r.returncode == 0, r.stderr
            pr = pd.read_csv(os.path.join(out, "pairs.csv")); res = pd.read_csv(os.path.join(out, "results.csv"))
            bad = pr[pr.pair_id.str.endswith("t_mirror")]
            assert len(bad) == 2 and bad.status.str.contains("MIRROR").all(), bad.status.tolist()
            idn = res[res.pair_id.str.endswith("t_ok")].set_index("pair_id").err_mean_px
            # identity's pose is the true one up to the shift between the pieces once the half-turned labels are understood
            if tag in ("points", "cycle"):
                assert all(abs(idn[k] - v) < 0.01 for k, v in shift.items()), (tag, idn)
                assert (res[res.pair_id.str.endswith("t_ok")].sym_rot_deg == 180).all()
            else:                                                  # a fixed centre is right for g0 only, and the log says so
                assert abs(idn["R/g0/t_ok"] - shift["R/g0/t_ok"]) < 0.01 and abs(idn["R/g1/t_ok"] - shift["R/g1/t_ok"]) > 20, idn
                assert "one fixed centre" in open(os.path.join(out, "run.log"), encoding="utf-8").read()


def test_symmetric_part_scoring():
    """An annotator who starts from a different (identical) feature labels the test points one sector round. With the
    symmetry declared, a correct alignment is scored against the nearest equivalent; without it, it is wrong. On an
    irregular part (features not exactly 60 deg apart) the label shift judges against the golden's real features, while an
    ideal turn about the centre is off by the irregularity."""
    import yaml
    src = synth.make_part(seed=7, shape="disc", dark_bg=True)
    H, W = src.shape[:2]
    c = np.array([(W - 1) / 2, (H - 1) / 2])
    P = G.translation(8, -5) @ G.rotation_about(10, tuple(c))                                # golden -> test
    live = cv2.warpAffine(src, P[:2], (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    ang = np.radians(np.array([0, 57, 121, 183, 236, 302]))                                 # six features, unevenly spaced
    t = np.vstack([c + 150 * np.column_stack([np.cos(ang), np.sin(ang)]), [c]])
    names = [f"s{i}" for i in range(6)] + ["centre"]
    l = G.apply(P, t[[1, 2, 3, 4, 5, 0, 6]])                                                # labels start one feature further
    with tempfile.TemporaryDirectory() as tmp:
        root = os.path.join(tmp, "sym")
        _store(root, "Full", {"000": (src, t)}, {"001.png": (live, l)}, names)
        res = {}
        for tag, sym in (("plain", {}), ("cycle", {"Full": {"order": 6, "cycle": names[:6]}}),
                         ("centre", {"Full": {"order": 6, "center": "centre"}})):
            cfgp = os.path.join(tmp, f"{tag}.yaml")
            yaml.safe_dump({"symmetry": sym}, open(cfgp, "w"))
            out = os.path.join(tmp, tag)
            r = _evaluate(["--config", cfgp, "--data", root, "--out", out, "--methods", "identity,sift_ransac", "--quiet", "--overlays", "none"])
            assert r.returncode == 0, r.stderr
            res[tag] = pd.read_csv(os.path.join(out, "results.csv")).set_index("method")
        assert res["plain"].loc["sift_ransac", "outcome"] == "silent_wrong"
        s_ = res["cycle"].loc["sift_ransac"]
        assert s_.outcome == "correct" and s_.err_mean_px < 0.5 and s_.sym_rot_deg in (60.0, 300.0), s_
        assert s_.err_mean_strict_px > 50 and abs(s_.err_mean_strict_px - res["plain"].loc["sift_ransac", "err_mean_px"]) < 1e-6
        c_ = res["centre"].loc["sift_ransac"]                                                  # the ideal turn misses by the irregularity
        assert c_.err_mean_px > 5 and c_.err_mean_px < 30, c_
        md = open(os.path.join(tmp, "cycle", "summary", "SUMMARY.md"), encoding="utf-8").read()
        assert "Symmetry-aware scoring for: Full" in md and "correct_via_symmetry" in md
        assert "label shift" in open(os.path.join(tmp, "cycle", "run.log"), encoding="utf-8").read()


def test_config_refusals():
    with tempfile.TemporaryDirectory() as tmp:
        bad = os.path.join(tmp, "c.yaml")
        for text, expect in (('symmetry: {"Full": 4}\ntau_px: 3\nsymmetry: {}\n', "written twice"),
                             ('data:\n  symmetry: {"Full": 4}\n', "top level"),
                             ('symmetry: {"Full": {"order": 4, "cycle": ["a", "b", "c"]}}\n', "multiple of the order"),
                             ('methods:\n  - {name: sift_ransac_anms}\n', "removed in 0.7.2"),
                             ('methods:\n  - {name: identity+rot}\n', "unknown method")):
            open(bad, "w").write(text)
            try:
                E.load_config(bad)
                raise AssertionError(f"accepted: {text!r}")
            except SystemExit as e:
                assert expect in str(e), (expect, str(e))
    assert E.symmetry_for({"symmetry": {"Full": 4}}, "Full/golden_b")["order"] == 4 and E.symmetry_for({}, "Full") is None
    assert METHODS.unknown_method_message(["identity", "lightglue_disk+rot"]) is None


def test_evaluate_cli_end_to_end():
    import make_demo
    with tempfile.TemporaryDirectory() as tmp:
        root = os.path.join(tmp, "demo")
        make_demo.build_landmarks(root)
        out, part = os.path.join(tmp, "out"), os.path.join(tmp, "part")
        meth = "identity,phase_correlation,sift_ransac,contour_shape_match,lightglue_disk"
        r = _evaluate(["--data", root, "--out", out, "--methods", meth, "--overlays", "failures", "--quiet"]); assert r.returncode == 0, r.stderr
        r = _evaluate(["--data", root, "--out", out, "--methods", meth, "--quiet"]); assert r.returncode != 0     # refuses a used folder
        r = _evaluate(["--data", root, "--out", part, "--methods", meth, "--limit", "5", "--quiet", "--overlays", "none"]); assert r.returncode == 0, r.stderr
        r = _evaluate(["--data", root, "--out", part, "--methods", meth, "--resume", "--quiet", "--overlays", "none"]); assert r.returncode == 0, r.stderr
        res = pd.read_csv(os.path.join(out, "results.csv"))
        n_m = 5 if _learned_installed() else 4
        assert len(res) == 11 * n_m and res.pair_id.nunique() == 11
        a, b = (pd.read_csv(os.path.join(d, "results.csv")).drop(columns=["latency_ms"]).sort_values(["pair_id", "method"]).reset_index(drop=True) for d in (out, part))
        pd.testing.assert_frame_equal(a, b)                                                  # resumable, row for row
        pts = pd.read_csv(os.path.join(out, "points.csv"))                                    # identity's error = the raw misalignment
        idn = pts[pts.method == "identity"]
        raw = np.hypot(idn.live_x - idn.tpl_x, idn.live_y - idn.tpl_y).groupby(idn.pair_id).mean()
        mine = res[res.method == "identity"].set_index("pair_id").err_mean_px
        assert np.allclose(raw.sort_index(), mine.sort_index())
        g = res[res.method == "sift_ransac"]                                                  # at the click floor on these easy pairs
        assert (g.outcome == "correct").all() and (g.excess_px.dropna() < 0.3).all(), g[["pair_id", "err_mean_px", "excess_px"]]
        c = res[res.method == "contour_shape_match"]
        assert (c[c.pair_id.str.endswith("board_004")].outcome != "no_pose").all()
        small = os.path.join(tmp, "small")                                                    # shrinking must not add an offset
        r = _evaluate(["--data", root, "--out", small, "--methods", "sift_ransac", "--work-long-side", "384", "--quiet", "--overlays", "none"]); assert r.returncode == 0, r.stderr
        rs = pd.read_csv(os.path.join(small, "results.csv")).set_index("pair_id").err_mean_px
        assert (rs - g.set_index("pair_id").err_mean_px).abs().max() < 0.6
        for f in ("run.log", "points.csv", "pairs.csv", "manifest.json", "summary/SUMMARY.md", "summary/summary_methods.csv",
                  "summary/confidence.csv", "summary/risk_coverage.csv", "summary/goldens.csv"):
            assert os.path.exists(os.path.join(out, f)), f
        assert len(os.listdir(os.path.join(out, "gt_check"))) == 11
        man = json.load(open(os.path.join(out, "manifest.json")))
        if not _learned_installed():
            assert "lightglue_disk" in man["unavailable"]
        GS.summarize(out, tau_px=0.25)
        t = pd.read_csv(os.path.join(out, "summary_tau0.25", "summary_methods.csv"))
        assert t.set_index("method").loc["sift_ransac", "correct"] < 1.0                     # tau below the click floor


def test_summary_building_blocks():
    # risk / coverage and AUROC on a hand-made case
    score = np.array([9, 8, 7, 6, 5, 4, np.nan]); right = np.array([1, 1, 0, 1, 0, 0, 0], bool)
    rc = GS.risk_coverage(score, right, 7)
    assert list(rc.accepted) == [1, 2, 3, 4, 5, 6] and list(rc.wrong) == [0, 0, 1, 1, 2, 3]
    assert abs(GS.auroc(score, right) - (3 + 3 + 2) / 9) < 1e-12                           # 8 of the 9 right>wrong pairs
    assert np.isnan(GS.auroc([1, 2], [True, False]))
    # own pick among goldens: the highest score wins, the ground truth plays no part
    rows = []
    for test, (s_a, e_a, s_b, e_b) in {"t1": (10, 1.0, 50, 9.0), "t2": (30, 1.0, 20, 9.0), "t3": (5, 9.0, 4, 1.0)}.items():
        for gold, s, e in (("g1", s_a, e_a), ("g2", s_b, e_b)):
            rows.append(dict(method="m", region="R", golden=gold, test=test, score=s, err_mean_px=e, tau_px=2.0,
                             success_b=s >= 6, checks_ok_b=True, has_pose=True))
    df = pd.DataFrame(rows)
    pk = GS.own_pick(df, 2).set_index("test")
    assert list(pk.loc[["t1", "t2", "t3"], "golden"]) == ["g2", "g1", "g1"]
    assert list(pk.loc[["t1", "t2", "t3"], "outcome_pick"]) == ["silent_wrong", "correct", "rejected"]
    cal = GS.decide(df, {"m": {"threshold": 25.0}})
    assert list(cal) == [False, True, True, False, False, False]
    assert not GS.decide(df, {"m": {"threshold": None, "accept_none": True}}).any()
    assert list(GS.decide(df, {"other": {"threshold": 1.0}})) == list(df.success_b)           # no threshold: own rule


def test_calibration_store_and_fit():
    import make_demo
    from inspalign import calibrate as C
    with tempfile.TemporaryDirectory() as tmp:
        test = os.path.join(tmp, "test")
        make_demo.build_landmarks(test)
        st = json.load(open(os.path.join(test, "landmarks.json")))
        names = st["regions"]["RegionA"]["point_names"]
        extra = os.path.join(tmp, "extra"); os.makedirs(extra)
        src = cv2.imread(os.path.join(test, "templates", "RegionA", "golden_template.png"))
        exp = {"version": 1, "regions": {"RegionA": {"point_names": names, "templates": {}, "images": []}}}
        tp = st["regions"]["RegionA"]["templates"]["golden_template"]["points"]
        for k in range(2):
            live, P = render(src, rot=3 * (k + 1), tx=5)
            cv2.imwrite(os.path.join(extra, f"calib_{k}.png"), live)
            pts = {n: list(map(float, G.apply(P, [tp[n]])[0])) for n in names}
            exp["regions"]["RegionA"]["images"].append({"id": "", "filename": f"calib_{k}.png", "width": 768, "height": 576, "points": pts})
        ep = os.path.join(tmp, "export.json"); json.dump(exp, open(ep, "w"))
        out = os.path.join(tmp, "calib")
        assert C.build_store(test, ep, extra, out) == 2
        cs = json.load(open(os.path.join(out, "landmarks.json")))["regions"]["RegionA"]
        assert set(cs["templates"]) == {"golden_template"} and len(cs["images"]) == 2
        assert os.path.isfile(os.path.join(out, "templates", "RegionA", "golden_template.png"))
        pairs, _ = A.discover_pairs(out)
        assert len(pairs) == 2
        # a test image smuggled into the calibration set is refused, and nothing is written
        first = st["regions"]["RegionA"]["images"][0]
        shutil.copy(A.live_image(test, first), os.path.join(extra, "sneaky.png"))
        exp["regions"]["RegionA"]["images"].append(dict(first, filename="sneaky.png"))
        json.dump(exp, open(ep, "w"))
        try:
            C.build_store(test, ep, extra, os.path.join(tmp, "calib2"))
            raise AssertionError("a test image was accepted for calibration")
        except SystemExit as e:
            assert "must not be test images" in str(e) and not os.path.exists(os.path.join(tmp, "calib2"))
    # fitting: the lowest threshold with at most 5 % wrong among the accepted; a method that cannot get there accepts nothing
    with tempfile.TemporaryDirectory() as tmp:
        rows = []
        for i in range(20):
            for m, s, e in (("good", i, 1.0 if i >= 6 else 50.0), ("bad", i, 50.0 if i >= 6 else 1.0)):
                rows.append(dict(pair_id=f"R/{i}", group="R", method=m, success=s >= 3, reason="", score=s, checks_ok=True,
                                 conf=s, n_inl=s, err_mean_px=e, tau_px=2.0, template="g.png", live=f"{i}.png"))
        pd.DataFrame(rows).to_csv(os.path.join(tmp, "results.csv"), index=False)
        t = C.fit(tmp)
        assert t["methods"]["good"]["threshold"] == 6.0 and t["methods"]["good"]["risk"] == 0.0
        assert t["methods"]["bad"].get("accept_none") and t["tau_px"] == 2.0


def test_report_renders():
    from inspalign import report as R
    with tempfile.TemporaryDirectory() as tmp:
        runs = []
        rng = np.random.default_rng(0)
        for part in ("part_a", "part_b"):
            d = os.path.join(tmp, part); os.makedirs(d)
            rows = []
            for g in ("g1", "g2"):
                for i in range(12):
                    for m in ("sift_ransac", "contour_shape_match", "sift_ransac+rot"):
                        e = float(rng.uniform(0, 8)); s = float(rng.uniform(0, 30))
                        rows.append(dict(pair_id=f"Full/{g}/{i}", group=f"Full/{g}", method=m, family="x", success=s > 10, reason="",
                                         score=s, checks_ok=True, conf=s, n_inl=s, err_mean_px=e, tau_px=4.0, template=f"{g}.png",
                                         live=f"{i}.png", gt_rot_deg=float(rng.uniform(-90, 90)), latency_ms=10.0))
            pd.DataFrame(rows).to_csv(os.path.join(d, "results.csv"), index=False)
            runs.append(d)
        out = os.path.join(tmp, "report")
        R.main(runs + ["--out", out])
        for f in ("REPORT.md", "carousel.pdf", "fig1_correct.png", "fig2_outcomes.png", "fig3_confidence.png", "fig4_rotation.png", "fig5_goldens.png"):
            assert os.path.isfile(os.path.join(out, f)), f
        assert "SIFT + RANSAC + rotation search" in open(os.path.join(out, "REPORT.md"), encoding="utf-8").read()


TESTS = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]

if __name__ == "__main__":
    failed = 0
    for t in TESTS:
        try:
            t()
            print(f"ok    {t.__name__}")
        except Exception:
            failed += 1
            print(f"FAIL  {t.__name__}\n{traceback.format_exc()}")
    print(f"\n{len(TESTS) - failed}/{len(TESTS)} passed")
    sys.exit(1 if failed else 0)
