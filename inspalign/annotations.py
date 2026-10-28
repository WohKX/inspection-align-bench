"""Reading a landmark store: one golden (template) image or several, the test images, and the clicked landmark points.

A data folder holds (DATA_FORMAT.md has the full description):

    <root>/landmarks.json                      regions -> point names, the goldens' points, every test image's points
    <root>/images/<id or filename>.<ext>       the test images
    <root>/templates/<region>/<golden>.<ext>   the golden images (or mapped in the config: data.templates / data.template_image)

tools/landmark_picker.html writes landmarks.json. Every test image of a region is paired with every golden of that region;
only the points both images have are used. Coordinates are pixels of the ORIGINAL image files, x to the right, y down,
OpenCV convention (the centre of the top-left pixel is (0, 0)); `coord_origin: corner` subtracts 0.5 for click tools whose
(0, 0) is the corner of the top-left pixel.
"""
import hashlib
import json
import os
import re
from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np

IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff")


@dataclass
class Pair:
    pair_id: str
    group: str                                   # <region> with one golden, <region>/<golden> with several
    template_path: str
    live_path: str
    gt_path: str                                 # the landmarks.json the points come from
    template_mask_path: Optional[str] = None
    gt_inline: Optional[dict] = None             # {"template": {name: xy}, "live": {name: xy}, "note", "point_names", "where"}
    expect_template_size: Optional[tuple] = None  # (w, h) of the golden the points were clicked on
    expect_live_size: Optional[tuple] = None      # (w, h) of the test image the points were clicked on


@dataclass
class GroundTruth:
    """Corresponding points: live_pts[i] (test image) shows the same physical spot as tpl_pts[i] (golden image).
    Both (N, 2), OpenCV pixel convention, original image pixels."""
    tpl_pts: np.ndarray
    live_pts: np.ndarray
    names: List[str]
    notes: List[str] = field(default_factory=list)


class AnnotationError(ValueError):
    pass


def _natural_key(s):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", str(s))]


def _find_by_stem(folder, stem, exts=IMAGE_EXTS):
    for e in exts:
        for cand in (e, e.upper()):
            p = os.path.join(folder, stem + cand)
            if os.path.isfile(p):
                return p
    return None


def sha1_12(path):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:12]


def read_store(root):
    """The parsed landmarks.json of a data folder (raises AnnotationError with the file name on any problem)."""
    path = os.path.join(root, "landmarks.json")
    if not os.path.isfile(path):
        raise FileNotFoundError(f"no landmarks.json in {root} (see DATA_FORMAT.md; tools/landmark_picker.html writes it)")
    try:
        with open(path, encoding="utf-8-sig") as f:
            store = json.load(f)
    except Exception as e:
        raise AnnotationError(f"{path}: {type(e).__name__}: {e}") from e
    if not isinstance(store, dict) or not isinstance(store.get("regions"), dict):
        raise AnnotationError(f"{path}: no 'regions' object")
    return store, path


def template_image(root, region, tname, templates=None, template_image=None):
    """The golden image of (region, golden name). Looked up in this order:
    data.templates["<region>/<golden>"], data.templates["<region>"], data.templates["<golden>"], data.template_image,
    then <root>/templates/<region>/<golden>.<ext>, <root>/templates/<region>.<ext>, <root>/templates/<golden>.<ext>."""
    templates = templates or {}
    ab = lambda p: p if os.path.isabs(p) else os.path.join(root, p)
    for key in (f"{region}/{tname}", region, tname):
        if key in templates and templates[key]:
            p = ab(str(templates[key]))
            return p if os.path.isfile(p) else None
    if template_image:
        p = ab(str(template_image))
        return p if os.path.isfile(p) else None
    tdir = os.path.join(root, "templates")
    return (_find_by_stem(os.path.join(tdir, region), tname) or _find_by_stem(tdir, region) or _find_by_stem(tdir, tname))


def live_image(root, im):
    """The file of one test-image entry: images/<id>.<ext>, else images/<filename>; None if neither exists."""
    img_dir = os.path.join(root, "images")
    iid = str(im.get("id") or "")
    fn = str(im.get("filename") or iid)
    p = _find_by_stem(img_dir, iid) if iid else None
    if p is None and fn and os.path.isfile(os.path.join(img_dir, fn)):
        p = os.path.join(img_dir, fn)
    return p


def discover_pairs(root, templates=None, template_image_path=None):
    """-> (pairs, notes). notes: list of (what, message) for anything worth a line in the log: goldens not found, images not
    found, a golden whose file no longer matches its source_hash, a test image that IS a golden (never paired with itself)."""
    root = os.path.abspath(root)
    if not os.path.isdir(root):
        raise FileNotFoundError(f"data folder not found: {root}")
    store, store_path = read_store(root)
    pairs, notes = [], []
    if store.get("version", 1) != 1:
        notes.append((store_path, f"version {store.get('version')!r} is not known; read as version 1"))
    for region in sorted(store["regions"], key=_natural_key):
        d = store["regions"][region] or {}
        point_names = [str(n) for n in d.get("point_names") or []]
        tpls = d.get("templates") or {}
        if not tpls:
            notes.append((region, "no golden points in this region; skipped"))
            continue
        resolved = []
        for tname in sorted(tpls, key=_natural_key):
            t = tpls[tname] or {}
            path = template_image(root, region, tname, templates, template_image_path)
            if path is None:
                notes.append((f"{region}/{tname}", f"golden image not found: put it at templates/{region}/{tname}.png next to "
                                                   f"landmarks.json, or map it in the config (data.templates); its pairs are skipped"))
                continue
            th = sha1_12(path)
            sh = t.get("source_hash")
            if sh and th != str(sh):
                notes.append((f"{region}/{tname}", f"{os.path.basename(path)}: its sha1 does not start with source_hash {sh}. "
                                                   f"If the golden was replaced after the points were clicked, they are stale "
                                                   f"(check gt_check/)"))
            size = t.get("size")
            resolved.append((tname, path, t, tuple(int(v) for v in size) if size else None, th))
        seen = set()
        for im in d.get("images") or []:
            fn = str(im.get("filename") or im.get("id") or "")
            live = live_image(root, im)
            if live is None:
                notes.append((f"{region}/{fn}", f"image file images/{im.get('id') or fn} not found; skipped"))
                continue
            stem = os.path.splitext(os.path.basename(fn))[0]
            wh = (int(im["width"]), int(im["height"])) if im.get("width") and im.get("height") else None
            live_hash = sha1_12(live)
            for tname, tpath, t, tsize, th in resolved:
                if live_hash == th:             # the golden image itself: a golden is never scored against itself
                    notes.append((f"{region}/{fn}", f"this image is the golden image '{tname}' itself (same file content); "
                                                    f"not paired with it"))
                    continue
                group = f"{region}/{tname}" if len(resolved) > 1 else region
                pid = f"{group}/{stem}"
                if pid in seen:
                    pid = f"{pid}#{im.get('id')}"
                seen.add(pid)
                inline = dict(template=t.get("points") or {}, live=im.get("points") or {}, note=str(im.get("note") or ""),
                              point_names=point_names, where=f"{os.path.basename(store_path)} {region}/{fn}")
                tmask = _find_by_stem(os.path.dirname(tpath), os.path.splitext(os.path.basename(tpath))[0] + "_mask")
                pairs.append(Pair(pid, group, tpath, live, store_path, template_mask_path=tmask, gt_inline=inline,
                                  expect_template_size=tsize, expect_live_size=wh))
    return pairs, notes


def _xy(v, where):
    try:
        if isinstance(v, dict):
            v = [v["x"], v["y"]]
        a = np.asarray(v, dtype=np.float64).reshape(-1)
        if a.size != 2 or not np.all(np.isfinite(a)):
            raise ValueError
        return a
    except Exception:
        raise AnnotationError(f"{where}: expected a point [x, y], got {v!r}")


def load_ground_truth(pair: Pair, coord_origin="center"):
    """The corresponding points of one pair: the names both images have, in the store's point order."""
    if coord_origin not in ("center", "corner"):
        raise ValueError("coord_origin must be 'center' or 'corner'")
    shift = -0.5 if coord_origin == "corner" else 0.0
    g = pair.gt_inline or {}
    where = g.get("where", pair.gt_path)
    tn = {str(k): _xy(v, f"{where} golden '{k}'") for k, v in (g.get("template") or {}).items()}
    ln = {str(k): _xy(v, f"{where} '{k}'") for k, v in (g.get("live") or {}).items()}
    order = list(g.get("point_names") or []) + sorted((set(tn) | set(ln)) - set(g.get("point_names") or []), key=_natural_key)
    common = [n for n in order if n in tn and n in ln]
    notes = []
    miss_l = [n for n in order if n in tn and n not in ln]
    miss_t = [n for n in order if n in ln and n not in tn]
    if miss_l:
        notes.append(f"not marked on this image: {','.join(miss_l)}")
    if miss_t:
        notes.append(f"not marked on the golden: {','.join(miss_t)}")
    if g.get("note"):
        notes.append(f"note: {g['note']}")
    if not common:
        raise AnnotationError(f"{where}: no point in common with the golden")
    t = np.array([tn[k] for k in common]).reshape(-1, 2)
    l = np.array([ln[k] for k in common]).reshape(-1, 2)
    return GroundTruth(t + shift, l + shift, common, notes=notes)


def file_digest(paths):
    """sha256 over the bytes of the given files (in order): ties a result folder to the exact data it was computed from."""
    h = hashlib.sha256()
    for p in paths:
        h.update(os.path.basename(p).encode())
        if p and os.path.isfile(p):
            with open(p, "rb") as f:
                for chunk in iter(lambda: f.read(1 << 20), b""):
                    h.update(chunk)
    return h.hexdigest()[:16]
