"""Common interface. A method receives the golden image, the golden's object mask and the test image, and returns a Result
whose matrix maps TEST-image pixels to GOLDEN pixels (3x3). The matrix is kept even when the method rejects its own pose, so
the summary can apply another acceptance threshold (a calibrated one) without re-running anything."""
from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass
class Result:
    success: bool                       # the method's own default acceptance
    M: Optional[np.ndarray] = None      # 3x3 test -> golden; None when the method produced no pose at all
    conf: Optional[float] = None        # the method's own confidence number; not comparable across methods
    n_good: Optional[int] = None        # candidate correspondences (keypoint methods)
    n_inl: Optional[int] = None         # RANSAC inliers (keypoint methods)
    reason: str = ""
    checks_ok: bool = True              # every acceptance condition OTHER than the score passed (e.g. the declared range)


class Method:
    name = "method"
    family = "none"                     # none | dense_global | classical_keypoints | learned_matcher | shape
    model = "identity"                  # the pose class it can express: identity | translation | similarity
    score_field = "conf"                # the number its accept / reject decision is a threshold on: "conf" or "n_inl"

    def align(self, live_bgr: np.ndarray, template_bgr: np.ndarray, template_mask: np.ndarray) -> Result:
        raise NotImplementedError

    def score(self, r: Result) -> float:
        """The decision score of one result (higher = more sure); -inf when there is none."""
        v = getattr(r, self.score_field, None)
        return float(v) if v is not None and np.isfinite(v) else float("-inf")


class Unavailable(Exception):
    """Raised by a method's constructor when an optional dependency is missing; the runner records the method as unavailable."""
