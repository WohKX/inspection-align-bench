"""Rotation search around any method: `<method>+rot`.

Methods whose features do not survive rotation (phase correlation finds a shift only; DISK is trained on upright images) can
only find poses close to the orientation they are given. The wrapper turns the test image to a fixed set of angles, runs the
method on each, and keeps the hypothesis with the highest DECISION SCORE of the method itself (inlier count for the
correspondence methods, correlation peak for phase correlation). The ground truth plays no part in the choice. The kept pose
is composed with the turn, so it still maps original test-image pixels to golden pixels, and it is accepted or rejected by
the method's own rule, exactly as without the search.

Angles: 0, step, 2 x step, ... below `range_deg`. For a part with n-fold symmetry the distinct orientations repeat every
360/n degrees, so range_deg = 360/n covers all of them (the part configs set it). The cost is the method's cost times the
number of angles; every hypothesis is recorded in `reason` only by its winning angle.
"""
import cv2
import numpy as np

from .. import geometry as G
from .base import Method, Result


def rotate_with_canvas(img, deg):
    """img turned by deg about its centre on a canvas large enough to keep every pixel. Returns (turned image, R) where R
    (3x3) maps original pixels to turned-image pixels. The new corners are filled with the median colour of the image's
    outer band, so the canvas edge is a step from the background colour, not from black."""
    h, w = img.shape[:2]
    c = ((w - 1) / 2.0, (h - 1) / 2.0)
    R = G.rotation_about(deg, c)
    corners = G.apply(R, np.array([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]], float))
    lo, hi = np.floor(corners.min(0)), np.ceil(corners.max(0))
    R = G.translation(-lo[0], -lo[1]) @ R
    W2, H2 = int(hi[0] - lo[0] + 1), int(hi[1] - lo[1] + 1)
    b = max(2, int(0.02 * min(h, w)))
    band = np.concatenate([img[:b].reshape(-1, img.shape[2] if img.ndim == 3 else 1), img[-b:].reshape(-1, img.shape[2] if img.ndim == 3 else 1),
                           img[:, :b].reshape(-1, img.shape[2] if img.ndim == 3 else 1), img[:, -b:].reshape(-1, img.shape[2] if img.ndim == 3 else 1)])
    fill = tuple(float(v) for v in np.median(band, axis=0))
    out = cv2.warpAffine(img, R[:2], (W2, H2), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=fill)
    return out, R


class RotationSearch(Method):
    def __init__(self, base, step_deg=15.0, range_deg=360.0, **base_params):
        from . import build                                   # late import: the registry imports this module
        self.base = build(base, base_params)
        self.name = f"{self.base.name}+rot"
        self.family, self.model, self.score_field = self.base.family, self.base.model, self.base.score_field
        step, rng = float(step_deg), float(range_deg)
        if step <= 0 or rng <= 0:
            raise ValueError("step_deg and range_deg must be > 0")
        self.angles = [float(a) for a in np.arange(0.0, rng - 1e-9, step)]

    def align(self, live_bgr, template_bgr, template_mask):
        best = None
        for a in self.angles:
            turned, R = rotate_with_canvas(live_bgr, a) if a else (live_bgr, np.eye(3))
            r = self.base.align(turned, template_bgr, template_mask)
            if r.M is None:
                continue
            s = self.base.score(r)
            if best is None or s > best[0]:
                best = (s, a, r, R)
        if best is None:
            return Result(False, None, n_good=0, n_inl=0, reason=f"no pose at any of {len(self.angles)} angles")
        _, a, r, R = best
        M = G.to3(r.M) @ R                                     # original test px -> turned test px -> golden px
        why = f"best of {len(self.angles)} angles: {a:g} deg" + (f"; {r.reason}" if r.reason else "")
        return Result(r.success, M, r.conf, r.n_good, r.n_inl, why, r.checks_ok)
