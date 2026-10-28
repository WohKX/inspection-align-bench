# Annotated-pair evaluation: summary

Pairs evaluated: 120. tau = 20.7 px (original image pixels, on the mean point error). Working long side: native.

Acceptance thresholds calibrated on results/chewing_gum_calib (max-risk 0.05: lowest threshold with at most 5% of accepted poses wrong); methods without one keep their own rule.

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
| phase_correlation | dense_global | 120 | 0.000 | 0.000 | 0.000 | 0.417 | 0.583 | 0.000 | 0.000 |  |  | 27.591 |  |  | 22.697 |
| sift_ransac | classical_keypoints | 120 | 0.000 | 0.000 | 0.000 | 0.075 | 0.925 | 0.000 | 0.000 |  |  | 487.099 |  |  | 476.685 |
| lightglue_disk | learned_matcher | 120 | 0.000 | 0.000 | 0.000 | 0.025 | 0.675 | 0.300 | 0.000 |  |  | 172.892 |  |  | 2143.946 |
| lightglue_sift | learned_matcher | 120 | 0.000 | 0.000 | 0.000 | 0.125 | 0.675 | 0.200 | 0.000 |  |  | 78.290 |  |  | 778.873 |
| contour_shape_match | shape | 120 | 0.975 | 0.975 | 0.000 | 0.025 | 0.000 | 0.000 | 0.000 | 8.248 | 15.179 | 8.323 | 2.515 | 0.557 | 1248.657 |
| phase_correlation+rot | dense_global | 120 | 0.000 | 0.000 | 0.000 | 0.350 | 0.650 | 0.000 | 0.000 |  |  | 81.629 |  |  | 580.115 |
| sift_ransac+rot | classical_keypoints | 120 | 0.000 | 0.000 | 0.000 | 0.125 | 0.875 | 0.000 | 0.000 |  |  | 486.162 |  |  | 7111.767 |
| lightglue_disk+rot | learned_matcher | 120 | 0.000 | 0.000 | 0.000 | 0.033 | 0.917 | 0.050 | 0.000 |  |  | 142.951 |  |  | 25671.719 |
| lightglue_sift+rot | learned_matcher | 120 | 0.000 | 0.000 | 0.000 | 0.133 | 0.767 | 0.100 | 0.000 |  |  | 77.291 |  |  | 10382.554 |

## 2b. Correct rate at other tolerances

The same poses and the same accept/reject decisions, judged with a range of tau values (the headline tau is the one fixed before the run). A method whose rate only rises at tolerances far above the floor is coarse, not wrong.

| method | <= 1 px | <= 2 px | <= 3 px | <= 5 px | <= 10 px | <= 20 px | <= 20.7 px | <= 41.4 px |
|---|---|---|---|---|---|---|---|---|
| identity | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.017 | 0.017 | 0.233 |
| phase_correlation | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| sift_ransac | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| lightglue_disk | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| lightglue_sift | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| contour_shape_match | 0.000 | 0.000 | 0.008 | 0.083 | 0.642 | 0.975 | 0.975 | 0.975 |
| phase_correlation+rot | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| sift_ransac+rot | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| lightglue_disk+rot | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| lightglue_sift+rot | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

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
| phase_correlation | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| sift_ransac | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| lightglue_disk | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| lightglue_sift | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| contour_shape_match | 1.000 | 0.925 | 1.000 | 1.000 | 0.000 | 1.000 | 0.000 | 1.000 | 0.000 | 1.000 | 1.000 |
| phase_correlation+rot | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| sift_ransac+rot | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| lightglue_disk+rot | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| lightglue_sift+rot | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

## 5. Per group and method

| group | method | n_pairs | correct | silent_wrong | lost | rejected | no_pose | err_median_accepted_px | latency_median_ms |
|---|---|---|---|---|---|---|---|---|---|
| Full/000 | identity | 40 | 0.025 | 0.975 | 0.000 | 0.000 | 0.000 | 70.665 | 0.017 |
| Full/000 | phase_correlation | 40 | 0.000 | 0.000 | 0.700 | 0.300 | 0.000 |  | 22.753 |
| Full/000 | sift_ransac | 40 | 0.000 | 0.000 | 0.100 | 0.900 | 0.000 |  | 466.967 |
| Full/000 | lightglue_disk | 40 | 0.000 | 0.000 | 0.025 | 0.700 | 0.275 |  | 2145.451 |
| Full/000 | lightglue_sift | 40 | 0.000 | 0.000 | 0.100 | 0.650 | 0.250 |  | 780.440 |
| Full/000 | contour_shape_match | 40 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 7.266 | 1146.293 |
| Full/000 | phase_correlation+rot | 40 | 0.000 | 0.000 | 0.550 | 0.450 | 0.000 |  | 587.461 |
| Full/000 | sift_ransac+rot | 40 | 0.000 | 0.000 | 0.175 | 0.825 | 0.000 |  | 7012.815 |
| Full/000 | lightglue_disk+rot | 40 | 0.000 | 0.000 | 0.025 | 0.975 | 0.000 |  | 26033.931 |
| Full/000 | lightglue_sift+rot | 40 | 0.000 | 0.000 | 0.150 | 0.775 | 0.075 |  | 10366.767 |
| Full/001 | identity | 40 | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | 53.379 | 0.021 |
| Full/001 | phase_correlation | 40 | 0.000 | 0.000 | 0.125 | 0.875 | 0.000 |  | 22.716 |
| Full/001 | sift_ransac | 40 | 0.000 | 0.000 | 0.025 | 0.975 | 0.000 |  | 486.278 |
| Full/001 | lightglue_disk | 40 | 0.000 | 0.000 | 0.000 | 0.550 | 0.450 |  | 2162.621 |
| Full/001 | lightglue_sift | 40 | 0.000 | 0.000 | 0.125 | 0.675 | 0.200 |  | 777.566 |
| Full/001 | contour_shape_match | 40 | 0.925 | 0.000 | 0.075 | 0.000 | 0.000 | 11.768 | 1210.642 |
| Full/001 | phase_correlation+rot | 40 | 0.000 | 0.000 | 0.125 | 0.875 | 0.000 |  | 571.482 |
| Full/001 | sift_ransac+rot | 40 | 0.000 | 0.000 | 0.075 | 0.925 | 0.000 |  | 7247.910 |
| Full/001 | lightglue_disk+rot | 40 | 0.000 | 0.000 | 0.000 | 0.850 | 0.150 |  | 25636.097 |
| Full/001 | lightglue_sift+rot | 40 | 0.000 | 0.000 | 0.100 | 0.750 | 0.150 |  | 10416.397 |
| Full/002 | identity | 40 | 0.025 | 0.975 | 0.000 | 0.000 | 0.000 | 59.017 | 0.018 |
| Full/002 | phase_correlation | 40 | 0.000 | 0.000 | 0.425 | 0.575 | 0.000 |  | 22.645 |
| Full/002 | sift_ransac | 40 | 0.000 | 0.000 | 0.100 | 0.900 | 0.000 |  | 475.243 |
| Full/002 | lightglue_disk | 40 | 0.000 | 0.000 | 0.050 | 0.775 | 0.175 |  | 2100.405 |
| Full/002 | lightglue_sift | 40 | 0.000 | 0.000 | 0.150 | 0.700 | 0.150 |  | 778.619 |
| Full/002 | contour_shape_match | 40 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 8.169 | 1576.187 |
| Full/002 | phase_correlation+rot | 40 | 0.000 | 0.000 | 0.375 | 0.625 | 0.000 |  | 582.195 |
| Full/002 | sift_ransac+rot | 40 | 0.000 | 0.000 | 0.125 | 0.875 | 0.000 |  | 7091.021 |
| Full/002 | lightglue_disk+rot | 40 | 0.000 | 0.000 | 0.075 | 0.925 | 0.000 |  | 25653.026 |
| Full/002 | lightglue_sift+rot | 40 | 0.000 | 0.000 | 0.150 | 0.775 | 0.075 |  | 10418.298 |
