"""Shape-based matching: edge-direction agreement over a bounded, coarse-to-fine pose search, then a sub-pixel
least-squares fit of the template's edges to the live image's edges.

Written for this repository from the published method; it does not reuse code from any other project.

References
  C. Steger, "Similarity measures for occlusion, clutter, and illumination invariant object recognition",
      DAGM 2001, LNCS 2191, pp. 148-154.  (the score below, eq. 2 and its polarity-ignoring variant)
  C. Steger, "Occlusion, clutter, and illumination invariant object recognition", ISPRS Archives XXXIV-3A, 2002.
      (image pyramid, exhaustive search on the top level, tracking of candidates down the pyramid)

How it works
  1. Model. Edge points of the TEMPLATE (gradient magnitude above a contrast floor, thinned by non-maximum suppression),
     restricted to the template mask grown by a few pixels so the part's own outline is included with its real polarity.
     Each point keeps its unit gradient direction. Coordinates are relative to a reference point (the mask centroid).
  2. Score. For a pose (rotation, scale, position of the reference point in the live image) the model points are mapped
     into the live image and the score is the mean cosine between each model direction (rotated by the pose) and the live
     image's gradient direction there (Steger's normalised measure). Only model points are evaluated, so extra edges in the
     live image cannot raise the score; a missing edge (occlusion) contributes 0. Range: 0..1 ("respect" polarity; negative
     values are clipped) and invariant to contrast changes.
  3. Search. Gaussian pyramid of both images. On the top level every pose inside the DECLARED RANGE is scored (rotation step
     ~ 1 px of arc at the model's outermost point, scale step likewise, every pixel of position). The best distinct
     candidates are tracked down the pyramid with a small local search on each level.
  4. Refinement. At full resolution each model point looks for the live edge along its normal (+/- 2 px, sub-pixel by a
     parabola through the gradient profile), and the similarity that minimises the point-to-edge-line distances is solved
     by iteratively re-weighted linear least squares (a similarity a,b,tx,ty enters the point-to-line residual linearly).
  5. Decision. Accepted when the final score >= min_score AND the refined pose lies inside the declared range.

Declared range = configuration. The search cannot return a pose outside max_rotation_deg / max_scale_deviation /
max_translation_ratio (rotation and scale of the live->template map; translation = how far the part's reference point
moves, as a fraction of the template width). A pose outside that range is reported as "no pose inside the declared range",
which is a limit of the configuration, not a property of the method. The benchmark records `in_declared_range` per attempt.

Cost grows with the declared range (rotation range x scale range x translation area on the top pyramid level) and with the
number of model points, not with clutter in the live image.
"""
import cv2
import numpy as np

from .. import geometry as G
from .base import Method, Result


# ---------------------------------------------------------------------------------------------------------------------------
# image helpers

def _gradients(gray_f32):
    """Per-pixel derivative estimates (Sobel / 8), float32."""
    gx = cv2.Sobel(gray_f32, cv2.CV_32F, 1, 0, ksize=3) / 8.0
    gy = cv2.Sobel(gray_f32, cv2.CV_32F, 0, 1, ksize=3) / 8.0
    return gx, gy


def _edge_points(gx, gy, region, min_contrast, rel_contrast):
    """Thin edge points inside `region` (bool): magnitude >= max(min_contrast, rel_contrast * p99 of the region's magnitudes)
    and a local maximum along the gradient direction (4-direction non-maximum suppression). Returns (xs, ys, ux, uy)."""
    mag = np.hypot(gx, gy)
    vals = mag[region]
    if vals.size == 0:
        return (np.zeros(0, np.float32),) * 4
    thr = max(float(min_contrast), float(rel_contrast) * float(np.percentile(vals, 99)))
    cand = region & (mag >= thr)
    cand[:1, :] = cand[-1:, :] = False
    cand[:, :1] = cand[:, -1:] = False
    ys, xs = np.nonzero(cand)
    if len(xs) == 0:
        return (np.zeros(0, np.float32),) * 4
    ang = (np.degrees(np.arctan2(gy[ys, xs], gx[ys, xs])) + 180.0) % 180.0          # gradient direction mod 180
    q = np.zeros(len(xs), np.int8)                                                  # 0: horizontal, 1: 45, 2: vertical, 3: 135
    q[(ang >= 22.5) & (ang < 67.5)] = 1
    q[(ang >= 67.5) & (ang < 112.5)] = 2
    q[(ang >= 112.5) & (ang < 157.5)] = 3
    dx = np.array([1, 1, 0, -1])[q]
    dy = np.array([0, 1, 1, 1])[q]
    m = mag[ys, xs]
    keep = (m >= mag[ys + dy, xs + dx]) & (m > mag[ys - dy, xs - dx])
    xs, ys, m = xs[keep], ys[keep], m[keep]
    ux, uy = gx[ys, xs] / m, gy[ys, xs] / m
    return xs.astype(np.float32), ys.astype(np.float32), ux.astype(np.float32), uy.astype(np.float32)


def _subsample(n, n_max):
    """Deterministic, evenly spread subset of range(n) of size <= n_max (raster order is spatially spread)."""
    if n <= n_max:
        return np.arange(n)
    return np.linspace(0, n - 1, n_max).round().astype(int)


class _Level:
    """One pyramid level: the model (template edge points relative to the reference point) and the live direction field."""

    def __init__(self, tpl, live, region, ref, min_contrast, rel_contrast, max_points):
        tgx, tgy = _gradients(tpl)
        xs, ys, ux, uy = _edge_points(tgx, tgy, region, min_contrast, rel_contrast)
        keep = _subsample(len(xs), max_points)
        self.px = (xs[keep] - ref[0]).astype(np.float32)
        self.py = (ys[keep] - ref[1]).astype(np.float32)
        self.dx, self.dy = ux[keep], uy[keep]
        self.n = len(self.px)
        self.radius = float(np.hypot(self.px, self.py).max()) if self.n else 0.0
        lgx, lgy = _gradients(live)
        mag = np.hypot(lgx, lgy)
        ok = mag >= 0.5 * min_contrast                       # flat regions: no direction (contributes 0)
        self.lux = np.where(ok, lgx / np.maximum(mag, 1e-6), 0).astype(np.float32)
        self.luy = np.where(ok, lgy / np.maximum(mag, 1e-6), 0).astype(np.float32)
        self.lgx, self.lgy = lgx, lgy                        # raw gradients, for the sub-pixel refinement
        self.h, self.w = live.shape
        self._pad = None

    def padded(self, need):
        """The live direction field with a zero border of at least `need` pixels (grown in steps, then reused)."""
        if self._pad is None or self._pad[3] < need:
            pad = int(need * 1.25) + 4
            ux = cv2.copyMakeBorder(self.lux, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=0)
            uy = cv2.copyMakeBorder(self.luy, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=0)
            self._pad = (ux.ravel(), uy.ravel(), ux.shape[1], pad)
        return self._pad


def _score_window(level, theta_deg, scale, cx0, cy0, ww, wh, polarity):
    """Score map for all reference-point positions (cx0 .. cx0+ww-1, cy0 .. cy0+wh-1) at one rotation and scale
    (nearest-pixel lookup). Returns an (wh, ww) float32 array."""
    t = np.radians(theta_deg)
    c, s = np.cos(t), np.sin(t)
    ox = np.rint(scale * (c * level.px - s * level.py)).astype(np.int64)
    oy = np.rint(scale * (s * level.px + c * level.py)).astype(np.int64)
    rdx = (c * level.dx - s * level.dy).astype(np.float32)
    rdy = (s * level.dx + c * level.dy).astype(np.float32)
    need = int(max(np.abs(ox).max(initial=0), np.abs(oy).max(initial=0))) + 2
    ux, uy, wp, pad = level.padded(need)
    gx, gy = np.meshgrid(np.arange(cx0, cx0 + ww), np.arange(cy0, cy0 + wh))
    base = ((gy + pad) * wp + (gx + pad)).ravel()                              # (P,)
    idx = base[:, None] + (oy * wp + ox)[None, :]                              # (P, n)
    cos = np.take(ux, idx) * rdx[None, :] + np.take(uy, idx) * rdy[None, :]
    if polarity == "ignore":
        cos = np.abs(cos)
    return (cos.mean(axis=1)).reshape(wh, ww).astype(np.float32)


def _score_exact(level, a, b, cx, cy, polarity):
    """Score at one pose with bilinear lookup (template->live: p = [[a,-b],[b,a]] p_rel + c)."""
    if level.n == 0:
        return 0.0
    mx = (a * level.px - b * level.py + cx).astype(np.float32)
    my = (b * level.px + a * level.py + cy).astype(np.float32)
    lux = cv2.remap(level.lux, mx[None, :], my[None, :], cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0).ravel()
    luy = cv2.remap(level.luy, mx[None, :], my[None, :], cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0).ravel()
    sc = np.hypot(a, b)
    rdx = (a * level.dx - b * level.dy) / sc
    rdy = (b * level.dx + a * level.dy) / sc
    cos = lux * rdx + luy * rdy
    if polarity == "ignore":
        cos = np.abs(cos)
    return float(np.clip(cos.mean(), 0.0, 1.0))


def _refine_lsq(level, a, b, cx, cy, polarity, min_contrast, search_px=2.0, iters=6, min_points=12):
    """Sub-pixel refinement: every model point finds the live edge along its normal, then the similarity minimising the
    (robustly weighted) point-to-edge-line distances is solved linearly. Returns (a, b, cx, cy, n_used)."""
    taus = np.arange(-search_px, search_px + 1e-9, 0.5, dtype=np.float32)                   # samples along the normal
    n_used = 0
    for _ in range(iters):
        sc = np.hypot(a, b)
        mx = a * level.px - b * level.py + cx
        my = b * level.px + a * level.py + cy
        nx = (a * level.dx - b * level.dy) / sc                                             # predicted edge normals (unit)
        ny = (b * level.dx + a * level.dy) / sc
        sx = (mx[:, None] + taus[None, :] * nx[:, None]).astype(np.float32)
        sy = (my[:, None] + taus[None, :] * ny[:, None]).astype(np.float32)
        gx = cv2.remap(level.lgx, sx, sy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        gy = cv2.remap(level.lgy, sx, sy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        prof = gx * nx[:, None] + gy * ny[:, None]                                          # gradient along the normal
        if polarity == "ignore":
            prof = np.abs(prof)
        k = np.argmax(prof, axis=1)
        inner = (k > 0) & (k < len(taus) - 1)
        rows = np.arange(len(k))
        f0 = prof[rows, np.clip(k - 1, 0, None)]
        f1 = prof[rows, k]
        f2 = prof[rows, np.clip(k + 1, None, len(taus) - 1)]
        den = f0 - 2 * f1 + f2
        off = np.where(inner & (den < 0), 0.5 * (f0 - f2) / np.where(den < 0, den, -1), 0.0)
        tau = taus[k] + 0.5 * off                                                            # 0.5 = sample spacing
        gmag = np.hypot(gx[rows, k], gy[rows, k])
        agree = prof[rows, k] / np.maximum(gmag, 1e-6)                                       # cosine of directions at the peak
        peak = prof[rows, k]
        floor = max(0.5 * min_contrast, 0.3 * float(np.median(peak[inner]))) if inner.any() else np.inf
        valid = inner & (peak >= floor) & (agree >= 0.8)                                     # a clear edge, same direction
        n_used = int(valid.sum())
        if n_used < min_points:
            break
        qx, qy = mx + tau * nx, my + tau * ny
        px, py, nxv, nyv = level.px[valid], level.py[valid], nx[valid], ny[valid]
        J = np.column_stack([nxv * px + nyv * py, nyv * px - nxv * py, nxv, nyv]).astype(np.float64)
        y = (nxv * qx[valid] + nyv * qy[valid]).astype(np.float64)
        w = np.ones(n_used)                     # row multipliers = sqrt of the Tukey biweight (1 - (r/c)^2)^2, c = 1.5 px
        for _irls in range(3):
            sol = np.linalg.lstsq(J * w[:, None], y * w, rcond=None)[0]
            r = J @ sol - y
            w = np.clip(1.0 - (r / 1.5) ** 2, 0.0, None)
            if (w > 0).sum() < min_points:
                break
        na, nb, ncx, ncy = (float(v) for v in sol)
        move = np.hypot((na - a) * level.px - (nb - b) * level.py + (ncx - cx),
                        (nb - b) * level.px + (na - a) * level.py + (ncy - cy)).max()   # largest shift of a model point
        a, b, cx, cy = na, nb, ncx, ncy
        if move < 0.01:
            break
    return a, b, cx, cy, n_used


# ---------------------------------------------------------------------------------------------------------------------------

class ContourShapeMatch(Method):
    name, family, model = "contour_shape_match", "shape", "similarity"

    def __init__(self, min_score=0.5, max_rotation_deg=15.0, max_scale_deviation=0.15, max_translation_ratio=0.15,
                 polarity="respect", min_contrast=4.0, rel_contrast=0.15, mask_band_px=4, top_min_side=32, max_levels=5,
                 top_max_points=200, max_model_points=1500, n_candidates=8, refine=True, blur_sigma=1.0):
        """min_score: acceptance floor on the final edge score (0..1). max_*: the declared search range (see module doc).
        polarity: 'respect' (an edge must have the same dark-to-bright direction as in the template) or 'ignore' (contrast
        reversals allowed). min_contrast: gradient floor in grey levels per pixel; rel_contrast: edge threshold relative to
        the strongest template edges. top_min_side: the part's longer side on the top pyramid level is kept >= this."""
        if polarity not in ("respect", "ignore"):
            raise ValueError("polarity must be 'respect' or 'ignore'")
        self.min_score = float(min_score)
        self.max_rotation_deg, self.max_scale_deviation = float(max_rotation_deg), float(max_scale_deviation)
        self.max_translation_ratio = float(max_translation_ratio)
        self.polarity, self.min_contrast, self.rel_contrast = polarity, float(min_contrast), float(rel_contrast)
        self.mask_band_px, self.top_min_side, self.max_levels = int(mask_band_px), int(top_min_side), int(max_levels)
        self.top_max_points, self.max_model_points = int(top_max_points), int(max_model_points)
        self.n_candidates, self.refine, self.blur_sigma = int(n_candidates), bool(refine), float(blur_sigma)

    # -- setup -----------------------------------------------------------------------------------------------------------
    def _region_and_ref(self, template_mask, shape):
        H, W = shape
        if template_mask is not None and template_mask.shape[:2] == (H, W) and (template_mask > 0).mean() >= 0.002:
            m = (template_mask > 0).astype(np.uint8)
            k = 2 * self.mask_band_px + 1
            region = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))) > 0
            mom = cv2.moments(m, binaryImage=True)
            ref = (mom["m10"] / mom["m00"], mom["m01"] / mom["m00"])
            x, y, w, h = cv2.boundingRect(m)
            extent = max(w, h)
        else:                                                    # no usable mask: the whole template is the model
            region = np.ones((H, W), bool)
            region[:3, :] = region[-3:, :] = False
            region[:, :3] = region[:, -3:] = False
            ref = ((W - 1) / 2.0, (H - 1) / 2.0)
            extent = max(W, H)
        return region, ref, extent

    def _pyramids(self, tpl, live, region, extent):
        n_lv = 0
        while (n_lv < self.max_levels and extent / 2 ** (n_lv + 1) >= self.top_min_side
               and min(tpl.shape) / 2 ** (n_lv + 1) >= 16 and min(live.shape) / 2 ** (n_lv + 1) >= 16):
            n_lv += 1
        tp, lp, rp = [tpl], [live], [region]
        rf = region.astype(np.float32)
        for _ in range(n_lv):
            tp.append(cv2.pyrDown(tp[-1]))
            lp.append(cv2.pyrDown(lp[-1]))
            rp.append(cv2.resize(rf, (tp[-1].shape[1], tp[-1].shape[0]), interpolation=cv2.INTER_AREA) > 0.01)
        return tp, lp, rp

    # -- main ------------------------------------------------------------------------------------------------------------
    def align(self, live_bgr, template_bgr, template_mask):
        tpl = cv2.cvtColor(template_bgr, cv2.COLOR_BGR2GRAY).astype(np.float32) if template_bgr.ndim == 3 else template_bgr.astype(np.float32)
        live = cv2.cvtColor(live_bgr, cv2.COLOR_BGR2GRAY).astype(np.float32) if live_bgr.ndim == 3 else live_bgr.astype(np.float32)
        if self.blur_sigma > 0:
            tpl = cv2.GaussianBlur(tpl, (0, 0), self.blur_sigma)
            live = cv2.GaussianBlur(live, (0, 0), self.blur_sigma)
        H, W = tpl.shape
        region, ref0, extent = self._region_and_ref(template_mask, (H, W))
        tp, lp, rp = self._pyramids(tpl, live, region, extent)
        top = len(tp) - 1
        levels = []
        for l in range(len(tp)):
            f = 2.0 ** l
            ref_l = (ref0[0] / f, ref0[1] / f)                                     # pyrDown: x_low = x_high / 2
            n_max = self.top_max_points if l == top else self.max_model_points
            levels.append(_Level(tp[l], lp[l], rp[l], ref_l, self.min_contrast, self.rel_contrast, n_max))
        if levels[top].n < 8 or levels[0].n < 12:
            return Result(False, None, reason=f"the template has too few edge points ({levels[0].n} at full resolution, "
                                              f"{levels[top].n} on the top level)")

        s_lo, s_hi = 1.0 / (1.0 + self.max_scale_deviation), 1.0 / max(1.0 - self.max_scale_deviation, 1e-3)   # template->live
        steps = []
        for lv in levels:
            r = max(lv.radius, 4.0)
            steps.append((float(np.clip(np.degrees(1.0 / r), 0.02, 6.0)), float(np.clip(1.0 / r, 0.002, 0.06))))

        # 1) exhaustive search on the top level --------------------------------------------------------------------------
        L = levels[top]
        a_step, s_step = steps[top]
        rot = self.max_rotation_deg
        angles = np.array([0.0]) if rot <= 0 else np.linspace(-rot, rot, int(np.ceil(2 * rot / a_step)) + 1)
        scales = (np.array([1.0]) if self.max_scale_deviation <= 0
                  else np.linspace(s_lo, s_hi, int(np.ceil((s_hi - s_lo) / s_step)) + 1))
        f_top = 2.0 ** top
        lim = self.max_translation_ratio * W / f_top
        rx, ry = ref0[0] / f_top, ref0[1] / f_top
        cx0 = int(np.clip(np.floor(rx - lim), 0, L.w - 1))
        cx1 = int(np.clip(np.ceil(rx + lim), 0, L.w - 1))
        cy0 = int(np.clip(np.floor(ry - lim), 0, L.h - 1))
        cy1 = int(np.clip(np.ceil(ry + lim), 0, L.h - 1))
        ww, wh = cx1 - cx0 + 1, cy1 - cy0 + 1
        cand = []                                                                     # (score, theta, scale, cx, cy)
        for th in angles:
            for sc in scales:
                S = _score_window(L, th, sc, cx0, cy0, ww, wh, self.polarity)
                peaks = (S == cv2.dilate(S, np.ones((3, 3), np.uint8))) & (S > 0)
                ys, xs = np.nonzero(peaks)
                if len(xs) == 0:
                    continue
                best = np.argsort(-S[ys, xs])[:3]
                for i in best:
                    cand.append((float(S[ys[i], xs[i]]), float(th), float(sc), float(cx0 + xs[i]), float(cy0 + ys[i])))
        if not cand:
            return Result(False, None, reason="no edge agreement anywhere inside the declared range")
        cand.sort(key=lambda c: -c[0])
        kept = []
        for c in cand:                                                                # pose-space non-maximum suppression
            if all(np.hypot(c[3] - k[3], c[4] - k[4]) > 2.0 or abs(c[1] - k[1]) > 2.5 * a_step for k in kept):
                kept.append(c)
                if len(kept) >= self.n_candidates:
                    break

        # 2) track the candidates down the pyramid ----------------------------------------------------------------------
        tracks = [(sc_, th, s, cx, cy) for sc_, th, s, cx, cy in kept]
        for l in range(top - 1, -1, -1):
            lv = levels[l]
            prev_a, prev_s = steps[l + 1]
            new = []
            for _, th, s, cx, cy in tracks:
                cx, cy = 2.0 * cx, 2.0 * cy
                best = (-1.0, th, s, cx, cy)
                ix, iy = int(round(cx)), int(round(cy))
                x0, y0 = int(np.clip(ix - 2, 0, lv.w - 1)), int(np.clip(iy - 2, 0, lv.h - 1))
                x1, y1 = int(np.clip(ix + 2, 0, lv.w - 1)), int(np.clip(iy + 2, 0, lv.h - 1))
                for dth in np.linspace(-prev_a, prev_a, 5):
                    for ds in (np.linspace(-prev_s, prev_s, 3) if self.max_scale_deviation > 0 else [0.0]):
                        s2 = float(np.clip(s + ds, s_lo, s_hi))
                        th2 = float(np.clip(th + dth, -rot, rot)) if rot > 0 else 0.0
                        S = _score_window(lv, th2, s2, x0, y0, x1 - x0 + 1, y1 - y0 + 1, self.polarity)
                        k = int(np.argmax(S))
                        if S.flat[k] > best[0]:
                            best = (float(S.flat[k]), th2, s2, float(x0 + k % S.shape[1]), float(y0 + k // S.shape[1]))
                new.append(best)
            new.sort(key=lambda c: -c[0])
            tracks = [t for t in new if t[0] >= new[0][0] - 0.25][: self.n_candidates]

        # 3) sub-pixel least-squares refinement at full resolution ------------------------------------------------------
        L0 = levels[0]
        best_pose, best_score, n_used = None, -1.0, 0
        for _, th, s, cx, cy in tracks[:3]:
            a, b = s * np.cos(np.radians(th)), s * np.sin(np.radians(th))
            nu = 0
            if self.refine:
                a, b, cx, cy, nu = _refine_lsq(L0, a, b, cx, cy, self.polarity, self.min_contrast)
            score = _score_exact(L0, a, b, cx, cy, self.polarity)
            if score > best_score:
                best_pose, best_score, n_used = (a, b, cx, cy), score, nu
        a, b, cx, cy = best_pose

        # template->live: p_live = A (p_tpl - ref) + c ; invert to live->template
        A = np.array([[a, -b], [b, a]])
        T = np.eye(3)
        T[:2, :2] = A
        T[:2, 2] = np.array([cx, cy]) - A @ np.array(ref0)
        M = np.linalg.inv(T)

        rot_deg = float(np.degrees(np.arctan2(-b, a)))                 # rotation of live->template
        scale = 1.0 / float(np.hypot(a, b))
        shift = float(np.hypot(cx - ref0[0], cy - ref0[1]))
        tol_a = steps[0][0]
        reasons = []
        if abs(rot_deg) > self.max_rotation_deg + tol_a:
            reasons.append(f"rotation {rot_deg:.1f} deg outside the declared +/-{self.max_rotation_deg:g}")
        if abs(scale - 1.0) > self.max_scale_deviation + 0.005:
            reasons.append(f"scale {scale:.3f} outside the declared 1 +/- {self.max_scale_deviation:g}")
        if shift > self.max_translation_ratio * W + 1.0:
            reasons.append(f"shift {shift:.0f} px outside the declared {self.max_translation_ratio:g} x width")
        checks_ok = not reasons                                       # the declared range; the score is judged separately
        if best_score < self.min_score:
            reasons.insert(0, f"edge score {best_score:.2f} below {self.min_score}")
        ok = checks_ok and best_score >= self.min_score
        return Result(ok, M, best_score, n_good=L0.n, n_inl=n_used, reason="; ".join(reasons), checks_ok=checks_ok)
