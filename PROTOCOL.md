# Protocol

Status: frozen on 2026-10-23 (package 0.8.0); final runs 2026-10-25 to 2026-10-27 (dates in each `manifest.json`). Written before the final run and changed afterwards only by a dated amendment at the bottom. The exact settings of every part
are in `configs/parts/<part>.yaml`; each result folder records the configuration, the package version and a fingerprint of the
data it was computed from (`manifest.json`).

## 1. Question

On real images of five parts, for five image-alignment methods:

1. how often is the returned pose **correct**, and how often does the method **accept a wrong pose** (silent wrong)?
2. does the method's own score **know the difference** between its right and wrong poses?
3. what changes with a **rotation search**, with **several golden images**, and with **acceptance thresholds calibrated** on
   held-out images?

## 2. Data

| Part | Source | Licence | What may be published |
|---|---|---|---|
| PCB | VisA, class `pcb1` (Zou et al., ECCV 2022) | CC BY 4.0 | numbers and pictures, with attribution |
| Chewing gum | VisA, class `chewinggum` | CC BY 4.0 | numbers and pictures, with attribution |
| Fryum | VisA, class `fryum` | CC BY 4.0 | numbers and pictures, with attribution |
| Metal nut | MVTec AD, class `metal_nut` (Bergmann et al., CVPR 2019) | CC BY-NC-SA 4.0 | numbers only (a conservative choice) |
| Screw | MVTec AD, class `screw` | CC BY-NC-SA 4.0 | numbers only |

* Only good (defect-free) images. Per part: **3 goldens and 40 test images**, the first 43 good images by file name (no
  hand-picking); the goldens are the first three. **10 calibration images** per part are the next ones in file order and are
  never test images (section 9).
* Every test image is evaluated against every golden: 120 pairs per part and method. The unit for uncertainty is the test image
  (40 per part), not the pair.

## 3. Ground truth

* Landmarks are clicked with `tools/landmark_picker.html` on every image, the goldens included, with the same point names per
  part. Repeated identical features (tabs, spokes, corners) are labelled starting at any of them and going round in the same
  direction (clockwise) on every image.
* The **reference pose** of a pair is the least-squares similarity (rotation, uniform scale, shift) between its two landmark sets:
  a Procrustes fit (Gower, Psychometrika 40:33-51, 1975). Golden and test image show *different pieces* that all pass visual
  inspection, so no rigid motion maps one exactly onto the other; the reference pose is defined, not measured.
* The **annotation floor** of a pair is the mean residual of that fit: click scatter plus the real shape difference between the two
  pieces (in statistical shape analysis, shape is what remains after location, rotation and scale are removed: Dryden & Mardia,
  *Statistical Shape Analysis*, 2nd ed., Wiley 2016). No similarity-model method can be expected to do better on that pair.
* Refused before anything is computed, with the reason in `pairs.csv`: fewer than 3 common points, a point outside its image,
  an image whose size differs from the one clicked on, a golden paired with itself, and points that fit a mirror image far better
  than any turn (labels going round in opposite directions).

## 4. Settings per part (all fixed before the final run)

| Part | tau (px) | Symmetry | Contour search | Rotation search |
|---|---|---|---|---|
| PCB | 7.2 | none | +/-180 deg | 24 angles over 360 deg |
| Metal nut | 10.3 | 4-fold: tabs p2-p5 | +/-45 deg | 6 angles over 90 deg |
| Screw | 6.1 | none | +/-180 deg | 24 angles over 360 deg |
| Chewing gum | 20.7 | 2-fold: corners TL-TR-BR-BL | +/-90 deg | 12 angles over 180 deg |
| Fryum | 36.6 | 6-fold: spokes p1-p6 | +/-30 deg | 4 angles over 60 deg |

* **tau** = 2 x the 95th percentile of the annotation floor over all pairs of the part (all three goldens), from an identity-only
  run, before any method ran. The floor describes the clicks and the pieces, not the methods. tau stays the same for every
  condition (1, 2 or 3 goldens; default or calibrated thresholds).
* **Symmetry** is declared only where nothing on the part tells the identical features apart. Equivalent poses are defined by
  **label shift**: the test point labelled p1 may equally be the golden's p2, p3, ...; each equivalent is judged against the
  golden's own clicked points (section 7).
* **Contour search** covers every distinct orientation (180/n deg for an n-fold part), anywhere in the frame
  (`max_translation_ratio 0.5`), scale +/-15 %. **Rotation search**: 15 deg steps over 360/n deg (section 6).

## 5. Methods

| Method | Family | Pose model | Decision score (accepted when >= threshold) | Default threshold |
|---|---|---|---|---|
| `identity` | reference line | identity | none (always "accepts") | |
| `phase_correlation` | dense / global | translation | correlation peak | 0.1 |
| `sift_ransac` | classical keypoints | similarity | RANSAC inliers | 6 |
| `lightglue_disk` | learned matcher | similarity | RANSAC inliers | 6 |
| `lightglue_sift` | learned matcher | similarity | RANSAC inliers | 6 |
| `contour_shape_match` | shape | similarity | edge score (0..1) | 0.5 |

* SIFT: OpenCV defaults, brute-force L2, ratio test 0.75. LightGlue (Lindenberger, Sarlin & Pollefeys, ICCV 2023) on DISK or SIFT
  keypoints: at most 2048 per image, longer side shrunk to 1024 px, filter threshold 0.1, adaptive depth/width off. All
  correspondence methods end in the same RANSAC similarity fit (5 px, >= 4 correspondences to try, >= 6 inliers to accept).
* Contour: edge-direction agreement (Steger 2001) over a pyramid search inside its declared range, then a sub-pixel least-squares
  refinement; a pose outside the declared range is rejected whatever its score.
* No plausibility gates (maximum rotation, shift, scale) on any method: a gate is a deployment policy, not a property of the method.
* Images at native resolution; LightGlue's own resize is the only downscaling.

## 6. Rotation search (`<method>+rot`)

The test image is turned to each angle on a canvas large enough to keep every pixel, the method runs on each, and the hypothesis
with the highest **decision score of the method itself** is kept (ground truth plays no part); the pose is composed with the turn
and accepted or rejected by the method's own rule. Run for phase correlation, SIFT and both LightGlue arms; the contour method
searches rotation natively (section 4).

## 7. Outcomes and metrics

* Error of a pose: mean distance between the test landmarks mapped by the pose and the golden landmarks, in original golden pixels.
  For a symmetric part, the smallest error over the equivalents; the error without symmetry is kept (`err_mean_strict_px`).
* Outcome: **correct** (accepted, error <= tau), **silent wrong** (accepted, error > tau), **lost** (rejected, error <= tau),
  **rejected** (rejected, error > tau), **no pose**.
* Without any threshold: **AUROC** of the decision score (right vs wrong poses), **coverage at 5 % risk** (the largest share of
  pairs a threshold can accept with at most 5 % of the accepted poses wrong).
* The same poses at other tolerances (tau sweep), excess over the floor, rotation and scale error, latency (median per pair,
  `--jobs 1`).

## 8. Several goldens

Reported from the 3-golden run: each golden alone; **own pick of k** (k = 1, 2, 3, the first k goldens by name): for every test
image the method keeps the golden whose attempt has its highest decision score, then accepts or rejects as usual; **best possible
of k**: a test image counts if any of the k goldens gives a correct pose. The best possible pick needs the ground truth and is
reported as an upper bound only.

## 9. Calibrated thresholds

Per part, the 10 calibration images are annotated like the test images and evaluated with the same configuration. For each method
the threshold on its decision score is the **lowest at which at most 5 % of the accepted calibration poses are wrong**; if none
achieves that, the method is calibrated to accept nothing. The thresholds are applied to the test results without re-running;
default and calibrated decisions are both reported. Test images never enter calibration (`calibrate store` refuses them by file
content and name). Thresholds are kept as fitted; the report lists every threshold with the number of calibration poses it
accepts and marks those resting on fewer than 5.

## 10. Reproducibility

`python tests/selftest.py` must pass before any number is read. Runs are deterministic (in the pilot, 2,400 attempts repeated in
different runs gave identical numbers) and resumable. Output files hold paths relative to the data folder only.

## 11. Threats to validity (stated with the results)

* 40 test images per part: a correct rate carries a 95 % interval of roughly +/-15 percentage points; only clear differences are
  claimed.
* The parts were chosen for a few distinct, clickable landmarks; heavily textured or cluttered parts are not covered.
* One annotator; the floor measures click scatter and piece-to-piece variation together.
* tau differs per part (it follows each part's floor); rates are compared within a part, not across parts.
* The methods run with their default parameters except the calibrated thresholds; tuning any method on these parts would change
  its numbers.
* Latency is measured on one CPU machine (see `manifest.json`); it ranks the methods, it does not predict another machine.
* The floor of a pair is the residual of a fit with 4 parameters, so it understates the click scatter more when a part has few points: by a factor of about sqrt((n-2)/n), i.e. 0.58 with 3 points (screw), 0.71 with 4 (chewing gum), 0.77 with 5 (PCB, metal nut), 0.85 with 7 (fryum). tau is therefore relatively stricter for parts with few landmarks; the tau sweep (SUMMARY.md, section 2b) shows every result at other tolerances.
* tau is in pixels at the landmarks, so on a long part a small rotation error moves the far points a lot (on the screw, about 10 px per degree at the tip).
* Calibration uses 30 pairs per part (10 images x 3 goldens); a threshold meeting 5 % risk on them can exceed it on the test images. The calibrated silent-wrong rates on the test images are reported as measured.

## Amendments

**A1 (2026-10-22, before the final run): `sift_ransac_anms` removed.** It was a within-family variant of `sift_ransac` that changes
only which keypoints are kept (adaptive non-maximal suppression, Brown, Szeliski & Winder, CVPR 2005: the 1000 best-spread
keypoints when the detector finds more). On the two pilot parts it made the same accept/reject decision as `sift_ransac` on every
pair (24 of 24 and 40 of 40), was correct on the same pairs, and never brought a pose within tolerance that `sift_ransac` had
missed. The benchmark compares method families, and a variant that changes no decision adds a row but no information.

**A2 (2026-10-23, before the final run): scope and settings after the pilot runs.** The pilot (all five parts, three goldens,
not reported) showed that the contour method's +/-15 deg range covered few metal-nut and screw pairs, that its default threshold
rejected every right pose on the PCB, and that DISK accepted many wrong poses. Decided before the final run:
the release contains the annotated-pair benchmark only (the synthetic perturbation ladder and its extra methods ORB, ECC and mask
moments are removed); the rotation search (section 6), label-shift symmetry (section 4), multi-golden reporting (section 8) and
calibrated thresholds (section 9) are added; the contour search covers 180/n deg anywhere in the frame; tau is set from the floor
over all three goldens. The pilot's numbers do not enter any reported result.
