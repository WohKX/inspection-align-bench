# Data: layout, landmarks, and what is computed

`evaluate.py` reads one data folder per part: golden (template) images, test images, and the landmark points clicked on all of
them. `tools/landmark_picker.html` writes the landmark file. `python tests/make_demo.py` writes a small example (`data/demo`).

## 1. Folder layout

```
data/pcb/
├── landmarks.json                    every point, of every image (written by the landmark picker)
├── images/<filename or id>.<ext>     the test images
└── templates/Full/<golden>.<ext>     the golden images; "Full" is the region name used in the picker
```

* Image types: png, jpg/jpeg, bmp, tif/tiff (the picker itself reads png, jpg, bmp, webp).
* Goldens elsewhere: `data.templates: {"Full/000": "path/to/000.png"}` in the config, or `--template` for one golden.
* An optional `<golden>_mask.png` next to a golden is its object mask (white = part); otherwise the mask is computed (Otsu).

## 2. landmarks.json

```json
{"version": 1,
 "regions": {
  "Full": {
   "point_names": ["p1", "p2", "p3", "p4", "p5", "p6", "p7"],
   "templates": {
     "000": {"size": [1500, 1000], "source_hash": "0a58772a8e6c", "points": {"p1": [654.77, 305.13], "p2": [893.83, 318.89]}},
     "001": {"size": [1500, 1000], "points": {"p1": [640.1, 300.2], "p2": [880.0, 310.7]}}},
   "images": [
     {"id": "1dced69fd00a", "filename": "003.JPG", "width": 1500, "height": 1000,
      "points": {"p1": [715.97, 283.19], "p2": [947.93, 366.78]}, "note": ""}]}}}
```

* Every test image of a region is paired with every golden of that region. Pair id: `Full/<test stem>` with one golden,
  `Full/<golden>/<test stem>` with several.
* Only the points both images have are used; a point missing on one image is listed in `run.log`, and so is the image's `note`.
* `source_hash` / `id`: the first 12 hex digits of the file's SHA-1. A golden whose file no longer matches is reported (its points
  may be stale).
* Coordinates: pixels of the original image files, x to the right, y down, OpenCV convention (the centre of the top-left pixel
  is (0, 0)) — what the picker writes. For a tool whose (0, 0) is the corner of the top-left pixel, set `data.coord_origin: corner`.

**Several goldens.** The picker exports one golden per file. To use three, annotate each golden once as the golden (or take
the points it got as a test image) and put all three under `templates` with their points. Every golden is also an annotated
image, so any of them can be swapped for another by moving its entry.

## 3. Checks before anything is computed

A pair is refused, with the reason in `pairs.csv` (and SUMMARY.md, last section), when:

* it has fewer than `data.min_points` (default 3) points in common with the golden;
* a point lies outside its image (wrong image, or wrong `coord_origin`);
* an image's pixel size differs from the size its points were clicked on (stale points);
* its points fit a **mirror image** far better than any turn: on one of the two images the labels go round in the opposite
  direction (two names swapped), or the part lies flipped over.

A test image whose file content is identical to a golden is not paired with that golden (a golden is never scored against
itself); `run.log` lists it.

## 4. What is computed

| column | definition |
|---|---|
| `err_mean_px` (primary) | mean over points of `|M(l_i) - t_i|`, original golden pixels (`M`: the method's test -> golden pose) |
| `err_median_px`, `err_rms_px`, `err_max_px` | the same distances, other statistics |
| `err_rot_deg`, `err_scale_pct` | rotation / scale of `M` minus those of the reference pose, at the points' centroid |
| `gt_floor_mean_px` | mean residual of the least-squares similarity fitted to the points themselves: click scatter + shape difference |
| `excess_px` | `err_mean_px - gt_floor_mean_px` |
| `score` | the method's decision score: RANSAC inliers (SIFT, LightGlue), correlation peak, edge score |
| `checks_ok` | every acceptance condition other than the score passed (the contour method's declared range) |
| `outcome` | `correct`, `silent_wrong`, `lost`, `rejected`, `no_pose` (PROTOCOL.md, section 7) |

`tau_px` is fixed per part before the run; other values can be applied afterwards without re-running:
`python -m inspalign.gtsummary results/pcb --tau-px 5`.

## 5. Parts with identical, interchangeable features (symmetry)

When a part looks the same after a fraction of a turn (four identical tabs, six spokes, a plain rectangle) and the application
does not care which feature ends up where, declare it at the top level of the part's config, before the run:

```yaml
symmetry: {"Full": {"order": 4, "cycle": ["p2", "p3", "p4", "p5"]}}
```

* `cycle`: the repeated points in order round the part. A pose is scored against the nearest of the `order` equivalent
  labellings: the test point labelled p2 may equally be the golden's p3, p4 or p5 (points outside the cycle, such as a centre
  point, stay). Each equivalent uses the golden's **own clicked points**, so a part that is only roughly symmetric (hand-made,
  food, or simply clicked by hand) is judged against its real features. The number of points must be a multiple of the order.
* Alternative, for an exactly symmetric part: `{"order": 4, "center": "p6"}` turns the golden points by 90 deg steps about a
  centre (a landmark name, `"points"` for the mean of the golden's points, `"mask"` for the mask centroid, or `[x, y]`). With
  several goldens use a name or `"points"`; `[x, y]` is a pixel of one golden only (run.log warns).
* Label on every image starting at ANY of the identical features and going round in the same direction. Only turns are
  equivalent, never a mirror image.
* `results.csv` keeps the error without symmetry (`err_mean_strict_px`), `sym_rot_deg` says which equivalent was nearest, and
  SUMMARY.md reports `correct_via_symmetry`.

## 6. Calibration images

Thresholds are calibrated on images that are not test images (PROTOCOL.md, section 9). Per part:

1. Take the next 10 good images in file order after the test images. In the landmark picker: **Start new part**, load golden 000
   and the 10 images, click the same point names, **Save landmarks.json** (to a new place, e.g. `calib_pcb.json`).
2. Build the calibration folder; it reuses the goldens (images and points) of the test folder and refuses any image that is
   also a test image or a golden:

   ```
   python -m inspalign.calibrate store --test data/pcb --export calib_pcb.json --images path/to/the/10/images --out data/pcb_calib
   ```
3. Run, fit, apply:

   ```
   python evaluate.py --config configs/parts/pcb.yaml --data data/pcb_calib --out results/pcb_calib
   python -m inspalign.calibrate fit results/pcb_calib
   python -m inspalign.gtsummary results/pcb --thresholds results/pcb_calib/thresholds.json
   ```

## 7. Outputs of one run

`run.log` (everything, readable), `results.csv` (one row per pair and method), `points.csv` (one row per point), `pairs.csv` (what
was read, the reference pose, the floor), `summary/SUMMARY.md` and its CSVs (outcomes, tau sweep, confidence and risk/coverage,
several goldens, per golden floor), `overlays/` (alignment pictures), `gt_check/` (the points as read), `manifest.json`
(configuration, versions, data fingerprint, where the learned methods ran). Paths inside are relative to the data folder.
