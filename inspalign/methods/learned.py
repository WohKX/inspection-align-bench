"""Learned matchers: LightGlue (Lindenberger, Sarlin & Pollefeys, ICCV 2023) on DISK or SIFT keypoints.

Optional dependency: torch + kornia + the `lightglue` package (https://github.com/cvg/LightGlue, Apache-2.0):

    pip install torch kornia
    pip install git+https://github.com/cvg/LightGlue.git

Without them the constructors raise `Unavailable`, and the runners record these arms as unavailable instead of crashing.

Licences (checked against the LightGlue README, 2026-10): the LightGlue code and its pre-trained weights are Apache-2.0;
DISK follows Apache-2.0 as well. SuperPoint (and therefore `lightglue_superpoint`) is under a restrictive, non-commercial
licence, which is why it is NOT one of the arms here.

Design: the matcher only proposes correspondences. The pose is fitted by the SAME `fit_similarity` (RANSAC, 5 px, >= 6
inliers) as the classical keypoint arms, so the difference between `sift_ransac` and `lightglue_sift` is exactly "nearest
neighbour + ratio test" versus "LightGlue" on (nearly) the same kind of keypoints.

Weights are downloaded once by the libraries on first use (torch hub cache); after that the arms run offline.
"""
import cv2
import numpy as np

from .base import Method, Result, Unavailable
from .keypoints import MIN_GOOD, MIN_INLIERS, RANSAC_PX, fit_similarity


def _import_lightglue():
    try:
        import torch
        import lightglue
        from lightglue.utils import numpy_image_to_torch, rbd
    except ImportError as e:  # pragma: no cover - depends on the environment
        raise Unavailable(f"learned matchers need torch, kornia and lightglue ({e}); see inspalign/methods/learned.py")
    return torch, lightglue, numpy_image_to_torch, rbd


class _LightGlueArm(Method):
    family = "learned_matcher"
    model = "similarity"
    score_field = "n_inl"                   # the same RANSAC fit and inlier threshold as sift_ransac
    features = None                     # 'disk' | 'sift' (LightGlue's name for the keypoint type)

    def __init__(self, max_keypoints=2048, resize=1024, filter_threshold=0.1, depth_confidence=-1, width_confidence=-1,
                 ransac_px=RANSAC_PX, min_inliers=MIN_INLIERS, min_good=MIN_GOOD, device="cpu", torch_threads=None):
        """max_keypoints: per image. resize: the longer image side is shrunk to this before extraction (never enlarged; None
        keeps the input size); keypoints are mapped back to input pixels by LightGlue's extractor. filter_threshold: LightGlue's
        match-confidence threshold (its default). depth_confidence / width_confidence = -1 switch off LightGlue's adaptive
        early stopping and point pruning, so the full network is measured (the authors' "maximum accuracy" setting)."""
        torch, lg, self._to_torch, self._rbd = _import_lightglue()
        self._torch = torch
        if torch_threads:
            torch.set_num_threads(int(torch_threads))
        self.device = device
        self.resize = None if resize in (None, 0) else int(resize)
        self.ransac_px, self.min_inliers, self.min_good = float(ransac_px), int(min_inliers), int(min_good)
        self.extractor = self._make_extractor(lg, int(max_keypoints)).eval().to(device)
        self.matcher = lg.LightGlue(features=self.features, filter_threshold=float(filter_threshold),
                                    depth_confidence=depth_confidence, width_confidence=width_confidence).eval().to(device)

    def _make_extractor(self, lg, max_keypoints):
        raise NotImplementedError

    def _image(self, bgr):
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB) if bgr.ndim == 3 else cv2.cvtColor(bgr, cv2.COLOR_GRAY2RGB)
        return self._to_torch(rgb).to(self.device)              # 3 x H x W, float in [0, 1]

    def _extract(self, bgr):
        h, w = bgr.shape[:2]
        kw = {}
        if self.resize is not None and max(h, w) > self.resize:   # shrink only; never enlarge
            kw["resize"] = self.resize
        else:
            kw["resize"] = None
        return self.extractor.extract(self._image(bgr), **kw)

    def align(self, live_bgr, template_bgr, template_mask):
        torch = self._torch
        with torch.inference_mode():
            f_live = self._extract(live_bgr)
            f_tpl = self._extract(template_bgr)
            out = self.matcher({"image0": f_live, "image1": f_tpl})
        f_live, f_tpl, out = self._rbd(f_live), self._rbd(f_tpl), self._rbd(out)
        matches = out["matches"].cpu().numpy().reshape(-1, 2)
        if len(matches) == 0:
            return Result(False, None, n_good=0, n_inl=0, reason="LightGlue returned no matches")
        q = f_live["keypoints"].cpu().numpy()[matches[:, 0]]
        t = f_tpl["keypoints"].cpu().numpy()[matches[:, 1]]
        return fit_similarity(q, t, self.ransac_px, self.min_inliers, self.min_good)


class LightGlueDisk(_LightGlueArm):
    """DISK keypoints (Tyszkiewicz et al., NeurIPS 2020; 'depth' weights via kornia) matched by LightGlue."""
    name, features = "lightglue_disk", "disk"

    def _make_extractor(self, lg, max_keypoints):
        return lg.DISK(max_num_keypoints=max_keypoints)


class LightGlueSift(_LightGlueArm):
    """SIFT keypoints (OpenCV backend of LightGlue's extractor, RootSIFT descriptors) matched by LightGlue."""
    name, features = "lightglue_sift", "sift"

    def _make_extractor(self, lg, max_keypoints):
        return lg.SIFT(max_num_keypoints=max_keypoints, backend="opencv")
