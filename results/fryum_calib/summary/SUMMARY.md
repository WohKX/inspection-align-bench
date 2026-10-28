# Annotated-pair evaluation: summary

Pairs evaluated: 30. tau = 36.6 px (original image pixels, on the mean point error). Working long side: native.


Symmetry-aware scoring for: Full (a pose counts against the nearest of the part's equivalent orientations; correct_via_symmetry = share of pairs that are correct only because of that; err_mean_strict_px in results.csv is the error without it).

Unavailable methods: none

## 1. The annotation floor (read this first)

Mean point error of the similarity that best fits the clicked points themselves: click scatter plus the real shape difference between the two pieces. No similarity-model method can be expected to do better on a pair; differences between methods smaller than it are not interpretable. tau should be clearly above floor_p95.

| pairs | pairs_with_floor | floor_median_px | floor_p95_px | floor_max_px | gt_points_median |
|---|---|---|---|---|---|
| 30 | 30 | 8.64 | 18.19 | 23.81 | 7.00 |


The same, per golden. Each pair's floor contains the clicks and the shape of BOTH images, so every golden brings its own floor; the pooled p95 above therefore changes with the set of goldens. Fix tau once per part and keep it for every golden condition.

| group | pairs | floor_median_px | floor_p95_px | floor_max_px |
|---|---|---|---|---|
| Full/000 | 10 | 10.36 | 16.55 | 17.63 |
| Full/001 | 10 | 8.38 | 21.31 | 23.81 |
| Full/002 | 10 | 8.55 | 17.41 | 18.12 |


The poses in the data (from the ground-truth fit):


| rot_abs_median_deg | rot_abs_max_deg | shift_median_px | shift_max_px | scale_dev_max_pct |
|---|---|---|---|---|
| 9.50 | 18.72 | 11.91 | 28.29 | 6.53 |

## 2. Per method (all pairs)

Rates are fractions of pairs. err_*_accepted: mean point error over the poses the method accepted; err_median_all: over every pose it returned (also rejected ones); excess = error minus that pair's floor. `identity` is the reference line: its error is the raw misalignment.

| method | family | n_pairs | accepted | correct | silent_wrong | lost | rejected | no_pose | correct_via_symmetry | err_median_accepted_px | err_p95_accepted_px | err_median_all_px | excess_median_px | rot_err_median_abs_deg | latency_median_ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| identity | none | 30 | 1.000 | 0.500 | 0.500 | 0.000 | 0.000 | 0.000 | 0.000 | 36.177 | 58.227 | 36.177 | 28.250 | 9.501 | 0.024 |
| phase_correlation | dense_global | 30 | 0.033 | 0.033 | 0.000 | 0.433 | 0.533 | 0.000 | 0.000 | 26.448 | 26.448 | 37.549 | 11.718 | 6.405 | 32.595 |
| sift_ransac | classical_keypoints | 30 | 0.533 | 0.467 | 0.067 | 0.200 | 0.267 | 0.000 | 0.000 | 9.159 | 344.255 | 16.268 | 1.739 | 0.631 | 400.055 |
| lightglue_disk | learned_matcher | 30 | 1.000 | 0.200 | 0.800 | 0.000 | 0.000 | 0.000 | 0.000 | 54.620 | 100.904 | 54.620 | 41.662 | 9.046 | 1817.196 |
| lightglue_sift | learned_matcher | 30 | 1.000 | 0.700 | 0.300 | 0.000 | 0.000 | 0.000 | 0.000 | 21.823 | 67.822 | 21.823 | 9.735 | 2.317 | 806.906 |
| contour_shape_match | shape | 30 | 0.100 | 0.100 | 0.000 | 0.900 | 0.000 | 0.000 | 0.000 | 6.767 | 7.197 | 10.589 | 1.171 | 0.235 | 511.974 |
| phase_correlation+rot | dense_global | 30 | 0.133 | 0.067 | 0.067 | 0.533 | 0.333 | 0.000 | 0.033 | 31.816 | 42.678 | 31.145 | 17.501 | 7.717 | 299.201 |
| sift_ransac+rot | classical_keypoints | 30 | 0.733 | 0.500 | 0.233 | 0.100 | 0.167 | 0.000 | 0.000 | 10.048 | 338.529 | 14.202 | 2.293 | 1.161 | 2081.149 |
| lightglue_disk+rot | learned_matcher | 30 | 1.000 | 0.233 | 0.767 | 0.000 | 0.000 | 0.000 | 0.067 | 54.039 | 100.904 | 54.039 | 44.556 | 7.824 | 7760.567 |
| lightglue_sift+rot | learned_matcher | 30 | 1.000 | 0.633 | 0.367 | 0.000 | 0.000 | 0.000 | 0.000 | 23.494 | 67.822 | 23.494 | 12.803 | 3.201 | 3541.612 |

## 2b. Correct rate at other tolerances

The same poses and the same accept/reject decisions, judged with a range of tau values (the headline tau is the one fixed before the run). A method whose rate only rises at tolerances far above the floor is coarse, not wrong.

| method | <= 1 px | <= 2 px | <= 3 px | <= 5 px | <= 10 px | <= 20 px | <= 36.4 px | <= 36.6 px | <= 73.2 px |
|---|---|---|---|---|---|---|---|---|---|
| identity | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.100 | 0.500 | 0.500 | 1.000 |
| phase_correlation | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.033 | 0.033 | 0.033 |
| sift_ransac | 0.000 | 0.000 | 0.000 | 0.000 | 0.433 | 0.467 | 0.467 | 0.467 | 0.467 |
| lightglue_disk | 0.000 | 0.000 | 0.000 | 0.000 | 0.100 | 0.167 | 0.200 | 0.200 | 0.767 |
| lightglue_sift | 0.000 | 0.000 | 0.000 | 0.000 | 0.200 | 0.433 | 0.700 | 0.700 | 0.933 |
| contour_shape_match | 0.000 | 0.000 | 0.000 | 0.000 | 0.100 | 0.100 | 0.100 | 0.100 | 0.100 |
| phase_correlation+rot | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.033 | 0.067 | 0.067 | 0.133 |
| sift_ransac+rot | 0.000 | 0.000 | 0.000 | 0.000 | 0.367 | 0.500 | 0.500 | 0.500 | 0.600 |
| lightglue_disk+rot | 0.000 | 0.000 | 0.000 | 0.000 | 0.133 | 0.200 | 0.233 | 0.233 | 0.733 |
| lightglue_sift+rot | 0.000 | 0.000 | 0.000 | 0.000 | 0.167 | 0.400 | 0.633 | 0.633 | 0.933 |

## 3. Does the method's own score tell right from wrong?

Without any threshold. auroc: how often a right pose (error <= tau) scores higher than a wrong one, over the poses the method returned (0.5 = no better than chance; blank = fewer than 3 right or 3 wrong poses). right_pose_any_decision: share of pairs whose pose is right, whatever the method decided. coverage_at_5pct_risk: the largest share of pairs a threshold on the score can accept while at most 5% of the accepted poses are wrong (0 = no threshold achieves it). risk_at_50pct_coverage: the share of wrong poses among the accepted ones when the threshold accepts half of the pairs. The full curves are in risk_coverage.csv.

| method | auroc | right_pose_any_decision | coverage_at_5pct_risk | risk_at_50pct_coverage |
|---|---|---|---|---|
| phase_correlation | 0.830 | 0.467 | 0.167 | 0.333 |
| sift_ransac | 0.705 | 0.667 | 0.000 | 0.133 |
| lightglue_disk | 0.424 | 0.200 | 0.033 | 0.867 |
| lightglue_sift | 0.505 | 0.700 | 0.167 | 0.333 |
| contour_shape_match |  | 1.000 | 1.000 | 0.000 |
| phase_correlation+rot | 0.704 | 0.600 | 0.067 | 0.267 |
| sift_ransac+rot | 0.773 | 0.600 | 0.033 | 0.133 |
| lightglue_disk+rot | 0.335 | 0.233 | 0.033 | 0.867 |
| lightglue_sift+rot | 0.636 | 0.633 | 0.167 | 0.333 |

## 4. Several goldens

golden i alone: correct rate with that golden only. own pick of k: the method is given the first k goldens, keeps the one its own decision score likes best (the ground truth plays no part), and accepts or rejects that pose as usual: what a system that stores k goldens would get. best possible of k: share of test images for which at least one of the k goldens gives a correct pose (an upper bound no method can claim).

| method | golden 1 alone | golden 2 alone | golden 3 alone | own pick of 1: correct | own pick of 1: silent_wrong | own pick of 2: correct | own pick of 2: silent_wrong | own pick of 3: correct | own pick of 3: silent_wrong | best possible of 2 | best possible of 3 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| phase_correlation | 0.000 | 0.100 | 0.000 | 0.000 | 0.000 | 0.100 | 0.000 | 0.100 | 0.000 | 0.100 | 0.100 |
| sift_ransac | 0.400 | 0.600 | 0.400 | 0.400 | 0.100 | 0.600 | 0.000 | 0.500 | 0.100 | 0.600 | 0.600 |
| lightglue_disk | 0.000 | 0.500 | 0.100 | 0.000 | 1.000 | 0.200 | 0.800 | 0.200 | 0.800 | 0.500 | 0.600 |
| lightglue_sift | 0.800 | 0.700 | 0.600 | 0.800 | 0.200 | 0.700 | 0.300 | 0.700 | 0.300 | 0.900 | 0.900 |
| contour_shape_match | 0.000 | 0.000 | 0.300 | 0.000 | 0.000 | 0.000 | 0.000 | 0.300 | 0.000 | 0.000 | 0.300 |
| phase_correlation+rot | 0.100 | 0.100 | 0.000 | 0.100 | 0.100 | 0.200 | 0.100 | 0.200 | 0.200 | 0.200 | 0.200 |
| sift_ransac+rot | 0.400 | 0.600 | 0.500 | 0.400 | 0.100 | 0.500 | 0.400 | 0.500 | 0.500 | 0.600 | 0.700 |
| lightglue_disk+rot | 0.100 | 0.400 | 0.200 | 0.100 | 0.900 | 0.200 | 0.800 | 0.200 | 0.800 | 0.400 | 0.600 |
| lightglue_sift+rot | 0.700 | 0.700 | 0.500 | 0.700 | 0.300 | 0.700 | 0.300 | 0.700 | 0.300 | 0.900 | 0.900 |

## 5. Per group and method

| group | method | n_pairs | correct | silent_wrong | lost | rejected | no_pose | err_median_accepted_px | latency_median_ms |
|---|---|---|---|---|---|---|---|---|---|
| Full/000 | identity | 10 | 0.600 | 0.400 | 0.000 | 0.000 | 0.000 | 34.464 | 0.024 |
| Full/000 | phase_correlation | 10 | 0.000 | 0.000 | 0.600 | 0.400 | 0.000 |  | 32.258 |
| Full/000 | sift_ransac | 10 | 0.400 | 0.100 | 0.200 | 0.300 | 0.000 | 9.268 | 404.776 |
| Full/000 | lightglue_disk | 10 | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | 54.768 | 1826.616 |
| Full/000 | lightglue_sift | 10 | 0.800 | 0.200 | 0.000 | 0.000 | 0.000 | 20.269 | 805.334 |
| Full/000 | contour_shape_match | 10 | 0.000 | 0.000 | 1.000 | 0.000 | 0.000 |  | 523.576 |
| Full/000 | phase_correlation+rot | 10 | 0.100 | 0.100 | 0.400 | 0.400 | 0.000 | 29.432 | 310.777 |
| Full/000 | sift_ransac+rot | 10 | 0.400 | 0.100 | 0.200 | 0.300 | 0.000 | 8.617 | 2147.759 |
| Full/000 | lightglue_disk+rot | 10 | 0.100 | 0.900 | 0.000 | 0.000 | 0.000 | 54.039 | 7760.567 |
| Full/000 | lightglue_sift+rot | 10 | 0.700 | 0.300 | 0.000 | 0.000 | 0.000 | 23.494 | 3560.205 |
| Full/001 | identity | 10 | 0.700 | 0.300 | 0.000 | 0.000 | 0.000 | 27.105 | 0.025 |
| Full/001 | phase_correlation | 10 | 0.100 | 0.000 | 0.600 | 0.300 | 0.000 | 26.448 | 30.836 |
| Full/001 | sift_ransac | 10 | 0.600 | 0.000 | 0.300 | 0.100 | 0.000 | 9.557 | 402.320 |
| Full/001 | lightglue_disk | 10 | 0.500 | 0.500 | 0.000 | 0.000 | 0.000 | 40.423 | 1818.048 |
| Full/001 | lightglue_sift | 10 | 0.700 | 0.300 | 0.000 | 0.000 | 0.000 | 26.478 | 792.157 |
| Full/001 | contour_shape_match | 10 | 0.000 | 0.000 | 1.000 | 0.000 | 0.000 |  | 519.539 |
| Full/001 | phase_correlation+rot | 10 | 0.100 | 0.000 | 0.700 | 0.200 | 0.000 | 26.448 | 292.874 |
| Full/001 | sift_ransac+rot | 10 | 0.600 | 0.300 | 0.000 | 0.100 | 0.000 | 10.158 | 2059.296 |
| Full/001 | lightglue_disk+rot | 10 | 0.400 | 0.600 | 0.000 | 0.000 | 0.000 | 55.228 | 7765.699 |
| Full/001 | lightglue_sift+rot | 10 | 0.700 | 0.300 | 0.000 | 0.000 | 0.000 | 26.478 | 3450.551 |
| Full/002 | identity | 10 | 0.200 | 0.800 | 0.000 | 0.000 | 0.000 | 46.667 | 0.021 |
| Full/002 | phase_correlation | 10 | 0.000 | 0.000 | 0.100 | 0.900 | 0.000 |  | 33.537 |
| Full/002 | sift_ransac | 10 | 0.400 | 0.100 | 0.100 | 0.400 | 0.000 | 7.171 | 398.440 |
| Full/002 | lightglue_disk | 10 | 0.100 | 0.900 | 0.000 | 0.000 | 0.000 | 55.442 | 1787.382 |
| Full/002 | lightglue_sift | 10 | 0.600 | 0.400 | 0.000 | 0.000 | 0.000 | 16.920 | 837.719 |
| Full/002 | contour_shape_match | 10 | 0.300 | 0.000 | 0.700 | 0.000 | 0.000 | 6.767 | 461.523 |
| Full/002 | phase_correlation+rot | 10 | 0.000 | 0.100 | 0.500 | 0.400 | 0.000 | 37.184 | 306.152 |
| Full/002 | sift_ransac+rot | 10 | 0.500 | 0.300 | 0.100 | 0.100 | 0.000 | 12.491 | 2107.331 |
| Full/002 | lightglue_disk+rot | 10 | 0.200 | 0.800 | 0.000 | 0.000 | 0.000 | 50.057 | 7751.629 |
| Full/002 | lightglue_sift+rot | 10 | 0.500 | 0.500 | 0.000 | 0.000 | 0.000 | 32.056 | 3564.492 |
