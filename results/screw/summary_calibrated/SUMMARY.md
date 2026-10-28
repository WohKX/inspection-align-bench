# Annotated-pair evaluation: summary

Pairs evaluated: 120. tau = 6.1 px (original image pixels, on the mean point error). Working long side: native.

Acceptance thresholds calibrated on results/screw_calib (max-risk 0.05: lowest threshold with at most 5% of accepted poses wrong); methods without one keep their own rule.


Unavailable methods: none

## 1. The annotation floor (read this first)

Mean point error of the similarity that best fits the clicked points themselves: click scatter plus the real shape difference between the two pieces. No similarity-model method can be expected to do better on a pair; differences between methods smaller than it are not interpretable. tau should be clearly above floor_p95.

| pairs | pairs_with_floor | floor_median_px | floor_p95_px | floor_max_px | gt_points_median |
|---|---|---|---|---|---|
| 120 | 120 | 1.64 | 3.06 | 3.73 | 3.00 |


The same, per golden. Each pair's floor contains the clicks and the shape of BOTH images, so every golden brings its own floor; the pooled p95 above therefore changes with the set of goldens. Fix tau once per part and keep it for every golden condition.

| group | pairs | floor_median_px | floor_p95_px | floor_max_px |
|---|---|---|---|---|
| Full/000 | 40 | 2.44 | 3.41 | 3.73 |
| Full/001 | 40 | 0.92 | 2.28 | 2.53 |
| Full/002 | 40 | 1.34 | 2.49 | 2.67 |


The poses in the data (from the ground-truth fit):


| rot_abs_median_deg | rot_abs_max_deg | shift_median_px | shift_max_px | scale_dev_max_pct |
|---|---|---|---|---|
| 91.47 | 178.86 | 142.34 | 251.93 | 1.62 |

## 2. Per method (all pairs)

Rates are fractions of pairs. err_*_accepted: mean point error over the poses the method accepted; err_median_all: over every pose it returned (also rejected ones); excess = error minus that pair's floor. `identity` is the reference line: its error is the raw misalignment.

| method | family | n_pairs | accepted | correct | silent_wrong | lost | rejected | no_pose | err_median_accepted_px | err_p95_accepted_px | err_median_all_px | excess_median_px | rot_err_median_abs_deg | latency_median_ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| identity | none | 120 | 1.000 | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | 626.834 | 877.304 | 626.834 | 624.509 | 91.470 | 0.019 |
| phase_correlation | dense_global | 120 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 0.000 |  |  | 638.542 |  |  | 13.302 |
| sift_ransac | classical_keypoints | 120 | 0.000 | 0.000 | 0.000 | 0.067 | 0.933 | 0.000 |  |  | 31.055 |  |  | 130.187 |
| lightglue_disk | learned_matcher | 120 | 0.000 | 0.000 | 0.000 | 0.000 | 0.850 | 0.150 |  |  | 725.328 |  |  | 2361.293 |
| lightglue_sift | learned_matcher | 120 | 0.050 | 0.008 | 0.042 | 0.058 | 0.758 | 0.133 | 10.625 | 22.003 | 49.487 | 9.465 | 0.188 | 791.803 |
| contour_shape_match | shape | 120 | 0.000 | 0.000 | 0.000 | 0.108 | 0.892 | 0.000 |  |  | 20.338 |  |  | 3883.553 |
| phase_correlation+rot | dense_global | 120 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 0.000 |  |  | 46.969 |  |  | 824.665 |
| sift_ransac+rot | classical_keypoints | 120 | 0.000 | 0.000 | 0.000 | 0.058 | 0.942 | 0.000 |  |  | 24.592 |  |  | 5036.206 |
| lightglue_disk+rot | learned_matcher | 120 | 0.000 | 0.000 | 0.000 | 0.067 | 0.933 | 0.000 |  |  | 31.560 |  |  | 56195.594 |
| lightglue_sift+rot | learned_matcher | 120 | 0.050 | 0.025 | 0.025 | 0.083 | 0.867 | 0.000 | 6.361 | 9.051 | 16.989 | 4.365 | 0.250 | 20308.206 |

## 2b. Correct rate at other tolerances

The same poses and the same accept/reject decisions, judged with a range of tau values (the headline tau is the one fixed before the run). A method whose rate only rises at tolerances far above the floor is coarse, not wrong.

| method | <= 1 px | <= 2 px | <= 3 px | <= 5 px | <= 6.1 px | <= 10 px | <= 12.2 px | <= 20 px |
|---|---|---|---|---|---|---|---|---|
| identity | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.008 | 0.008 | 0.017 |
| phase_correlation | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| sift_ransac | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| lightglue_disk | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| lightglue_sift | 0.000 | 0.000 | 0.000 | 0.000 | 0.008 | 0.017 | 0.042 | 0.042 |
| contour_shape_match | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| phase_correlation+rot | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| sift_ransac+rot | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| lightglue_disk+rot | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| lightglue_sift+rot | 0.000 | 0.000 | 0.000 | 0.017 | 0.025 | 0.050 | 0.050 | 0.050 |

## 3. Does the method's own score tell right from wrong?

Without any threshold. auroc: how often a right pose (error <= tau) scores higher than a wrong one, over the poses the method returned (0.5 = no better than chance; blank = fewer than 3 right or 3 wrong poses). right_pose_any_decision: share of pairs whose pose is right, whatever the method decided. coverage_at_5pct_risk: the largest share of pairs a threshold on the score can accept while at most 5% of the accepted poses are wrong (0 = no threshold achieves it). risk_at_50pct_coverage: the share of wrong poses among the accepted ones when the threshold accepts half of the pairs. The full curves are in risk_coverage.csv.

| method | auroc | right_pose_any_decision | coverage_at_5pct_risk | risk_at_50pct_coverage |
|---|---|---|---|---|
| phase_correlation |  | 0.000 | 0.000 | 1.000 |
| sift_ransac | 0.747 | 0.067 | 0.000 | 0.900 |
| lightglue_disk |  | 0.000 | 0.000 | 1.000 |
| lightglue_sift | 0.818 | 0.067 | 0.000 | 0.889 |
| contour_shape_match | 0.949 | 0.108 | 0.033 | 0.783 |
| phase_correlation+rot |  | 0.000 | 0.000 | 1.000 |
| sift_ransac+rot | 0.826 | 0.058 | 0.000 | 0.891 |
| lightglue_disk+rot | 0.405 | 0.067 | 0.000 | 0.967 |
| lightglue_sift+rot | 0.807 | 0.108 | 0.008 | 0.817 |

## 4. Several goldens

golden i alone: correct rate with that golden only. own pick of k: the method is given the first k goldens, keeps the one its own decision score likes best (the ground truth plays no part), and accepts or rejects that pose as usual: what a system that stores k goldens would get. best possible of k: share of test images for which at least one of the k goldens gives a correct pose (an upper bound no method can claim).

| method | golden 1 alone | golden 2 alone | golden 3 alone | own pick of 1: correct | own pick of 1: silent_wrong | own pick of 2: correct | own pick of 2: silent_wrong | own pick of 3: correct | own pick of 3: silent_wrong | best possible of 2 | best possible of 3 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| phase_correlation | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| sift_ransac | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| lightglue_disk | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| lightglue_sift | 0.025 | 0.000 | 0.000 | 0.025 | 0.075 | 0.025 | 0.100 | 0.025 | 0.100 | 0.025 | 0.025 |
| contour_shape_match | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| phase_correlation+rot | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| sift_ransac+rot | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| lightglue_disk+rot | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| lightglue_sift+rot | 0.050 | 0.000 | 0.025 | 0.050 | 0.075 | 0.050 | 0.075 | 0.075 | 0.075 | 0.050 | 0.075 |

## 5. Per group and method

| group | method | n_pairs | correct | silent_wrong | lost | rejected | no_pose | err_median_accepted_px | latency_median_ms |
|---|---|---|---|---|---|---|---|---|---|
| Full/000 | identity | 40 | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | 656.418 | 0.020 |
| Full/000 | phase_correlation | 40 | 0.000 | 0.000 | 0.000 | 1.000 | 0.000 |  | 13.332 |
| Full/000 | sift_ransac | 40 | 0.000 | 0.000 | 0.100 | 0.900 | 0.000 |  | 129.117 |
| Full/000 | lightglue_disk | 40 | 0.000 | 0.000 | 0.000 | 0.875 | 0.125 |  | 2363.355 |
| Full/000 | lightglue_sift | 40 | 0.025 | 0.075 | 0.075 | 0.650 | 0.175 | 9.606 | 790.782 |
| Full/000 | contour_shape_match | 40 | 0.000 | 0.000 | 0.125 | 0.875 | 0.000 |  | 3979.694 |
| Full/000 | phase_correlation+rot | 40 | 0.000 | 0.000 | 0.000 | 1.000 | 0.000 |  | 813.174 |
| Full/000 | sift_ransac+rot | 40 | 0.000 | 0.000 | 0.075 | 0.925 | 0.000 |  | 5002.953 |
| Full/000 | lightglue_disk+rot | 40 | 0.000 | 0.000 | 0.125 | 0.875 | 0.000 |  | 56206.682 |
| Full/000 | lightglue_sift+rot | 40 | 0.050 | 0.075 | 0.075 | 0.800 | 0.000 | 7.134 | 20249.801 |
| Full/001 | identity | 40 | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | 535.593 | 0.019 |
| Full/001 | phase_correlation | 40 | 0.000 | 0.000 | 0.000 | 1.000 | 0.000 |  | 13.284 |
| Full/001 | sift_ransac | 40 | 0.000 | 0.000 | 0.025 | 0.975 | 0.000 |  | 130.312 |
| Full/001 | lightglue_disk | 40 | 0.000 | 0.000 | 0.000 | 0.975 | 0.025 |  | 2367.232 |
| Full/001 | lightglue_sift | 40 | 0.000 | 0.025 | 0.050 | 0.800 | 0.125 | 10.955 | 790.231 |
| Full/001 | contour_shape_match | 40 | 0.000 | 0.000 | 0.100 | 0.900 | 0.000 |  | 3873.454 |
| Full/001 | phase_correlation+rot | 40 | 0.000 | 0.000 | 0.000 | 1.000 | 0.000 |  | 822.460 |
| Full/001 | sift_ransac+rot | 40 | 0.000 | 0.000 | 0.025 | 0.975 | 0.000 |  | 5044.820 |
| Full/001 | lightglue_disk+rot | 40 | 0.000 | 0.000 | 0.025 | 0.975 | 0.000 |  | 56161.982 |
| Full/001 | lightglue_sift+rot | 40 | 0.000 | 0.000 | 0.100 | 0.900 | 0.000 |  | 20311.588 |
| Full/002 | identity | 40 | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | 598.122 | 0.019 |
| Full/002 | phase_correlation | 40 | 0.000 | 0.000 | 0.000 | 1.000 | 0.000 |  | 13.317 |
| Full/002 | sift_ransac | 40 | 0.000 | 0.000 | 0.075 | 0.925 | 0.000 |  | 131.599 |
| Full/002 | lightglue_disk | 40 | 0.000 | 0.000 | 0.000 | 0.700 | 0.300 |  | 2355.902 |
| Full/002 | lightglue_sift | 40 | 0.000 | 0.025 | 0.050 | 0.825 | 0.100 | 11.926 | 795.777 |
| Full/002 | contour_shape_match | 40 | 0.000 | 0.000 | 0.100 | 0.900 | 0.000 |  | 3472.599 |
| Full/002 | phase_correlation+rot | 40 | 0.000 | 0.000 | 0.000 | 1.000 | 0.000 |  | 840.292 |
| Full/002 | sift_ransac+rot | 40 | 0.000 | 0.000 | 0.075 | 0.925 | 0.000 |  | 5077.078 |
| Full/002 | lightglue_disk+rot | 40 | 0.000 | 0.000 | 0.050 | 0.950 | 0.000 |  | 56196.185 |
| Full/002 | lightglue_sift+rot | 40 | 0.025 | 0.000 | 0.075 | 0.900 | 0.000 | 4.205 | 20336.899 |
