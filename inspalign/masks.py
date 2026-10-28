"""One deliberately simple object-mask source for ALL arms: Otsu threshold + morphology.

No learned segmentation. It works on clean, uniform backgrounds and fails on textured or uneven ones; the
`info` dict says how much to trust the result, so a class can be excluded by a rule written down in advance.
"""
import cv2
import numpy as np


def object_mask(bgr, border_frac=0.03, min_area_frac=0.003, blur_sigma=1.5, close_frac=0.015, open_frac=0.004):
    """Returns (mask uint8 0/255, info dict).

    Foreground = the side of the Otsu threshold that does NOT contain the median grey level of the outer border band.
    info: otsu_t, bg_level, polarity ('fg_darker'|'fg_brighter'), area_frac, n_components, touches_border,
          separation (|mean_fg - mean_bg| / (std_bg + 1): a rough contrast-to-noise score).
    """
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY) if bgr.ndim == 3 else bgr
    H, W = gray.shape
    sm = cv2.GaussianBlur(gray, (0, 0), blur_sigma)
    b = max(2, int(round(border_frac * min(H, W))))
    band = np.concatenate([sm[:b].ravel(), sm[-b:].ravel(), sm[:, :b].ravel(), sm[:, -b:].ravel()])
    bg_level = float(np.median(band))
    t, _ = cv2.threshold(sm, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    fg_darker = bg_level > t
    fg = (sm <= t) if fg_darker else (sm > t)
    fg = fg.astype(np.uint8) * 255

    k = max(3, int(round(close_frac * min(H, W))) | 1)
    fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    k = max(3, int(round(open_frac * min(H, W))) | 1)
    fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))

    # fill holes: everything not reachable from the border through background
    inv = cv2.bitwise_not(fg)
    flood = inv.copy()
    ff = np.zeros((H + 2, W + 2), np.uint8)
    for seed in ((0, 0), (W - 1, 0), (0, H - 1), (W - 1, H - 1)):
        if flood[seed[1], seed[0]] == 255:
            cv2.floodFill(flood, ff, seed, 0)
    fg = cv2.bitwise_or(fg, flood)

    n, labels, stats, _ = cv2.connectedComponentsWithStats((fg > 0).astype(np.uint8), connectivity=8)
    keep = np.zeros(H * W, bool)
    count = 0
    for i in range(1, n):
        if stats[i, cv2.CC_STAT_AREA] >= min_area_frac * H * W:
            keep |= (labels.ravel() == i)
            count += 1
    mask = (keep.reshape(H, W).astype(np.uint8)) * 255

    inside = mask > 0
    mean_fg = float(sm[inside].mean()) if inside.any() else 0.0
    bgpix = sm[~inside]
    info = {
        "otsu_t": float(t), "bg_level": bg_level, "polarity": "fg_darker" if fg_darker else "fg_brighter",
        "area_frac": float(inside.mean()), "n_components": int(count),
        "touches_border": bool(inside[0].any() or inside[-1].any() or inside[:, 0].any() or inside[:, -1].any()),
        "separation": float(abs(mean_fg - float(bgpix.mean())) / (float(bgpix.std()) + 1.0)) if inside.any() and bgpix.size else 0.0,
    }
    return mask, info
