# Annotated-pair evaluation: summary

Pairs evaluated: 30. tau = 10.3 px (original image pixels, on the mean point error). Working long side: native.


Symmetry-aware scoring for: Full (a pose counts against the nearest of the part's equivalent orientations; correct_via_symmetry = share of pairs that are correct only because of that; err_mean_strict_px in results.csv is the error without it).

Unavailable methods: none

## 1. The annotation floor (read this first)

Mean point error of the similarity that best fits the clicked points themselves: click scatter plus the real shape difference between the two pieces. No similarity-model method can be expected to do better on a pair; differences between methods smaller than it are not interpretable. tau should be clearly above floor_p95.

| pairs | pairs_with_floor | floor_median_px | floor_p95_px | floor_max_px | gt_points_median |
|---|---|---|---|---|---|
| 30 | 30 | 3.30 | 4.55 | 4.67 | 5.00 |


The same, per golden. Each pair's floor contains the clicks and the shape of BOTH images, so every golden brings its own floor; the pooled p95 above therefore changes with the set of goldens. Fix tau once per part and keep it for every golden condition.

| group | pairs | floor_median_px | floor_p95_px | floor_max_px |
|---|---|---|---|---|
| Full/000 | 10 | 3.11 | 4.11 | 4.44 |
| Full/001 | 10 | 4.01 | 4.65 | 4.67 |
| Full/002 | 10 | 2.73 | 3.42 | 3.45 |


The poses in the data (from the ground-truth fit):


| rot_abs_median_deg | rot_abs_max_deg | shift_median_px | shift_max_px | scale_dev_max_pct |
|---|---|---|---|---|
| 23.85 | 44.65 | 2.64 | 5.37 | 0.52 |

## 2. Per method (all pairs)

Rates are fractions of pairs. err_*_accepted: mean point error over the poses the method accepted; err_median_all: over every pose it returned (also rejected ones); excess = error minus that pair's floor. `identity` is the reference line: its error is the raw misalignment.

| method | family | n_pairs | accepted | correct | silent_wrong | lost | rejected | no_pose | correct_via_symmetry | err_median_accepted_px | err_p95_accepted_px | err_median_all_px | excess_median_px | rot_err_median_abs_deg | latency_median_ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| identity | none | 30 | 1.000 | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 100.009 | 177.272 | 100.009 | 96.422 | 23.853 | 0.017 |
| phase_correlation | dense_global | 30 | 0.333 | 0.000 | 0.333 | 0.000 | 0.667 | 0.000 | 0.000 | 108.889 | 177.656 | 177.294 | 105.213 | 25.980 | 6.255 |
| sift_ransac | classical_keypoints | 30 | 0.067 | 0.033 | 0.033 | 0.100 | 0.833 | 0.000 | 0.033 | 8.652 | 13.023 | 109.258 | 6.727 | 1.035 | 90.154 |
| lightglue_disk | learned_matcher | 30 | 1.000 | 0.067 | 0.933 | 0.000 | 0.000 | 0.000 | 0.033 | 80.847 | 175.270 | 80.847 | 78.564 | 18.876 | 1461.474 |
| lightglue_sift | learned_matcher | 30 | 0.900 | 0.200 | 0.700 | 0.000 | 0.100 | 0.000 | 0.133 | 18.216 | 165.488 | 18.346 | 15.480 | 2.791 | 701.750 |
| contour_shape_match | shape | 30 | 0.000 | 0.000 | 0.000 | 0.867 | 0.133 | 0.000 | 0.000 |  |  | 4.771 |  |  | 255.240 |
| phase_correlation+rot | dense_global | 30 | 0.633 | 0.067 | 0.567 | 0.067 | 0.300 | 0.000 | 0.000 | 79.108 | 174.399 | 65.593 | 75.400 | 18.745 | 86.850 |
| sift_ransac+rot | classical_keypoints | 30 | 0.133 | 0.067 | 0.067 | 0.200 | 0.667 | 0.000 | 0.067 | 7.448 | 217.931 | 94.397 | 5.073 | 1.123 | 762.571 |
| lightglue_disk+rot | learned_matcher | 30 | 1.000 | 0.100 | 0.900 | 0.000 | 0.000 | 0.000 | 0.067 | 78.958 | 179.731 | 78.958 | 75.367 | 18.444 | 10117.641 |
| lightglue_sift+rot | learned_matcher | 30 | 0.933 | 0.300 | 0.633 | 0.000 | 0.067 | 0.000 | 0.200 | 17.998 | 164.377 | 18.346 | 14.871 | 3.763 | 4745.685 |

## 2b. Correct rate at other tolerances

The same poses and the same accept/reject decisions, judged with a range of tau values (the headline tau is the one fixed before the run). A method whose rate only rises at tolerances far above the floor is coarse, not wrong.

| method | <= 1 px | <= 2 px | <= 3 px | <= 5 px | <= 9.1 px | <= 10 px | <= 10.3 px | <= 20 px | <= 20.6 px |
|---|---|---|---|---|---|---|---|---|---|
| identity | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.033 | 0.033 |
| phase_correlation | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| sift_ransac | 0.000 | 0.000 | 0.000 | 0.033 | 0.033 | 0.033 | 0.033 | 0.067 | 0.067 |
| lightglue_disk | 0.000 | 0.000 | 0.033 | 0.033 | 0.067 | 0.067 | 0.067 | 0.100 | 0.100 |
| lightglue_sift | 0.000 | 0.000 | 0.000 | 0.067 | 0.167 | 0.200 | 0.200 | 0.500 | 0.500 |
| contour_shape_match | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| phase_correlation+rot | 0.000 | 0.000 | 0.000 | 0.000 | 0.033 | 0.033 | 0.067 | 0.167 | 0.167 |
| sift_ransac+rot | 0.000 | 0.000 | 0.033 | 0.067 | 0.067 | 0.067 | 0.067 | 0.100 | 0.100 |
| lightglue_disk+rot | 0.000 | 0.000 | 0.000 | 0.033 | 0.100 | 0.100 | 0.100 | 0.267 | 0.267 |
| lightglue_sift+rot | 0.000 | 0.000 | 0.000 | 0.067 | 0.233 | 0.300 | 0.300 | 0.567 | 0.567 |

## 3. Does the method's own score tell right from wrong?

Without any threshold. auroc: how often a right pose (error <= tau) scores higher than a wrong one, over the poses the method returned (0.5 = no better than chance; blank = fewer than 3 right or 3 wrong poses). right_pose_any_decision: share of pairs whose pose is right, whatever the method decided. coverage_at_5pct_risk: the largest share of pairs a threshold on the score can accept while at most 5% of the accepted poses are wrong (0 = no threshold achieves it). risk_at_50pct_coverage: the share of wrong poses among the accepted ones when the threshold accepts half of the pairs. The full curves are in risk_coverage.csv.

| method | auroc | right_pose_any_decision | coverage_at_5pct_risk | risk_at_50pct_coverage |
|---|---|---|---|---|
| phase_correlation |  | 0.000 | 0.000 | 1.000 |
| sift_ransac | 0.692 | 0.133 | 0.000 | 0.810 |
| lightglue_disk |  | 0.067 | 0.000 | 0.875 |
| lightglue_sift | 0.719 | 0.200 | 0.033 | 0.800 |
| contour_shape_match | 0.692 | 0.867 | 0.367 | 0.067 |
| phase_correlation+rot | 0.385 | 0.133 | 0.000 | 0.933 |
| sift_ransac+rot | 0.636 | 0.267 | 0.067 | 0.714 |
| lightglue_disk+rot | 0.926 | 0.100 | 0.033 | 0.800 |
| lightglue_sift+rot | 0.722 | 0.300 | 0.033 | 0.625 |

## 4. Several goldens

golden i alone: correct rate with that golden only. own pick of k: the method is given the first k goldens, keeps the one its own decision score likes best (the ground truth plays no part), and accepts or rejects that pose as usual: what a system that stores k goldens would get. best possible of k: share of test images for which at least one of the k goldens gives a correct pose (an upper bound no method can claim).

| method | golden 1 alone | golden 2 alone | golden 3 alone | own pick of 1: correct | own pick of 1: silent_wrong | own pick of 2: correct | own pick of 2: silent_wrong | own pick of 3: correct | own pick of 3: silent_wrong | best possible of 2 | best possible of 3 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| phase_correlation | 0.000 | 0.000 | 0.000 | 0.000 | 0.500 | 0.000 | 0.900 | 0.000 | 0.900 | 0.000 | 0.000 |
| sift_ransac | 0.000 | 0.000 | 0.100 | 0.000 | 0.000 | 0.000 | 0.000 | 0.100 | 0.100 | 0.000 | 0.100 |
| lightglue_disk | 0.100 | 0.000 | 0.100 | 0.100 | 0.900 | 0.100 | 0.900 | 0.200 | 0.800 | 0.100 | 0.200 |
| lightglue_sift | 0.200 | 0.100 | 0.300 | 0.200 | 0.800 | 0.200 | 0.800 | 0.300 | 0.700 | 0.200 | 0.400 |
| contour_shape_match | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| phase_correlation+rot | 0.000 | 0.000 | 0.200 | 0.000 | 0.800 | 0.000 | 1.000 | 0.000 | 1.000 | 0.000 | 0.200 |
| sift_ransac+rot | 0.000 | 0.000 | 0.200 | 0.000 | 0.100 | 0.000 | 0.100 | 0.200 | 0.000 | 0.000 | 0.200 |
| lightglue_disk+rot | 0.200 | 0.000 | 0.100 | 0.200 | 0.800 | 0.200 | 0.800 | 0.200 | 0.800 | 0.200 | 0.300 |
| lightglue_sift+rot | 0.300 | 0.200 | 0.400 | 0.300 | 0.700 | 0.300 | 0.700 | 0.500 | 0.500 | 0.400 | 0.600 |

## 5. Per group and method

| group | method | n_pairs | correct | silent_wrong | lost | rejected | no_pose | err_median_accepted_px | latency_median_ms |
|---|---|---|---|---|---|---|---|---|---|
| Full/000 | identity | 10 | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | 81.843 | 0.015 |
| Full/000 | phase_correlation | 10 | 0.000 | 0.500 | 0.000 | 0.500 | 0.000 | 103.501 | 6.282 |
| Full/000 | sift_ransac | 10 | 0.000 | 0.000 | 0.100 | 0.900 | 0.000 |  | 93.888 |
| Full/000 | lightglue_disk | 10 | 0.100 | 0.900 | 0.000 | 0.000 | 0.000 | 61.327 | 1470.143 |
| Full/000 | lightglue_sift | 10 | 0.200 | 0.800 | 0.000 | 0.000 | 0.000 | 17.996 | 733.764 |
| Full/000 | contour_shape_match | 10 | 0.000 | 0.000 | 0.900 | 0.100 | 0.000 |  | 259.148 |
| Full/000 | phase_correlation+rot | 10 | 0.000 | 0.800 | 0.100 | 0.100 | 0.000 | 117.890 | 87.824 |
| Full/000 | sift_ransac+rot | 10 | 0.000 | 0.100 | 0.200 | 0.700 | 0.000 | 11.005 | 777.138 |
| Full/000 | lightglue_disk+rot | 10 | 0.200 | 0.800 | 0.000 | 0.000 | 0.000 | 19.062 | 10138.868 |
| Full/000 | lightglue_sift+rot | 10 | 0.300 | 0.700 | 0.000 | 0.000 | 0.000 | 17.779 | 4713.670 |
| Full/001 | identity | 10 | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | 92.474 | 0.020 |
| Full/001 | phase_correlation | 10 | 0.000 | 0.400 | 0.000 | 0.600 | 0.000 | 99.323 | 6.263 |
| Full/001 | sift_ransac | 10 | 0.000 | 0.000 | 0.100 | 0.900 | 0.000 |  | 89.358 |
| Full/001 | lightglue_disk | 10 | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | 78.235 | 1485.804 |
| Full/001 | lightglue_sift | 10 | 0.100 | 0.600 | 0.000 | 0.300 | 0.000 | 25.427 | 712.130 |
| Full/001 | contour_shape_match | 10 | 0.000 | 0.000 | 0.900 | 0.100 | 0.000 |  | 256.036 |
| Full/001 | phase_correlation+rot | 10 | 0.000 | 0.700 | 0.000 | 0.300 | 0.000 | 26.038 | 83.348 |
| Full/001 | sift_ransac+rot | 10 | 0.000 | 0.100 | 0.100 | 0.800 | 0.000 | 254.448 | 764.464 |
| Full/001 | lightglue_disk+rot | 10 | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | 97.402 | 10138.679 |
| Full/001 | lightglue_sift+rot | 10 | 0.200 | 0.600 | 0.000 | 0.200 | 0.000 | 22.737 | 4742.181 |
| Full/002 | identity | 10 | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | 111.288 | 0.017 |
| Full/002 | phase_correlation | 10 | 0.000 | 0.100 | 0.000 | 0.900 | 0.000 | 173.675 | 6.247 |
| Full/002 | sift_ransac | 10 | 0.100 | 0.100 | 0.100 | 0.700 | 0.000 | 8.652 | 86.173 |
| Full/002 | lightglue_disk | 10 | 0.100 | 0.900 | 0.000 | 0.000 | 0.000 | 95.374 | 1458.805 |
| Full/002 | lightglue_sift | 10 | 0.300 | 0.700 | 0.000 | 0.000 | 0.000 | 16.204 | 683.455 |
| Full/002 | contour_shape_match | 10 | 0.000 | 0.000 | 0.800 | 0.200 | 0.000 |  | 255.050 |
| Full/002 | phase_correlation+rot | 10 | 0.200 | 0.200 | 0.100 | 0.500 | 0.000 | 10.833 | 86.861 |
| Full/002 | sift_ransac+rot | 10 | 0.200 | 0.000 | 0.300 | 0.500 | 0.000 | 2.949 | 750.481 |
| Full/002 | lightglue_disk+rot | 10 | 0.100 | 0.900 | 0.000 | 0.000 | 0.000 | 96.506 | 10090.082 |
| Full/002 | lightglue_sift+rot | 10 | 0.400 | 0.600 | 0.000 | 0.000 | 0.000 | 14.363 | 4779.101 |
