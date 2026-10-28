"""Image reading and writing that also work with non-ASCII paths on Windows (cv2.imread / cv2.imwrite do not)."""
import os

import cv2
import numpy as np


def imread(path, flags=cv2.IMREAD_COLOR):
    """Like cv2.imread (None when the file is missing or unreadable). IMREAD_COLOR gives 8-bit BGR for any input and applies
    a JPEG's EXIF orientation."""
    try:
        data = np.fromfile(path, dtype=np.uint8)
    except OSError:
        return None
    return cv2.imdecode(data, flags) if data.size else None


def imwrite(path, img):
    """Like cv2.imwrite; the format follows the file extension."""
    ok, buf = cv2.imencode(os.path.splitext(path)[1] or ".png", img)
    if ok:
        buf.tofile(path)
    return bool(ok)
