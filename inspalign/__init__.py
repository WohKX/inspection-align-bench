"""inspalign (repository: inspection-align-bench): image alignment for visual inspection, measured against hand-clicked ground truth.

One run per part = `python evaluate.py --config configs/parts/<part>.yaml` -> results.csv, points.csv, pairs.csv, run.log,
summary/. Calibration (calibrate.py) and the cross-part report (report.py) are computed from those files.
"""
__version__ = "0.9.0"
