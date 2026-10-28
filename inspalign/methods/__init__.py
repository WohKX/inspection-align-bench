"""Method registry. build(name, params) -> Method instance (raises Unavailable when an optional dependency is missing).

The five methods, by family:
    dense_global          phase_correlation
    classical_keypoints   sift_ransac
    learned_matcher       lightglue_disk, lightglue_sift          (optional: torch + kornia + lightglue)
    shape                 contour_shape_match
Reference line (not a competitor): identity.
Any of them followed by "+rot" (e.g. lightglue_disk+rot) runs inside a rotation search (rotsearch.py); its params are
step_deg, range_deg and the method's own params.
"""
from .base import Method, Result, Unavailable

HEADLINE = ["phase_correlation", "sift_ransac", "lightglue_disk", "lightglue_sift", "contour_shape_match"]
ROT_SUFFIX = "+rot"


def _lazy(module, cls):
    def make(**params):
        import importlib
        return getattr(importlib.import_module(f"{__package__}.{module}"), cls)(**params)
    return make


REGISTRY = {
    "identity": _lazy("simple", "Identity"),
    "phase_correlation": _lazy("simple", "PhaseCorrelation"),
    "sift_ransac": _lazy("keypoints", "SiftRansac"),
    "lightglue_disk": _lazy("learned", "LightGlueDisk"),
    "lightglue_sift": _lazy("learned", "LightGlueSift"),
    "contour_shape_match": _lazy("contour", "ContourShapeMatch"),
}

# Arms that existed in earlier versions: a config that still lists one gets this reason instead of a bare 'unknown'.
REMOVED = {
    "sift_ransac_anms": "removed in 0.7.2 (PROTOCOL.md, amendment A1); delete it from the methods list",
    "orb_ransac": "removed in 0.8.0: not part of the released benchmark; delete it from the methods list",
    "ecc_rigid": "removed in 0.8.0: not part of the released benchmark; delete it from the methods list",
    "mask_moments": "removed in 0.8.0: not part of the released benchmark; delete it from the methods list",
}


def known(name):
    base = name[: -len(ROT_SUFFIX)] if name.endswith(ROT_SUFFIX) else name
    return base in REGISTRY and not (name.endswith(ROT_SUFFIX) and base == "identity")


def unknown_method_message(names):
    """One readable line for method names that are not in the registry (None when all are known)."""
    bad = [n for n in names if not known(n)]
    if not bad:
        return None
    why = [f"'{n}' was {REMOVED[n]}" for n in bad if n in REMOVED]
    rest = [n for n in bad if n not in REMOVED]
    valid = sorted(REGISTRY) + [m + ROT_SUFFIX for m in HEADLINE]
    parts = why + ([f"unknown method(s) {rest}; known: {valid}"] if rest else [])
    return "; ".join(parts)


def build(name, params=None):
    if not known(name):
        raise KeyError(unknown_method_message([name]))
    params = dict(params or {})
    if name.endswith(ROT_SUFFIX):
        from .rotsearch import RotationSearch
        return RotationSearch(name[: -len(ROT_SUFFIX)], **params)
    return REGISTRY[name](**params)


def score_field(name):
    """The result column a method's accept / reject decision is a threshold on (also for its +rot version)."""
    base = name[: -len(ROT_SUFFIX)] if name.endswith(ROT_SUFFIX) else name
    return "n_inl" if base in ("sift_ransac", "lightglue_disk", "lightglue_sift") else "conf"
