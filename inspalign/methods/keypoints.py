"""Sparse-correspondence methods: find point correspondences, then fit a 4-DOF similarity with RANSAC.

Every correspondence-based arm in this package (SIFT and the two LightGlue arms in learned.py) ends in the
SAME estimator, `fit_similarity`, with the same settings, so the only thing that differs between those arms is how the
correspondences were found.

No plausibility gates (maximum rotation, scale, shift): the raw estimator is what is measured. A gate is a deployment policy,
not a property of the method, and it would hide the failures this benchmark exists to count.

Both images are processed inside align(), so the latency is the full cost of one pair.
"""
import cv2
import numpy as np

from .. import geometry as G
from .base import Method, Result

RANSAC_PX = 5.0        # reprojection threshold, pixels of the template image
MIN_INLIERS = 6        # fewer RANSAC inliers than this: the pose is reported but rejected
MIN_GOOD = 4           # fewer correspondences than this: no fit is attempted


def fit_similarity(q_live, t_tpl, ransac_px=RANSAC_PX, min_inliers=MIN_INLIERS, min_good=MIN_GOOD, n_good=None):
    """Fit live -> template similarity (rotation, uniform scale, translation) to correspondences with RANSAC.

    q_live, t_tpl: (N, 2) arrays of matching points (live image, template image).
    Returns a Result. conf = inlier ratio (n_inl / n_good); it is this family's own confidence number and is not
    comparable with the confidences of other families.
    """
    q = np.asarray(q_live, np.float32).reshape(-1, 2)
    t = np.asarray(t_tpl, np.float32).reshape(-1, 2)
    n = len(q) if n_good is None else int(n_good)
    if len(q) < min_good:
        return Result(False, None, n_good=n, n_inl=0, reason=f"only {len(q)} correspondences (need >= {min_good})")
    M, inl = cv2.estimateAffinePartial2D(q.reshape(-1, 1, 2), t.reshape(-1, 1, 2), method=cv2.RANSAC,
                                         ransacReprojThreshold=float(ransac_px), maxIters=2000, confidence=0.995,
                                         refineIters=10)
    if M is None or inl is None:
        return Result(False, None, n_good=n, n_inl=0, reason="RANSAC found no transform")
    n_inl = int(inl.sum())
    ok = n_inl >= min_inliers
    return Result(bool(ok), G.to3(M), n_inl / max(n, 1), n, n_inl, "" if ok else f"only {n_inl} RANSAC inliers (need >= {min_inliers})")


def ratio_test(knn_pairs, ratio):
    """Lowe's ratio test on k=2 nearest-neighbour matches."""
    return [p[0] for p in knn_pairs if len(p) == 2 and p[0].distance < ratio * p[1].distance]


class _KeypointRansac(Method):
    model = "similarity"
    family = "classical_keypoints"
    score_field = "n_inl"                               # accepted when the RANSAC inlier count reaches min_inliers

    def __init__(self, ratio, ransac_px, min_inliers, min_good, use_template_mask):
        self.ratio, self.ransac_px = float(ratio), float(ransac_px)
        self.min_inliers, self.min_good = int(min_inliers), int(min_good)
        self.use_template_mask = bool(use_template_mask)

    def _detect(self, gray, mask):                      # -> keypoints, descriptors
        raise NotImplementedError

    def _matcher(self):
        raise NotImplementedError

    def align(self, live_bgr, template_bgr, template_mask):
        gl = cv2.cvtColor(live_bgr, cv2.COLOR_BGR2GRAY)
        gt = cv2.cvtColor(template_bgr, cv2.COLOR_BGR2GRAY)
        tmask = None
        if self.use_template_mask and template_mask is not None and template_mask.any():
            tmask = cv2.dilate(template_mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))
        kl, dl = self._detect(gl, None)
        kt, dt = self._detect(gt, tmask)
        if dl is None or dt is None or len(kl) < 2 or len(kt) < 2:
            return Result(False, None, n_good=0, reason="no descriptors on one of the images")
        good = ratio_test(self._matcher().knnMatch(dl, dt, k=2), self.ratio)
        q = np.float32([kl[m.queryIdx].pt for m in good]).reshape(-1, 2)
        t = np.float32([kt[m.trainIdx].pt for m in good]).reshape(-1, 2)
        return fit_similarity(q, t, self.ransac_px, self.min_inliers, self.min_good)


class SiftRansac(_KeypointRansac):
    """OpenCV SIFT (default parameters), brute-force L2, ratio test 0.75, RANSAC similarity."""
    name = "sift_ransac"

    def __init__(self, ratio=0.75, ransac_px=RANSAC_PX, min_inliers=MIN_INLIERS, min_good=MIN_GOOD, use_template_mask=False, nfeatures=0):
        super().__init__(ratio, ransac_px, min_inliers, min_good, use_template_mask)
        self._sift = cv2.SIFT_create(nfeatures=int(nfeatures))
        self._bf = cv2.BFMatcher(cv2.NORM_L2)

    def _detect(self, gray, mask):
        return self._sift.detectAndCompute(gray, mask)

    def _matcher(self):
        return self._bf
