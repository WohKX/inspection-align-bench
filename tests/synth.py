"""Synthetic 'parts on a clean background' for tests: textured, with holes and marks, so keypoints and masks both work."""
import cv2
import numpy as np


def make_part(seed=0, shape="plate", size=(768, 576), dark_bg=True, radius_frac=0.36):
    """Part centred in the frame and inside the inscribed circle, so it stays in frame under any rotation about the centre."""
    rng = np.random.default_rng(seed)
    W, H = size
    bg = 25 if dark_bg else 225
    img = np.full((H, W, 3), bg, np.uint8)
    img = np.clip(img.astype(np.float32) + rng.normal(0, 2.0, img.shape), 0, 255).astype(np.uint8)
    cx, cy, R = W / 2.0, H / 2.0, radius_frac * min(W, H)
    body = np.zeros((H, W), np.uint8)
    if shape == "plate":
        w, h = int(R * 1.5), int(R * 1.0)
        cv2.rectangle(body, (int(cx - w / 2), int(cy - h / 2)), (int(cx + w / 2), int(cy + h / 2)), 255, -1)
    elif shape == "lshape":
        w, h = int(R * 1.4), int(R * 1.4)
        x0, y0 = int(cx - w / 2), int(cy - h / 2)
        cv2.rectangle(body, (x0, y0), (x0 + w, y0 + int(h * 0.4)), 255, -1)
        cv2.rectangle(body, (x0, y0), (x0 + int(w * 0.4), y0 + h), 255, -1)
    elif shape == "disc":
        cv2.circle(body, (int(cx), int(cy)), int(R * 0.8), 255, -1)
    else:
        raise ValueError(shape)
    tex = cv2.GaussianBlur(rng.standard_normal((H, W)).astype(np.float32), (0, 0), 2.5)
    tex = (tex / (tex.std() + 1e-9) * 28).astype(np.float32)
    base = 150 if dark_bg else 90
    part = np.clip(base + tex, 0, 255)
    for _ in range(40):                                        # dark and bright marks (distinctive keypoints)
        x, y = int(rng.uniform(cx - R, cx + R)), int(rng.uniform(cy - R, cy + R))
        cv2.circle(part, (x, y), int(rng.uniform(3, 9)), float(rng.choice([40, 230])), -1)
    part3 = cv2.merge([part] * 3).astype(np.uint8)
    img[body > 0] = part3[body > 0]
    if shape == "plate":                                       # a few holes
        for hx, hy in [(-0.5, -0.25), (0.5, -0.25), (-0.5, 0.25), (0.45, 0.2)]:
            cv2.circle(img, (int(cx + hx * R * 1.2), int(cy + hy * R * 1.2)), int(R * 0.09), (bg, bg, bg), -1)
    return cv2.GaussianBlur(img, (0, 0), 0.8)
