"""Methods without keypoints: identity (the reference line) and phase correlation (global translation)."""
import cv2
import numpy as np

from .. import geometry as G
from .base import Method, Result


class Identity(Method):
    """No alignment. Its error is the raw misalignment of the pair: the reference line every other method is read against."""
    name, family, model = "identity", "none", "identity"

    def align(self, live_bgr, template_bgr, template_mask):
        return Result(True, np.eye(3), 1.0)


class PhaseCorrelation(Method):
    """Translation only, from the frequency domain (cv2.phaseCorrelate with a Hanning window). Score = correlation peak."""
    name, family, model = "phase_correlation", "dense_global", "translation"

    def __init__(self, min_peak=0.1):
        self.min_peak = float(min_peak)

    def align(self, live_bgr, template_bgr, template_mask):
        l = cv2.cvtColor(live_bgr, cv2.COLOR_BGR2GRAY).astype(np.float32)
        t = cv2.cvtColor(template_bgr, cv2.COLOR_BGR2GRAY).astype(np.float32)
        if l.shape != t.shape:                                   # different sizes: pad both (bottom/right) to a common canvas
            H, W = max(l.shape[0], t.shape[0]), max(l.shape[1], t.shape[1])
            l = cv2.copyMakeBorder(l, 0, H - l.shape[0], 0, W - l.shape[1], cv2.BORDER_CONSTANT, value=float(np.median(l)))
            t = cv2.copyMakeBorder(t, 0, H - t.shape[0], 0, W - t.shape[1], cv2.BORDER_CONSTANT, value=float(np.median(t)))
        win = cv2.createHanningWindow((l.shape[1], l.shape[0]), cv2.CV_32F)
        (dx, dy), peak = cv2.phaseCorrelate(l * win, t * win)   # golden ~ test image shifted by (dx, dy)
        M = G.translation(dx, dy)
        ok = peak >= self.min_peak
        return Result(bool(ok), M, float(peak), reason="" if ok else f"peak {peak:.3f} below {self.min_peak}")
