# Annotated-pair evaluation: summary

Pairs evaluated: 120. tau = 36.6 px (original image pixels, on the mean point error). Working long side: native.

Acceptance thresholds calibrated on results/fryum_calib (max-risk 0.05: lowest threshold with at most 5% of accepted poses wrong); methods without one keep their own rule.

Symmetry-aware scoring for: Full (a pose counts against the nearest of the part's equivalent orientations; correct_via_symmetry = share of pairs that are correct only because of that; err_mean_strict_px in results.csv is the error without it).

Unavailable methods: none

## 1. The annotation floor (read this first)

Mean point error of the similarity that best fits the clicked points themselves: click scatter plus the real shape difference between the two pieces. No similarity-model method can be expected to do better on a pair; differences between methods smaller than it are not interpretable. tau should be clearly above floor_p95.

| pairs | pairs_with_floor | floor_median_px | floor_p95_px | floor_max_px | gt_points_median |
|---|---|---|---|---|---|
| 120 | 120 | 9.36 | 18.28 | 21.91 | 7.00 |


The same, per golden. Each pair's floor contains the clicks and the shape of BOTH images, so every golden brings its own floor; the pooled p95 above therefore changes with the set of goldens. Fix tau once per part and keep it for every golden condition.

| group | pairs | floor_median_px | floor_p95_px | floor_max_px |
|---|---|---|---|---|
| Full/000 | 40 | 8.14 | 13.49 | 14.42 |
| Full/001 | 40 | 11.73 | 20.29 | 21.91 |
| Full/002 | 40 | 7.64 | 15.64 | 17.63 |


The poses in the data (from the ground-truth fit):


| rot_abs_median_deg | rot_abs_max_deg | shift_median_px | shift_max_px | scale_dev_max_pct |
|---|---|---|---|---|
| 12.77 | 29.85 | 15.04 | 46.99 | 5.94 |

## 2. Per method (all pairs)

Rates are fractions of pairs. err_*_accepted: mean point error over the poses the method accepted; err_median_all: over every pose it returned (also rejected ones); excess = error minus that pair's floor. `identity` is the reference line: its error is the raw misalignment.

| method | family | n_pairs | accepted | correct | silent_wrong | lost | rejected | no_pose | correct_via_symmetry | err_median_accepted_px | err_p95_accepted_px | err_median_all_px | excess_median_px | rot_err_median_abs_deg | latency_median_ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| identity | none | 120 | 1.000 | 0.358 | 0.642 | 0.000 | 0.000 | 0.000 | 0.000 | 48.237 | 97.744 | 48.237 | 37.357 | 12.773 | 0.023 |
| phase_correlation | dense_global | 120 | 0.117 | 0.108 | 0.008 | 0.242 | 0.642 | 0.000 | 0.000 | 18.899 | 40.170 | 48.627 | 10.682 | 4.028 | 23.579 |
| sift_ransac | classical_keypoints | 120 | 0.000 | 0.000 | 0.000 | 0.617 | 0.383 | 0.000 | 0.000 |  |  | 17.951 |  |  | 363.534 |
| lightglue_disk | learned_matcher | 120 | 0.033 | 0.008 | 0.025 | 0.300 | 0.667 | 0.000 | 0.000 | 55.797 | 73.081 | 54.142 | 48.457 | 13.432 | 1791.266 |
| lightglue_sift | learned_matcher | 120 | 0.158 | 0.150 | 0.008 | 0.458 | 0.383 | 0.000 | 0.000 | 19.768 | 30.295 | 24.420 | 10.795 | 3.700 | 776.494 |
| contour_shape_match | shape | 120 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.075 | 11.912 | 23.509 | 11.912 | 2.028 | 1.197 | 500.423 |
| phase_correlation+rot | dense_global | 120 | 0.150 | 0.142 | 0.008 | 0.542 | 0.308 | 0.000 | 0.058 | 17.406 | 29.891 | 25.729 | 5.522 | 1.961 | 267.250 |
| sift_ransac+rot | classical_keypoints | 120 | 0.033 | 0.033 | 0.000 | 0.658 | 0.308 | 0.000 | 0.000 | 6.211 | 7.379 | 15.555 | 1.318 | 0.808 | 1994.988 |
| lightglue_disk+rot | learned_matcher | 120 | 0.033 | 0.008 | 0.025 | 0.292 | 0.675 | 0.000 | 0.000 | 55.797 | 73.081 | 56.265 | 48.457 | 13.432 | 7925.851 |
| lightglue_sift+rot | learned_matcher | 120 | 0.142 | 0.133 | 0.008 | 0.600 | 0.258 | 0.000 | 0.000 | 18.430 | 32.135 | 18.968 | 10.795 | 3.700 | 3477.234 |

## 2b. Correct rate at other tolerances

The same poses and the same accept/reject decisions, judged with a range of tau values (the headline tau is the one fixed before the run). A method whose rate only rises at tolerances far above the floor is coarse, not wrong.

| method | <= 1 px | <= 2 px | <= 3 px | <= 5 px | <= 10 px | <= 20 px | <= 36.6 px | <= 73.2 px |
|---|---|---|---|---|---|---|---|---|
| identity | 0.000 | 0.000 | 0.000 | 0.000 | 0.008 | 0.092 | 0.358 | 0.808 |
| phase_correlation | 0.000 | 0.000 | 0.000 | 0.000 | 0.025 | 0.058 | 0.108 | 0.117 |
| sift_ransac | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| lightglue_disk | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.008 | 0.008 | 0.025 |
| lightglue_sift | 0.000 | 0.000 | 0.000 | 0.000 | 0.017 | 0.083 | 0.150 | 0.158 |
| contour_shape_match | 0.000 | 0.000 | 0.000 | 0.000 | 0.342 | 0.883 | 1.000 | 1.000 |
| phase_correlation+rot | 0.000 | 0.000 | 0.000 | 0.000 | 0.033 | 0.092 | 0.142 | 0.150 |
| sift_ransac+rot | 0.000 | 0.000 | 0.000 | 0.008 | 0.033 | 0.033 | 0.033 | 0.033 |
| lightglue_disk+rot | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.008 | 0.008 | 0.025 |
| lightglue_sift+rot | 0.000 | 0.000 | 0.000 | 0.000 | 0.017 | 0.083 | 0.133 | 0.142 |

## 3. Does the method's own score tell right from wrong?

Without any threshold. auroc: how often a right pose (error <= tau) scores higher than a wrong one, over the poses the method returned (0.5 = no better than chance; blank = fewer than 3 right or 3 wrong poses). right_pose_any_decision: share of pairs whose pose is right, whatever the method decided. coverage_at_5pct_risk: the largest share of pairs a threshold on the score can accept while at most 5% of the accepted poses are wrong (0 = no threshold achieves it). risk_at_50pct_coverage: the share of wrong poses among the accepted ones when the threshold accepts half of the pairs. The full curves are in risk_coverage.csv.

| method | auroc | right_pose_any_decision | coverage_at_5pct_risk | risk_at_50pct_coverage |
|---|---|---|---|---|
| phase_correlation | 0.787 | 0.350 | 0.075 | 0.467 |
| sift_ransac | 0.786 | 0.617 | 0.033 | 0.211 |
| lightglue_disk | 0.374 | 0.308 | 0.000 | 0.800 |
| lightglue_sift | 0.701 | 0.608 | 0.208 | 0.274 |
| contour_shape_match |  | 1.000 | 1.000 | 0.000 |
| phase_correlation+rot | 0.730 | 0.683 | 0.242 | 0.150 |
| sift_ransac+rot | 0.645 | 0.692 | 0.058 | 0.233 |
| lightglue_disk+rot | 0.328 | 0.300 | 0.000 | 0.817 |
| lightglue_sift+rot | 0.542 | 0.733 | 0.092 | 0.274 |

## 4. Several goldens

golden i alone: correct rate with that golden only. own pick of k: the method is given the first k goldens, keeps the one its own decision score likes best (the ground truth plays no part), and accepts or rejects that pose as usual: what a system that stores k goldens would get. best possible of k: share of test images for which at least one of the k goldens gives a correct pose (an upper bound no method can claim).

| method | golden 1 alone | golden 2 alone | golden 3 alone | own pick of 1: correct | own pick of 1: silent_wrong | own pick of 2: correct | own pick of 2: silent_wrong | own pick of 3: correct | own pick of 3: silent_wrong | best possible of 2 | best possible of 3 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| phase_correlation | 0.175 | 0.100 | 0.050 | 0.175 | 0.000 | 0.250 | 0.025 | 0.275 | 0.025 | 0.250 | 0.275 |
| sift_ransac | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| lightglue_disk | 0.025 | 0.000 | 0.000 | 0.025 | 0.050 | 0.025 | 0.075 | 0.025 | 0.075 | 0.025 | 0.025 |
| lightglue_sift | 0.175 | 0.150 | 0.125 | 0.175 | 0.000 | 0.325 | 0.025 | 0.375 | 0.025 | 0.325 | 0.375 |
| contour_shape_match | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 1.000 | 0.000 | 1.000 | 0.000 | 1.000 | 1.000 |
| phase_correlation+rot | 0.200 | 0.000 | 0.225 | 0.200 | 0.000 | 0.200 | 0.025 | 0.425 | 0.025 | 0.200 | 0.425 |
| sift_ransac+rot | 0.050 | 0.025 | 0.025 | 0.050 | 0.000 | 0.075 | 0.000 | 0.100 | 0.000 | 0.075 | 0.100 |
| lightglue_disk+rot | 0.025 | 0.000 | 0.000 | 0.025 | 0.050 | 0.025 | 0.075 | 0.025 | 0.075 | 0.025 | 0.025 |
| lightglue_sift+rot | 0.175 | 0.100 | 0.125 | 0.175 | 0.000 | 0.275 | 0.025 | 0.325 | 0.025 | 0.275 | 0.325 |

## 5. Per group and method

| group | method | n_pairs | correct | silent_wrong | lost | rejected | no_pose | err_median_accepted_px | latency_median_ms |
|---|---|---|---|---|---|---|---|---|---|
| Full/000 | identity | 40 | 0.425 | 0.575 | 0.000 | 0.000 | 0.000 | 40.816 | 0.021 |
| Full/000 | phase_correlation | 40 | 0.175 | 0.000 | 0.225 | 0.600 | 0.000 | 13.331 | 23.304 |
| Full/000 | sift_ransac | 40 | 0.000 | 0.000 | 0.750 | 0.250 | 0.000 |  | 367.925 |
| Full/000 | lightglue_disk | 40 | 0.025 | 0.050 | 0.350 | 0.575 | 0.000 | 49.247 | 1798.566 |
| Full/000 | lightglue_sift | 40 | 0.175 | 0.000 | 0.475 | 0.350 | 0.000 | 15.554 | 788.086 |
| Full/000 | contour_shape_match | 40 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 10.475 | 501.168 |
| Full/000 | phase_correlation+rot | 40 | 0.200 | 0.000 | 0.550 | 0.250 | 0.000 | 12.866 | 271.080 |
| Full/000 | sift_ransac+rot | 40 | 0.050 | 0.000 | 0.825 | 0.125 | 0.000 | 5.910 | 2017.935 |
| Full/000 | lightglue_disk+rot | 40 | 0.025 | 0.050 | 0.275 | 0.650 | 0.000 | 49.247 | 7932.687 |
| Full/000 | lightglue_sift+rot | 40 | 0.175 | 0.000 | 0.575 | 0.250 | 0.000 | 15.554 | 3441.957 |
| Full/001 | identity | 40 | 0.350 | 0.650 | 0.000 | 0.000 | 0.000 | 51.682 | 0.024 |
| Full/001 | phase_correlation | 40 | 0.100 | 0.025 | 0.225 | 0.650 | 0.000 | 24.358 | 23.739 |
| Full/001 | sift_ransac | 40 | 0.000 | 0.000 | 0.600 | 0.400 | 0.000 |  | 363.196 |
| Full/001 | lightglue_disk | 40 | 0.000 | 0.025 | 0.225 | 0.750 | 0.000 | 74.975 | 1789.901 |
| Full/001 | lightglue_sift | 40 | 0.150 | 0.025 | 0.400 | 0.425 | 0.000 | 25.653 | 772.008 |
| Full/001 | contour_shape_match | 40 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 14.043 | 532.918 |
| Full/001 | phase_correlation+rot | 40 | 0.000 | 0.025 | 0.575 | 0.400 | 0.000 | 43.453 | 264.954 |
| Full/001 | sift_ransac+rot | 40 | 0.025 | 0.000 | 0.650 | 0.325 | 0.000 | 5.233 | 1997.148 |
| Full/001 | lightglue_disk+rot | 40 | 0.000 | 0.025 | 0.275 | 0.700 | 0.000 | 74.975 | 7909.647 |
| Full/001 | lightglue_sift+rot | 40 | 0.100 | 0.025 | 0.650 | 0.225 | 0.000 | 25.653 | 3465.227 |
| Full/002 | identity | 40 | 0.300 | 0.700 | 0.000 | 0.000 | 0.000 | 47.416 | 0.023 |
| Full/002 | phase_correlation | 40 | 0.050 | 0.000 | 0.275 | 0.675 | 0.000 | 15.855 | 23.316 |
| Full/002 | sift_ransac | 40 | 0.000 | 0.000 | 0.500 | 0.500 | 0.000 |  | 359.683 |
| Full/002 | lightglue_disk | 40 | 0.000 | 0.000 | 0.325 | 0.675 | 0.000 |  | 1778.168 |
| Full/002 | lightglue_sift | 40 | 0.125 | 0.000 | 0.500 | 0.375 | 0.000 | 18.430 | 776.553 |
| Full/002 | contour_shape_match | 40 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 10.254 | 441.478 |
| Full/002 | phase_correlation+rot | 40 | 0.225 | 0.000 | 0.500 | 0.275 | 0.000 | 18.030 | 266.417 |
| Full/002 | sift_ransac+rot | 40 | 0.025 | 0.000 | 0.500 | 0.475 | 0.000 | 7.412 | 1975.582 |
| Full/002 | lightglue_disk+rot | 40 | 0.000 | 0.000 | 0.325 | 0.675 | 0.000 |  | 7934.477 |
| Full/002 | lightglue_sift+rot | 40 | 0.125 | 0.000 | 0.575 | 0.300 | 0.000 | 18.430 | 3488.616 |
