"""Small geometry helpers.

Conventions (these are part of the protocol; do not change them silently):
  * Pixel coordinates follow OpenCV: the CENTRE of the top-left pixel is (0, 0).
  * Matrices are 3x3, float64, acting on column vectors [x, y, 1].
  * An alignment result M maps LIVE pixel coordinates to TEMPLATE pixel coordinates (warpAffine(live, M[:2]) puts the live
    image onto the template).
"""
import numpy as np


def to3(M):
    """2x3 or 3x3 -> 3x3 float64."""
    M = np.asarray(M, dtype=np.float64)
    if M.shape == (3, 3):
        return M
    if M.shape == (2, 3):
        out = np.eye(3)
        out[:2, :] = M
        return out
    raise ValueError(f"matrix must be 2x3 or 3x3, got {M.shape}")


def apply(M3, pts):
    """Apply a 3x3 (affine or homography) to Nx2 points."""
    pts = np.asarray(pts, dtype=np.float64).reshape(-1, 2)
    h = np.hstack([pts, np.ones((len(pts), 1))]) @ np.asarray(M3, dtype=np.float64).T
    return h[:, :2] / h[:, 2:3]


def translation(tx, ty):
    M = np.eye(3)
    M[0, 2], M[1, 2] = tx, ty
    return M


def rotation_about(deg, centre):
    a = np.radians(deg)
    c, s = np.cos(a), np.sin(a)
    R = np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])
    return translation(*centre) @ R @ translation(-centre[0], -centre[1])


def scaling_about(scale, centre):
    S = np.diag([scale, scale, 1.0])
    return translation(*centre) @ S @ translation(-centre[0], -centre[1])


def tilt_homography(width, height, tilt_deg, axis_deg, focal=None):
    """Homography of a plane tilted by tilt_deg about an axis through the image centre
    (axis direction axis_deg in the image plane), seen by a pinhole camera with the given focal length in pixels."""
    import cv2
    f = float(focal or max(width, height))
    cx, cy = (width - 1) / 2.0, (height - 1) / 2.0
    K = np.array([[f, 0.0, cx], [0.0, f, cy], [0.0, 0.0, 1.0]])
    a = np.radians(axis_deg)
    rvec = np.array([np.cos(a), np.sin(a), 0.0]) * np.radians(tilt_deg)
    R, _ = cv2.Rodrigues(rvec)
    return K @ R @ np.linalg.inv(K)


def wrap_deg(a):
    """Wrap an angle in degrees to (-180, 180]."""
    a = np.asarray(a, dtype=np.float64)
    w = -((-a + 180.0) % 360.0 - 180.0)          # in (-180, 180]: +180 and -180 both give +180
    return w if np.ndim(a) else float(w)


def jacobian_params(M3, pt):
    """Local rotation (deg), uniform scale and 'reflected' flag of the map M3 at the point pt (numerical Jacobian).
    Exact for similarities; a best-fit rotation/scale for anything else."""
    h = 0.5
    pt = np.asarray(pt, dtype=np.float64)
    f = lambda p: apply(M3, [p])[0]
    ex = (f(pt + [h, 0.0]) - f(pt - [h, 0.0])) / (2 * h)
    ey = (f(pt + [0.0, h]) - f(pt - [0.0, h])) / (2 * h)
    J = np.column_stack([ex, ey])
    det = float(np.linalg.det(J))
    rot = float(np.degrees(np.arctan2(J[1, 0] - J[0, 1], J[0, 0] + J[1, 1])))
    return rot, float(np.sqrt(abs(det))), det < 0
