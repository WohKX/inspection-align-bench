# Annotated-pair evaluation: summary

Pairs evaluated: 120. tau = 20.7 px (original image pixels, on the mean point error). Working long side: native.


Symmetry-aware scoring for: Full (a pose counts against the nearest of the part's equivalent orientations; correct_via_symmetry = share of pairs that are correct only because of that; err_mean_strict_px in results.csv is the error without it).

Unavailable methods: none

## 1. The annotation floor (read this first)

Mean point error of the similarity that best fits the clicked points themselves: click scatter plus the real shape difference between the two pieces. No similarity-model method can be expected to do better on a pair; differences between methods smaller than it are not interpretable. tau should be clearly above floor_p95.

| pairs | pairs_with_floor | floor_median_px | floor_p95_px | floor_max_px | gt_points_median |
|---|---|---|---|---|---|
| 120 | 120 | 5.88 | 10.35 | 16.77 | 4.00 |


The same, per golden. Each pair's floor contains the clicks and the shape of BOTH images, so every golden brings its own floor; the pooled p95 above therefore changes with the set of goldens. Fix tau once per part and keep it for every golden condition.

| group | pairs | floor_median_px | floor_p95_px | floor_max_px |
|---|---|---|---|---|
| Full/000 | 40 | 5.52 | 9.25 | 9.36 |
| Full/001 | 40 | 8.13 | 12.13 | 16.77 |
| Full/002 | 40 | 5.37 | 8.62 | 9.56 |


The poses in the data (from the ground-truth fit):


| rot_abs_median_deg | rot_abs_max_deg | shift_median_px | shift_max_px | scale_dev_max_pct |
|---|---|---|---|---|
| 1.90 | 5.82 | 54.79 | 140.10 | 2.96 |

## 2. Per method (all pairs)

Rates are fractions of pairs. err_*_accepted: mean point error over the poses the method accepted; err_median_all: over every pose it returned (also rejected ones); excess = error minus that pair's floor. `identity` is the reference line: its error is the raw misalignment.

| method | family | n_pairs | accepted | correct | silent_wrong | lost | rejected | no_pose | correct_via_symmetry | err_median_accepted_px | err_p95_accepted_px | err_median_all_px | excess_median_px | rot_err_median_abs_deg | latency_median_ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| identity | none | 120 | 1.000 | 0.017 | 0.983 | 0.000 | 0.000 | 0.000 | 0.000 | 58.876 | 116.608 | 58.876 | 53.955 | 1.898 | 0.019 |
| phase_correlation | dense_global | 120 | 0.042 | 0.008 | 0.033 | 0.408 | 0.550 | 0.000 | 0.000 | 371.090 | 612.348 | 27.591 | 363.549 | 4.211 | 22.697 |
| sift_ransac | classical_keypoints | 120 | 0.058 | 0.000 | 0.058 | 0.075 | 0.867 | 0.000 | 0.000 | 668.997 | 1189.169 | 487.099 | 661.486 | 4.108 | 476.685 |
| lightglue_disk | learned_matcher | 120 | 0.350 | 0.000 | 0.350 | 0.025 | 0.325 | 0.300 | 0.000 | 405.088 | 1052.009 | 172.892 | 401.240 | 2.021 | 2143.946 |
| lightglue_sift | learned_matcher | 120 | 0.158 | 0.000 | 0.158 | 0.125 | 0.517 | 0.200 | 0.000 | 396.200 | 1074.918 | 78.290 | 394.357 | 1.829 | 778.873 |
| contour_shape_match | shape | 120 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 8.323 | 15.156 | 8.323 | 2.561 | 0.591 | 1248.657 |
| phase_correlation+rot | dense_global | 120 | 0.042 | 0.008 | 0.033 | 0.342 | 0.617 | 0.000 | 0.000 | 371.090 | 612.348 | 81.629 | 363.549 | 4.211 | 580.115 |
| sift_ransac+rot | classical_keypoints | 120 | 0.100 | 0.000 | 0.100 | 0.125 | 0.775 | 0.000 | 0.000 | 397.503 | 1141.976 | 486.162 | 389.404 | 3.393 | 7111.767 |
| lightglue_disk+rot | learned_matcher | 120 | 0.392 | 0.000 | 0.392 | 0.033 | 0.525 | 0.050 | 0.000 | 364.799 | 1034.016 | 142.951 | 360.321 | 2.244 | 25671.719 |
| lightglue_sift+rot | learned_matcher | 120 | 0.217 | 0.008 | 0.208 | 0.125 | 0.558 | 0.100 | 0.000 | 372.288 | 1038.253 | 77.291 | 363.147 | 1.725 | 10382.554 |

## 2b. Correct rate at other tolerances

The same poses and the same accept/reject decisions, judged with a range of tau values (the headline tau is the one fixed before the run). A method whose rate only rises at tolerances far above the floor is coarse, not wrong.

| method | <= 1 px | <= 2 px | <= 3 px | <= 5 px | <= 10 px | <= 20 px | <= 20.7 px | <= 41.4 px |
|---|---|---|---|---|---|---|---|---|
| identity | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.017 | 0.017 | 0.233 |
| phase_correlation | 0.000 | 0.000 | 0.000 | 0.008 | 0.008 | 0.008 | 0.008 | 0.008 |
| sift_ransac | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| lightglue_disk | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.008 |
| lightglue_sift | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.008 |
| contour_shape_match | 0.000 | 0.000 | 0.008 | 0.083 | 0.642 | 1.000 | 1.000 | 1.000 |
| phase_correlation+rot | 0.000 | 0.000 | 0.000 | 0.008 | 0.008 | 0.008 | 0.008 | 0.008 |
| sift_ransac+rot | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| lightglue_disk+rot | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.025 |
| lightglue_sift+rot | 0.000 | 0.000 | 0.000 | 0.000 | 0.008 | 0.008 | 0.008 | 0.017 |

## 3. Does the method's own score tell right from wrong?

Without any threshold. auroc: how often a right pose (error <= tau) scores higher than a wrong one, over the poses the method returned (0.5 = no better than chance; blank = fewer than 3 right or 3 wrong poses). right_pose_any_decision: share of pairs whose pose is right, whatever the method decided. coverage_at_5pct_risk: the largest share of pairs a threshold on the score can accept while at most 5% of the accepted poses are wrong (0 = no threshold achieves it). risk_at_50pct_coverage: the share of wrong poses among the accepted ones when the threshold accepts half of the pairs. The full curves are in risk_coverage.csv.

| method | auroc | right_pose_any_decision | coverage_at_5pct_risk | risk_at_50pct_coverage |
|---|---|---|---|---|
| phase_correlation | 0.872 | 0.417 | 0.000 | 0.300 |
| sift_ransac | 0.692 | 0.075 | 0.000 | 0.901 |
| lightglue_disk | 0.309 | 0.025 | 0.000 | 0.968 |
| lightglue_sift | 0.506 | 0.125 | 0.000 | 0.800 |
| contour_shape_match |  | 1.000 | 1.000 | 0.000 |
| phase_correlation+rot | 0.911 | 0.350 | 0.000 | 0.333 |
| sift_ransac+rot | 0.680 | 0.125 | 0.000 | 0.816 |
| lightglue_disk+rot | 0.418 | 0.033 | 0.000 | 0.968 |
| lightglue_sift+rot | 0.469 | 0.133 | 0.000 | 0.831 |

## 4. Several goldens

golden i alone: correct rate with that golden only. own pick of k: the method is given the first k goldens, keeps the one its own decision score likes best (the ground truth plays no part), and accepts or rejects that pose as usual: what a system that stores k goldens would get. best possible of k: share of test images for which at least one of the k goldens gives a correct pose (an upper bound no method can claim).

| method | golden 1 alone | golden 2 alone | golden 3 alone | own pick of 1: correct | own pick of 1: silent_wrong | own pick of 2: correct | own pick of 2: silent_wrong | own pick of 3: correct | own pick of 3: silent_wrong | best possible of 2 | best possible of 3 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| phase_correlation | 0.000 | 0.000 | 0.025 | 0.000 | 0.025 | 0.000 | 0.100 | 0.025 | 0.100 | 0.000 | 0.025 |
| sift_ransac | 0.000 | 0.000 | 0.000 | 0.000 | 0.025 | 0.000 | 0.125 | 0.000 | 0.175 | 0.000 | 0.000 |
| lightglue_disk | 0.000 | 0.000 | 0.000 | 0.000 | 0.225 | 0.000 | 0.650 | 0.000 | 0.800 | 0.000 | 0.000 |
| lightglue_sift | 0.000 | 0.000 | 0.000 | 0.000 | 0.125 | 0.000 | 0.275 | 0.000 | 0.425 | 0.000 | 0.000 |
| contour_shape_match | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 1.000 | 0.000 | 1.000 | 0.000 | 1.000 | 1.000 |
| phase_correlation+rot | 0.000 | 0.000 | 0.025 | 0.000 | 0.025 | 0.000 | 0.100 | 0.025 | 0.100 | 0.000 | 0.025 |
| sift_ransac+rot | 0.000 | 0.000 | 0.000 | 0.000 | 0.050 | 0.000 | 0.200 | 0.000 | 0.300 | 0.000 | 0.000 |
| lightglue_disk+rot | 0.000 | 0.000 | 0.000 | 0.000 | 0.275 | 0.000 | 0.700 | 0.000 | 0.825 | 0.000 | 0.000 |
| lightglue_sift+rot | 0.000 | 0.025 | 0.000 | 0.000 | 0.150 | 0.025 | 0.350 | 0.025 | 0.550 | 0.025 | 0.025 |

## 5. Per group and method

| group | method | n_pairs | correct | silent_wrong | lost | rejected | no_pose | err_median_accepted_px | latency_median_ms |
|---|---|---|---|---|---|---|---|---|---|
| Full/000 | identity | 40 | 0.025 | 0.975 | 0.000 | 0.000 | 0.000 | 70.665 | 0.017 |
| Full/000 | phase_correlation | 40 | 0.000 | 0.025 | 0.700 | 0.275 | 0.000 | 371.090 | 22.753 |
| Full/000 | sift_ransac | 40 | 0.000 | 0.025 | 0.100 | 0.875 | 0.000 | 985.118 | 466.967 |
| Full/000 | lightglue_disk | 40 | 0.000 | 0.225 | 0.025 | 0.475 | 0.275 | 177.568 | 2145.451 |
| Full/000 | lightglue_sift | 40 | 0.000 | 0.125 | 0.100 | 0.525 | 0.250 | 176.303 | 780.440 |
| Full/000 | contour_shape_match | 40 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 7.266 | 1146.293 |
| Full/000 | phase_correlation+rot | 40 | 0.000 | 0.025 | 0.550 | 0.425 | 0.000 | 371.090 | 587.461 |
| Full/000 | sift_ransac+rot | 40 | 0.000 | 0.050 | 0.175 | 0.775 | 0.000 | 568.436 | 7012.815 |
| Full/000 | lightglue_disk+rot | 40 | 0.000 | 0.275 | 0.025 | 0.700 | 0.000 | 177.568 | 26033.931 |
| Full/000 | lightglue_sift+rot | 40 | 0.000 | 0.150 | 0.150 | 0.625 | 0.075 | 351.346 | 10366.767 |
| Full/001 | identity | 40 | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | 53.379 | 0.021 |
| Full/001 | phase_correlation | 40 | 0.000 | 0.075 | 0.125 | 0.800 | 0.000 | 382.461 | 22.716 |
| Full/001 | sift_ransac | 40 | 0.000 | 0.100 | 0.025 | 0.875 | 0.000 | 524.968 | 486.278 |
| Full/001 | lightglue_disk | 40 | 0.000 | 0.450 | 0.000 | 0.100 | 0.450 | 435.192 | 2162.621 |
| Full/001 | lightglue_sift | 40 | 0.000 | 0.150 | 0.125 | 0.525 | 0.200 | 396.862 | 777.566 |
| Full/001 | contour_shape_match | 40 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 11.973 | 1210.642 |
| Full/001 | phase_correlation+rot | 40 | 0.000 | 0.075 | 0.125 | 0.800 | 0.000 | 382.461 | 571.482 |
| Full/001 | sift_ransac+rot | 40 | 0.000 | 0.150 | 0.075 | 0.775 | 0.000 | 397.503 | 7247.910 |
| Full/001 | lightglue_disk+rot | 40 | 0.000 | 0.450 | 0.000 | 0.400 | 0.150 | 435.192 | 25636.097 |
| Full/001 | lightglue_sift+rot | 40 | 0.025 | 0.200 | 0.075 | 0.550 | 0.150 | 382.521 | 10416.397 |
| Full/002 | identity | 40 | 0.025 | 0.975 | 0.000 | 0.000 | 0.000 | 59.017 | 0.018 |
| Full/002 | phase_correlation | 40 | 0.025 | 0.000 | 0.400 | 0.575 | 0.000 | 4.577 | 22.645 |
| Full/002 | sift_ransac | 40 | 0.000 | 0.050 | 0.100 | 0.850 | 0.000 | 1151.250 | 475.243 |
| Full/002 | lightglue_disk | 40 | 0.000 | 0.375 | 0.050 | 0.400 | 0.175 | 399.796 | 2100.405 |
| Full/002 | lightglue_sift | 40 | 0.000 | 0.200 | 0.150 | 0.500 | 0.150 | 444.853 | 778.619 |
| Full/002 | contour_shape_match | 40 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 8.169 | 1576.187 |
| Full/002 | phase_correlation+rot | 40 | 0.025 | 0.000 | 0.350 | 0.625 | 0.000 | 4.577 | 582.195 |
| Full/002 | sift_ransac+rot | 40 | 0.000 | 0.100 | 0.125 | 0.775 | 0.000 | 701.859 | 7091.021 |
| Full/002 | lightglue_disk+rot | 40 | 0.000 | 0.450 | 0.075 | 0.475 | 0.000 | 326.150 | 25653.026 |
| Full/002 | lightglue_sift+rot | 40 | 0.000 | 0.275 | 0.150 | 0.500 | 0.075 | 338.607 | 10418.298 |
