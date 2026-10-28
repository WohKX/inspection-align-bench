"""Writes a small demo landmark store (synthetic parts, known poses, "clicked" points with a little noise), so the data layout
in DATA_FORMAT.md can be seen and evaluate.py tried end to end without any dataset:

    python tests/make_demo.py                       # -> data/demo
    python evaluate.py --data data/demo --out results/demo

RegionA: one golden; one image misses a point (with a note), one has only 2 points (skipped: fewer than 3).
RegionB: two goldens (every image is evaluated against both); the second one's source_hash does not match its file.
RegionC: its golden file is not the size the points were clicked on (stale points: every pair is refused).
"""
import json
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import synth  # noqa: E402
from inspalign import geometry as G  # noqa: E402
from inspalign import masks as MK  # noqa: E402

# (rotation deg, scale, shift x px, shift y px) of the live image relative to the template; the last one is outside the
# shape arm's default declared range (+/-15 deg), on purpose
POSES = [(0.0, 1.0, 3.0, -2.0), (4.0, 1.0, 18.0, 7.0), (-9.0, 1.02, -25.0, 12.0), (12.0, 0.97, 30.0, -20.0), (25.0, 1.0, -10.0, 15.0)]


def landmarks(mask, n, rng):
    """n template points inside the part (away from its border), well spread."""
    core = cv2.erode((mask > 0).astype(np.uint8), np.ones((15, 15), np.uint8))
    ys, xs = np.nonzero(core)
    pts = [np.array([xs[len(xs) // 2], ys[len(ys) // 2]], float)]
    cand = np.column_stack([xs, ys]).astype(float)[rng.choice(len(xs), min(4000, len(xs)), replace=False)]
    while len(pts) < n:                                      # farthest-point sampling
        d = np.min(np.hypot(cand[:, None, 0] - np.array(pts)[None, :, 0], cand[:, None, 1] - np.array(pts)[None, :, 1]), axis=1)
        pts.append(cand[int(np.argmax(d))])
    return np.array(pts) + rng.uniform(-0.5, 0.5, (n, 2))   # sub-pixel, like a click


def make_live(src, rot, scale, sx, sy, rng):
    """live = template rendered under pose P (template -> live). Returns (live image, P)."""
    H, W = src.shape[:2]
    c = ((W - 1) / 2.0, (H - 1) / 2.0)
    P = G.translation(sx, sy) @ G.rotation_about(rot, c) @ G.scaling_about(scale, c)
    live = cv2.warpAffine(src, P[:2], (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    gain = rng.uniform(0.9, 1.1)
    live = np.clip(live.astype(np.float32) * gain + rng.normal(0, 2.0, live.shape), 0, 255).astype(np.uint8)
    return live, P


def _png_with_id(img, folder):
    """Write img as <sha1 of the PNG bytes, 12 hex>.png (the landmark store's id convention); returns the id."""
    import hashlib
    ok, buf = cv2.imencode(".png", img)
    iid = hashlib.sha1(buf.tobytes()).hexdigest()[:12]
    buf.tofile(os.path.join(folder, iid + ".png"))
    return iid


def build_landmarks(out, click_noise_px=0.3, seed=1, n_points=8):
    """A landmark store (DATA_FORMAT.md, layout C): landmarks.json + images/<id>.png + templates/<region>/<template>.png.
    RegionA: one template; one image misses a point (with a note), one has only 2 points (skipped: fewer than 3).
    RegionB: two templates (every image is evaluated against both); the second one's source_hash does not match its file.
    RegionC: its template file is not the size the points were clicked on (stale points: every pair is refused).
    Returns {pair_id: exact live -> template matrix}."""
    import hashlib
    rng = np.random.default_rng(seed)
    os.makedirs(os.path.join(out, "images"), exist_ok=True)
    store = {"version": 1, "regions": {}}
    truth = {}
    names = [f"pt{i + 1}" for i in range(n_points)]
    for ri, (region, shape, dark) in enumerate([("RegionA", "plate", True), ("RegionB", "lshape", False), ("RegionC", "disc", True)]):
        src = synth.make_part(seed=40 + ri, shape=shape, dark_bg=dark)
        H, W = src.shape[:2]
        tdir = os.path.join(out, "templates", region)
        os.makedirs(tdir, exist_ok=True)
        mask, _ = MK.object_mask(src)
        tpts = landmarks(mask, n_points, rng)
        templates = {"golden_template": (src, np.eye(3))}
        if region == "RegionB":                                     # a second reference: the same part, shifted by (6, -4) px
            templates["golden_b"] = (cv2.warpAffine(src, G.translation(6, -4)[:2], (W, H), borderMode=cv2.BORDER_REPLICATE), G.translation(6, -4))
        tjson = {}
        for tname, (timg, A_) in templates.items():
            path = os.path.join(tdir, tname + ".png")
            if region == "RegionC":                                 # stale: the file on disk was replaced by a bigger capture
                cv2.imwrite(path, cv2.copyMakeBorder(timg, 0, 16, 0, 16, cv2.BORDER_REPLICATE))
            else:
                cv2.imwrite(path, timg)
            sha = hashlib.sha1(open(path, "rb").read()).hexdigest()[:12]
            pts_t = G.apply(A_, tpts)
            tjson[tname] = {"size": [W, H], "source_hash": sha if tname != "golden_b" else "000000000000",
                            "points": {n: [round(float(x), 2), round(float(y), 2)] for n, (x, y) in zip(names, pts_t)}}
        images = []
        for k, (rot, sc, sx, sy) in enumerate(POSES[:4], 1):
            live, P = make_live(src, rot, sc, sx, sy, rng)
            iid = _png_with_id(live, os.path.join(out, "images"))
            lpts = G.apply(P, tpts) + rng.normal(0, click_noise_px, tpts.shape)
            keep = list(range(n_points))
            note = ""
            if region == "RegionA" and k == 2:
                keep, note = keep[:-1], f"{names[-1]} hidden by a cable"
            if region == "RegionA" and k == 4:
                keep = keep[:2]
            images.append({"id": iid, "filename": f"board_{k:03d}.png", "width": W, "height": H, "added": "2026-10-05T09:07:41",
                           "points": {names[i]: [round(float(lpts[i, 0]), 2), round(float(lpts[i, 1]), 2)] for i in keep}, "note": note})
            for tname, (_, A_) in templates.items():
                group = f"{region}/{tname}" if len(templates) > 1 else region
                truth[f"{group}/board_{k:03d}"] = A_ @ np.linalg.inv(P)
        store["regions"][region] = {"point_names": names, "templates": tjson, "images": images}
    with open(os.path.join(out, "landmarks.json"), "w", encoding="utf-8") as f:
        json.dump(store, f, indent=1)
    return truth


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join("data", "demo")
    build_landmarks(out)
    print(f"wrote {out}")
